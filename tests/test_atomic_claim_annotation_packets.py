import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_atomic_claim_annotation_packets import build  # noqa: E402

SPEC = importlib.util.spec_from_file_location("fixtures", ROOT / "tests/test_evidence_calibration_reference.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)


def inputs():
    current = next(item for item in FIXTURES.bundle()["conditions"]
                   if item["condition"]["condition_id"] == "e3")
    response = {
        "response_id": "response-e3-B4", "method_id": "B4", "condition_id": "e3",
        "method_configuration_sha256": "4" * 64,
        "final_response": "The action aborted. Commanded motion was not reflected in measured motion.",
        "atomic_claims": [
            {"claim_id": "claim-task-abort", "text": "The action aborted.",
             "response_span": "The action aborted.", "asserted_abstraction_level": "task_outcome",
             "support_references": ["action"]},
            {"claim_id": "claim-command-motion-discrepancy",
             "text": "Commanded motion was not reflected in measured motion.",
             "response_span": "Commanded motion was not reflected in measured motion.",
             "asserted_abstraction_level": "execution_discrepancy", "support_references": ["command", "odometry"]},
        ],
    }
    rubric = {
        "rubric_id": "command-motion-annotation-v1", "question_text": "Why did navigation fail?",
        "required_unit_prompts": ["recorded outcome", "strongest supported command-motion diagnosis"],
        "abstraction_level_options": ["outcome", "command_observation", "execution_discrepancy", "specific_physical_cause"],
        "limitation_prompts": ["a discrepancy alone does not identify a unique physical cause"],
        "false_premise_applicable": False,
        "sanitized_physical_facts": [{"fact": "The evaluator trace records negligible body motion."}],
    }
    return current, response, rubric


def test_two_forms_are_blinded_and_key_is_separate():
    packets, key = build(*inputs(), "development-blinding-secret-v1")
    serialized = json.dumps(packets, sort_keys=True)
    assert packets["packet_count"] == 2
    assert {form["annotator_slot"] for form in packets["forms"]} == {"A", "B"}
    assert '"method_id"' not in serialized and "claim-task-abort" not in serialized
    assert key["method_id"] == "B4"
    assert key["join_after_adjudication"]
    assert len(key["claim_items"]) == 2
    assert all(item["label"] is None for item in packets["forms"][0]["atomic_statements"])


def test_packet_builder_rejects_intervention_identity_in_physical_view():
    current, response, rubric = inputs()
    rubric["sanitized_physical_facts"] = [{"intervention_identity": "hold"}]
    with pytest.raises(ValueError, match="intervention identity"):
        build(current, response, rubric, "development-blinding-secret-v1")


def test_claim_items_are_deterministic_but_not_independent_samples():
    first, _ = build(*inputs(), "development-blinding-secret-v1")
    second, _ = build(*inputs(), "development-blinding-secret-v1")
    assert first == second
    assert "independent_sample" not in json.dumps(first)


def test_packet_builder_rejects_an_atomic_claim_without_a_verbatim_response_span():
    current, response, rubric = inputs()
    response["atomic_claims"][1]["response_span"] = "The motor failed."
    with pytest.raises(ValueError, match="span must occur verbatim"):
        build(current, response, rubric, "development-blinding-secret-v1")
