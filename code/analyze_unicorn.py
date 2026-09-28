#!/usr/bin/env python3
"""Analyze the hidden query_debug_info field and write data/unicorn-debug-analysis.json.

Every raw catalog response carries tool_responses[].metadata.query_debug_info: a link
to Meta's internal Unicorn query page (with the tier name), a product_count, and a list
of product_ids. This script reads every raw response saved in evidence/ (in place,
nothing extracted or executed) and measures how the printed product list relates to
that debug list and to the response's flywheel_identifiers list. With --check it
compares against the existing JSON instead of writing it. Standard library only.
"""
import collections
import json
import re
import statistics
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/unicorn-debug-analysis.json"
TIER = re.compile(r"^unicorn\.aggregator\.alacorn-genai-synapse-products\.211\.([a-z]+)\.s00\.r(\d+)-prod$")


def tool_responses(raw):
    try:
        doc = json.loads(raw)
    except ValueError:
        return []
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
    return found


def kendall_tau(ranks):
    concordant = discordant = 0
    for i in range(len(ranks)):
        for j in range(i + 1, len(ranks)):
            concordant += ranks[i] < ranks[j]
            discordant += ranks[i] > ranks[j]
    return (concordant - discordant) / (concordant + discordant) if concordant + discordant else None


calls = []
for archive in sorted((ROOT / "evidence").rglob("*.zip")):
    with zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            raw = z.read(member)
            if b"query_debug_info" not in raw:
                continue
            for response in tool_responses(raw):
                metadata = response.get("metadata")
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                debug = (metadata or {}).get("query_debug_info") or []
                if not debug:
                    continue
                printed = re.findall(r"<product_id>(.*?)</product_id>", response.get("result_content") or "")
                flywheel = [str(f["fbid"]) for f in response.get("flywheel_identifiers") or []]
                calls.append({"archive": archive.relative_to(ROOT).as_posix(), "member": member, "debug": debug, "printed": printed, "flywheel": flywheel})

links = [entry for call in calls for entry in call["debug"]]
sites, replicas, handles = collections.Counter(), collections.Counter(), collections.Counter()
for entry in links:
    link = entry["uqc_link"]
    assert link.startswith("https://www.internalfb.com/unicorn/query?tier="), link
    tier = re.search(r"tier=([^&]+)", link).group(1)
    match = TIER.match(tier)
    assert match, tier
    sites[match.group(1)] += 1
    replicas[f"{match.group(1)}.r{match.group(2)}"] += 1
    handles[re.search(r"baseRequestHandle=([^&]+)", link).group(1)] += 1

single = [c for c in calls if len(c["debug"]) == 1 and c["printed"]]
subset = order_kept = outside = 0
for call in single:
    ids = [str(i) for i in call["debug"][0]["product_ids"]]
    position = {pid: k for k, pid in enumerate(ids)}
    inside = [position[p] for p in call["printed"] if p in position]
    outside += len(call["printed"]) - len(inside)
    subset += len(inside) == len(call["printed"])
    order_kept += inside == sorted(inside)

