#!/usr/bin/env python3
"""Check this repository: fingerprints, archives, recomputed numbers and links.

    python3 code/check.py                   # verify everything
    python3 code/check.py --write-manifest  # rewrite MANIFEST.sha256 after an intentional change

1. Every file matches its SHA-256 in MANIFEST.sha256, and no file is missing or unlisted.
2. Every ZIP archive passes its CRC check, matches evidence/REDACTIONS.json, and has no
   unblanked request handle left in it.
3. data/raw-tags-analysis.json, data/unicorn-debug-analysis.json and data/stage-analysis.json
   match a fresh recomputation from the archives.
4. The experiment totals in the report's "How this report works" table recompute from data/.
5. Every relative link in every Markdown file points to a file that exists.

Standard library only; nothing inside the evidence archives is executed.
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"
failures = []


def fail(message):
    failures.append(message)
    print(f"FAIL  {message}")


def ok(message):
    print(f"ok    {message}")


def tracked_files():
    return sorted(
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(ROOT).parts and "__pycache__" not in p.parts and p != MANIFEST and p.name != ".DS_Store"
    )


def digest(path):
    h = hashlib.sha256()
    with open(ROOT / path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if "--write-manifest" in sys.argv[1:]:
    files = tracked_files()
    MANIFEST.write_text("".join(f"{digest(p)}  {p}\n" for p in files))
    print(f"wrote {MANIFEST.name} with {len(files)} files")
    sys.exit(0)

# 1. fingerprints
listed = {}
for line in MANIFEST.read_text().splitlines():
    sha, path = line.split("  ", 1)
    listed[path] = sha
present = set(tracked_files())
for path in sorted(set(listed) - present):
    fail(f"missing file: {path}")
for path in sorted(present - set(listed)):
    fail(f"file not in {MANIFEST.name}: {path}")
bad = [p for p in sorted(present & set(listed)) if digest(p) != listed[p]]
for path in bad:
    fail(f"fingerprint mismatch: {path}")
if not bad:
    ok(f"{len(present & set(listed))} files match {MANIFEST.name}")

# 2. archives
zips = sorted(p for p in present if p.endswith(".zip"))
broken = []
handle = re.compile(rb"baseRequestHandle=(?!REDACTED)")
unblanked = []
for path in zips:
    with zipfile.ZipFile(ROOT / path) as z:
        if z.testzip() is not None:
            broken.append(path)
        if any(handle.search(z.read(name)) for name in z.namelist()):
            unblanked.append(path)
for path in broken:
    fail(f"ZIP CRC failed: {path}")
for path in unblanked:
    fail(f"unblanked request handle in {path}")
if not broken and not unblanked:
    ok(f"{len(zips)} ZIP archives pass their CRC check; no request handle left unblanked")

log = json.loads((ROOT / "evidence/REDACTIONS.json").read_text())
logged = {"evidence/" + e["archive"]: e for e in log["entries"]}
mismatch = [p for p in zips if p not in logged or digest(p) != (logged[p]["redacted_sha256"] or logged[p]["original_sha256"])]
mismatch += [p for p in logged if p not in zips]
for path in mismatch:
    fail(f"archive does not match evidence/REDACTIONS.json: {path}")
if not mismatch:
    ok(f"{len(zips)} archives match evidence/REDACTIONS.json ({log['handles_redacted']} handles blanked in {log['archives_changed']})")

# 3. recomputations
for script in ("analyze_raw_tags.py", "analyze_unicorn.py", "analyze_stages.py"):
    run = subprocess.run([sys.executable, str(ROOT / "code" / script), "--check"], capture_output=True, text=True)
    (ok if run.returncode == 0 else fail)((run.stdout or run.stderr).strip())

# 4. experiment totals (report: "How this report works")
data = ROOT / "data"
jsonl = lambda name: [json.loads(line) for line in (data / name).read_text().splitlines() if line.strip()]
catalog = [r for r in jsonl("catalog-runs.jsonl") if r["output_kind"] != "metadata_text"]
upstream = jsonl("upstream-runs.jsonl")
combined = jsonl("query-multiplicity-runs.jsonl")
panel = json.loads((data / "merchant-benchmark-2026-09-27.json").read_text())
taste = json.loads((data / "taste-study-summary.json").read_text())
cases = json.loads((data / "ranking-math-2026-09-27.json").read_text())["shopping_cases"]
totals = {
    "Early catalog runs": ((len(catalog), sum(r["product_count"] for r in catalog)), (182, 6314)),
    "Brand and color tests": ((len(upstream), sum(r["product_count"] for r in upstream)), (27, 1200)),
    "Combined-search tests": ((len(combined), sum(r["product_count"] for r in combined)), (21, 1104)),
    "Broad store panel": ((panel["successful_calls"], panel["returned_occurrences"], panel["distinct_product_ids"]), (100, 4088, 3827)),
    "Fashion wording study": ((taste["calls"], taste["record_occurrences"], taste["unique_product_ids"]), (72, 3827, 1125)),
    "Home-goods shopping tasks": ((len(cases), sum(c["catalog_records"] for c in cases), sum(c["displayed_cards"] for c in cases)), (5, 270, 14)),
}
for label, (actual, printed) in totals.items():
    (ok if actual == printed else fail)(f"{label}: {actual} (report: {printed})")

# 5. links
link = re.compile(r"\]\(([^)\s]+)\)")
dead = []
for md in sorted(p for p in present if p.endswith(".md")):
    for target in link.findall((ROOT / md).read_text()):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        if path and not ((ROOT / md).parent / path).exists():
            dead.append(f"{md} -> {target}")
for entry in dead:
    fail(f"broken link: {entry}")
if not dead:
    ok("all relative Markdown links resolve")

print(f"\n{'FAILED' if failures else 'PASSED'}: {len(failures)} problem(s)")
sys.exit(1 if failures else 0)
