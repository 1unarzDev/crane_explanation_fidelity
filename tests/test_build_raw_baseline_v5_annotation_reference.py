import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_raw_baseline_v5_annotation_reference import build  # noqa: E402


CONTRACT = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/development"
        / "raw-baseline-v5-language-screen-v1.json"
    ).read_text()
)
RESULT_ROOT = ROOT / "model_outputs/dev/raw-baseline-v5-language-screen-v1/results"


def _keys(value):
    if isinstance(value, dict):
        result = set(value)
        for item in value.values():
            result |= _keys(item)
        return result
    if isinstance(value, list):
        result = set()
        for item in value:
            result |= _keys(item)
        return result
    return set()


def test_references_bind_raw_evidence_and_exclude_proposed_diagnostic_as_gold():
    for case in CONTRACT["cases"]:
        result = json.loads((RESULT_ROOT / f"{case['case_id']}.json").read_text())
        reference = build(CONTRACT, result, case["case_id"])
        allowed = reference["allowed_evidence"]
        assert "primitive_diagnostic" not in allowed
        assert "diagnostic_result" not in _keys(allowed)
        assert "reference_computation" not in _keys(allowed)
        binding = allowed["raw_robot_visible_evidence_binding"]
        assert binding["raw_evidence_sha256"] == case["baseline_evidence_sha256"]
        assert binding["visibility"] == "robot_visible"
        audit = reference["completeness_audit"]
        assert audit["raw_baseline_hash_verified"] is True
        assert audit["proposed_diagnostic_excluded_from_gold"] is True
        assert audit["evaluator_truth_excluded"] is True


def test_geometry_binding_does_not_embed_large_costmap_cells():
    case = next(item for item in CONTRACT["cases"] if item["case_id"] == "ccv5-geometry-001")
    result = json.loads((RESULT_ROOT / f"{case['case_id']}.json").read_text())
    reference = build(CONTRACT, result, case["case_id"])
    binding = reference["allowed_evidence"]["raw_robot_visible_evidence_binding"]
    inventory = binding["raw_geometry_inventory"]
    assert inventory["costmap_cell_payload_present"] is True
    assert "data" not in inventory["costmap_metadata"]
    assert inventory["costmap_metadata"]["dataSha256"]
