"""Tests for the model-strength annotation summary deriver.

The strongest check available is that the deriver reproduces the frozen Luna control's retained
summary exactly from that file's own per-response labels. If it does, the Claude arm's summary is
computed by the same arithmetic the frozen selection used.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from derive_control_annotation_summary import UNITS_PER_QUESTION, derive_summary

WORKSPACE = Path(__file__).resolve().parent.parent
LUNA = (
    WORKSPACE
    / "research/explanation_fidelity/annotations/development"
    / "land-nav-provenance-model-strength-luna-v1.json"
)


def label(correct: int, total: int, **overrides):
    return {
        "material_error": False,
        "specificity_correct": correct,
        "specificity_total": total,
    } | overrides


def episode(identifier: str = "e001", **overrides):
    questions = {
        "recovery-mechanism": {condition: label(8, 8) for condition in ("F", "G", "H")},
        "failure-cause": {condition: label(5, 5) for condition in ("F", "G", "H")},
    }
    return {"episode_id": identifier, "questions": questions} | overrides


def test_frozen_inventory_sizes_match_the_guide():
    assert UNITS_PER_QUESTION == {"recovery-mechanism": 8, "failure-cause": 5}


def test_deriver_reproduces_the_retained_luna_control_summary():
    payload = json.loads(LUNA.read_text(encoding="utf-8"))
    assert derive_summary(payload["episodes"]) == payload["summary"]


def test_clean_single_episode_totals():
    summary = derive_summary([episode()])
    assert summary["responses_per_condition"] == 2
    assert summary["specificity_total"] == 13
    assert summary["material_errors"] == {"F": 0, "G": 0, "H": 0}
    assert summary["substantive_coverage"] == {"F": 1.0, "G": 1.0, "H": 1.0}


def test_material_errors_are_counted_per_condition():
    one = episode()
    one["questions"]["recovery-mechanism"]["F"] = label(
        7, 8, material_error=True, error_categories=["unsupported_fact"], rationale="unsupported"
    )
    summary = derive_summary([one])
    assert summary["material_errors"] == {"F": 1, "G": 0, "H": 0}
    assert summary["specificity_correct"]["F"] == 12


def test_abstention_lowers_substantive_coverage():
    one = episode()
    one["questions"]["failure-cause"]["G"] = label(3, 5, substantive_answer=False)
    assert derive_summary([one])["substantive_coverage"]["G"] == pytest.approx(0.5)


def test_wrong_specificity_total_is_rejected_rather_than_summed():
    one = episode()
    one["questions"]["failure-cause"]["F"] = label(5, 8)
    with pytest.raises(SystemExit, match="frozen"):
        derive_summary([one])


def test_specificity_above_the_inventory_is_rejected():
    one = episode()
    one["questions"]["failure-cause"]["F"] = {
        "material_error": False,
        "specificity_correct": 6,
        "specificity_total": 5,
    }
    with pytest.raises(SystemExit, match="exceeds the inventory"):
        derive_summary([one])


def test_material_error_without_a_category_is_rejected():
    one = episode()
    one["questions"]["failure-cause"]["F"] = label(5, 5, material_error=True, rationale="x")
    with pytest.raises(SystemExit, match="without a category"):
        derive_summary([one])


def test_material_error_without_a_rationale_is_rejected():
    one = episode()
    one["questions"]["failure-cause"]["F"] = label(
        5, 5, material_error=True, error_categories=["unsupported_fact"]
    )
    with pytest.raises(SystemExit, match="without a rationale"):
        derive_summary([one])


def test_missing_condition_is_rejected():
    one = episode()
    del one["questions"]["failure-cause"]["H"]
    with pytest.raises(SystemExit, match="exactly F/G/H"):
        derive_summary([one])
