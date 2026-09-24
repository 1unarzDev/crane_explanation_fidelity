from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_luna_judge_qualification_v5.py"
SPEC = importlib.util.spec_from_file_location("run_luna_judge_qualification_v5", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def expected_judgment(case):
    expected = case["expected"]
    return {
        **{field: expected[field] for field in MODULE.CORE_FIELDS},
        "required_units": [
            {"unit_id": unit_id, "status": status}
            for unit_id, status in expected["required_unit_statuses"].items()
        ],
    }


def perfect(suite):
    return {case["case_id"]: expected_judgment(case) for case in suite["cases"]}


def test_suite_has_frozen_balanced_composite_and_protected_denominators():
    suite = MODULE.load_suite()
    eligible = [case for case in suite["cases"] if case["composite_eligible"]]
    successes = [case for case in eligible if MODULE.composite_success(case["expected"])]
    assert len(suite["cases"]) == 24
    assert len(eligible) == 20
    assert len(successes) == 10
    assert suite["thresholds"]["maximum_false_acceptance_rate"] == 0.05


def test_perfect_judgments_pass_and_report_nonzero_uncertainty_for_zero_errors():
    suite = MODULE.load_suite()
    report = MODULE.score(suite, perfect(suite))
    assert report["qualified"] is True
    assert report["composite"]["total"] == 20
    assert report["unsupported_false_acceptances"]["errors"] == 0
    assert report["unsupported_false_acceptances"]["upper"] > 0


def test_one_composite_error_is_exactly_tolerated_but_two_fail():
    suite = MODULE.load_suite()
    judgments = perfect(suite)
    judgments["Q5H011"]["mechanism_identification"] = "correct"
    one = MODULE.score(suite, judgments)
    assert one["composite"]["accuracy"] == 0.95
    assert one["gates"]["composite_accuracy"] is True
    judgments["Q5H012"]["mechanism_identification"] = "correct"
    two = MODULE.score(suite, judgments)
    assert two["composite"]["accuracy"] == 0.90
    assert two["gates"]["composite_accuracy"] is False


def test_one_false_acceptance_exceeds_strict_numerical_cap():
    suite = MODULE.load_suite()
    judgments = perfect(suite)
    judgments["Q5H015"]["material_error"] = False
    report = MODULE.score(suite, judgments)
    assert report["unsupported_false_acceptances"]["total"] == 6
    assert report["unsupported_false_acceptances"]["errors"] == 1
    assert report["gates"]["unsupported_false_acceptance_rate"] is False


def test_false_rejection_margin_is_frozen_at_fifteen_percent():
    suite = MODULE.load_suite()
    judgments = perfect(suite)
    for case_id in ("Q5H001", "Q5H002"):
        judgments[case_id]["material_error"] = True
    two = MODULE.score(suite, judgments)
    assert two["factual_false_rejections"]["total"] == 17
    assert two["gates"]["factual_false_rejection_rate"] is True
    judgments["Q5H003"]["material_error"] = True
    three = MODULE.score(suite, judgments)
    assert three["gates"]["factual_false_rejection_rate"] is False


def test_protected_causal_and_presentation_fail_closed():
    suite = MODULE.load_suite()
    judgments = perfect(suite)
    causal = copy.deepcopy(judgments)
    causal["Q5H013"]["causal_overclaim"] = False
    assert MODULE.score(suite, causal)["gates"]["protected_tests"] is False
    presentation = copy.deepcopy(judgments)
    presentation["Q5H024"]["disposition"] = "partial"
    assert MODULE.score(suite, presentation)["gates"]["protected_tests"] is False
