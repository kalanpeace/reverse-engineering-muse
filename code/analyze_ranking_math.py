from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
from collections import defaultdict
from itertools import combinations
import argparse
import hashlib
import json


def load_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def score(product):
    value = product.get("ranking_score")
    return Decimal(value) if value is not None else None


def order_statistics(products):
    values = [score(p) for p in products]
    adjacent = [(a, b) for a, b in zip(values, values[1:]) if a is not None and b is not None]
    pairs = [(a, b) for a, b in combinations(values, 2) if a is not None and b is not None]
    return {"records": len(values), "adjacent_pairs": len(adjacent),
            "adjacent_upturns": sum(a < b for a, b in adjacent),
            "all_pairs": len(pairs), "discordant_pairs": sum(a < b for a, b in pairs),
            "tied_pairs": sum(a == b for a, b in pairs)}


def compact(product):
    return {key: product[key] for key in ("product_id", "position", "ranking_score", "url_host")}


def run_map(run):
    return {p["product_id"]: p for p in run["products"]}


def build(repo):
    data = repo / "data"
    names = ["catalog-runs.jsonl", "upstream-runs.jsonl", "query-multiplicity-runs.jsonl",
             "merchant-benchmark-2026-09-27.json", "tie-audit.json", "resolver-audit.json"]
    sources = [{"path": "data/" + n, "sha256": hashlib.sha256((data / n).read_bytes()).hexdigest()} for n in names]
    baseline = load_lines(data / names[0])
    upstream = load_lines(data / names[1])
    multi = load_lines(data / names[2])
    merchant = json.loads((data / names[3]).read_text())
    eligible = [r for r in baseline if len(r["products"]) >= 3 and all(score(p) is not None for p in r["products"])]
    stats = [dict(run_id=r["run_id"], **order_statistics(r["products"])) for r in eligible]
    neutral = next(r for r in baseline if r["cohort"] == "neutral_baseline")
    quince = next(p for p in neutral["products"] if p["product_id"] == "25671310895791560")
    qscore = score(quince)
    neutral_result = {"run_id": neutral["run_id"], "products": [compact(p) for p in neutral["products"]],
                      "quince_score_only_rank_range": [1 + sum(score(p) > qscore for p in neutral["products"]),
                                                       sum(score(p) >= qscore for p in neutral["products"])],
                      "position_40_to_41_delta": str(qscore - score(neutral["products"][39]))}
    strong = []
    for r in baseline:
        if r["cohort"] != "brand63" or r["condition"] not in ("C2", "C5"):
            continue
        domain = r["domain"]
        own = lambda p: p["url_host"] == domain or p["url_host"].endswith("." + domain)
        rows = r["products"]
        prefix = next((i for i, p in enumerate(rows) if not own(p)), len(rows))
        contiguous = prefix > 0 and not any(own(p) for p in rows[prefix:])
        boundary = 0 < prefix < len(rows) and score(rows[prefix]) > score(rows[prefix - 1])
        within = order_statistics(rows[:prefix])["adjacent_upturns"] + order_statistics(rows[prefix:])["adjacent_upturns"]
        strong.append({"run_id": r["run_id"], "case": r["case"], "condition": r["condition"],
                       "prefix": prefix, "contiguous_own_prefix": contiguous,
                       "boundary_upturn": boundary, "group_then_score_fails": bool(within)})
    levoit = next(r for r in baseline if r["cohort"] == "brand63" and r["case"] == "L" and r["condition"] == "C2")
    tie_groups = defaultdict(list)
    for r in baseline:
        if r["cohort"] in ("brand63", "misen21"):
            tie_groups[(r["cohort"], tuple(r["argv"]))].append(r)
    pair_occurrences = 0
    repeated_pairs = []
    for group, runs in tie_groups.items():
        seen = defaultdict(list)
        for r in runs:
            for a, b in combinations(r["products"], 2):
                if score(a) is not None and score(a) == score(b):
                    pair_occurrences += 1
                    key = tuple(sorted((a["product_id"], b["product_id"])))
                    seen[key].append(a["product_id"])
        repeated_pairs.extend(v for v in seen.values() if len(v) >= 2)
    ties = {"calls": sum(map(len, tie_groups.values())), "argument_groups": len(tie_groups),
            "within_call_tied_pair_occurrences": pair_occurrences,
            "repeated_pair_groups": len(repeated_pairs),
            "reversing_pair_groups": sum(len(set(x)) > 1 for x in repeated_pairs)}
    published_ties = json.loads((data / "tie-audit.json").read_text())["summary"]
    assert ties["repeated_pair_groups"] == published_ties["same_group_pairs_tied_in_at_least_two_calls"]
    assert ties["reversing_pair_groups"] == published_ties["reversing_pair_groups"]
    pref = {c: sorted([r for r in upstream if r["cohort"] == "color" and r["condition"] == c], key=lambda r:r["repeat"]) for c in ("BASE", "BRAND", "GREEN", "PREFER")}
    preference = {}
    base = run_map(pref["BASE"][0])
    for c, rr in pref.items():
        pm = run_map(rr[0]); shared = sorted(set(base) & set(pm))
        base_order = [p["product_id"] for p in pref["BASE"][0]["products"] if p["product_id"] in shared]
        new_order = [p["product_id"] for p in rr[0]["products"] if p["product_id"] in shared]
        preference[c] = {"records_per_repeat": [len(r["products"]) for r in rr], "matched_ids": len(shared),
                         "changed_matched_scores": sum(score(base[i]) != score(pm[i]) for i in shared),
                         "common_relative_order_equal": base_order == new_order,
                         "primary": [compact(run_map(r)["27333065053055404"]) if "27333065053055404" in run_map(r) else None for r in rr]}
    fusion_id = "25362822463335514"
    fusion = {}
    for c in ("A", "B", "AB", "BA", "AA"):
        rr = [r for r in upstream if r["cohort"] == "fusion" and r["condition"] == c]
        fusion[c] = sorted({run_map(r)[fusion_id]["ranking_score"] for r in rr})
    sa, sb, sab = (Decimal(fusion[c][0]) for c in ("A", "B", "AB"))
    formula = [{"rule": name, "prediction": str(value), "observed": str(sab), "observed_minus_prediction": str(sab-value)}
               for name, value in (("max", max(sa,sb)), ("mean",(sa+sb)/2), ("sum",sa+sb))]
    composition = []
    stability = {}
    for repeat in (1,2,3):
        rm = {r["condition"]: r for r in multi if r["repeat"] == repeat}
        sets = {c: set(run_map(r)) for c,r in rm.items()}
        ab, a, b, joined = (sets[c] for c in ("AB","A","B","JOIN"))
        unchanged = sum(score(run_map(rm["AB"])[i]) == score(run_map(rm[c])[i]) for c in ("A","B") for i in ab & sets[c])
        composition.append({"repeat": repeat, "solo_intersection": len(a&b), "AB_records": len(ab),
                            "from_A": len(ab&a), "from_B":len(ab&b), "absent_from_solo_union":sorted(ab-(a|b)),
                            "matched_unchanged_scores":unchanged, "AB_JOIN_intersection":len(ab&joined),
                            "AB_JOIN_union":len(ab|joined),
                            "AB_JOIN_jaccard":str(Decimal(len(ab&joined))/Decimal(len(ab|joined)))})
    for c in sorted({r["condition"] for r in multi}):
        rr = [r for r in multi if r["condition"] == c]
        common = set.intersection(*(set(run_map(r)) for r in rr))
        stable = sum(len({run_map(r)[i]["ranking_score"] for r in rr}) == 1 for i in common)
        stability[c] = {"counts":[len(r["products"]) for r in rr], "common_ids":len(common),
                        "stable_score_ids":stable,
                        "distinct_id_sequences":len({tuple(p["product_id"] for p in r["products"]) for r in rr})}
    scores = [score(p) for r in baseline for p in r["products"] if score(p) is not None]
    counts = defaultdict(list)
    for r in baseline:
        if r["cohort"] == "boundary36":
            counts[r["case"] + "/" + r["condition"]].append(r["product_count"])
    resolver = json.loads((data / "resolver-audit.json").read_text())
    return {"author":"Astra (gpt-6-astra)","scope":"Recalculation of existing saved observations; no new remote data or fitted internal coefficients.",
            "sources":sources,
            "historical": {"total_invocations":len(baseline), "eligible_scored_runs":len(eligible),
                "nonmonotone_runs":sum(x["adjacent_upturns"]>0 for x in stats),
                "single_upturn_runs":sum(x["adjacent_upturns"]==1 for x in stats),
                "adjacent_pairs":sum(x["adjacent_pairs"] for x in stats),
                "adjacent_upturns":sum(x["adjacent_upturns"] for x in stats),
                "all_pairs":sum(x["all_pairs"] for x in stats),
                "discordant_pairs":sum(x["discordant_pairs"] for x in stats),
                "tied_pairs":sum(x["tied_pairs"] for x in stats),
                "scored_occurrences":len(scores), "unique_printed_numeric_scores":len(set(scores)),
                "min_printed_score":str(min(scores)), "max_printed_score":str(max(scores)),
                "within_half_last_decimal_of_k_over_256":sum(abs(s-(s*256).to_integral_value(rounding=ROUND_HALF_EVEN)/256)<=Decimal('0.0000005') for s in scores)},
            "run_order_statistics":stats,"neutral":neutral_result,
            "levoit":{"run_id":levoit["run_id"],"products":[compact(p) for p in levoit["products"]]},
            "strong_brand_tests":strong,"ties":ties,"preference":preference,
            "fusion_scores":fusion,"literal_fusion_tests":formula,
            "query_composition":composition,"query_stability":stability,"count_boundary":dict(sorted(counts.items())),
            "merchant_panel":{k:merchant[k] for k in ("queries","returned_occurrences","distinct_product_ids","zero_result_successes","returned_count","numeric_score_order","fields")},
            "shopping_cases":merchant["separate_shopping_cases"],
            "resolver_fixed_source_tests":len(resolver["tests"]),
            "resolver_all_follow_first_unique_id_order":all(x["matches_first_occurrence_unique_input_order"] for x in resolver["tests"])}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing analysis output")
    result=build(args.repo_root)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"historical":result["historical"],"ties":result["ties"],"fusion":result["literal_fusion_tests"]},indent=2))
