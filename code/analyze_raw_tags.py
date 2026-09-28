#!/usr/bin/env python3
"""Analyze the Part 5 raw-tags collection and write data/raw-tags-analysis.json.

Input: evidence/raw-tags-2026-09-27/raw-tags-20260927T234719067674Z.zip, read in place
(nothing is extracted to disk and nothing inside the archive is executed).

The public archive has its request handles blanked (see evidence/REDACTIONS.json).
Unchanged members are checked against the archive's own MANIFEST.csv; each redacted
member is checked against the original hash in MANIFEST.csv and the redacted hash in
the redaction log. Redaction touches only the debug link, never a product or score.

Every count the report prints for this experiment is recomputed here and checked
against the printed value; the script stops if the data and the report disagree.
With --check it compares against the existing JSON instead of writing it.
Standard library only.
"""
import collections
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "evidence/raw-tags-2026-09-27/raw-tags-20260927T234719067674Z.zip"
ORIGINAL_SHA256 = "d0fec8cf6ad6c668b3c0f7e988281158e20dfe5da5aef0aa0ef36f95e1a521aa"
OUT = ROOT / "data/raw-tags-analysis.json"


def expect(label, actual, printed):
    if actual != printed:
        sys.exit(f"{label}: data gives {actual!r}, report prints {printed!r}")


def mean(values):
    return sum(values) / len(values)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------ integrity
archive_bytes = ARCHIVE.read_bytes()
redactions = json.loads((ROOT / "evidence/REDACTIONS.json").read_text())
redaction = next(e for e in redactions["entries"] if e["archive"] == ARCHIVE.relative_to(ROOT / "evidence").as_posix())
expect("original archive SHA-256 in the redaction log", redaction["original_sha256"], ORIGINAL_SHA256)
expect("redacted archive SHA-256", sha256(archive_bytes), redaction["redacted_sha256"])
redacted = {m["member"]: m for m in redaction["members_changed"]}
with zipfile.ZipFile(ARCHIVE) as z:
    expect("ZIP CRC check", z.testzip(), None)
    names = [n for n in z.namelist() if not n.endswith("/")]
    prefix = names[0].split("/")[0] + "/"
    manifest = list(csvrow.split(",") for csvrow in z.read(prefix + "MANIFEST.csv").decode().splitlines()[1:])
    for path, size, digest in manifest:
        data = z.read(prefix + path)
        change = redacted.get(prefix + path)
        if change:
            ok = change["original_sha256"] == digest and change["redacted_sha256"] == sha256(data)
        else:
            ok = len(data) == int(size) and sha256(data) == digest
        if not ok:
            sys.exit(f"manifest mismatch: {path}")
    expect("files checked against the manifest", len(manifest), 148)
    expect("members with a blanked request handle", len(redacted), 48)
    schedule = json.loads(z.read(prefix + "schedule.json"))
    identity = json.loads(z.read(prefix + "tool-identity.json"))
    runs, executions = {}, {}
    for entry in schedule:
        rid = entry["run_id"]
        executions[rid] = json.loads(z.read(f"{prefix}{rid}/execution.json"))
        runs[rid] = json.loads(z.read(f"{prefix}{rid}/stdout.bin"))

expect("searches", len(runs), 48)
expect("exit codes", {e["exit_code"] for e in executions.values()}, {0})


# ------------------------------------------------------------ parse products
def parse(response):
    products = []
    for block in re.findall(r"<PRODUCT>(.*?)</PRODUCT>", response["result_content"], re.S):
        field = lambda tag: (m.group(1) if (m := re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)) else None)
        products.append(
            {
                "product_id": field("product_id"),
                "name": field("name"),
                "brand": field("brand"),
                "seller_quality": field("seller_quality"),
                "ranking_score": field("ranking_score"),
                "is_native_commerce": field("is_native_commerce") == "true",
                "shopify_product_id": field("shopify_product_id") is not None,
                "host": re.sub(r"^https?://(www\.)?", "", field("url")).split("/")[0],
            }
        )
    return products


