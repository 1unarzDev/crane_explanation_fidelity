import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_raw_baseline_v5_evidence_closure import build  # noqa: E402


ARM = "raw-baseline-v5-language-screen-v1"
REFERENCE_ROOT = ROOT / f"model_outputs/dev/{ARM}/references"
RAW_ROOT = ROOT / "data/robot_visible/dev/coverage-complete-v5-raw-baseline"


def _build(case: str, raw_name: str):
    raw_path = RAW_ROOT / raw_name
    raw_bytes = raw_path.read_bytes()
    return build(
        json.loads((REFERENCE_ROOT / f"{case}.json").read_text()),
        json.loads(raw_bytes),
        hashlib.sha256(raw_bytes).hexdigest(),
    )


def test_command_closure_exposes_exact_low_cardinality_census_and_record_locators():
    reference = _build("ccv5-missing-odometry-004m", "ccv5-missing-odometry-004m.json")
    closure = reference["allowed_evidence"]["raw_evidence_closure"]
    assert closure["family"] == "command_motion"
    assert closure["command_samples"]["count"] == 414
    assert closure["command_samples"]["exact_speed_frequencies"] == [
        {"planar_speed_mps": 0.0, "count": 3},
        {"planar_speed_mps": 0.26, "count": 411},
    ]
    assert closure["odometry_samples"]["count"] == 0
    method = closure["method_configuration_and_execution"]
    assert method["accepted_goal_record_id"]
    assert method["action_result_record_id"]
    assert "command_samples" not in method and "odometry_samples" not in method


def test_geometry_closure_systematically_covers_route_cells_plans_trajectory_and_bt():
    reference = _build("ccv5-geometry-001", "ccv5-geometry-001.json")
    closure = reference["allowed_evidence"]["raw_evidence_closure"]
    assert closure["family"] == "geometry"
    assert closure["costmap"]["first_direct_route_cost_at_least_253"]["center_x_m"] == 12.42500001378359
    assert closure["costmap"]["first_direct_route_cost_254"]["center_x_m"] == pytest.approx(
        13.175, abs=1e-6
    )
    assert len(closure["plans"]) == 3
    assert closure["plans"][1]["wallSeconds"] == pytest.approx(24.674, abs=0.001)
    assert closure["trajectory"]["maximum_y"]["y"] > 1.3
    assert closure["trajectory"]["minimum_y"]["y"] < -1.32
    assert closure["behavior_tree_capture"]["orderedTransitions"]
    assert reference["completeness_audit"]["systematic_raw_evidence_closure"] is True


def test_masked_geometry_closure_does_not_reintroduce_costmap_cells():
    reference = _build(
        "ccv5-geometry-masked-001m", "ccv5-geometry-masked-001m.json"
    )
    costmap = reference["allowed_evidence"]["raw_evidence_closure"]["costmap"]
    assert costmap["cell_payload_available"] is False
    assert costmap["full_grid_cost_histogram"] is None
    assert all(item["cost"] is None for item in costmap["requested_direct_route_cells"])
