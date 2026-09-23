import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import zlib


SCRIPT = Path(__file__).parents[1] / "analysis" / "export_geometric_route_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("export_geometric_route_diagnostic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_export_uses_only_robot_visible_inputs_and_preserves_connected_grid(tmp_path):
    raw = bytes([254 if index == 2 * 10 + 4 else 0 for index in range(50)])
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "goal": {"position": {"x": 8.5, "y": 2.5}, "yaw": 0.0},
        "initialPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "actionResultPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "status": "aborted",
        "wallSeconds": 70.8,
        "trajectory": [
            {"x": 0.5, "y": 2.5},
            {"x": 4.0, "y": 4.0},
        ],
        "behaviorTreeTransitionCounts": {"ComputePathToPose:RUNNING->SUCCESS": 3},
        "behaviorTreeCapture": {"completeness": {"terminalTransitionObserved": False}},
        "latestCostmapSnapshot": {
            "frameId": "odom",
            "stamp": {"sec": 70, "nanosec": 0},
            "resolution": 1.0,
            "sizeX": 10,
            "sizeY": 5,
            "origin": {"x": 0.0, "y": 0.0, "yaw": 0.0},
            "dataEncoding": "base64+zlib+uint8-row-major",
            "dataSha256": hashlib.sha256(raw).hexdigest(),
            "data": base64.b64encode(zlib.compress(raw)).decode("ascii"),
        },
    }), encoding="utf-8")
    nav2_config = tmp_path / "nav2.yaml"
    nav2_config.write_text("robot_radius: 0.22\n", encoding="utf-8")
    bt_xml = tmp_path / "tree.xml"
    bt_xml.write_text('<Timeout msec="70000"/>\n', encoding="utf-8")
    payload = MODULE.export(
        fixture,
        "land-blockage-global-002",
        nav2_config,
        bt_xml,
        robot_radius_m=0.22,
        inflation_radius_m=0.55,
        deadline_seconds=70.0,
    )

    assert payload["visibility"] == "robot_visible"
    assert payload["reference_computation"]["direct_route"]["has_lethal_cell"]
    assert payload["reference_computation"]["connected_below_cost_253"]
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["reference_computation"]["status"] == "completed"
    assert "evaluator" not in json.dumps(payload["method_input"]).lower()
    assert payload["final_text_verification"]["accepted"]


def test_export_fails_closed_when_costmap_cell_payload_is_withheld(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "goal": {"position": {"x": 8.5, "y": 2.5}, "yaw": 0.0},
        "initialPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "actionResultPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "status": "aborted",
        "wallSeconds": 70.8,
        "trajectory": [{"x": 0.5, "y": 2.5}, {"x": 4.0, "y": 4.0}],
        "behaviorTreeTransitionCounts": {"ComputePathToPose:RUNNING->SUCCESS": 3},
        "behaviorTreeCapture": {"completeness": {"terminalTransitionObserved": False}},
        "latestCostmapSnapshot": {
            "frameId": "odom",
            "stamp": {"sec": 70, "nanosec": 0},
            "resolution": 1.0,
            "sizeX": 10,
            "sizeY": 5,
            "origin": {"x": 0.0, "y": 0.0, "yaw": 0.0},
            "dataEncoding": "base64+zlib+uint8-row-major",
            "dataSha256": "a" * 64
        },
    }), encoding="utf-8")
    nav2_config = tmp_path / "nav2.yaml"
    nav2_config.write_text("robot_radius: 0.22\n", encoding="utf-8")
    bt_xml = tmp_path / "tree.xml"
    bt_xml.write_text('<Timeout msec="70000"/>\n', encoding="utf-8")

    payload = MODULE.export(
        fixture,
        "masked-episode",
        nav2_config,
        bt_xml,
        robot_radius_m=0.22,
        inflation_radius_m=0.55,
        deadline_seconds=70.0,
    )

    assert payload["method_input"]["costmap_payload_available"] is False
    assert payload["method_input"]["costmap_data_sha256_verified"] is False
    assert payload["reference_computation"]["status"] == "not_run_missing_costmap_cell_payload"
    assert payload["diagnostic_result"]["disposition"] == "insufficient"
    assert "direct-route cost classification" in payload["diagnostic_result"]["limits"]
    assert "retained-grid connectivity" in payload["diagnostic_result"]["limits"]
    assert payload["diagnostic_result"]["mechanism"] == (
        "deadline_aligned_abort_with_unresolved_geometry"
    )
    assert "action abort was aligned" in payload["diagnostic_result"]["diagnosis"]
    assert payload["final_text_verification"]["accepted"]
