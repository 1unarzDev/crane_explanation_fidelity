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
        "planHistoryProvenance": "delivered-plan-not-proven-controller-consumed",
        "planHistory": [
            {
                "wallSeconds": 1.0,
                "pathId": "sha256:" + "b" * 64,
                "poseCount": 2,
                "plannedLengthMeters": 8.0,
                "minimumSignedLateralDeviationFromRequestedRouteMeters": 0.0,
                "maximumSignedLateralDeviationFromRequestedRouteMeters": 0.0,
                "maximumAbsLateralDeviationFromRequestedRouteMeters": 0.0,
                "poses": [{"x": 0.0, "y": 0.0}, {"x": 8.0, "y": 0.0}],
            }
        ],
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
    assert result["delivered_plan_summaries"]["records"][0]["poseCount"] == 2
    assert "poses" not in result["delivered_plan_summaries"]["records"][0]
    assert result["delivered_plan_summaries"]["retained_poses_supplied"] is False
    assert (
        result["delivered_plan_summaries"]["independent_summary_recomputation_supplied"]
        is False
    )


def test_caller_factory_rejects_unknown_provider(tmp_path):
    try:
        MODULE.caller_for("unknown", tmp_path, "model", "low")
    except ValueError as error:
        assert "unsupported provider" in str(error)
    else:
        raise AssertionError("unknown provider was accepted")


def test_repository_prompt_v2_resolves_episode_without_unresolved_placeholders():
    result = MODULE.load_prompt(
        "diagnostic_repository_agent_dev_v2.txt",
        {"QUESTION": "Why?", "EPISODE_ID": "masked-episode"},
    )

    assert "--episode-id masked-episode" in result
    assert "Question: Why?" in result
    assert "{{" not in result


def test_plan_geometry_repository_prompt_uses_exact_v2_runtime_contract():
    result = MODULE.load_prompt(
        "diagnostic_repository_agent_plan_geometry_dev_v1.txt",
        {"QUESTION": "What changed?", "EPISODE_ID": "diagnostic-land-dev-004"},
    )

    assert "--episode-id diagnostic-land-dev-004" in result
    assert "--computation-version geometric-route-restriction-v2" in result
    assert "nav2_roboboat_distance_replanning.xml" in result
    assert "--deadline-seconds 100" in result
    assert "Question: What changed?" in result
    assert "{{" not in result


def test_cli_accepts_versioned_realization_prompt(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--fixture", "fixture.json",
            "--diagnostic", "diagnostic.json",
            "--nav2-config", "nav2.yaml",
            "--bt-xml", "tree.xml",
            "--repository", "crane_ml",
            "--repository-url", "https://example.invalid/crane_ml.git",
            "--repository-commit", "a" * 40,
            "--core-repository", "crane_explain",
            "--core-repository-commit", "b" * 40,
            "--provider", "codex",
            "--model", "gpt-6-sol",
            "--cache", str(tmp_path / "cache"),
            "--output", str(tmp_path / "output.json"),
            "--realization-prompt", "diagnostic_realization_dev_v2.txt",
        ],
    )

    args = MODULE.parse_args()

    assert args.realization_prompt == "diagnostic_realization_dev_v2.txt"
