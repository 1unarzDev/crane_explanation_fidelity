import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_diagnostic_land_pilot.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("run_diagnostic_land_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_no_diagnostic_presentation_drops_costmap_payload_and_derived_claims():
    fixture = {
        "status": "aborted",
        "wallSeconds": 70.8,
        "goal": {"position": {"x": 18.0, "y": 0.0}},
        "initialPose": {"x": 0.0, "y": 0.0},
        "actionResultPose": {"x": -1.0, "y": -2.0},
        "trajectory": [{"x": 0.0, "y": 0.0}, {"x": 6.0, "y": -2.0}],
        "latestCostmapSnapshot": {
            "data": "secret-compressed-cells",
            "dataSha256": "a" * 64,
            "frameId": "odom",
        },
        "costmapObservations": 3,
        "maximumOccupiedCostmapCells": 7,
        "costmapProvenance": "delivered-not-proven-consumed",
        "behaviorTreeTransitionCounts": {"ComputePathToPose:RUNNING->SUCCESS": 2},
        "behaviorTreeCapture": {"completeness": {"terminalTransitionObserved": False}},
    }
    root = Path(__file__).parents[1]
    result = MODULE.no_diagnostic_presentation(
        fixture,
        root / "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        root / "packages/crane_ml/Tools/Performance/nav2_warehouse_replanning_deadline.xml",
    )

    assert "data" not in result["costmap_delivery"]["latest_snapshot_metadata"]
    assert result["costmap_delivery"]["decoded_route_or_connectivity_computation"] is None
    assert "connected" not in str(result["costmap_delivery"]).lower()
    assert result["execution"]["trajectory_bounds"]["max_y"] == 0.0


def test_caller_factory_rejects_unknown_provider(tmp_path):
    try:
        MODULE.caller_for("unknown", tmp_path, "model", "low")
    except ValueError as error:
        assert "unsupported provider" in str(error)
    else:
        raise AssertionError("unknown provider was accepted")
