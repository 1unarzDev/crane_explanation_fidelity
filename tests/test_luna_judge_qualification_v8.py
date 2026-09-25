from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "analysis/run_luna_judge_qualification_v8.py"
BUILDER_PATH = ROOT / "analysis/build_luna_v8_qualification_suite.py"
SUITE_PATH = (
    ROOT
    / "research/explanation_fidelity/qualification/luna-model-judge-v8-cases.json"
)
FREEZE_PATH = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective/"
    "luna-model-judge-v8-endpoint-first-freeze.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("run_luna_judge_qualification_v8", RUNNER_PATH)
BUILDER = load_module("build_luna_v8_qualification_suite", BUILDER_PATH)


def expected_judgment(case):
    expected = case["expected"]
    return {
        **{field: expected[field] for field in RUNNER.CORE_FIELDS},
        "required_units": [
            {"unit_id": unit_id, "status": status}
            for unit_id, status in expected["required_unit_statuses"].items()
        ],
    }


def perfect(suite):
    return {case["case_id"]: expected_judgment(case) for case in suite["cases"]}


def test_builder_reproduces_checked_in_suite_and_registered_denominators():
    checked_in = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    built = BUILDER.build_suite()
    BUILDER.validate(built)
    assert built == checked_in
    assert len(built["cases"]) == 52
    assert sum(case["accuracy_eligible"] for case in built["cases"]) == 48
    assert sum(not case["accuracy_eligible"] for case in built["cases"]) == 4


def test_freeze_pins_suite_runner_builder_prompt_schema_and_caller():
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert RUNNER.validate_freeze(freeze, SUITE_PATH) == "high"
    assert freeze["qualification_suite"]["model_executions_at_freeze"] == 0
    assert freeze["hard_stop"].startswith("Run exactly two isolated passes once")


def test_perfect_reference_passes_with_balanced_classes_and_uncertainty():
    suite = RUNNER.load_suite()
    report = RUNNER.score(suite, perfect(suite))
    assert report["qualified"] is True
    assert report["composite"]["successes"] == 48
    assert report["composite"]["total"] == 48
    assert report["classwise"]["reference_composite_success"]["total"] == 24
    assert report["classwise"]["reference_composite_failure"]["total"] == 24
    assert report["factual_false_rejections"]["total"] == 24
    assert report["unsupported_false_acceptances"]["total"] == 24
    assert report["unsupported_false_acceptances"]["upper"] > 0


def test_auxiliary_cases_do_not_enter_accuracy_or_error_denominators():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    baseline = RUNNER.score(suite, judgments)
    judgments["Q8P011"]["material_error"] = True
    changed = RUNNER.score(suite, judgments)
    assert changed["composite"] == baseline["composite"]
    assert changed["required_units"] == baseline["required_units"]
    assert changed["core_fields"] == baseline["core_fields"]
    assert changed["factual_false_rejections"] == baseline["factual_false_rejections"]
    assert changed["unsupported_false_acceptances"] == baseline["unsupported_false_acceptances"]
    assert changed["gates"]["protected_tests"] is False


def test_truthful_omission_is_composite_failure_without_material_error():
    suite = RUNNER.load_suite()
    case = next(case for case in suite["cases"] if case["case_id"] == "Q8P011")
    expected = case["expected"]
    assert expected["material_error"] is False
    assert expected["mechanism_identification"] == "omitted"
    assert RUNNER.composite_success(expected) is False


def test_limitation_answers_and_speculation_use_rubric_abstention_semantics():
    suite = RUNNER.load_suite()
    for case in suite["cases"]:
        unit_ids = {item["unit_id"] for item in case["required_units"]}
        if not case["accuracy_eligible"] or not unit_ids & {"u-limit", "u-scope"}:
            continue
        if case["expected"]["material_error"]:
            assert case["expected"]["correct_abstention"] is False
        else:
            assert case["expected"]["correct_abstention"] is True


def test_reference_arithmetic_for_decisive_comparisons():
    suite = RUNNER.load_suite()
    by_id = {case["case_id"]: case for case in suite["cases"]}
    assert round(0.91 - 0.79, 2) == 0.12
    assert "0.12 m" in by_id["Q8H02S"]["candidate_answer"]
    assert round(16.9 - 13.2, 1) == 3.7
    assert "3.7 m" in by_id["Q8H03S"]["candidate_answer"]
    assert round(42.3 - 42.1, 1) == 0.2
    assert "0.2 s" in by_id["Q8H05S"]["candidate_answer"]
    assert round(0.90 - 0.76, 2) == 0.14
    assert "0.14 m" in by_id["Q8P021"]["required_units"][0]["text"]


def test_secondary_disposition_mismatch_does_not_fail_protected_boundary():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    judgments["Q8H01E"]["disposition"] = "nonanswer"
    report = RUNNER.score(suite, judgments)
    assert report["case_results"][1]["core_field_matches"]["disposition"] is False
    assert report["gates"]["protected_tests"] is True


def test_material_or_declared_boundary_unit_error_fails_protected_boundary():
    suite = RUNNER.load_suite()
    material = perfect(suite)
    material["Q8H01E"]["material_error"] = False
    material_report = RUNNER.score(suite, material)
    assert material_report["gates"]["protected_tests"] is False
    assert "Q8H01E" in material_report["protected_failures"]["protected_boundary"]

    unit = perfect(suite)
    for item in unit["Q8H01E"]["required_units"]:
        if item["unit_id"] == "u-limit":
            item["status"] = "omitted"
    unit_report = RUNNER.score(suite, unit)
    assert unit_report["gates"]["protected_tests"] is False
    assert "Q8H01E" in unit_report["protected_failures"]["protected_boundary"]


def test_protected_causal_uses_only_predeclared_endpoint_predicates():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    judgments["Q8H01E"]["mechanism_identification"] = "incorrect"
    report = RUNNER.score(suite, judgments)
    assert report["gates"]["protected_tests"] is True
    judgments["Q8H01E"]["causal_overclaim"] = False
    assert RUNNER.score(suite, judgments)["gates"]["protected_tests"] is False


def test_five_percent_false_acceptance_cap_allows_one_of_24_but_rejects_two():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    judgments["Q8H19E"]["material_error"] = False
    one = RUNNER.score(suite, judgments)
    assert one["unsupported_false_acceptances"]["errors"] == 1
    assert one["unsupported_false_acceptances"]["rate"] == 1 / 24
    assert one["gates"]["unsupported_false_acceptance_rate"] is True

    judgments["Q8H02E"]["material_error"] = False
    two = RUNNER.score(suite, judgments)
    assert two["unsupported_false_acceptances"]["errors"] == 2
    assert two["unsupported_false_acceptances"]["rate"] == 2 / 24
    assert two["gates"]["unsupported_false_acceptance_rate"] is False


def test_invariance_compares_only_registered_endpoint_and_boundary_fields():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    judgments["Q8P011"]["disposition"] = "partial"
    report = RUNNER.score(suite, judgments)
    pair = next(
        item for item in report["presentation_pairs"] if item["pair_id"] == "motion-omission"
    )
    assert pair["invariant"] is True
    judgments["Q8P011"]["evidence_problem"] = True
    assert RUNNER.score(suite, judgments)["gates"]["protected_tests"] is False


def test_judgment_required_unit_inventory_fails_closed():
    suite = RUNNER.load_suite()
    judgments = perfect(suite)
    judgments["Q8H01S"]["required_units"].pop()
    try:
        RUNNER.score(suite, judgments)
    except ValueError as error:
        assert "required-unit inventory differs" in str(error)
    else:
        raise AssertionError("missing required unit was accepted")
