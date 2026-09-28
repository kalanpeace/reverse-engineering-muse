#!/usr/bin/env python3
"""Blank the request handles inside Meta's internal debug links.

    python3 code/redact_request_handles.py --originals <dir> --out evidence

Muse's raw catalog responses include a debug link of the form

    https://www.internalfb.com/unicorn/query?tier=<tier name>&baseRequestHandle=flat/nobody-<32 hex>

This script keeps the domain, path and tier name and replaces each handle value with
REDACTED. It walks every ZIP under --originals, rewrites only the archive members that
contain a handle, and copies every other member byte for byte with its original name,
timestamp and compression. Archives without handles are copied unchanged.

It also leaves out the members named in REMOVE_MEMBERS below. That is Muse's listing of a
whole function of the catalog program (26,925 bytes, every instruction with its bytes);
this repository publishes only four small pieces of the program.

It writes evidence/REDACTIONS.json: for every archive and every changed member, the
SHA-256 before and after, and the number of handles blanked; for every removed member,
its name and original SHA-256. The unredacted originals are held privately; their
fingerprints here let anyone holding them confirm the match.
Standard library only; nothing inside the archives is executed.
"""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

HANDLE = re.compile(rb"(baseRequestHandle=)flat/nobody-[0-9A-F]{32}")
LEFTOVER = re.compile(rb"baseRequestHandle=(?!REDACTED)")
REMOVE_MEMBERS = {
    "catalog-runs/ordering-evidence-2026-09-26.zip": ["ordering-evidence-2026-09-26/stdout-search/caller-region.txt"],
}

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--originals", type=Path, required=True, help="directory holding the unredacted evidence archives")
parser.add_argument("--out", type=Path, required=True, help="evidence directory to write redacted copies into")
args = parser.parse_args()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


log = []
for source in sorted(args.originals.rglob("*.zip")):
    rel = source.relative_to(args.originals)
    target = args.out / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    changed, removed, total = [], [], 0
    drop = set(REMOVE_MEMBERS.get(rel.as_posix(), []))
    with zipfile.ZipFile(source) as zin:
        members = [(info, zin.read(info.filename)) for info in zin.infolist()]
    if drop - {info.filename for info, _ in members}:
        raise SystemExit(f"member to remove not found in {rel}: {sorted(drop)}")
    rewritten = []
    for info, data in members:
        if info.filename in drop:
            removed.append({"member": info.filename, "original_sha256": sha256(data)})
            continue
        new, count = HANDLE.subn(rb"\1REDACTED", data)
        if LEFTOVER.search(new):
            raise SystemExit(f"unrecognized handle format in {rel}:{info.filename}")
        if count:
            total += count
            changed.append({"member": info.filename, "handles": count, "original_sha256": sha256(data), "redacted_sha256": sha256(new)})
        rewritten.append((info, new))
    if not total and not removed:
        shutil.copyfile(source, target)
    else:
        with zipfile.ZipFile(target, "w") as zout:
            for info, data in rewritten:
                zout.writestr(info, data, compress_type=info.compress_type)
        with zipfile.ZipFile(target) as check:
            if check.testzip() is not None:
                raise SystemExit(f"CRC failure after rewriting {rel}")
    original = source.read_bytes()
    written = target.read_bytes()
    log.append(
        {
            "archive": rel.as_posix(),
            "original_sha256": sha256(original),
            "original_bytes": len(original),
            "redacted_sha256": sha256(written) if total or removed else None,
            "handles_redacted": total,
            "members_changed": changed,
            "members_removed": removed,
        }
    )
    print(f"{total:4d} handles  {len(removed)} removed  {rel}")

summary = {
    "what": "baseRequestHandle values in internalfb.com/unicorn/query debug links replaced with REDACTED; domain, path and tier name kept. Members listed under members_removed were left out of the public copy.",
    "archives": len(log),
    "archives_changed": sum(1 for entry in log if entry["handles_redacted"] or entry["members_removed"]),
    "handles_redacted": sum(entry["handles_redacted"] for entry in log),
    "members_removed": sum(len(entry["members_removed"]) for entry in log),
    "entries": log,
}
(args.out / "REDACTIONS.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"{summary['handles_redacted']} handles blanked and {summary['members_removed']} member(s) removed in {summary['archives_changed']} of {summary['archives']} archives")
