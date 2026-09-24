import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "build_diagnostic_annotation_packet.py"
SPEC = importlib.util.spec_from_file_location("build_diagnostic_annotation_packet", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixtures():
    result = {
        "episode_id": "episode-1",
        "question_id": "question-1",
        "question_kind": "diagnosis",
        "question": "Why?",
        "provider": "provider",
        "model": "model",
        "evaluator_truth_available_to_methods": False,
        "outputs": [
            {"condition": "R", "text": "answer R", "used_template_fallback": False},
            {"condition": "P", "text": "same answer", "used_template_fallback": True},
            {"condition": "T", "text": "same answer", "used_template_fallback": False},
        ],
    }
    reference = {
        "visibility": "robot_visible_reference",
        "episode_id": "episode-1",
        "question_id": "question-1",
        "diagnosable": True,
        "reference_status": "DEVELOPMENT_NOT_INDEPENDENT",
        "required_units": ["mechanism"],
        "prohibited_claims": ["oracle identity"],
        "allowed_evidence": {"status": "aborted"},
    }
    return result, reference


def test_builder_blinds_conditions_and_keeps_duplicate_final_answers():
    result, reference = fixtures()
    rows, key = MODULE.build_rows(result, reference, "secret")
    assert len(rows) == 3
    assert sum(row["response_text"] == "same answer" for row in rows) == 2
    assert all(not (set(row) & MODULE.FORBIDDEN_PACKET_KEYS) for row in rows)
    assert {entry["condition"] for entry in key} == {"R", "P", "T"}
    assert len({entry["response_id"] for entry in key}) == 3


def test_builder_rejects_evaluator_truth_or_mismatched_reference():
    result, reference = fixtures()
    result["evaluator_truth_available_to_methods"] = True
    try:
        MODULE.build_rows(result, reference, "secret")
    except ValueError as error:
        assert "evaluator truth" in str(error)
    else:
        raise AssertionError("evaluator truth was accepted")

    result["evaluator_truth_available_to_methods"] = False
    reference["episode_id"] = "other"
    try:
        MODULE.build_rows(result, reference, "secret")
    except ValueError as error:
        assert "mismatch" in str(error)
    else:
        raise AssertionError("mismatched reference was accepted")


def test_builder_preserves_and_enforces_declared_evidence_identifiers():
    result, reference = fixtures()
    evidence_id = "events-sha256:" + "a" * 64
    result["permitted_evidence_identifiers"] = [evidence_id]
    reference["allowed_evidence_identifiers"] = [evidence_id]
    result["outputs"][0]["text"] += f" Evidence IDs: {evidence_id}."

    rows, _ = MODULE.build_rows(result, reference, "secret")
    assert all(row["allowed_evidence"]["evidence_identifiers"] == [evidence_id] for row in rows)

    result["outputs"][0]["text"] += " other-sha256:" + "b" * 64
    with pytest.raises(ValueError, match="outside the declared robot-visible set"):
        MODULE.build_rows(result, reference, "secret")


def test_builder_rejects_mismatched_identifier_contracts():
    result, reference = fixtures()
    result["permitted_evidence_identifiers"] = ["events-sha256:" + "a" * 64]
    with pytest.raises(ValueError, match="citation-identifier contracts differ"):
        MODULE.build_rows(result, reference, "secret")


def test_builder_requires_and_propagates_v2_reference_completeness():
    result, reference = fixtures()
    reference["schema"] = "crane-command-motion-annotation-reference/v2"
    reference["evidence_completeness"] = "All question-relevant facts are present."
    reference["completeness_audit"] = {"accepted": False}
    with pytest.raises(ValueError, match="completeness audit did not pass"):
        MODULE.build_rows(result, reference, "secret")

    reference["completeness_audit"]["accepted"] = True
    rows, _ = MODULE.build_rows(result, reference, "secret")
    assert all(
        row["evidence_completeness"] == "All question-relevant facts are present."
        for row in rows
    )
