from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import argparse
import csv
import json
import random
from analyze_upstream import digest, require
from build_dataset import parse_output


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "upstream-formula-phase2-2026-09-27"
COLLECTION = "catalog-upstream-synonyms-20260927T032502655438Z"


def expected_plan():
    a, b = "stainless steel frying pan", "stainless steel skillet"
    conditions = {"A": [a], "B": [b], "AB": [a, b], "BA": [b, a], "AAB": [a, a, b], "ABB": [a, b, b], "JOIN": [a + " " + b]}
    rng = random.Random(20260929)
    plan = []
    for repeat in range(1, 4):
        names = list(conditions)
        rng.shuffle(names)
        for name in names:
            argv = ["/opt/hatch/bin/meta-catalog-search"]
            for query in conditions[name]:
                argv.extend(["--query", query])
            argv.extend(["-n", "50", "--conversation-id", "upstream-synonyms-20260927-Astra-01", "--retries", "0", "--timeout-secs", "30", "--raw"])
            plan.append({"run_id": f"R{len(plan)+1:02d}-{name}-{repeat}", "condition": name, "repeat": repeat, "argv": argv, "user_id_present": False})
    return plan


def build(source):
    base = source / EXPERIMENT
    folder = base / "extracted" / COLLECTION
    require((folder / "collector.py").read_bytes() == (base / "collect_upstream_synonyms.py").read_bytes(), "Collector differs")
    for row in csv.DictReader((folder / "MANIFEST.csv").open()):
        path = folder / row["path"]
        require(path.stat().st_size == int(row["bytes"]) and digest(path) == row["sha256"], "Manifest mismatch")
    plan = json.loads((folder / "plan.json").read_text())
    require(plan == expected_plan(), "Downloaded plan differs from prespecified schedule")
    require(len(list(folder.glob("R*/execution.json"))) == 21, "Unexpected attempt count")
    runs = []
    for scheduled in plan:
        run_folder = folder / scheduled["run_id"]
        receipt_path = run_folder / "execution.json"
        receipt = json.loads(receipt_path.read_text())
        require(receipt["argv"] == scheduled["argv"] == json.loads((run_folder / "argv.json").read_text()), "Argument mismatch")
        for stream in ("stdout", "stderr"):
            path = run_folder / f"{stream}.bin"
            require(path.stat().st_size == receipt[f"{stream}_bytes"] and digest(path) == receipt[f"{stream}_sha256"], "Stream receipt mismatch")
        require(receipt["exit_code"] == 0 and receipt["exception"] is None, "Failed call needs separate handling")
        stdout = run_folder / "stdout.bin"
        kind, rows, _, _ = parse_output(stdout.read_bytes())
        debug = []
        responses = json.loads(stdout.read_bytes())["tool_responses"]
        for index, response in enumerate(responses):
            require(response["success"] is True, "Tool failure")
            metadata = response["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            for entry in metadata.get("query_debug_info", []):
                debug.append({"response_index": index, "query": entry["query"], "reported_count": entry["product_count"], "product_ids": [str(i) for i in entry["product_ids"]]})
        runs.append({"run_id": "synonyms/" + scheduled["run_id"], "condition": scheduled["condition"], "repeat": scheduled["repeat"], "argv": receipt["argv"], "utc_start": receipt["start_utc"], "utc_end": receipt["end_utc"], "exit_code": receipt["exit_code"], "output_kind": kind, "product_count": len(rows), "products": rows, "response_count": len(responses), "debug_queries": debug, "source_path": stdout.relative_to(source).as_posix(), "source_sha256": digest(stdout), "execution_source_path": receipt_path.relative_to(source).as_posix(), "execution_sha256": digest(receipt_path)})
    return runs


def summarize(runs):
    groups = defaultdict(list)
    for run in runs:
        groups[run["condition"]].append(run)
    stable = {}
    conditions = []
    for name, group in sorted(groups.items()):
        maps = [{row["product_id"]: row for row in run["products"]} for run in group]
        common = set.intersection(*(set(mapping) for mapping in maps))
        stable[name] = {identity: Decimal(maps[0][identity]["ranking_score"]) for identity in common if len({mapping[identity]["ranking_score"] for mapping in maps}) == 1}
        conditions.append({"condition": name, "counts": [run["product_count"] for run in group], "common_ids": len(common), "stable_score_ids": len(stable[name]), "distinct_id_sequences": len({tuple(mapping) for mapping in maps}), "distinct_id_score_sequences": len({tuple((row["product_id"], row["ranking_score"]) for row in run["products"]) for run in group}), "score_upturns": [sum(Decimal(a["ranking_score"]) < Decimal(b["ranking_score"]) for a, b in zip(run["products"], run["products"][1:])) for run in group]})
    contrasts = []
    composition = []
    for repeat in range(1, 4):
        selected = {name: next(run for run in group if run["repeat"] == repeat) for name, group in groups.items()}
        maps = {name: {row["product_id"]: row for row in run["products"]} for name, run in selected.items()}
        a, b, ab = (maps[name] for name in ("A", "B", "AB"))
        source_comparisons = []
        for name in ("A", "B"):
            single = maps[name]
            common = sorted(set(single) & set(ab))
            original_debug = selected[name]["debug_queries"][0]
            combined_debug = next(entry for entry in selected["AB"]["debug_queries"] if entry["query"] == original_debug["query"])
            source_comparisons.append({"single_condition": name, "shared_with_AB": len(common), "changed_scores": [identity for identity in common if single[identity]["ranking_score"] != ab[identity]["ranking_score"]], "debug_id_sequence_equal": original_debug["product_ids"] == combined_debug["product_ids"]})
        extra_ids = sorted(set(ab) - set(a) - set(b))
        solo_debug = {name: set(selected[name]["debug_queries"][0]["product_ids"]) for name in ("A", "B")}
        composition.append({"repeat": repeat, "solo_AB_shared_ids": sorted(set(a) & set(b)), "AB_ids_absent_from_both_solo_returns": extra_ids, "extra_AB_ids_in_solo_debug": {identity: [name for name in ("A", "B") if identity in solo_debug[name]] for identity in extra_ids}, "solo_debug_overlap_count": len(solo_debug["A"] & solo_debug["B"]), "solo_comparisons": source_comparisons})
        for name in ("BA", "AAB", "ABB", "JOIN"):
            right = maps[name]
            shared = sorted(set(ab) & set(right))
            contrasts.append({"repeat": repeat, "right_condition": name, "AB_count": len(ab), "right_count": len(right), "shared_ids": len(shared), "id_sequences_equal": list(ab) == list(right), "AB_only_ids": sorted(set(ab) - set(right)), "right_only_ids": sorted(set(right) - set(ab)), "score_differences": [{"product_id": identity, "AB": ab[identity]["ranking_score"], "right": right[identity]["ranking_score"]} for identity in shared if ab[identity]["ranking_score"] != right[identity]["ranking_score"]]})
    common = sorted(set(stable["A"]) & set(stable["B"]) & set(stable["AB"]))
    debug_groups = defaultdict(list)
    for run in runs:
        require([entry["query"] for entry in run["debug_queries"]] == [run["argv"][i + 1] for i, value in enumerate(run["argv"]) if value == "--query"], "Debug queries differ from recorded query arguments")
        for entry in run["debug_queries"]:
            require(entry["reported_count"] == len(entry["product_ids"]) == len(set(entry["product_ids"])), "Debug count or uniqueness mismatch")
            debug_groups[entry["query"]].append(entry)
    metadata = [{"query": query, "groups": len(entries), "counts": sorted({len(entry["product_ids"]) for entry in entries}), "distinct_id_sequences": len({tuple(entry["product_ids"]) for entry in entries})} for query, entries in sorted(debug_groups.items())]
    return {"author": "Astra (gpt-6-astra)", "calls": len(runs), "record_occurrences": sum(run["product_count"] for run in runs), "conditions": conditions, "combined_list_composition": composition, "blocked_contrasts": contrasts, "debug_metadata": metadata, "formula_test": {"stable_A_B_AB_common_ids": len(common), "ids": common, "literal_arithmetic_status": "not evaluable: no jointly observed stable solo scores" if not common else "requires explicit comparison", "normalized_vector_hypothesis_status": "not run: fewer than 10 stable common IDs" if len(common) < 10 else "requires prespecified held-out evaluation", "no_fitted_coefficients": True}, "scope": "Per-query debug-list agreement and preserved matched scores are observations, not an authenticated execution trace or proof of a merging algorithm."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    runs = build(args.source_root.resolve())
    summary = summarize(runs)
    if args.write:
        (ROOT / "data/query-multiplicity-runs.jsonl").write_text("".join(json.dumps(run, sort_keys=True) + "\n" for run in runs))
        (ROOT / "data/query-multiplicity-audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
