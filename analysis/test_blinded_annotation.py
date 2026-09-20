"""Tests for blinded annotation packaging and dual-annotator adjudication.

These check the properties that make the workflow trustworthy rather than merely present: that the
packet leaks nothing about condition, that an incomplete or non-independent annotation pass is
refused, and that a final label set cannot be produced while disagreements remain unresolved.
"""

from __future__ import annotations

import json

import pytest
from adjudicate_annotations import (
    BINARY_FIELDS,
    ERROR_CATEGORIES,
    REQUIRED_FIELDS,
    cohen_kappa,
    validate_pass,
)
from build_blinded_annotation_packet import (
    CONDITION_REVEALING_KEYS,
    NON_MODEL_CONDITIONS,
    QUESTION_TEXT,
    UNIT_INVENTORIES,
    WORKSPACE,
    blinded_rows,
    response_id,
)

RESULT_PATH = WORKSPACE / "model_outputs/final/pn-0001/recovery-mechanism.json"


def result(condition_texts: dict[str, str], question_kind: str = "recovery-mechanism"):
    outputs = []
    for condition, text in condition_texts.items():
        output = {"condition": condition, "text": text}
        if condition == "G":
            # The realization path adds exactly the fields that would betray the condition.
            output |= {
                "checked_plan": {"disposition": "full"},
                "verification_accepted": False,
                "unsupported_sentences": ["x"],
                "used_template_fallback": True,
                "raw_candidate": "candidate",
                "disposition": "full",
            }
        else:
            output |= {"disposition": "uncontrolled", "used_template_fallback": False}
        outputs.append(output)
    return {
        "episode_id": "pn-0001-worker-0",
        "question_kind": question_kind,
        "question": QUESTION_TEXT[question_kind],
        "model": "some-model",
        "outputs": outputs,
        "information_parity": {
            "accepted": True,
            "runtime_presentation_sha256": "a" * 64,
            "audit_sha256": "b" * 64,
            "unit_count": 8,
        },
    }


def test_frozen_unit_inventories_match_the_guide():
    assert len(UNIT_INVENTORIES["recovery-mechanism"]) == 8
    assert len(UNIT_INVENTORIES["failure-cause"]) == 5


def test_packet_rows_carry_no_condition_revealing_field():
    rows, _ = blinded_rows(
        [("luna", RESULT_PATH, result({"F": "f", "G": "g", "H": "h"}))],
        secret="s" * 64,
        include_non_model=False,
    )
    assert rows
    for row in rows:
        for field in CONDITION_REVEALING_KEYS:
            assert field not in row


def test_packet_row_carries_what_the_annotator_needs():
    rows, _ = blinded_rows(
        [("luna", RESULT_PATH, result({"F": "f"}))], secret="s" * 64, include_non_model=False
    )
    row = rows[0]
    assert row["question"] == QUESTION_TEXT["recovery-mechanism"]
    assert row["answerable_units_total"] == 8
    assert row["response_text"] == "f"
    assert row["allowed_evidence"]["information_parity_accepted"] is True


def test_response_ids_differ_across_arms_conditions_and_questions():
    secret = "s" * 64
    base = response_id(secret, "luna", "pn-0001-worker-0", "recovery-mechanism", "F")
    assert base != response_id(secret, "claude", "pn-0001-worker-0", "recovery-mechanism", "F")
    assert base != response_id(secret, "luna", "pn-0002-worker-0", "recovery-mechanism", "F")
    assert base != response_id(secret, "luna", "pn-0001-worker-0", "failure-cause", "F")
    assert base != response_id(secret, "luna", "pn-0001-worker-0", "recovery-mechanism", "G")


def test_response_ids_are_stable_for_the_same_secret_and_unstable_across_secrets():
    args = ("luna", "pn-0001-worker-0", "recovery-mechanism", "F")
    assert response_id("s" * 64, *args) == response_id("s" * 64, *args)
    assert response_id("s" * 64, *args) != response_id("t" * 64, *args)


def test_deterministic_smoke_conditions_are_excluded_by_default():
    rows, key = blinded_rows(
        [("luna", RESULT_PATH, result({"A": "a", "F": "f"}))], secret="s" * 64, include_non_model=False
    )
    assert len(rows) == 1
    assert [entry["condition"] for entry in key] == ["F"]


def test_smoke_conditions_are_labeled_as_non_model_when_included():
    _, key = blinded_rows(
        [("luna", RESULT_PATH, result({"A": "a", "F": "f"}))], secret="s" * 64, include_non_model=True
    )
    flags = {entry["condition"]: entry["is_model_condition"] for entry in key}
    assert flags == {"A": False, "F": True}
    assert "A" in NON_MODEL_CONDITIONS


