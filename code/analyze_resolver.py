from pathlib import Path
import argparse
import csv
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
CONTINUATION = "catalog-code-continuation-2026-09-26"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def analyze(source):
    base = source / CONTINUATION
    rounds = [base / "extracted-round-3/resolver-order-evidence-20260927", base / "extracted-round-4/resolver-order2-evidence-20260927"]
    manifests = []
    for folder in rounds:
        rows = list(csv.DictReader((folder / "MANIFEST.csv").open()))
        for row in rows:
            path = folder / row["export_path"]
            require(path.stat().st_size == int(row["bytes"]) and sha(path) == row["sha256"], f"Manifest mismatch: {path}")
        manifests.append({"path": (folder / "MANIFEST.csv").relative_to(source).as_posix(), "rows_verified": len(rows), "sha256": sha(folder / "MANIFEST.csv")})
    exp = rounds[0] / "resolver-experiment"
    catalog_path = exp / "inputs/source-catalog-copy.json"
    browser_path = exp / "inputs/source-browser-copy.json"
    originals = source / "shopping-funnel-2026-09-26/extracted/mattress-q250-01"
    require(catalog_path.read_bytes() == (originals / "catalog/meta-catalog-search.mattress-q250-01.json").read_bytes(), "Catalog copy differs")
    require(browser_path.read_bytes() == (originals / "browser/browser-completion-product-results.json").read_bytes(), "Browser copy differs")
    catalog = json.loads(catalog_path.read_text())["products"]
    browser = json.loads(browser_path.read_text())["products"]
    browser_by_url = {p["url"]: p["result_id"] for p in browser}
    catalog_by_id = {str(p["product_id"]): p for p in catalog}
    require(len(browser_by_url) == len(browser) and len(catalog_by_id) == len(catalog), "Ambiguous source joins")
    sources_by_id = catalog_by_id | {p["result_id"]: p for p in browser}
    stable_records = {}
    results = []
    for number in range(1, 6):
        tag = f"T{number}"
        folder = rounds[number >= 4] / "resolver-experiment"
        request_path = folder / f"requests/{tag}-request.json"
        output_path = folder / f"returned-files/{tag}-shopping-results.json"
        request = json.loads(request_path.read_text())
        output = json.loads(output_path.read_text())
        ids = []
        projections = []
        for product in output["products"]:
            identity = str(product["product_id"]) if product["type"] == "catalog" else browser_by_url[product["url"]]
            ids.append(identity)
            original = sources_by_id[identity]
            shared = sorted(set(product) & set(original))
            changes = [key for key in shared if product[key] != original[key]]
            projections.append({"selected_id": identity, "type": product["type"], "output_field_names": sorted(product), "source_only_fields": sorted(set(original) - set(product)), "changed_shared_fields": changes})
            require(not changes, f"Shared field changed: {tag}, {identity}")
            if identity in stable_records:
                require(product == stable_records[identity], f"Product content changed: {tag}, {identity}")
            stable_records[identity] = product
        unique_ids = list(dict.fromkeys(request["selected_ids"]))
        require(output["count"] == len(output["products"]) == 4, f"Count mismatch: {tag}")
        require(ids == unique_ids, f"Order mismatch: {tag}")
        results.append({"test": tag, "input_ids": request["selected_ids"], "output_ids_joined_to_source": ids, "matches_first_occurrence_unique_input_order": True, "output_count": output["count"], "source_file_order": ["catalog" if "/catalog/" in path else "browser" for path in request["result_paths"]], "request_sha256": sha(request_path), "returned_file_sha256": sha(output_path), "field_projection": projections})
    require(results[0]["returned_file_sha256"] == results[3]["returned_file_sha256"], "T1/T4 byte comparison differs")
    folder = rounds[1] / "resolver-experiment"
    limit_request = folder / "requests/T6-request.json"
    limit_response = folder / "responses/T6-tool-response-verbatim.txt"
    requested = json.loads(limit_request.read_text())["selected_ids"]
    require(requested == list(catalog_by_id)[:51] and len(set(requested)) == 51, "T6 IDs differ from first 51 source IDs")
    error_text = "shopping.resolve_results requires 1 to 50 selected_ids"
    require(error_text in limit_response.read_text(), "T6 error absent from transcription")
    require(not list((folder / "returned-files").glob("T6*")), "Unexpected T6 output")
    return {"author": "Astra (gpt-6-astra)", "scope": "Five supplied normalized output files for four products from two unchanged saved sources; one additional rejection reported in a transcription and UI activity summary.", "manifests": manifests, "original_input_byte_copies_match": True, "input_sha256": {"catalog": sha(catalog_path), "browser": sha(browser_path)}, "source_product_counts": {"catalog": len(catalog), "browser": len(browser)}, "product_values_identical_across_five_outputs": True, "T1_T4_outputs_byte_identical": True, "browser_join": "Exact unique URL in saved browser source; result_id is omitted in normalized browser products.", "tests": results, "limit_test": {"test": "T6", "selected_count": len(requested), "distinct_count": len(set(requested)), "first_51_distinct_catalog_ids_match": True, "reported_error": error_text, "request_sha256": sha(limit_request), "response_transcription_sha256": sha(limit_response), "returned_file_present": False, "provenance": "Muse-authored transcription corroborated by displayed UI activity summary; no native raw call/response export."}, "limits": ["No original implementation source recovered or supplied code executed.", "No widget created in this experiment; normalized order is distinct from visible UI order.", "No new catalog retrieval calls; no conclusion about scoring or catalog order.", "Consistency checks do not independently authenticate remote execution or origin.", "Unknown IDs, identity collisions, other record types, and 50 valid IDs were not tested."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.source_root.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
