#!/usr/bin/env python3
"""Replay the blind extractor-tag triage binding without treating its roles as gold."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs, load_interruption


DEFAULT_MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-extractor-tag-triage-v1.json"
CALL_ROOT = ROOT / "model_outputs/automated_annotations/evidence-calibration-b2-b4-pilot-v1-atomization-v2"
DEEP_TAGS = {"command_motion_discrepancy", "physical_execution_mechanism", "specific_physical_cause"}


def audit(manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-pilot-extractor-tag-triage/v1"
            or manifest.get("status") != "PRELIMINARY_METHOD_BLIND_AGENT_ASSISTED_TRIAGE_NOT_QUALIFICATION"
            or manifest.get("support_annotation_authorized") is not False
            or manifest.get("method_join_key_opened") is not False):
        raise ValueError("extractor-tag triage boundary is invalid")
    _, entries, _, _, _, _ = load_declared_inputs()
    skipped = load_interruption(entries, CALL_ROOT)
    interruption = json.loads((ROOT / manifest["retained_call_prefix"]["manifest"]).read_text(encoding="utf-8"))
    prefix = interruption["retained_prefix"]
    if (skipped != interruption["ambiguous_request"]["opaque_response_id"]
            or manifest["retained_call_prefix"]["sorted_filename_and_raw_sha256_record_set_sha256"]
            != prefix["sorted_filename_and_raw_sha256_record_set_sha256"]):
        raise ValueError("extractor-tag triage is not bound to the retained prefix")
    tags: Counter[str] = Counter()
    deep_claims: set[tuple[str, int]] = set()
    cause_tagged: set[tuple[str, int]] = set()
    claims = 0
    for entry in entries[:prefix["valid_structural_return_count"]]:
        response_id = entry["opaque_response_id"]
        call = json.loads((CALL_ROOT / f"{response_id}.json").read_text(encoding="utf-8"))
        if call.get("status") != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            raise ValueError("retained prefix contains a nonstructural call")
        inventory = call["parsed_final"]["claims"]
        claims += len(inventory)
        for index, claim in enumerate(inventory):
            tag = claim["asserted_abstraction_level"]
            if tag in DEEP_TAGS:
                tags[tag] += 1
                deep_claims.add((response_id, index))
                if tag == "specific_physical_cause":
                    cause_tagged.add((response_id, index))
    if (claims != manifest["retained_call_prefix"]["candidate_claims"]
            or dict(tags) != manifest["extractor_tag_counts"]):
        raise ValueError("extractor-tag counts changed")
    roles = manifest["preliminary_assertion_roles"]
    if set(roles) != {"command_observation_without_discrepancy", "visible_evidence_absence",
                      "explicit_non_entailment_or_limitation"}:
        raise ValueError("extractor-tag triage roles changed")
    listed = [tuple(item) for group in roles.values() for item in group]
    if len(listed) != len(set(listed)) or set(listed) != deep_claims:
        raise ValueError("extractor-tag triage must partition every deep-tagged claim exactly once")
    if not cause_tagged <= {tuple(item) for item in roles["explicit_non_entailment_or_limitation"]}:
        raise ValueError("specific-cause tags no longer match the reviewed non-entailment examples")
    return {
        "schema": "crane-evidence-calibration-pilot-extractor-tag-triage-audit/v1",
        "status": "PASS_BOUND_PRELIMINARY_TRIAGE_ONLY",
        "structural_returns": prefix["valid_structural_return_count"],
        "candidate_claims": claims,
        "deep_tagged_claims": len(deep_claims),
        "preliminary_role_counts": {key: len(value) for key, value in roles.items()},
        "abstraction_treatment_qualified": False,
        "support_annotation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(audit(args.manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
