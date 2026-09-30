#!/usr/bin/env python3
"""Check the retained blind inventory triage without approving atomic claims."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run_evidence_calibration_pilot_atomization import load_declared_inputs, load_interruption


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-inventory-triage-v1.json"
DEFAULT_PREFIX_REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-inventory-prefix-review-v1.json"
EXPECTED_REPAIRS = {
    ("ax-e40daca7a99ef38a2d4e8d4d6889f798", 3): "The trace records two FollowPath failures.",
    ("ax-ff10727fb4a1d16159a2b77e3862eac9", 3): "The trace records three FollowPath attempts.",
    ("ax-ff10727fb4a1d16159a2b77e3862eac9", 4): "The trace records two FollowPath failures.",
}


def audit(manifest_path: Path = DEFAULT_MANIFEST,
          prefix_review_path: Path = DEFAULT_PREFIX_REVIEW) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-pilot-inventory-triage/v1"
            or manifest.get("status") != "PRELIMINARY_METHOD_BLIND_TRIAGE_NOT_SEMANTIC_APPROVAL"
            or manifest.get("semantic_inventory_approved") is not False
            or manifest.get("support_annotation_authorized") is not False):
        raise ValueError("inventory triage authorization boundary changed")

    scope = manifest["scope"]
    if scope.get("method_join_key_opened") is not False or scope.get("evaluator_truth_opened") is not False:
        raise ValueError("inventory triage is no longer blinded")
    # The original triage covered the first 17 forms. Later extraction added 96
    # forms to the same directory, so select the frozen prefix by its bound IDs.
    review = json.loads(prefix_review_path.read_text(encoding="utf-8"))
    ids = [row["opaque_response_id"] for row in review["per_response_provisional_disposition"]]
    if len(ids) != len(set(ids)) or len(ids) != scope["review_forms_inspected"]:
        raise ValueError("provisional prefix review is not an exact 17-form inventory")
    root = ROOT / scope["review_form_root"]
    paths = sorted(root / f"{response_id}.json" for response_id in ids)
    pairs = [[path.name, hashlib.sha256(path.read_bytes()).hexdigest()] for path in paths]
    pair_hash = hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()
    if len(paths) != scope["review_forms_inspected"] or pair_hash != scope["sorted_filename_and_raw_sha256_pairs_json_sha256"]:
        raise ValueError("retained blind review forms changed")

    declaration, entries, _, _, _, _ = load_declared_inputs()
    call_root = ROOT / declaration["output_root"]
    skipped = load_interruption(entries, call_root)
    bank_entries = {entry["opaque_response_id"]: entry for entry in entries}
    forms = {}
    claim_count = 0
    for path in paths:
        form = json.loads(path.read_text(encoding="utf-8"))
        response_id = path.stem
        if (form.get("opaque_response_id") != response_id
                or form.get("status") != "PROJECT_REVIEW_PENDING"
                or form.get("method_identity_visible") is not False
                or form.get("support_annotation_authorized") is not False
                or any(value is not None for value in form["review_fields"].values())):
            raise ValueError(f"blind review boundary changed: {response_id}")
        if (response_id == skipped or response_id not in bank_entries
                or form.get("blind_bank_raw_sha256") != declaration["blinded_bank"]["raw_sha256"]
                or form.get("response_text") != bank_entries[response_id]["response_text"]):
            raise ValueError(f"blind response provenance changed: {response_id}")
        call_path = call_root / f"{response_id}.json"
        if (not call_path.is_file() or form.get("extractor_call_raw_sha256")
                != hashlib.sha256(call_path.read_bytes()).hexdigest()):
            raise ValueError(f"extractor call provenance changed: {response_id}")
        call = json.loads(call_path.read_text(encoding="utf-8"))
        if call.get("status") != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            raise ValueError(f"extractor call is not structurally valid: {response_id}")
        candidates = [
            {"candidate_index": index, "response_span": claim["response_span"],
             "claim_text": claim["claim_text"]}
            for index, claim in enumerate(call["parsed_final"]["claims"])
        ]
        if form["atomic_claim_candidates"] != candidates:
            raise ValueError(f"review form differs from extractor inventory: {response_id}")
        forms[response_id] = form
        claim_count += len(candidates)
    if claim_count != scope["candidate_claims_inspected"]:
        raise ValueError("candidate claim count changed")

    repairs = {}
    for finding in manifest["findings"]:
        response_id = finding["opaque_response_id"]
        if response_id not in forms:
            raise ValueError(f"finding has no retained review form: {response_id}")
        replacements = finding["proposed_claim_text_replacements"]
        if set(replacements) != {str(index) for index in finding["candidate_indices"]}:
            raise ValueError("finding and proposed repair indices differ")
        candidates = forms[response_id]["atomic_claim_candidates"]
        for raw_index, replacement in replacements.items():
            index = int(raw_index)
            key = (response_id, index)
            if (index >= len(candidates) or candidates[index]["candidate_index"] != index
                    or replacement == candidates[index]["claim_text"]):
                raise ValueError(f"invalid proposed repair: {key}")
            repairs[key] = replacement
    if repairs != EXPECTED_REPAIRS:
        raise ValueError("bound proposed repairs changed")

    review_scope = review["scope"]
    if (review.get("schema") != "crane-evidence-calibration-pilot-inventory-prefix-review/v1"
            or review.get("status") != "PROVISIONAL_AGENT_ASSESSED_METHOD_BLIND_PREFIX_REVIEW"
            or review.get("semantic_inventory_approved") is not False
            or review.get("support_annotation_authorized") is not False
            or review.get("endpoint_scoring_authorized") is not False
            or review_scope.get("method_join_key_opened") is not False
            or review_scope.get("evaluator_truth_opened") is not False):
        raise ValueError("provisional prefix review authorization boundary changed")
    if (review_scope["triage_manifest_raw_sha256"] != hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            or review_scope["sorted_filename_and_raw_sha256_pairs_json_sha256"] != pair_hash
            or review_scope["reviewed_retained_forms"] != len(forms)
            or review_scope["candidate_claims"] != claim_count):
        raise ValueError("provisional prefix review source binding changed")
    rows = review["per_response_provisional_disposition"]
    if (len(rows) != len(forms) or len({row["opaque_response_id"] for row in rows}) != len(forms)
            or {row["opaque_response_id"] for row in rows} != set(forms)
            or review.get("proposed_omitted_atomic_claims") != []
            or review.get("rejected_candidate_indices") != []):
        raise ValueError("provisional prefix review is not an exact 17-form inventory")
    for row in rows:
        response_id = row["opaque_response_id"]
        expected_indices = sorted(index for key_id, index in repairs if key_id == response_id)
        expected_finding = "ACTOR_QUALIFIER_REPAIR_PROPOSED" if expected_indices else "NO_OMISSION_FOUND"
        if (row["candidate_count"] != len(forms[response_id]["atomic_claim_candidates"])
                or row["finding"] != expected_finding
                or row.get("candidate_indices", []) != expected_indices):
            raise ValueError(f"provisional prefix review differs from triage: {response_id}")

    return {
        "schema": "crane-evidence-calibration-pilot-inventory-triage-audit/v1",
        "status": "PASS_BOUND_PROPOSED_REPAIRS_ONLY",
        "review_forms": len(paths),
        "candidate_claims": claim_count,
        "proposed_claim_repairs": len(repairs),
        "provisional_prefix_review_forms": len(rows),
        "semantic_inventory_approved": False,
        "support_annotation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--prefix-review", type=Path, default=DEFAULT_PREFIX_REVIEW)
    args = parser.parse_args()
    print(json.dumps(audit(args.manifest, args.prefix_review), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
