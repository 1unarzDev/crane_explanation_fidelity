import hashlib
import json
from pathlib import Path

from aggregate_luna_v7_endpoint_extension import aggregate, round_up_four


ROOT = Path(__file__).resolve().parents[1]


def _base():
    row = {
        "qualified": True, "composite_correct": 20, "composite_total": 20,
        "required_unit_correct": 32, "required_unit_total": 32,
        "core_correct": 176, "core_total": 187,
        "false_rejections": 0, "factual_total": 17,
        "false_acceptances": 0, "unsupported_total": 6,
        "protected_failures": 0,
    }
    return {"status": "HELDOUT_QUALIFIED", "passes": {"pass_1": row, "pass_2": row}}


def _extension(*, false_acceptances=0):
    row = {
        "qualified": false_acceptances == 0,
        "composite": {"successes": 20, "total": 20},
        "required_units": {"successes": 30, "total": 30},
        "core_fields": {"successes": 180, "total": 190},
        "factual_false_rejections": {"errors": 0, "total": 10},
        "unsupported_false_acceptances": {"errors": false_acceptances, "total": 14},
        "protected_failures": {}, "call_failure_count": 0,
    }
    return {"status": "QUALIFIED" if false_acceptances == 0 else "FAILED", "passes": {"pass-1": row, "pass-2": row}}


def test_aggregate_adds_all_denominators_and_shrinks_zero_error_bounds():
    result = aggregate(_base(), _extension())
    assert result["status"] == "QUALIFIED_AGGREGATE"
    assert result["passes"]["pass_1"]["factual_total"] == 27
    assert result["passes"]["pass_1"]["unsupported_total"] == 20
    assert result["largest_pass_specific_sensitivity_upper_bounds"]["false_acceptance"] == 0.1612
    assert result["largest_pass_specific_sensitivity_upper_bounds"]["false_rejection"] == 0.1246


def test_failed_extension_is_retained_and_cannot_amend_bounds():
    result = aggregate(_base(), _extension(false_acceptances=1))
    assert result["status"] == "FAILED_EXTENSION_RETAIN_PRIOR_V7"
    assert result["eligible_for_prospective_amendment"] is False


def test_upward_rounding_is_conservative():
    assert round_up_four(0.1611251) == 0.1612


def test_extension_freeze_hashes_and_case_inventory_are_closed():
    freeze = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/luna-model-judge-v7-endpoint-threat-extension-1-freeze.json").read_text())
    suite_path = ROOT / freeze["inputs"]["extension_suite_path"]
    assert hashlib.sha256(suite_path.read_bytes()).hexdigest() == freeze["inputs"]["extension_suite_sha256"]
    suite = json.loads(suite_path.read_text())
    prior = json.loads((ROOT / "research/explanation_fidelity/qualification/luna-model-judge-v7-cases.json").read_text())
    assert {case["case_id"] for case in suite["cases"]}.isdisjoint(
        {case["case_id"] for case in prior["cases"]}
    )
    assert len(suite["cases"]) == 24
    assert sum(case["composite_eligible"] for case in suite["cases"]) == 20
    assert sum(case["expected"]["material_error"] is False for case in suite["cases"]) == 10
    assert sum(case["expected"]["material_error"] is True for case in suite["cases"]) == 14
