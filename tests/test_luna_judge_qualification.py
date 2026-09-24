from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_luna_judge_qualification.py"
SPEC = importlib.util.spec_from_file_location("run_luna_judge_qualification", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def expected(case):
    return {
        "schema": "crane-luna-model-judge-output/v1",
        "annotation_origin": "automated",
        "arm_id": "luna-model-judge-v1",
        "opaque_response_id": case["case_id"],
        "pass_id": "qualification",
        "rubric": case["rubric"],
        **{field: case["expected"][field] for field in MODULE.CORE_FIELDS},
        "material_error_categories": ["unsupported_fact"] if case["expected"]["material_error"] else [],
        "claims": [],
        "required_units": [
            {
                "unit_id": unit_id,
                "status": status,
                "response_span": None,
                "justification": "Expected qualification fixture status.",
            }
            for unit_id, status in case["expected"]["required_unit_statuses"].items()
        ],
        "evidence_problem_detail": "Packet inconsistency." if case["expected"]["evidence_problem"] else None,
        "unresolved_fields": [],
        "rationale": "Expected qualification fixture judgment.",
    }


def test_suite_is_valid_and_balanced_between_declared_splits():
    suite = MODULE.load_suite()
    development = [case for case in suite["cases"] if case["split"] == "development"]
    heldout = [case for case in suite["cases"] if case["split"] == "heldout"]
    assert len(development) == 14
    assert len(heldout) == 14
    assert not ({case["case_id"] for case in development} & {case["case_id"] for case in heldout})


def test_perfect_expected_judgments_pass_all_gates():
    suite = MODULE.load_suite()
    for split in ("development", "heldout"):
        cases = [case for case in suite["cases"] if case["split"] == split]
        report = MODULE.score(cases, {case["case_id"]: expected(case) for case in cases})
        assert report["qualified"] is True
        assert all(report["gates"].values())


def test_one_false_acceptance_fails_closed():
    suite = MODULE.load_suite()
    cases = [case for case in suite["cases"] if case["split"] == "heldout"]
    judgments = {case["case_id"]: expected(case) for case in cases}
    erroneous = next(case for case in cases if case["expected"]["material_error"] is True)
    judgments[erroneous["case_id"]]["material_error"] = False
    judgments[erroneous["case_id"]]["material_error_categories"] = []
    report = MODULE.score(cases, judgments)
    assert report["qualified"] is False
    assert report["gates"]["zero_false_acceptances"] is False


def test_presentation_pair_disagreement_fails_invariance_gate():
    suite = MODULE.load_suite()
    cases = [case for case in suite["cases"] if case["split"] == "heldout"]
    judgments = {case["case_id"]: expected(case) for case in cases}
    pair = [case for case in cases if case.get("presentation_pair_id") == "heldout-pair-1"]
    judgments[pair[0]["case_id"]]["disposition"] = "partial"
    report = MODULE.score(cases, judgments)
    assert report["qualified"] is False
    assert report["gates"]["presentation_disposition_invariance"] is False
