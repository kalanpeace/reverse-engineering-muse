#!/usr/bin/env python3
"""Blank the account id and access token in the muse.ai file-share links in the chat.

    python3 code/redact_share_links.py --export <Meta export folder>

In the chat, Muse shares files it made with links of the form

    https://muse.ai/files/<account id>/<file id>/<24-character token>/<file name>

Anyone holding the token can download the file without signing in. This script keeps the
domain, the file id and the file name and replaces the account id and the token with
REDACTED. It changes nothing else: every other byte, and every line break, stays as the
export has it, so line numbers in the transcript are the same as in the original.

Inputs, from the unzipped Meta export ("EYI Package_…"):
    Conversation with Muse AI_<date>_<id>.txt  ->  transcript/muse-chat-2026-09-28.txt
    manifest.json                              ->  transcript/muse-chat-2026-09-28.manifest.json

It also writes evidence/TRANSCRIPT-REDACTIONS.json: for each file, the SHA-256 before and
after and the number of links blanked. The unredacted export is held privately; these
fingerprints let anyone holding it confirm the match. Standard library only.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(rb"(https://muse\.ai/files/)[0-9]+(/[0-9]+/)[a-z0-9]{24}(/)")
LEFTOVER = re.compile(rb"muse\.ai/files/(?!REDACTED/[0-9]+/REDACTED/)")

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--export", type=Path, required=True, help="unzipped Meta export folder")
parser.add_argument("--out", type=Path, default=ROOT / "transcript", help="folder for the redacted transcript files")
parser.add_argument("--log", type=Path, default=ROOT / "evidence" / "TRANSCRIPT-REDACTIONS.json", help="redaction log to write")
args = parser.parse_args()

chats = sorted(args.export.glob("Conversation with Muse AI_*.txt"))
if len(chats) != 1:
    raise SystemExit(f"expected one 'Conversation with Muse AI_*.txt' in {args.export}, found {len(chats)}")
pairs = [
    (chats[0], "muse-chat-2026-09-28.txt"),
    (args.export / "manifest.json", "muse-chat-2026-09-28.manifest.json"),
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


entries = []
for source, name in pairs:
    original = source.read_bytes()
    redacted, count = LINK.subn(rb"\1REDACTED\2REDACTED\3", original)
    if LEFTOVER.search(redacted):
        raise SystemExit(f"unrecognized share-link format in {source.name}")
    if redacted.count(b"\n") != original.count(b"\n"):
        raise SystemExit(f"line count changed in {source.name}")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / name).write_bytes(redacted)
    entries.append(
        {
            "file": f"transcript/{name}",
            "original_name": source.name,
            "original_sha256": sha256(original),
            "original_bytes": len(original),
            "redacted_sha256": sha256(redacted),
            "links_redacted": count,
        }
    )
    print(f"{count:4d} links  {name}")

log = {
    "what": "account id and access token in muse.ai/files share links replaced with REDACTED; domain, file id and file name kept; nothing else changed",
    "files": entries,
}
args.log.parent.mkdir(parents=True, exist_ok=True)
args.log.write_text(json.dumps(log, indent=2) + "\n")