lists, flywheel_complete = {}, 0
for rid, doc in runs.items():
    responses = doc["tool_responses"]
    assert len(responses) == 1
    response = responses[0]
    expect(f"{rid} success field", response["success"], True)
    products = parse(response)
    fbids = {str(f["fbid"]) for f in response.get("flywheel_identifiers") or []}
    flywheel_complete += bool(products) and {p["product_id"] for p in products} <= fbids
    lists[rid] = products

records = [p for products in lists.values() for p in products]
expect("product records", len(records), 2542)
quality = collections.Counter(p["seller_quality"] for p in records)
expect("seller_quality counts", dict(quality), {"good": 2103, "elite": 401, "acceptable": 33, "poor": 5})
shopify = sum(p["shopify_product_id"] for p in records)
expect("records with shopify_product_id", shopify, 2241)
expect("responses whose flywheel_identifiers include every product ID", flywheel_complete, 48)
expect("program fingerprint", (identity["before"]["sha256"][:8], identity["before"]["bytes"]), ("eb99783b", 11532776))
expect("program unchanged during the run", identity["before"]["sha256"], identity["after"]["sha256"])

queries = collections.OrderedDict()
for entry in schedule:
    arm, rep, q = entry["run_id"].split("-")
    queries.setdefault((arm, q), {"query": entry["query"], "repeats": {}})["repeats"][int(rep[1:])] = entry["run_id"]


def score(p):
    return float(p["ranking_score"])


# ------------------------------------------------------------ stability (Test result 5)
same_products = 0
repeated_scores = unchanged_scores = 0
for (arm, q), info in queries.items():
    sets = [frozenset(p["product_id"] for p in lists[rid]) for rid in info["repeats"].values()]
    same_products += len(set(sets)) == 1
    first = {p["product_id"]: p["ranking_score"] for p in lists[info["repeats"][1]]}
    for rep in (2, 3):
        for p in lists[info["repeats"][rep]]:
            if p["product_id"] in first:
                repeated_scores += 1
                unchanged_scores += p["ranking_score"] == first[p["product_id"]]
expect("searches whose three repeats returned identical products", (same_products, len(queries)), (9, 16))

# ------------------------------------------------------------ elite vs good, native checkout (Test result 2), repeat 1
categories = []
for (arm, q), info in queries.items():
    if arm != "A":
        continue
    products = lists[info["repeats"][1]]
    elite = [score(p) for p in products if p["seller_quality"] == "elite"]
    good = [score(p) for p in products if p["seller_quality"] == "good"]
    native = [score(p) for p in products if p["is_native_commerce"]]
    other = [score(p) for p in products if not p["is_native_commerce"]]
    categories.append(
        {
            "query": info["query"],
            "run_id": info["repeats"][1],
            "elite_records": len(elite),
            "good_records": len(good),
            "elite_minus_good_mean_score": round(mean(elite) - mean(good), 6),
            "native_records": len(native),
            "non_native_records": len(other),
            "native_minus_non_native_mean_score": round(mean(native) - mean(other), 6),
        }
    )
gaps = [c["elite_minus_good_mean_score"] for c in categories]
expect("categories where elite averaged higher", sum(g > 0 for g in gaps), 8)
expect("elite-minus-good range", (round(min(gaps), 3), round(max(gaps), 3)), (-0.027, 0.061))
expect("categories where native checkout averaged lower", sum(c["native_minus_non_native_mean_score"] < 0 for c in categories), 10)


# ------------------------------------------------------------ same product, different store (Test result 3)
def listing(run_id, name_part, host):
    hits = [p for p in lists[run_id] if name_part.lower() in (p["name"] or "").lower() and p["host"] == host]
    best = max(hits, key=score)
    return {"host": best["host"], "seller_quality": best["seller_quality"], "ranking_score": best["ranking_score"], "name": best["name"]}


