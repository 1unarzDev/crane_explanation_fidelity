from __future__ import annotations

from pathlib import Path

from analysis.build_contract_complete_luna_qualification import build_suite, validate
from analysis.run_contract_complete_luna_qualification import score, validate_freeze


ROOT = Path(__file__).resolve().parents[1]


def expected_judgment(case: dict) -> dict:
    expected = case["expected"]
    return {
        field: expected[field] for field in case["scored_core_fields"]
    } | {
        "required_units": [
            {"unit_id": unit_id, "status": status}
            for unit_id, status in expected["required_unit_statuses"].items()
        ]
    }


def test_contract_qualification_covers_declared_failure_modes() -> None:
    suite = build_suite()
    validate(suite)

    assert len(suite["cases"]) == 12
    assert {case["variant"] for case in suite["cases"]} >= {
        "full-supported",
        "omit-measurement",
        "wrong-measurement",
        "recovery-outcome-limit",
        "unsupported-causal-connective",
        "missing-decisive-evidence",
        "valid-extra-fact",
        "unsupported-extra-fact",
        "instruction-in-evidence",
    }
    assert all(
        [unit["unit_id"] for unit in case["required_units"]] == ["M", "Q", "O", "L"]
        for case in suite["cases"]
    )


def test_perfect_contract_qualification_labels_pass_every_gate() -> None:
    suite = build_suite()
    result = score(
        suite,
        {case["case_id"]: expected_judgment(case) for case in suite["cases"]},
    )

    assert result["qualified"] is True
    assert all(result["gates"].values())
    assert result["endpoint_changing_errors"] == []


def test_causal_false_acceptance_fails_protected_gate() -> None:
    suite = build_suite()
    judgments = {
        case["case_id"]: expected_judgment(case) for case in suite["cases"]
    }
    case = next(
        case for case in suite["cases"]
        if case["variant"] == "unsupported-causal-connective"
    )
    judgment = judgments[case["case_id"]]
    judgment["material_error"] = False
    judgment["causal_overclaim"] = False
    judgment["material_error_categories"] = []
    for unit in judgment["required_units"]:
        if unit["unit_id"] == "L":
            unit["status"] = "covered"

    result = score(suite, judgments)
    assert result["qualified"] is False
    assert result["gates"]["protected_causal_cases"] is False


def test_frozen_qualification_binds_the_executable_resources() -> None:
    suite = ROOT / "research/explanation_fidelity/qualification/contract-complete-luna-qualification-v1.json"
    freeze = ROOT / (
        "research/explanation_fidelity/experiment_configs/prospective/"
        "contract-complete-luna-qualification-v1-freeze.json"
    )
    value = validate_freeze(freeze, suite)
    assert value["passes"] == ["pass-1", "pass-2"]
    assert value["confirmatory_alpha_consumed"] == 0.0
