import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_luna_v10_qualification_suite",
    ROOT / "analysis/build_luna_v10_qualification_suite.py",
)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)

RUN_SPEC = importlib.util.spec_from_file_location(
    "run_luna_v10_qualification",
    ROOT / "analysis/run_luna_v10_qualification.py",
)
RUNNER = importlib.util.module_from_spec(RUN_SPEC)
assert RUN_SPEC.loader is not None
RUN_SPEC.loader.exec_module(RUNNER)


def test_v10_suite_has_fresh_balanced_atomic_inventory():
    suite = BUILDER.build_suite()
    BUILDER.validate(suite)
    cases = suite["cases"]
    assert len(cases) == 26
    assert sum(case["accuracy_eligible"] for case in cases) == 24
    assert len({case["case_id"] for case in cases}) == 26
    assert all(case["split"] == "heldout" for case in cases)
    assert all(case["case_id"].startswith("Q10") for case in cases)


def test_v10_covers_required_campaign_failure_modes():
    families = {case["family"] for case in BUILDER.build_suite()["cases"]}
    assert {
        "persistent_discrepancy",
        "successful_compensation",
        "paired_geometry_abort",
        "paired_execution_abort",
        "nominal_false_premise",
        "missing_decisive_evidence",
        "visible_not_consumed",
        "route_change_without_trigger",
        "logged_obstacle_assertion",
        "ambiguous_motion_measurements",
        "irrelevant_obstacle",
    } <= families


def test_v10_references_preserve_median_scope_and_do_not_reuse_v8_ids():
    cases = BUILDER.build_suite()["cases"]
    serialized = __import__("json").dumps(cases)
    assert "Q8H" not in serialized
    assert "command remained" not in serialized.lower()
    assert "commands coincided" not in serialized.lower()
    persistent = next(case for case in cases if case["case_id"] == "Q10H01S")
    assert persistent["candidate_answer"].count("median") >= 3


def test_v10_freeze_rejects_mismatched_suite_hash(tmp_path):
    suite = ROOT / "research/explanation_fidelity/qualification/luna-model-judge-v10-cases.json"
    freeze = {
        "schema": "crane-luna-judge-freeze/v10",
        "status": "FROZEN_BEFORE_ANY_V10_QUALIFICATION_CALL",
        "suite_sha256": "0" * 64,
        "prompt_sha256": RUNNER.digest_path(RUNNER.PROMPT),
        "output_schema_sha256": RUNNER.digest_path(RUNNER.SCHEMA),
        "caller_source_sha256": RUNNER.digest_path(ROOT / "analysis/luna_model_judge.py"),
        "runner_source_sha256": RUNNER.digest_path(ROOT / "analysis/run_luna_v10_qualification.py"),
        "suite_builder_sha256": RUNNER.digest_path(RUNNER.BUILDER),
        "passes": ["pass-1", "pass-2"],
        "model": {"requested_id": "gpt-6-luna", "reasoning_effort": "high"},
    }
    path = tmp_path / "freeze.json"
    path.write_text(__import__("json").dumps(freeze), encoding="utf-8")
    try:
        RUNNER.validate_freeze(path, suite)
    except ValueError as error:
        assert "suite_sha256" in str(error)
    else:
        raise AssertionError("v10 freeze accepted a mismatched suite")
