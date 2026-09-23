import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import zlib

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "export_geometric_route_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("export_geometric_route_diagnostic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _retained_plan(points, wall_seconds):
    canonical = json.dumps(points, sort_keys=True, separators=(",", ":")).encode("utf-8")
    length = sum(
        ((end["x"] - start["x"]) ** 2 + (end["y"] - start["y"]) ** 2) ** 0.5
        for start, end in zip(points, points[1:])
    )
    signed = [point["y"] for point in points]
    return {
        "wallSeconds": wall_seconds,
        "pathId": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
        "poseCount": len(points),
        "plannedLengthMeters": length,
        "minimumSignedLateralDeviationFromRequestedRouteMeters": min(signed),
        "maximumSignedLateralDeviationFromRequestedRouteMeters": max(signed),
        "maximumAbsLateralDeviationFromRequestedRouteMeters": max(map(abs, signed)),
        "poses": points,
    }


def _successful_plan_change_fixture():
    raw = bytes([0] * 25)
    direct = [{"x": 0.5, "y": 0.0}, {"x": 8.5, "y": 0.0}]
    detour = [
        {"x": 0.5, "y": 0.0},
        {"x": 4.5, "y": 1.0},
        {"x": 8.5, "y": 0.0},
    ]
    return {
        "goal": {"position": {"x": 8.5, "y": 0.0}, "yaw": 0.0},
        "initialPose": {"x": 0.5, "y": 0.0, "yaw": 0.0},
        "actionResultPose": {"x": 8.4, "y": 0.0, "yaw": 0.0},
        "status": "succeeded",
        "wallSeconds": 42.0,
        "trajectory": [
            {"x": 0.5, "y": 0.0},
            {"x": 4.5, "y": 0.9},
            {"x": 8.4, "y": 0.0},
        ],
        "planHistory": [
            _retained_plan(direct, 0.1),
            _retained_plan(detour, 1.0),
        ],
        "planHistoryProvenance": {
            "interpretation": "delivered-global-plan-not-proven-controller-consumed"
        },
        "behaviorTreeTransitionCounts": {"ComputePathToPose:RUNNING->SUCCESS": 2},
        "behaviorTreeCapture": {"completeness": {"terminalTransitionObserved": False}},
        "latestCostmapSnapshot": {
            "frameId": "odom",
            "stamp": {"sec": 42, "nanosec": 0},
            "resolution": 1.0,
            "sizeX": 5,
            "sizeY": 5,
            "origin": {"x": 4.0, "y": -2.0, "yaw": 0.0},
            "dataEncoding": "base64+zlib+uint8-row-major",
            "dataSha256": hashlib.sha256(raw).hexdigest(),
            "data": base64.b64encode(zlib.compress(raw)).decode("ascii"),
        },
    }


def _source_files(tmp_path):
    nav2_config = tmp_path / "nav2.yaml"
    nav2_config.write_text("robot_radius: 0.22\n", encoding="utf-8")
    bt_xml = tmp_path / "tree.xml"
    bt_xml.write_text('<Timeout msec="70000"/>\n', encoding="utf-8")
    return nav2_config, bt_xml


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
    assert payload["reference_computation"]["direct_route"]["fully_covered"]
    assert payload["reference_computation"]["connected_below_cost_253"]
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["reference_computation"]["status"] == "completed"
    assert "evaluator" not in json.dumps(payload["method_input"]).lower()
    assert payload["final_text_verification"]["accepted"]


def test_export_fails_closed_when_rolling_grid_does_not_cover_direct_route(tmp_path):
    raw = bytes([0] * 25)
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "goal": {"position": {"x": 8.5, "y": 2.5}, "yaw": 0.0},
        "initialPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "actionResultPose": {"x": 4.5, "y": 2.5, "yaw": 0.0},
        "status": "aborted",
        "wallSeconds": 70.8,
        "trajectory": [{"x": 0.5, "y": 2.5}, {"x": 4.5, "y": 2.5}],
        "behaviorTreeTransitionCounts": {"ComputePathToPose:RUNNING->SUCCESS": 3},
        "behaviorTreeCapture": {"completeness": {"terminalTransitionObserved": False}},
        "latestCostmapSnapshot": {
            "frameId": "odom",
            "stamp": {"sec": 70, "nanosec": 0},
            "resolution": 1.0,
            "sizeX": 5,
            "sizeY": 5,
            "origin": {"x": 4.0, "y": 0.0, "yaw": 0.0},
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
        "partial-grid",
        nav2_config,
        bt_xml,
        robot_radius_m=0.22,
        inflation_radius_m=0.55,
        deadline_seconds=70.0,
    )

    direct = payload["reference_computation"]["direct_route"]
    assert direct["fully_covered"] is False
    assert direct["has_lethal_cell"] is None
    assert direct["minimum_lethal_clearance_m"] is None
    assert payload["diagnostic_result"]["disposition"] == "insufficient"
    assert "direct-route cost classification" in payload["diagnostic_result"]["limits"]


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


