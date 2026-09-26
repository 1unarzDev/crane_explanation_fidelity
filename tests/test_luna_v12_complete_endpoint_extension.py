from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load(
    "build_luna_v12_complete_endpoint_extension",
    ROOT / "analysis/build_luna_v12_complete_endpoint_extension.py",
)
RUNNER = load(
    "run_luna_v12_complete_endpoint_extension",
    ROOT / "analysis/run_luna_v12_complete_endpoint_extension.py",
)


def judgment(case: dict) -> dict:
    expected = case["expected"]
    return {
        field: expected[field]
        for field in case["scored_core_fields"]
    } | {
        "required_units": [
            {"unit_id": unit_id, "status": status}
            for unit_id, status in expected["required_unit_statuses"].items()
        ]
    }


def test_suite_is_balanced_across_three_families_and_omission_types():
    suite = BUILDER.build_suite()
    BUILDER.validate(suite)
    cases = suite["cases"]

    assert len(cases) == 18
    assert {case["family"] for case in cases} == {"geometry", "persistent", "recovery"}
    assert sum(case["variant"].startswith("full-") for case in cases) == 9
    assert sum(case["variant"] == "omit-measurement" for case in cases) == 3
    assert sum(case["variant"] == "omit-outcome" for case in cases) == 3
    assert sum(case["variant"] == "omit-limit" for case in cases) == 3
    assert all(len(case["complete_endpoint_unit_ids"]) == 4 for case in cases)


def test_complete_endpoint_distinguishes_full_from_each_omission():
    suite = BUILDER.build_suite()
    for case in suite["cases"]:
        actual = judgment(case)
        expected_success = case["variant"].startswith("full-")
        assert RUNNER.complete_success(case, actual) is expected_success


def test_perfect_expected_judgments_pass_all_gates():
    suite = BUILDER.build_suite()
    result = RUNNER.score(
        suite,
        {case["case_id"]: judgment(case) for case in suite["cases"]},
    )
    assert result["qualified"] is True
    assert all(result["gates"].values())


def test_systematic_measurement_omission_failure_is_not_qualified():
    suite = BUILDER.build_suite()
    judgments = {case["case_id"]: judgment(case) for case in suite["cases"]}
    for case in suite["cases"]:
        if case["variant"] == "omit-measurement":
            unit = next(
                item
                for item in judgments[case["case_id"]]["required_units"]
                if item["unit_id"] == "u-measurement"
            )
            unit["status"] = "covered"
    result = RUNNER.score(suite, judgments)
    assert result["qualified"] is False
    assert result["gates"]["omission_categories"] is False
