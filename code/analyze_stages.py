#!/usr/bin/env python3
"""Which search settings change Unicorn's candidate pool, and which only change the cut?

Every raw response names the ~100 candidates Unicorn retrieved (query_debug_info) and
the products the catalog actually returned. For each controlled comparison in the saved
experiments, this script holds the query constant, changes one setting, and measures:

  pool_shared   how many of Unicorn's candidates the two conditions share (of 100)
  output_shared how many returned products the two conditions share

Writes data/stage-analysis.json (--check compares instead). Standard library only;
archives are read in place and nothing inside them is executed.
"""
import collections
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/stage-analysis.json"


def key(path):
    parts = Path(path).parts
    return "/".join(parts[-2:])


# Index every raw response in the archives by its last two path components.
responses = {}
for archive in sorted((ROOT / "evidence").rglob("*.zip")):
    with zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            raw = z.read(member)
            if b"query_debug_info" not in raw:
                continue
            try:
                doc = json.loads(raw)
            except ValueError:
                continue
            found = []

            def walk(node):
                if isinstance(node, dict):
                    if "tool_responses" in node:
                        found.extend(node["tool_responses"])
                    else:
                        for value in node.values():
                            walk(value)
                elif isinstance(node, list):
                    for value in node:
                        walk(value)

            walk(doc)
            if len(found) != 1:
                continue
            response = found[0]
            metadata = json.loads(response["metadata"]) if isinstance(response["metadata"], str) else response["metadata"]
            responses[key(member)] = {
                "pools": [[str(i) for i in q["product_ids"]] for q in metadata["query_debug_info"]],
                "output": re.findall(r"<product_id>(.*?)</product_id>", response["result_content"]),
            }


def rows(name):
    return [json.loads(line) for line in (ROOT / "data" / name).read_text().splitlines() if line.strip()]


def settings(argv):
    """Everything except output-format and bookkeeping flags."""
    ignore_value = {"--conversation-id", "--out", "--retries", "--timeout-secs"}
    ignore_flag = {"--raw", "--json", "--stdout", "--no-save"}
    out, i = [], 1
    while i < len(argv):
        if argv[i] in ignore_value:
            i += 2
        elif argv[i] in ignore_flag:
            i += 1
        else:
            out.append(argv[i])
            i += 1
    return tuple(out)


runs = collections.defaultdict(list)
for name in ("catalog-runs.jsonl", "upstream-runs.jsonl", "query-multiplicity-runs.jsonl"):
    for row in rows(name):
        record = responses.get(key(row.get("source_path") or ""))
        if record and row.get("argv"):
            runs[settings(row["argv"])].append(record)
with zipfile.ZipFile(next((ROOT / "evidence/raw-tags-2026-09-27").glob("*.zip"))) as z:
    for member in z.namelist():
        if member.endswith("/execution.json"):
            argv = json.loads(z.read(member))["argv"]
            record = responses.get(key(member.replace("execution.json", "stdout.bin")))
            if record:
                runs[settings(argv)].append(record)
taste = json.loads((ROOT / "data/taste-study-runs.json").read_text())["runs"]
for run in taste:
    record = responses.get(key(run["source_path"]))
    if record:
        runs[("--query", run["query"], "-n", "50")].append(record)


def pool(setting):
    records = runs[setting]
    assert records, setting
    return records[0]["pools"][0], records[0]["output"]


def compare(label, base, changed):
    base_pool, base_out = pool(base)
    new_pool, new_out = pool(changed)
    return {
        "change": label,
        "baseline": " ".join(base),
        "changed": " ".join(changed),
        "pool_shared_of_100": len(set(base_pool) & set(new_pool)),
        "output_shared": len(set(base_out) & set(new_out)),
        "output_sizes": [len(base_out), len(new_out)],
    }


Q = lambda text, *rest: ("--query", text, *rest)
pan, bottle, purifier = "stainless steel frying pan", "32 oz stainless steel insulated water bottle", "small air purifier for a bedroom"
comparisons = [
    compare("--brand", Q(bottle, "-n", "50"), Q(bottle, "--brand", "Hydro Flask", "-n", "50")),
    compare("--color", Q(bottle, "-n", "50"), Q(bottle, "--color", "green", "-n", "50")),
    compare("--prefer-brand", Q(bottle, "-n", "50"), Q(bottle, "--prefer-brand", "Hydro Flask", "-n", "50")),
    compare("--brand", Q(pan, "-n", "50"), Q(pan, "--brand", "Misen", "-n", "50")),
    compare("--prefer-brand", Q(pan, "-n", "50"), Q(pan, "--prefer-brand", "Misen", "-n", "50")),
    compare("brand word in the query", Q(pan, "-n", "50"), Q("Misen " + pan, "-n", "50")),
    compare("-n 10 instead of 50", Q(purifier, "--brand", "Levoit", "-n", "50"), Q(purifier, "--brand", "Levoit", "-n", "10")),
    compare("-n 11 instead of 50", Q(pan, "--brand", "Misen", "-n", "50"), Q(pan, "--brand", "Misen", "-n", "11")),
    compare("\"Show me … .\" wording", Q("women's dresses", "-n", "50"), Q("Show me women's dresses.", "-n", "50")),
    compare("\"fashionable\" added", Q("women's dresses", "-n", "50"), Q("fashionable women's dresses", "-n", "50")),
]

# Repeats of identical settings: does the pool ever move while the output does?
repeat_groups = [recs for recs in runs.values() if len(recs) >= 2]
same_pool = sum(1 for recs in repeat_groups if len({tuple(map(tuple, r["pools"])) for r in recs}) == 1)
same_pool_output_moved = sum(
    1
    for recs in repeat_groups
    if len({tuple(map(tuple, r["pools"])) for r in recs}) == 1 and len({frozenset(r["output"]) for r in recs}) > 1
)

# Multiple --query flags: one Unicorn list per query, and the merge draws only from those lists.
A, B = Q(pan, "-n", "50"), Q("stainless steel skillet", "-n", "50")
AB = ("--query", pan, "--query", "stainless steel skillet", "-n", "50")
a_pool, a_out = pool(A)
b_pool, b_out = pool(B)
ab = runs[AB][0]
neither = set(ab["output"]) - set(a_out) - set(b_out)
multi_query = {
    "unicorn_lists_for_two_queries": len(ab["pools"]),
    "lists_identical_to_solo_searches": ab["pools"] == [a_pool, b_pool],
    "combined_output_within_union_of_lists": set(ab["output"]) <= set(a_pool) | set(b_pool),
    "union_of_lists": len(set(a_pool) | set(b_pool)),
    "returned_by_neither_solo_search": len(neither),
    "of_those_in_frying_pan_list": len(neither & set(a_pool)),
    "of_those_in_skillet_list": len(neither & set(b_pool)),
}

result = {
    "responses_indexed": len(responses),
    "setting_groups": len(runs),
    "comparisons": comparisons,
    "repeats": {
        "groups_with_2_or_more_runs": len(repeat_groups),
        "groups_with_identical_pool_every_run": same_pool,
        "of_those_output_still_changed": same_pool_output_moved,
    },
    "multiple_queries": multi_query,
}
text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
if "--check" in sys.argv[1:]:
    if OUT.read_text() != text:
        sys.exit(f"{OUT.relative_to(ROOT)} differs from a fresh recomputation")
    print(f"{OUT.relative_to(ROOT)} matches a fresh recomputation")
else:
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