def test_export_rejects_false_failure_premise_for_successful_action(tmp_path):
    raw = bytes([0] * 50)
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "goal": {"position": {"x": 8.5, "y": 2.5}, "yaw": 0.0},
        "initialPose": {"x": 0.5, "y": 2.5, "yaw": 0.0},
        "actionResultPose": {"x": 8.3, "y": 2.5, "yaw": 0.0},
        "status": "succeeded",
        "wallSeconds": 69.9,
        "trajectory": [{"x": 0.5, "y": 2.5}, {"x": 8.3, "y": 2.5}],
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
        "successful-nominal",
        nav2_config,
        bt_xml,
        robot_radius_m=0.22,
        inflation_radius_m=0.55,
        deadline_seconds=70.0,
    )

    result = payload["diagnostic_result"]
    assert result["disposition"] == "not_triggered"
    assert result["mechanism"] == "no_failure_observed"
    assert "failure premise is false" in payload["final_answer"]
    assert "action_status=succeeded status" in payload["final_answer"]
    assert "direct_route_minimum_clearance" not in payload["final_answer"]
    assert payload["final_text_verification"]["accepted"]


def test_v2_export_reports_successful_plan_change_with_partial_rolling_grid(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(_successful_plan_change_fixture()), encoding="utf-8"
    )
    nav2_config, bt_xml = _source_files(tmp_path)

    payload = MODULE.export(
        fixture,
        "successful-plan-change",
        nav2_config,
        bt_xml,
        robot_radius_m=0.22,
        inflation_radius_m=0.55,
        deadline_seconds=70.0,
        computation_version="geometric-route-restriction-v2",
    )

    assert payload["reference_computation"]["direct_route"]["fully_covered"] is False
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["diagnostic_result"]["mechanism"] == (
        "recorded_plan_change_with_unresolved_physical_trigger"
    )
    assert payload["method_input"]["delivered_plan_geometry"]["summary_parity_passed"]
    assert "successful route change" in payload["final_answer"]
    assert "does not prove controller consumption" in payload["final_answer"]
    assert payload["final_text_verification"]["accepted"]


def test_v2_export_fails_closed_when_plan_poses_are_missing(tmp_path):
    fixture_payload = _successful_plan_change_fixture()
    fixture_payload["planHistory"][0].pop("poses")
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(fixture_payload), encoding="utf-8")
    nav2_config, bt_xml = _source_files(tmp_path)

    with pytest.raises(ValueError, match="requires retained delivered plan poses"):
        MODULE.export(
            fixture,
            "missing-plan-poses",
            nav2_config,
            bt_xml,
            robot_radius_m=0.22,
            inflation_radius_m=0.55,
            deadline_seconds=70.0,
            computation_version="geometric-route-restriction-v2",
        )


def test_v2_export_fails_closed_when_retained_plan_summary_is_tampered(tmp_path):
    fixture_payload = _successful_plan_change_fixture()
    fixture_payload["planHistory"][1]["plannedLengthMeters"] += 0.1
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(fixture_payload), encoding="utf-8")
    nav2_config, bt_xml = _source_files(tmp_path)

    with pytest.raises(ValueError, match="retained summary mismatch"):
        MODULE.export(
            fixture,
            "tampered-plan-summary",
            nav2_config,
            bt_xml,
            robot_radius_m=0.22,
            inflation_radius_m=0.55,
            deadline_seconds=70.0,
            computation_version="geometric-route-restriction-v2",
        )