seller_pairs = []
for label, run_id, name_part, low_host, high_host, printed in (
    ("Moccamaster KM5 burr grinder", "A-R1-Q09", "Moccamaster KM5", "readingcoffee.com", "juliancoffee.com", ("0.550781", "0.710938")),
    ("Baratza Encore grinder", "A-R1-Q09", "Baratza Encore Grinder", "treelinecoffee.com", "pegasuscoffee.com", ("0.593750", "0.683594")),
    ("Vitamix Explorian E310, black", "B-R1-Q03", "Explorian E310 Blender - Black", "bestbuy.com", "flexshopper.com", ("0.746094", "0.792969")),
):
    low, high = listing(run_id, name_part, low_host), listing(run_id, name_part, high_host)
    expect(f"{label} scores", (low["ranking_score"], high["ranking_score"]), printed)
    seller_pairs.append({"product": label, "run_id": run_id, "lower": low, "higher": high})

# ------------------------------------------------------------ the tail after the score jump (Test result 4), repeat 1
tail = {"lists_with_jump": [], "before": collections.Counter(), "after": collections.Counter()}
for (arm, q), info in queries.items():
    rid = info["repeats"][1]
    scores = [score(p) for p in lists[rid]]
    jumps = [i for i in range(1, len(scores)) if scores[i] > scores[i - 1]]
    if not jumps:
        continue
    tail["lists_with_jump"].append({"run_id": rid, "query": info["query"], "first_jump_position": jumps[0] + 1, "list_length": len(scores)})
    tail["before"].update("native" if p["is_native_commerce"] else "non_native" for p in lists[rid][: jumps[0]])
    tail["after"].update("native" if p["is_native_commerce"] else "non_native" for p in lists[rid][jumps[0]:])
by_arm = collections.Counter(j["run_id"][0] for j in tail["lists_with_jump"])
expect("category / product lists with a jump", (by_arm["A"], by_arm["B"]), (4, 3))
expect("before the jump (native, non-native)", (tail["before"]["native"], tail["before"]["non_native"]), (137, 169))
expect("after the jump (native, non-native)", (tail["after"]["native"], tail["after"]["non_native"]), (0, 16))

pan = lists[queries[("A", "Q01")]["repeats"][1]]
quince = next(i for i, p in enumerate(pan) if p["brand"] == "Quince")
expect("Quince in the raw-tags pan list", (quince + 1, pan[quince]["ranking_score"], pan[quince - 1]["ranking_score"]), (40, "0.765625", "0.546875"))

result = {
    "archive": {
        "path": str(ARCHIVE.relative_to(ROOT)),
        "original_sha256": ORIGINAL_SHA256,
        "redacted_sha256": redaction["redacted_sha256"],
        "manifest_files_verified": len(manifest),
        "members_with_blanked_request_handle": len(redacted),
    },
    "program": {"sha256": identity["before"]["sha256"], "bytes": identity["before"]["bytes"]},
    "searches": len(runs),
    "product_records": len(records),
    "seller_quality_counts": dict(quality.most_common()),
    "records_with_shopify_product_id": shopify,
    "responses_with_complete_flywheel_identifiers": flywheel_complete,
    "stability": {
        "searches": len(queries),
        "searches_with_identical_products_in_all_three_repeats": same_products,
        "repeated_product_scores_compared": repeated_scores,
        "repeated_product_scores_unchanged": unchanged_scores,
    },
    "elite_and_native_by_category_repeat_1": categories,
    "same_product_different_store": seller_pairs,
    "tail_after_first_score_jump_repeat_1": {
        "lists_with_jump": tail["lists_with_jump"],
        "before_jump": dict(tail["before"]),
        "after_jump": dict(tail["after"]),
    },
    "quince_in_pan_list_repeat_1": {"position": quince + 1, "ranking_score": pan[quince]["ranking_score"], "previous_ranking_score": pan[quince - 1]["ranking_score"], "previous_brand": pan[quince - 1]["brand"]},
}
text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
if "--check" in sys.argv[1:]:
    if OUT.read_text() != text:
        sys.exit(f"{OUT.relative_to(ROOT)} differs from a fresh recomputation")
    print(f"{OUT.relative_to(ROOT)} matches a fresh recomputation")
else:
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