def test_key_records_the_arm_so_pooled_packets_stay_separable():
    _, key = blinded_rows(
        [
            ("luna", RESULT_PATH, result({"F": "f"})),
            ("claude", RESULT_PATH, result({"F": "f"})),
        ],
        secret="s" * 64,
        include_non_model=False,
    )
    assert sorted(entry["arm"] for entry in key) == ["claude", "luna"]


def annotation_row(response_id_value: str, annotator: str, **overrides):
    row = {
        "response_id": response_id_value,
        "episode_id": "pn-0001-worker-0",
        "scenario_family": "recovery_followed_by_success",
        "question_kind": "recovery-mechanism",
        "condition_blinded_id": "blind-1",
        "material_error": False,
        "error_categories": [],
        "disposition": "full",
        "substantive_answer": True,
        "requested_conclusion_answerable": True,
        "correct_abstention": False,
        "answerable_units_total": 8,
        "answerable_units_correct": 7,
        "claim_count": 5,
        "unsupported_claim_count": 0,
        "source_reference_count": 2,
        "correct_source_reference_count": 2,
        "source_references_total_answerable": 2,
        "physical_evidence_claim_count": 0,
        "correct_physical_evidence_claim_count": 0,
        "causal_overclaim": False,
        "qualification_correct": True,
        "evidence_problem": False,
        "annotator_id": annotator,
        "rationale": "supported throughout",
    }
    return row | overrides


def test_required_field_list_matches_the_guide():
    assert len(REQUIRED_FIELDS) == 25
    for field in ("response_id", "annotator_id", "rationale", "evidence_problem"):
        assert field in REQUIRED_FIELDS
    assert BINARY_FIELDS == ("material_error", "substantive_answer", "correct_abstention")


def test_complete_consistent_pass_is_accepted():
    rows = [annotation_row("r1", "ann-1"), annotation_row("r2", "ann-1")]
    assert validate_pass(rows, {"r1", "r2"}, "a") == "ann-1"


def test_incomplete_pass_is_rejected():
    with pytest.raises(SystemExit, match="incomplete"):
        validate_pass([annotation_row("r1", "ann-1")], {"r1", "r2"}, "a")


def test_material_error_without_a_category_is_rejected():
    rows = [annotation_row("r1", "ann-1", material_error=True)]
    with pytest.raises(SystemExit, match="no category"):
        validate_pass(rows, {"r1"}, "a")


def test_unknown_error_category_is_rejected():
    rows = [
        annotation_row("r1", "ann-1", material_error=True, error_categories=["vibes_were_off"])
    ]
    with pytest.raises(SystemExit, match="unknown error categories"):
        validate_pass(rows, {"r1"}, "a")
    assert "vibes_were_off" not in ERROR_CATEGORIES


def test_disposition_inconsistent_with_substantive_answer_is_rejected():
    rows = [annotation_row("r1", "ann-1", disposition="abstained")]
    with pytest.raises(SystemExit, match="substantive_answer disagrees"):
        validate_pass(rows, {"r1"}, "a")


def test_unit_coverage_above_the_inventory_is_rejected():
    rows = [annotation_row("r1", "ann-1", answerable_units_correct=9)]
    with pytest.raises(SystemExit, match="exceeds the inventory"):
        validate_pass(rows, {"r1"}, "a")


def test_two_annotator_ids_in_one_pass_are_rejected():
    rows = [annotation_row("r1", "ann-1"), annotation_row("r2", "ann-2")]
    with pytest.raises(SystemExit, match="exactly one annotator_id"):
        validate_pass(rows, {"r1", "r2"}, "a")


def test_kappa_is_one_for_perfect_nontrivial_agreement():
    assert cohen_kappa([True, False, True], [True, False, True]) == pytest.approx(1.0)


def test_kappa_is_undefined_when_a_rater_uses_one_category_throughout():
    assert cohen_kappa([True, True], [True, True]) is None


def test_kappa_is_zero_at_chance_agreement():
    first = [True, True, False, False]
    second = [True, False, True, False]
    assert cohen_kappa(first, second) == pytest.approx(0.0)


def test_packet_and_key_round_trip_through_json():
    rows, key = blinded_rows(
        [("luna", RESULT_PATH, result({"F": "f", "G": "g"}))], secret="s" * 64, include_non_model=False
    )
    assert json.loads(json.dumps(rows)) == rows
    assert {entry["response_id"] for entry in key} == {row["response_id"] for row in rows}
