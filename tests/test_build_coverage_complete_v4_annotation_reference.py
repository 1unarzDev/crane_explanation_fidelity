import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_coverage_complete_v4_annotation_reference import build  # noqa: E402


CONTRACT = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/development"
        / "coverage-complete-v4-language-screen-v1.json"
    ).read_text()
)
RESULT_ROOT = ROOT / "model_outputs/dev/coverage-complete-v4-language-screen-v1/results"


def _result(case_id: str) -> dict:
    return json.loads((RESULT_ROOT / f"{case_id}.json").read_text())


def test_all_seven_immutable_results_bind_to_corrected_references():
    for case in CONTRACT["cases"]:
        case_id = case["case_id"]
        result = _result(case_id)
        reference = build(CONTRACT, result, case_id)

        assert reference["question_id"] == result["question_id"]
        correction = reference["transport_binding_correction"]
        assert correction["inherited_question_id"] == f"checked-composition:{case_id}"
        assert correction["inherited_canonical_reference_sha256"] == (
            result["inputs"]["annotation_reference_sha256"]
        )
        assert correction["scientific_content_changed"] is False


def test_binding_correction_fails_closed_on_result_hash_mutation():
    case_id = CONTRACT["cases"][0]["case_id"]
    result = copy.deepcopy(_result(case_id))
    result["inputs"]["annotation_reference_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="not bound"):
        build(CONTRACT, result, case_id)


def test_exact_one_shot_result_inventory_has_unique_call_keys():
    results = [_result(case["case_id"]) for case in CONTRACT["cases"]]
    assert len(results) == 7
    assert {item["case_id"] for item in results} == {
        item["case_id"] for item in CONTRACT["cases"]
    }
    assert all(len(item["calls"]) == 1 for item in results)
    keys = [item["calls"][0]["cache_key"] for item in results]
    assert len(keys) == len(set(keys)) == 7
