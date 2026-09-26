import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load("build_luna_v9_development_suite", ROOT / "analysis/build_luna_v9_development_suite.py")
RUNNER = load("run_luna_v9_development", ROOT / "analysis/run_luna_v9_development.py")


def test_v9_development_suite_is_bounded_and_uses_exposed_cases_only():
    suite = BUILDER.build()
    assert suite["status"] == "DEVELOPMENT_ONLY_EXPOSED_CASES"
    assert len(suite["cases"]) == 16
    assert all(case["split"] == "development" for case in suite["cases"])
    assert len({case["case_id"] for case in suite["cases"]}) == 16


def test_reference_corrections_make_units_atomic_and_disposition_mechanical():
    by_source = {case["source_case_id"]: case for case in BUILDER.build()["cases"]}
    assert by_source["Q8H01E"]["expected"]["required_unit_statuses"] == {
        "u-mech": "omitted",
        "u-limit": "incorrect",
    }
    assert by_source["Q8H10E"]["expected"]["required_unit_statuses"]["u-mech"] == "covered"
    for case in by_source.values():
        statuses = list(case["expected"]["required_unit_statuses"].values())
        expected_disposition = (
            "full" if all(item == "covered" for item in statuses)
            else "partial" if any(item == "covered" for item in statuses)
            else "nonanswer"
        )
        assert case["expected"]["disposition"] == expected_disposition


def test_freeze_validation_fails_closed_on_hash_mismatch(tmp_path):
    suite_path = ROOT / "research/explanation_fidelity/qualification/luna-model-judge-v9-development.json"
    freeze = {
        "schema": "crane-luna-judge-development-freeze/v9",
        "status": "FROZEN_BEFORE_ANY_V9_DEVELOPMENT_CALL",
        "suite_sha256": "0" * 64,
        "prompt_sha256": RUNNER.digest_path(RUNNER.PROMPT),
        "output_schema_sha256": RUNNER.digest_path(RUNNER.SCHEMA),
        "caller_source_sha256": RUNNER.digest_path(ROOT / "analysis/luna_model_judge.py"),
        "runner_source_sha256": RUNNER.digest_path(ROOT / "analysis/run_luna_v9_development.py"),
        "suite_builder_sha256": RUNNER.digest_path(RUNNER.BUILDER),
        "model": {"requested_id": "gpt-6-luna", "reasoning_effort": "high"},
        "passes": ["development-pass-1"],
        "confirmatory_use": False,
    }
    path = tmp_path / "freeze.json"
    path.write_text(__import__("json").dumps(freeze), encoding="utf-8")
    try:
        RUNNER.validate_freeze(path, suite_path)
    except ValueError as error:
        assert "suite_sha256" in str(error)
    else:
        raise AssertionError("mismatched suite hash was accepted")
