#!/usr/bin/env python3
"""Verify the prospective ontology wording repair without changing old evidence contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from evidence_calibration_io import ontology_from_dict


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "configs/evidence_calibration_claim_contracts_v1.json"
NEW = ROOT / "configs/evidence_calibration_claim_contracts_v2_development.json"
MANIFEST = ROOT / "manifests/study/evidence-calibration-ontology-v2-wording-amendment.json"
RATIONALES = {
    "ne-discrepancy-does-not-identify-physical-cause":
        "The discrepancy alone does not establish motor failure, collision, wheel slip, or external obstruction.",
    "ne-recovery-does-not-establish-outcome":
        "Recovery invocation order alone does not establish the eventual task outcome or show that recovery caused it.",
    "ne-response-recovery-does-not-establish-task-outcome":
        "Measured response recovery alone does not establish the eventual task outcome or show that recovery caused it.",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(manifest_path: Path = MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-ontology-wording-amendment/v1"
            or manifest.get("status") != "PROSPECTIVE_DEVELOPMENT_CANDIDATE_NOT_P11_FROZEN"
            or manifest.get("old_ontology_raw_sha256") != digest(OLD)
            or manifest.get("new_ontology_raw_sha256") != digest(NEW)
            or manifest.get("old_pilot_input_validation_raw_sha256")
               != digest(ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json")
            or any(manifest.get(key) is not False for key in
                   ("old_outputs_rewritten", "old_outputs_rescored", "fresh_pilot_run",
                    "p11_authorized", "endpoint_scoring_authorized"))):
        raise ValueError("ontology wording amendment governance boundary changed")
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = json.loads(NEW.read_text(encoding="utf-8"))
    ontology_from_dict(old)
    ontology_from_dict(new)
    expected = copy.deepcopy(old)
    expected["catalog_id"] = "crane-land-evidence-calibration-contracts-v2-development"
    expected["catalog_version"] = "2.0.0-development"
    seen = set()
    for relation in expected["non_entailments"]:
        identifier = relation["non_entailment_id"]
        if identifier in RATIONALES:
            relation["rationale"] = RATIONALES[identifier]
            seen.add(identifier)
    if seen != set(RATIONALES) or new != expected:
        raise ValueError("ontology v2 changes evidence or claim contracts beyond the reviewed wording")
    if manifest.get("changed_non_entailment_ids") != sorted(RATIONALES):
        raise ValueError("ontology wording amendment changed its reviewed relation IDs")
    pilot = json.loads((ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json")
                       .read_text(encoding="utf-8"))
    responses = [diagnostic["b4_final_response"] for episode in pilot["episodes"]
                 for diagnostic in episode["diagnostics"]]
    counts = {
        "deictic_physical_cause": sum("these specific physical causes" in response
                                       for response in responses),
        "overstrong_negative_recovery_causation": sum(
            "Measured response recovery does not establish or cause" in response
            for response in responses),
    }
    if len(responses) != 60 or counts != manifest.get("old_output_phrase_counts"):
        raise ValueError("retained B4 wording observation changed")
    return {"schema": "crane-evidence-calibration-ontology-v2-wording-audit/v1",
            "status": "PASS_PROSPECTIVE_WORDING_ONLY", "changed_rationales": len(RATIONALES),
            "old_b4_response_count": len(responses), "old_output_phrase_counts": counts,
            "evidence_requirements_changed": False, "claim_contracts_changed": False,
            "diagnostic_nodes_changed": False, "old_outputs_rescored": False,
            "fresh_pilot_run": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