full = [c for c in single if len(c["debug"][0]["product_ids"]) == 100]
taus, sizes = [], []
kept, seen = collections.Counter(), collections.Counter()
for call in full:
    ids = [str(i) for i in call["debug"][0]["product_ids"]]
    position = {pid: k for k, pid in enumerate(ids)}
    tau = kendall_tau([position[p] for p in call["printed"]])
    if tau is not None:
        taus.append(tau)
    sizes.append(len(call["printed"]))
    printed = set(call["printed"])
    for k, pid in enumerate(ids):
        seen[k // 10] += 1
        kept[k // 10] += pid in printed

empty_with_list = sum(1 for c in calls if not c["printed"] and any(e["product_ids"] for e in c["debug"]))

# Raw-tags run: same query, three repeats. Did the printed list change while the debug list did not?
repeats = collections.defaultdict(list)
for call in calls:
    if "raw-tags" in call["archive"]:
        run_id = call["member"].split("/")[1]
        arm, rep, q = run_id.split("-")
        repeats[(arm, q)].append((rep, tuple(call["debug"][0]["product_ids"]), frozenset(call["printed"]), call["debug"][0]["uqc_link"]))
same_list_changed_output = []
for (arm, q), runs in sorted(repeats.items()):
    lists = {r[1] for r in runs}
    outputs = {r[2] for r in runs}
    if len(lists) == 1 and len(outputs) > 1:
        same_list_changed_output.append(f"{arm}-{q}")
raw_tags_sites = collections.Counter(TIER.match(re.search(r"tier=([^&]+)", r[3]).group(1)).group(1) for runs in repeats.values() for r in runs)

# The Quince record from Finding 1 (neutral_baseline/ncap-n50-run2).
neutral = next(c for c in calls if c["member"].endswith("ncap-n50-run2.raw.txt"))
quince_index = [str(i) for i in neutral["debug"][0]["product_ids"]].index("25671310895791560")

# Three nested lists: Unicorn's candidates ⊇ flywheel_identifiers ⊇ returned products.
with_flywheel = [c for c in single if c["flywheel"]]


def quartiles(values):
    q = statistics.quantiles(values, n=4)
    return {"q1": q[0], "median": statistics.median(values), "q3": q[2]}


three = [c for c in with_flywheel if len(c["debug"][0]["product_ids"]) == 100]
flywheel_result = {
    "responses_with_empty_flywheel": sum(1 for c in calls if not c["flywheel"]),
    "of_those_returning_no_products": sum(1 for c in calls if not c["flywheel"] and not c["printed"]),
    "single_search_calls_with_products": len(single),
    "of_those_with_flywheel_list": len(with_flywheel),
    "returned_within_flywheel": sum(set(c["printed"]) <= set(c["flywheel"]) for c in with_flywheel),
    "flywheel_within_unicorn_list": sum(set(c["flywheel"]) <= {str(i) for i in c["debug"][0]["product_ids"]} for c in with_flywheel),
    "flywheel_order_same_as_unicorn_order": sum(
        (lambda pos: [pos[f] for f in c["flywheel"]] == sorted(pos[f] for f in c["flywheel"]))({str(i): k for k, i in enumerate(c["debug"][0]["product_ids"])})
        for c in with_flywheel
    ),
    "flywheel_starts_with_returned_in_order": sum(c["flywheel"][: len(c["printed"])] == c["printed"] for c in with_flywheel),
    "sizes_when_unicorn_list_is_100": {
        "calls": len(three),
        "flywheel": quartiles([len(set(c["flywheel"])) for c in three]),
        "returned": quartiles([len(c["printed"]) for c in three]),
        "flywheel_max": max(len(set(c["flywheel"])) for c in three),
        "flywheel_exactly_80": sum(len(set(c["flywheel"])) == 80 for c in three),
        "pairs_flywheel_returned": sorted([len(set(c["flywheel"])), len(c["printed"])] for c in three),
    },
}

result = {
    "raw_responses_with_debug_info": len(calls),
    "debug_links": len(links),
    "tier_template": "unicorn.aggregator.alacorn-genai-synapse-products.211.<site>.s00.r<replica>-prod",
    "links_by_site": dict(sites.most_common()),
    "links_by_site_and_replica": dict(sorted(replicas.items())),
    "request_handles": dict(handles),
    "debug_product_count": dict(collections.Counter(e["product_count"] for e in links).most_common()),
    "single_search_calls_with_printed_products": {
        "calls": len(single),
        "all_printed_products_in_debug_list": subset,
        "printed_products_not_in_debug_list": outside,
        "printed_order_same_as_debug_order": order_kept,
    },
    "calls_with_100_debug_ids": {
        "calls": len(full),
        "printed_products": {"min": min(sizes), "median": statistics.median(sizes), "max": max(sizes)},
        "kendall_tau_printed_vs_debug_order": {"median": round(statistics.median(taus), 3), "min": min(taus), "max": max(taus)},
        "share_kept_by_debug_position_block_of_10": [round(kept[d] / seen[d], 3) for d in range(10)],
    },
    "empty_printed_lists_with_debug_ids": empty_with_list,
    "raw_tags": {
        "links_by_site": dict(raw_tags_sites),
        "searches_with_identical_debug_list_but_changed_printed_list": same_list_changed_output,
    },
    "quince_neutral_run": {"printed_position": 41, "debug_list_index_zero_based": quince_index},
    "flywheel": flywheel_result,
}
text = json.dumps(result, indent=2) + "\n"
if "--check" in sys.argv[1:]:
    if OUT.read_text() != text:
        sys.exit(f"{OUT.relative_to(ROOT)} differs from a fresh recomputation")
    print(f"{OUT.relative_to(ROOT)} matches a fresh recomputation")
else:
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
