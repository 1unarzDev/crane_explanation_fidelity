from __future__ import annotations

from pathlib import Path

from analysis.build_contract_complete_luna_qualification_v2 import build_suite, validate
from analysis.run_contract_complete_luna_qualification_v2 import score, validate_freeze


ROOT = Path(__file__).resolve().parents[1]


def judgment(case: dict) -> dict:
    expected = case["expected"]
    return {
        field: expected[field] for field in case["endpoint_scored_fields"]
    } | {
        "material_error_categories": expected["material_error_categories"],
        "correct_abstention": expected["correct_abstention"],
        "answerability": expected["answerability"],
        "required_units": [
            {"unit_id": key, "status": value}
            for key, value in expected["required_unit_statuses"].items()
        ],
    }


def test_v2_uses_fresh_cases_and_question_specific_units() -> None:
    suite = build_suite()
    validate(suite)
    assert len(suite["cases"]) == 12
    assert all(case["case_id"].startswith("CCL2") for case in suite["cases"])
    missing = next(case for case in suite["cases"] if case["variant"] == "missing-evidence-correct")
    units = {unit["unit_id"]: unit["text"] for unit in missing["required_units"]}
    assert "cannot be established" in units["M"]
    assert "zero independent odometry" in units["Q"]
    assert "interval" not in units["Q"]


def test_v2_perfect_endpoint_labels_qualify() -> None:
    suite = build_suite()
    result = score(suite, {case["case_id"]: judgment(case) for case in suite["cases"]})
    assert result["qualified"] is True
    assert all(result["gates"].values())


def test_secondary_category_name_mismatch_does_not_veto_endpoint() -> None:
    suite = build_suite()
    judgments = {case["case_id"]: judgment(case) for case in suite["cases"]}
    target = next(case for case in suite["cases"] if case["variant"] == "unsupported-extra")
    judgments[target["case_id"]]["material_error_categories"] = ["unsupported_identity"]
    result = score(suite, judgments)
    assert result["qualified"] is True
    assert result["secondary_mismatches"]


def test_v2_protected_causal_miss_fails() -> None:
    suite = build_suite()
    judgments = {case["case_id"]: judgment(case) for case in suite["cases"]}
    target = next(case for case in suite["cases"] if case["variant"] == "causal-overclaim")
    judgments[target["case_id"]]["material_error"] = False
    judgments[target["case_id"]]["causal_overclaim"] = False
    result = score(suite, judgments)
    assert result["qualified"] is False
    assert result["gates"]["protected_causal_cases"] is False


def test_v2_freeze_binds_fresh_suite_and_unchanged_judge() -> None:
    suite = ROOT / "research/explanation_fidelity/qualification/contract-complete-luna-qualification-v2.json"
    freeze = ROOT / (
        "research/explanation_fidelity/experiment_configs/prospective/"
        "contract-complete-luna-qualification-v2-freeze.json"
    )
    value = validate_freeze(freeze, suite)
    assert value["model"]["requested_id"] == "gpt-6-luna"
    assert value["confirmatory_alpha_consumed"] == 0.0
