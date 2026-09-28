from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import argparse
import csv
import hashlib
import json
from build_dataset import parse_output


ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {
    "fusion": "extracted-round-6/catalog-upstream-fusion-20260927T030208193835Z",
    "color": "extracted-round-7/catalog-upstream-color-20260927T030553670330Z",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(source):
    base = source / "catalog-code-continuation-2026-09-26"
    runs = []
    for cohort, location in COLLECTIONS.items():
        folder = base / location
        require((folder / "collector.py").read_bytes() == (base / f"collect_upstream_{cohort}.py").read_bytes(), "Collector bytes differ")
        for row in csv.DictReader((folder / "MANIFEST.csv").open()):
            path = folder / row["path"]
            require(path.stat().st_size == int(row["bytes"]) and digest(path) == row["sha256"], "Manifest differs")
        plan = json.loads((folder / "plan.json").read_text())
        for scheduled in plan:
            run_folder = folder / scheduled["run_id"]
            receipt_path = run_folder / "execution.json"
            receipt = json.loads(receipt_path.read_text())
            require(receipt["argv"] == scheduled["argv"] == json.loads((run_folder / "argv.json").read_text()), "Argument mismatch")
            for stream in ("stdout", "stderr"):
                path = run_folder / f"{stream}.bin"
                require(path.stat().st_size == receipt[f"{stream}_bytes"] and digest(path) == receipt[f"{stream}_sha256"], "Receipt mismatch")
            require(receipt["exit_code"] == 0 and receipt["exception"] is None, "Failed call must be investigated")
            stdout = run_folder / "stdout.bin"
            kind, rows, counts, _ = parse_output(stdout.read_bytes())
            envelope = json.loads(stdout.read_bytes())
            debug = []
            boundaries = []
            for number, response in enumerate(envelope["tool_responses"]):
                require(response["success"] is True, "Tool failure")
                boundaries.append({"response_index": number, "tool_name": response["tool_name"], "product_blocks": response["result_content"].count("<PRODUCT>")})
                metadata = response.get("metadata")
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                for entry in (metadata or {}).get("query_debug_info", []):
                    debug.append({"response_index": number, "query": entry.get("query"), "reported_product_count": entry.get("product_count"), "product_ids": [str(value) for value in entry.get("product_ids", [])], "field_names": sorted(entry)})
            runs.append({"run_id": cohort + "/" + scheduled["run_id"], "cohort": cohort, "condition": scheduled["condition"], "repeat": scheduled["repeat"], "argv": receipt["argv"], "utc_start": receipt["start_utc"], "utc_end": receipt["end_utc"], "exit_code": receipt["exit_code"], "output_kind": kind, "product_count": len(rows), "products": rows, "response_boundaries": boundaries, "debug_queries": debug, "source_path": stdout.relative_to(source).as_posix(), "source_sha256": digest(stdout), "execution_source_path": receipt_path.relative_to(source).as_posix(), "execution_sha256": digest(receipt_path)})
    return runs


def summarize(runs):
    groups = defaultdict(list)
    for run in runs:
        groups[(run["cohort"], run["condition"])].append(run)
    stable = {}
    condition_stats = []
    for key, group in sorted(groups.items()):
        maps = [{row["product_id"]: row for row in run["products"]} for run in group]
        require(all(len(mapping) == run["product_count"] for mapping, run in zip(maps, group)), "Repeated IDs require a different join")
        common = set.intersection(*(set(mapping) for mapping in maps))
        stable[key] = {identity: Decimal(maps[0][identity]["ranking_score"]) for identity in common if len({mapping[identity]["ranking_score"] for mapping in maps}) == 1}
        condition_stats.append({"cohort": key[0], "condition": key[1], "runs": len(group), "counts": [run["product_count"] for run in group], "common_ids": len(common), "stable_score_ids": len(stable[key]), "distinct_id_sequences": len({tuple(mapping) for mapping in maps}), "distinct_id_score_sequences": len({tuple((row["product_id"], row["ranking_score"]) for row in run["products"]) for run in group}), "score_upturn_counts": [sum(Decimal(a["ranking_score"]) < Decimal(b["ranking_score"]) for a, b in zip(run["products"], run["products"][1:])) for run in group], "debug_entries_per_run": [len(run["debug_queries"]) for run in group]})
    formulas = []
    for combined in ("AB", "BA"):
        a, b, combined_scores = (stable[("fusion", name)] for name in ("A", "B", combined))
        common = sorted(set(a) & set(b) & set(combined_scores))
        rows = [{"product_id": identity, "A": str(a[identity]), "B": str(b[identity]), "combined": str(combined_scores[identity]), "matches_max": combined_scores[identity] == max(a[identity], b[identity]), "matches_mean": combined_scores[identity] == (a[identity] + b[identity]) / 2, "matches_sum": combined_scores[identity] == a[identity] + b[identity]} for identity in common]
        formulas.append({"combined_condition": combined, "stable_common_ids": len(common), "products": rows})
    color_comparisons = []
    for condition in ("GREEN", "PREFER", "BRAND"):
        baseline, current = stable[("color", "BASE")], stable[("color", condition)]
        common = sorted(set(baseline) & set(current))
        changed = [{"product_id": identity, "baseline_score": str(baseline[identity]), "condition_score": str(current[identity]), "difference": str(current[identity] - baseline[identity])} for identity in common if baseline[identity] != current[identity]]
        color_comparisons.append({"condition": condition, "matched_ids_stable_in_both_conditions": len(common), "score_changes": changed})
    primary = []
    for run in runs:
        if run["cohort"] != "color":
            continue
        rows = [row for row in run["products"] if row["product_id"] == "27333065053055404"]
        primary.append({"run_id": run["run_id"], "present": bool(rows), "score": rows[0]["ranking_score"] if rows else None, "position": rows[0]["position"] if rows else None, "present_in_debug_ids": any("27333065053055404" in entry["product_ids"] for entry in run["debug_queries"])})
    sequence = lambda run: [(row["product_id"], row["ranking_score"]) for row in run["products"]]
    duplicate_identity = all(sequence(a) == sequence(aa) for a in groups[("fusion", "A")] for aa in groups[("fusion", "AA")])
    return {"author": "Astra (gpt-6-astra)", "catalog_calls": len(runs), "returned_record_occurrences": sum(run["product_count"] for run in runs), "conditions": condition_stats, "fusion_A_and_AA_all_id_score_sequences_equal": duplicate_identity, "fusion_literal_formula_comparisons": formulas, "color_stable_matched_id_comparisons": color_comparisons, "prespecified_primary_product": {"product_id": "27333065053055404", "observations": primary}, "scope": "Separate live requests through the supported catalog interface; these are neither a same-response stage trace nor recovered implementation coefficients.", "limitations": ["Three repetitions per condition in one research chat and one CLI context per experiment.", "Stable matched-product subsets exclude absent IDs; missing scores are not zero.", "Debug ID list semantics and stage are undocumented.", "Full URLs, opaque handles and debug links excluded from derived records; originals retained locally."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    runs = build(args.source_root.resolve())
    summary = summarize(runs)
    if args.write:
        (ROOT / "data/upstream-runs.jsonl").write_text("".join(json.dumps(run, sort_keys=True) + "\n" for run in runs))
        (ROOT / "data/upstream-audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
