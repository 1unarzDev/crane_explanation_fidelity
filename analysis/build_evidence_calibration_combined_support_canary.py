#!/usr/bin/env python3
"""Fresh synthetic combined-format references; never reads pilot answers or method keys."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from adjudicate_evidence_calibration_annotations import compare
from build_evidence_calibration_agent_qualification import LEVELS
from build_evidence_calibration_pilot_support_packets import build_packet, write_once
from evidence_calibration_io import canonical_sha256
from evidence_calibration_support_execution import validate_support, validate_adjudication

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/explanation_fidelity/qualification/evidence-calibration-combined-support-canary-v1.json"
AGENTS = {slot: f"agent-{slot}-combined-support-canary-v1" for slot in ("A", "B", "C")}


def build() -> dict:
    statements = [
        "The configured progress check requires 0.18 m of displacement within 12 s.",
        "The synchronized record shows 0.81 m of displacement during that interval.",
        "Wheel slip occurred during the interval.",
        "The progress-check configuration alone does not identify a physical cause.",
    ]
    answer = " ".join(statements)
    source_text = "# Synthetic compatibility fixture, not a recorded robot configuration.\nprogress_checker:\n  required_movement_radius: 0.18\n  movement_time_allowance: 12.0\n"
    source = {"asset_id": "synthetic/progress_checker.yaml", "text": source_text,
              "sha256": hashlib.sha256(source_text.encode()).hexdigest()}
    evidence = {"schema": "crane-normalized-method-evidence/v1", "episode_id": "synthetic-canary-episode",
                "configuration_id": "synthetic-canary-configuration", "question": "What does this record establish?",
                "evidence": {"source_binding": {"asset_id": source["asset_id"], "sha256": source["sha256"]},
                             "synchronized_odometry": {"interval_start_s": 22.0, "interval_end_s": 34.0,
                                                       "displacement_m": 0.04, "valid": True},
                             "visible_evidence_limitations": ["No wheel-slip measurement or unique physical cause evidence is available."]}}
    condition = {"condition": {"condition_id": "synthetic-canary-condition", "episode_id": evidence["episode_id"],
                               "configuration_id": evidence["configuration_id"], "method_packet_sha256": canonical_sha256(evidence)},
                 "method_packet": evidence}
    response = {"response_id": "synthetic-canary-answer", "method_id": "SYNTHETIC_FIXTURE",
                "condition_id": "synthetic-canary-condition", "final_response": answer,
                "method_configuration_sha256": None,
                "atomic_claims": [{"claim_id": f"synthetic-s{i}", "text": text, "response_span": text,
                                   "asserted_abstraction_level": None} for i, text in enumerate(statements, 1)]}
    rubric = {"rubric_id": "synthetic-combined-rubric", "question_text": evidence["question"],
              "required_unit_prompts": ["state the configured progress-check threshold", "state whether measured response recovered"],
              "abstraction_level_options": list(LEVELS),
              "limitation_prompts": ["preserve that progress-check configuration alone cannot identify a physical cause"],
              "false_premise_applicable": False,
              "sanitized_physical_facts": [{"fact": "Wheel slip occurred during the registered interval.", "value": True}]}
    packet, _discarded_synthetic_key = build_packet(condition, response, rubric, "synthetic-combined-canary-fixed-salt", [source])
    labels = ["SUPPORTED_BY_VISIBLE_EVIDENCE", "CONTRADICTED_BY_VISIBLE_EVIDENCE",
              "PHYSICALLY_TRUE_BUT_UNSUPPORTED", "SUPPORTED_BY_VISIBLE_EVIDENCE"]
    references = {}
    for slot in ("A", "B"):
        form = next(form for form in packet["forms"] if form["annotator_slot"] == slot)
        references[slot] = {"schema": "crane-blinded-atomic-annotation-return/v1", "packet_set_sha256": canonical_sha256(packet),
                            "form_id": form["form_id"], "packet_id": form["packet_id"], "annotator_slot": slot,
                            "annotator_id": AGENTS[slot], "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
                            "atomic_labels": [{"item_id": item["item_id"], "label": label, "annotation_notes": None}
                                              for item, label in zip(form["atomic_statements"], labels)],
                            "required_unit_coverage": [{"unit_prompt": rubric["required_unit_prompts"][0], "communicated": True,
                                                       "response_span": statements[0]},
                                                      {"unit_prompt": rubric["required_unit_prompts"][1], "communicated": False,
                                                       "response_span": None}],
                            "limitation_preservation": [{"limitation_prompt": rubric["limitation_prompts"][0], "preserved": True,
                                                        "response_span": statements[3]}],
                            # Present only to make the constructed reference structurally valid. Never scored.
                            "highest_asserted_abstraction_level": "specific_physical_cause",
                            "false_premise_handling": "NOT_APPLICABLE"}
        validate_support(packet, references[slot], AGENTS[slot], slot)
    constructed_a, constructed_b = copy.deepcopy(references["A"]), copy.deepcopy(references["B"])
    # Alternate correct sides across deliberately constructed disagreements. These are not observed returns.
    constructed_a["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    constructed_a["required_unit_coverage"][1].update(communicated=True, response_span=statements[1])
    constructed_b["limitation_preservation"][0].update(preserved=False, response_span=None)
    report = compare(packet, constructed_a, constructed_b)
    expected = {f"claim:{packet['forms'][0]['atomic_statements'][0]['item_id']}": "SUPPORTED_BY_VISIBLE_EVIDENCE"}
    for row in report["disagreements"]:
        if row["decision_key"].startswith("unit:"):
            expected[row["decision_key"]] = False
        if row["decision_key"].startswith("limitation:"):
            expected[row["decision_key"]] = True
    adjudication = {"schema": "crane-blinded-atomic-annotation-adjudication/v1",
                    "agreement_report_sha256": canonical_sha256(report), "adjudicator_id": AGENTS["C"],
                    "decisions": [{"disagreement_id": row["disagreement_id"], "selected_value": expected[row["decision_key"]],
                                   "rationale": "Project-constructed synthetic reference; not an observed adjudication."}
                                  for row in report["disagreements"]],
                    "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE"}
    validate_adjudication(report, adjudication, AGENTS["C"])
    return {"schema": "crane-combined-support-canary-suite/v1", "synthetic_only": True,
            "study_answers_included": False, "method_key_accessed": False, "packet": packet, "agents": AGENTS,
            "support_references": references, "constructed_adjudication_inputs": {"A": constructed_a, "B": constructed_b},
            "constructed_disagreement_report": report, "adjudication_reference": adjudication,
            "reference_review": "PROJECT_CONSTRUCTION_REVIEW_NOT_INDEPENDENT_OR_HUMAN_VALIDATION",
            "highest_level_qualified": False, "raw_rank_endpoint_use_prohibited": True,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    suite = build()
    write_once(OUTPUT, suite)
    print(json.dumps({"status": "SYNTHETIC_COMBINED_CANARY_REFERENCES_BUILT_NO_CALL", "suite_sha256": canonical_sha256(suite)}, indent=2))
