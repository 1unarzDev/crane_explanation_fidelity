import hashlib
import json

from reference_land_plan_geometry import calculate


def plan(points, *, wall_seconds=1.0):
    canonical = json.dumps(points, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signed = [float(point["y"]) for point in points]
    return {
        "wallSeconds": wall_seconds,
        "poseCount": len(points),
        "pathId": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
        "plannedLengthMeters": sum(
            ((end["x"] - start["x"]) ** 2 + (end["y"] - start["y"]) ** 2) ** 0.5
            for start, end in zip(points, points[1:])
        ),
        "minimumSignedLateralDeviationFromRequestedRouteMeters": min(signed),
        "maximumSignedLateralDeviationFromRequestedRouteMeters": max(signed),
        "maximumAbsLateralDeviationFromRequestedRouteMeters": max(map(abs, signed)),
        "poses": points,
    }


def fixture():
    direct = [
        {"x": 0.0, "y": 0.0, "yaw": 0.0},
        {"x": 10.0, "y": 0.0, "yaw": 0.0},
    ]
    changed = [
        {"x": 0.0, "y": 0.0, "yaw": 0.0},
        {"x": 3.0, "y": -1.0, "yaw": 0.0},
        {"x": 7.0, "y": 1.5, "yaw": 0.0},
        {"x": 10.0, "y": 0.0, "yaw": 0.0},
    ]
    return {
        "initialPose": {"x": 0.0, "y": 0.0},
        "goal": {"position": {"x": 10.0, "y": 0.0}},
        "status": "succeeded",
        "planHistory": [plan(direct), plan(changed, wall_seconds=2.0)],
    }


def test_independent_reference_recomputes_hash_length_and_signed_deviation():
    result = calculate(fixture(), episode_id="plan-test")

    assert result["reference_findings"]["summary_parity_passed"] is True
    assert result["reference_findings"]["multiple_distinct_delivered_plans"] is True
    assert result["reference_findings"]["substantial_plan_deviation_observed"] is True
    assert result["reference_findings"]["plans_observed_on_both_sides_of_requested_route"] is True
    assert result["measurements"]["first_plan_maximum_absolute_lateral_deviation_m"] == 0.0
    assert result["measurements"]["all_plans_minimum_signed_lateral_deviation_m"] == -1.0
    assert result["measurements"]["all_plans_maximum_signed_lateral_deviation_m"] == 1.5


def test_independent_reference_reports_summary_mismatch_fail_closed():
    value = fixture()
    value["planHistory"][1]["plannedLengthMeters"] += 1.0

    result = calculate(value, episode_id="mismatch")

    assert result["reference_findings"]["summary_parity_passed"] is False
    assert "plannedLengthMeters" in " ".join(result["measurements"]["summary_mismatches"])
