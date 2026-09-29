import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from maximal_supported_diagnosis import diagnose  # noqa: E402


SPEC = importlib.util.spec_from_file_location(
    "reference_fixtures", ROOT / "tests/test_evidence_calibration_reference.py"
)
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)
ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())


def fact_packet(condition_entry, ambiguity=()):
    condition_id = condition_entry["condition"]["condition_id"]
    reference = FIXTURES.reference_input(FIXTURES.bundle())
    assessment = next(item for item in reference["condition_assessments"] if item["condition_id"] == condition_id)
    return {
        "schema": "crane-visible-evidence-requirement-facts/v1",
        "condition_id": condition_id,
        "method_packet_sha256": condition_entry["condition"]["method_packet_sha256"],
        "question_contract": {
            "question_id": "command-motion-question-v1",
            "failure_premise": True,
            "required_mechanism_families": ["command_motion"],
        },
        "requirement_evaluations": assessment["requirement_evaluations"],
        "ambiguity_node_ids": list(ambiguity),
    }


def entry(identifier):
    return next(item for item in FIXTURES.bundle()["conditions"] if item["condition"]["condition_id"] == identifier)


def test_engine_retains_partial_facts_without_overclaiming_then_deepens():
    e0 = diagnose(ONTOLOGY, entry("e0"), fact_packet(entry("e0")))
    assert e0["state"] == "INSUFFICIENT_EVIDENCE"
    assert "claim-task-abort" in e0["approved_claim_ids"]
    assert "claim-command-motion-discrepancy" not in e0["approved_claim_ids"]

    e3 = diagnose(ONTOLOGY, entry("e3"), fact_packet(entry("e3")))
    assert e3["state"] == "SUPPORTED_PARTIAL"
    assert "claim-command-motion-discrepancy" in e3["approved_claim_ids"]
    assert "claim-external-obstruction" not in e3["approved_claim_ids"]
    assert set(e3["required_non_entailment_ids"]) == {
        "ne-discrepancy-does-not-identify-physical-cause",
        "ne-discrepancy-does-not-reveal-intervention",
        "ne-recovery-does-not-establish-outcome",
    }

    e4 = diagnose(ONTOLOGY, entry("e4"), fact_packet(entry("e4")))
    assert e4["state"] == "KNOWN"
    assert "node-external-obstruction" in e4["maximal_node_ids"]
    assert "claim-external-obstruction" in e4["approved_claim_ids"]


def test_missing_odometry_cannot_license_discrepancy():
    result = diagnose(ONTOLOGY, entry("e2"), fact_packet(entry("e2")))
    assert result["state"] == "SUPPORTED_PARTIAL"
    assert "claim-command-observed" in result["approved_claim_ids"]
    assert "claim-command-motion-discrepancy" not in result["approved_claim_ids"]
    assert "req-odometry-stream-valid" in result["missing_requirement_ids"]


def test_explicit_incomparable_alternatives_produce_ambiguity_without_guessing():
    current = entry("e3")
    result = diagnose(
        ONTOLOGY, current,
        fact_packet(current, ambiguity=("node-motor-failure", "node-collision")),
    )
    assert result["state"] == "AMBIGUOUS"
    assert result["ambiguity_node_ids"] == ("node-motor-failure", "node-collision")
    assert "claim-motor-failure" not in result["approved_claim_ids"]
    assert "claim-collision" not in result["approved_claim_ids"]


def test_engine_rejects_hidden_or_unavailable_support_references():
    current = entry("e0")
    facts = fact_packet(current)
    row = next(item for item in facts["requirement_evaluations"] if item["requirement_id"] == "req-command-stream-valid")
    row.update(status="SATISFIED", support_references=["evaluator-intervention"])
    with pytest.raises(ValueError, match="unavailable"):
        diagnose(ONTOLOGY, current, facts)


def test_false_premise_state_requires_supported_public_rejection_claim():
    current = entry("e4")
    facts = fact_packet(current)
    facts["question_contract"] = {
        "question_id": "false-premise-v1", "failure_premise": True,
        "required_mechanism_families": ["false_premise"],
    }
    for row in facts["requirement_evaluations"]:
        row.update(status="ABSENT", support_references=[])
        if row["requirement_id"] in {"req-action-result-valid", "req-action-succeeded", "req-no-failure-triggered"}:
            row.update(status="SATISFIED", support_references=[
                "diagnostic" if row["requirement_id"] == "req-no-failure-triggered" else "action"
            ])
    result = diagnose(ONTOLOGY, current, facts)
    assert result["state"] == "FALSE_PREMISE"
    assert "claim-false-premise-success" in result["approved_claim_ids"]
