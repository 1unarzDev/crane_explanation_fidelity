#!/usr/bin/env python3
"""Read-only audit of retained synthetic assertion-role qualification calls.

Exact comparison to construction gold is a mechanical candidate score. It does not replace
independent project semantic review or authorize role labels on development responses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run_evidence_calibration_claim_role_qualification import (
    DEFAULT_OUTPUT, VALID_STATUS, call_once, load_bound_freeze,
)


def audit(output_root: Path = DEFAULT_OUTPUT) -> dict:
    freeze, cases, prompt, schema = load_bound_freeze()
    canary = {"case_id": "non-study-schema-canary", "response_text": "The recorded action succeeded.",
              "claims": [{"item_id": "c1", "response_span": "The recorded action succeeded.",
                          "claim_text": "The recorded action succeeded."}]}
    expected = [("canary", canary)] + [(slot, case) for slot in ("A", "B") for case in cases]
    allowed = {output_root / slot / f"{case['case_id']}{suffix}"
               for slot, case in expected for suffix in (".json", ".intent")}
    if output_root.exists():
        unexpected = {path for path in output_root.rglob("*") if path.is_file() and path not in allowed}
        if unexpected:
            raise ValueError(f"unexpected retained role qualification file: {sorted(unexpected)[0]}")
    rows = []
    for slot, case in expected:
        path = output_root / slot / f"{case['case_id']}.json"
        intent = path.with_suffix(".intent")
        if not path.exists() and not intent.exists():
            rows.append({"slot": slot, "case_id": case["case_id"], "status": "UNCALLED"})
            continue
        if not path.exists():
            rows.append({"slot": slot, "case_id": case["case_id"], "status": "INTENT_WITHOUT_TERMINAL_NO_RETRY",
                         "intent_raw_sha256": hashlib.sha256(intent.read_bytes()).hexdigest()})
            continue
        if not intent.exists():
            raise ValueError(f"orphan role call record: {path}")
        retained = json.loads(path.read_text(encoding="utf-8"))
        identity = retained.get("request_identity")
        if not isinstance(identity, dict) or not isinstance(identity.get("cli_version"), str):
            raise ValueError(f"invalid retained role identity: {path}")
        verified = call_once(case=case, slot=slot, freeze=freeze, prompt=prompt, schema=schema,
                             output_root=output_root, cli_version=identity["cli_version"])
        row = {"slot": slot, "case_id": case["case_id"], "status": verified["status"],
               "record_raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "intent_raw_sha256": hashlib.sha256(intent.read_bytes()).hexdigest()}
        if verified["status"] == VALID_STATUS and slot in {"A", "B"}:
            expected_labels = [(claim["item_id"], claim["role"], claim["asserted_diagnostic_level"])
                               for claim in case["expected"]]
            returned_labels = [(claim["item_id"], claim["role"], claim["asserted_diagnostic_level"])
                               for claim in verified["parsed_final"]["claim_roles"]]
            row["reviewed_atomic_claims"] = len(expected_labels)
            row["exact_role_level_matches"] = sum(left == right for left, right in zip(expected_labels, returned_labels, strict=True))
            row["reference_exact_match"] = expected_labels == returned_labels
        rows.append(row)
    per_pass = {}
    for slot in ("A", "B"):
        selected = [row for row in rows if row["slot"] == slot]
        per_pass[slot] = {
            "expected_cases": len(cases),
            "structurally_valid_cases": sum(row["status"] == VALID_STATUS for row in selected),
            "retained_failures": sum(row["status"] == "FAILED_NO_RETRY" for row in selected),
            "uncalled": sum(row["status"] == "UNCALLED" for row in selected),
            "interrupted_intents": sum(row["status"] == "INTENT_WITHOUT_TERMINAL_NO_RETRY" for row in selected),
            "heldout_exact_matches": sum(row.get("reference_exact_match") is True for row in selected
                                          if row["case_id"].startswith("role-ho-")),
            "heldout_cases": 20,
        }
    canary_status = rows[0]["status"]
    all_calls_structural = canary_status == VALID_STATUS and all(
        item["structurally_valid_cases"] == item["expected_cases"] for item in per_pass.values()
    )
    exact_candidate = all_calls_structural and all(
        item["heldout_exact_matches"] == item["heldout_cases"] for item in per_pass.values()
    )
    status = ("COMPLETE_EXACT_CANDIDATE_PROJECT_REVIEW_REQUIRED" if exact_candidate else
              "COMPLETE_STRUCTURAL_BUT_REFERENCE_MISMATCH_PROJECT_REVIEW_REQUIRED" if all_calls_structural else
              "INCOMPLETE_OR_RETAINED_FAILURE_NO_QUALIFICATION")
    return {"schema": "crane-evidence-calibration-claim-role-qualification-audit/v1",
            "status": status, "canary_status": canary_status, "per_pass": per_pass,
            "rows": rows, "all_calls_structurally_valid": all_calls_structural,
            "exact_candidate": exact_candidate, "independent_semantic_review_complete": False,
            "role_qualification_authorized": False, "pilot_role_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "model_calls_made_by_audit": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    result = audit(args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["exact_candidate"] or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
