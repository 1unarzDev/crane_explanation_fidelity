#!/usr/bin/env python3
"""Fail closed when empirical numbers in the living paper lose artifact traceability."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/main.tex"


def load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {relative}")
    return value


def digest(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def pointer(value: Any, path: str) -> Any:
    current = value
    for token in path.strip("/").split("/") if path.strip("/") else []:
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, found {actual!r}")


def require_close(actual: float, expected: float, tolerance: float, label: str) -> None:
    if not math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance):
        raise AssertionError(f"{label}: expected {expected} +/- {tolerance}, found {actual}")


def measurement(document: dict[str, Any], identifier: str) -> dict[str, Any]:
    matches = [
        item
        for item in document["diagnostic_result"]["measurements"]
        if item["id"] == identifier
    ]
    if len(matches) != 1:
        raise AssertionError(f"measurement {identifier!r}: expected one match, found {len(matches)}")
    return matches[0]


def require_measurement(
    document: dict[str, Any], identifier: str, expected: float | str, tolerance: float = 0.0
) -> None:
    actual = measurement(document, identifier)["value"]
    if isinstance(expected, float):
        require_close(float(actual), expected, tolerance, identifier)
    else:
        require_equal(actual, expected, identifier)


def require_interval(
    document: dict[str, Any], identifier: str, expected: list[float], tolerance: float = 1e-9
) -> None:
    actual = measurement(document, identifier)["interval_s"]
    require_equal(len(actual), len(expected), f"{identifier} interval length")
    for index, expected_value in enumerate(expected):
        require_close(actual[index], expected_value, tolerance, f"{identifier} interval[{index}]")


def require_governed(source: str, manifest: str) -> None:
    manifest_text = (ROOT / manifest).read_text(encoding="utf-8")
    source_hash = digest(source)
    if source not in manifest_text:
        raise AssertionError(f"{manifest} does not name {source}")
    if source_hash not in manifest_text:
        raise AssertionError(f"{manifest} does not pin current SHA-256 for {source}")


def normalized_paper() -> str:
    return " ".join(
        PAPER.read_text(encoding="utf-8")
        .replace("~", " ")
        .replace("\\%", "%")
        .replace("$", "")
        .split()
    )


def require_paper_fragments(fragments: list[str]) -> None:
    paper = normalized_paper()
    missing = [fragment for fragment in fragments if fragment not in paper]
    if missing:
        raise AssertionError(f"manuscript numeric fragments missing: {missing}")


def main() -> int:
    checked_assertions = 0

    legacy = load("manifests/study/research-redirect-20260922.json")
    for path, expected in (
        ("/legacy_study/included_episodes", 33),
        ("/legacy_study/recovery_followed_by_success", 17),
        ("/legacy_study/terminal_recovery_abort", 16),
        ("/legacy_study/frozen_minimum", 40),
        ("/legacy_study/frozen_target", 50),
        ("/legacy_final_generation/model_calls", 198),
        ("/legacy_final_generation/g_fallback_total", 46),
        ("/legacy_final_generation/g_response_total", 66),
    ):
        require_equal(pointer(legacy, path), expected, f"legacy{path}")
        checked_assertions += 1
    require_close(100 * 46 / 66, 69.7, 0.05, "legacy fallback percentage")
    checked_assertions += 1

    boat_path = "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json"
    require_governed(
        boat_path, "manifests/data/roboboat-terminal-margin-development-v1.robot-visible.json"
    )
    boat = load(boat_path)
    for identifier, expected, tolerance in (
        ("action_return_error", 0.3738084684842852, 1e-12),
        ("measured_speed_at_return", 0.0486084585847379, 1e-12),
        ("configured_goal_tolerance", 0.4, 1e-12),
        ("configured_stopped_speed", 0.05, 1e-12),
        ("task_margin_at_return", 0.02619153151571485, 1e-12),
        ("post_result_displacement", 0.1875955526646154, 1e-12),
        ("settled_error", 0.5613816624013539, 1e-12),
    ):
        require_measurement(boat, identifier, expected, tolerance)
        checked_assertions += 1

    blockage_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/"
        "geometric-diagnostic.json"
    )
    blockage_manifest = "manifests/data/land-blockage-global-002.robot-visible.json"
    require_governed(blockage_path, blockage_manifest)
    blockage = load(blockage_path)
    for identifier, expected, tolerance in (
        ("goal_distance", 18.0, 1e-12),
        ("first_lethal_route_x", 8.45, 1e-12),
        ("configured_robot_radius", 0.22, 1e-12),
        ("configured_inflation_radius", 0.55, 1e-12),
        ("maximum_forward_progress", 6.9489426612854, 1e-12),
        ("maximum_lateral_deviation", 2.704580307006836, 1e-12),
        ("action_wall_time", 70.86018458599574, 1e-12),
        ("configured_deadline", 70.0, 1e-12),
        ("absolute_deadline_timing_difference", 0.8601845859957393, 1e-12),
    ):
        require_measurement(blockage, identifier, expected, tolerance)
        checked_assertions += 1
    blockage_fixture_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/fixture-summary.json"
    )
    require_governed(blockage_fixture_path, blockage_manifest)
    require_equal(len(load(blockage_fixture_path)["planHistory"]), 69, "blockage planning updates")
    checked_assertions += 1

    s_turn_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-s-turn-unexpected-abort-001/"
        "geometric-diagnostic-v2.json"
    )
    s_turn_manifest = "manifests/data/land-s-turn-unexpected-abort-001.robot-visible.json"
    require_governed(s_turn_path, s_turn_manifest)
    s_turn = load(s_turn_path)
    for identifier, expected, tolerance in (
        ("first_lethal_route_x", 3.5500000000000007, 1e-12),
        ("maximum_lateral_deviation", 1.6994519233703613, 1e-12),
        ("absolute_deadline_timing_difference", 0.9178990819782484, 1e-12),
        ("configured_deadline", 70.0, 1e-12),
    ):
        require_measurement(s_turn, identifier, expected, tolerance)
        checked_assertions += 1
    s_turn_fixture_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-s-turn-unexpected-abort-001/"
        "fixture-summary.json"
    )
    require_governed(s_turn_fixture_path, s_turn_manifest)
    require_equal(len(load(s_turn_fixture_path)["planHistory"]), 69, "S-turn planning updates")
    checked_assertions += 1

    nominal_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/diagnostic-land-nominal-20260922-001/"
        "geometric-diagnostic.json"
    )
    nominal_manifest = "manifests/data/diagnostic-land-nominal-20260922-001.robot-visible.json"
    require_governed(nominal_path, nominal_manifest)
    nominal = load(nominal_path)
    for identifier, expected, tolerance in (
        ("maximum_forward_progress", 17.47705078125, 1e-12),
        ("maximum_lateral_deviation", 0.08441401273012161, 1e-12),
        ("configured_deadline", 90.0, 1e-12),
    ):
        require_measurement(nominal, identifier, expected, tolerance)
        checked_assertions += 1

    recovery_path = (
        "data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/"
        "recovery-execution-diagnostic.json"
    )
    require_governed(
        recovery_path,
        "manifests/data/ecological-warehouse-recovery-development-v1.robot-visible.json",
    )
    recovery = load(recovery_path)
    require_measurement(recovery, "minimum_source_qualified_recovery_invocation_count", 4)
    require_measurement(
        recovery,
        "qualified_recovery_sequence",
        "Spin->SUCCESS, Wait->SUCCESS, BackUp->SUCCESS, Spin->SUCCESS",
    )
    checked_assertions += 2

    plan_path = "data/robot_visible/dev/diagnostic-land-dev-004/geometric-route-diagnostic-v2.json"
    plan_manifest = "manifests/data/diagnostic-land-dev-004.robot-visible.json"
    require_governed(plan_path, plan_manifest)
    plan = load(plan_path)
    for identifier, expected, tolerance in (
        ("delivered_plan_count", 70.0, 0.0),
        ("unique_delivered_plan_count", 70.0, 0.0),
        ("all_plans_minimum_signed_lateral_deviation", -1.1749038696289054, 1e-12),
        ("all_plans_maximum_signed_lateral_deviation", 1.0350578308105458, 1e-12),
        ("maximum_lateral_deviation", 1.1041951179504395, 1e-12),
    ):
        require_measurement(plan, identifier, expected, tolerance)
        checked_assertions += 1
    plan_fixture_path = "data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json"
    require_governed(plan_fixture_path, plan_manifest)
    plan_fixture = load(plan_fixture_path)
    require_equal(
        sum(len(item["poses"]) for item in plan_fixture["planHistory"]),
        12_975,
        "retained plan poses",
    )
    checked_assertions += 1

    command_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/"
        "evidence-and-diagnostic.json"
    )
    require_governed(command_path, "manifests/data/diagnostic-motion-dev-cm-001.robot-visible.json")
    command = load(command_path)
    for identifier, expected, tolerance in (
        ("calibrated_healthy_planar_speed", 0.2597399950027466, 1e-12),
        ("discrepancy_commanded_planar_speed", 0.8, 1e-12),
        ("discrepancy_measured_planar_speed", 0.0, 1e-12),
        ("sustained_discrepancy_duration", 10.0, 1e-12),
        ("follow_path_failures", 2.0, 0.0),
        ("source_qualified_wait_recoveries", 2.0, 0.0),
    ):
        require_measurement(command, identifier, expected, tolerance)
        checked_assertions += 1
    require_interval(command, "discrepancy_commanded_planar_speed", [7.0, 17.0])
    checked_assertions += 1
    command_reference_path = (
        "research/explanation_fidelity/annotations/development/"
        "diagnostic-command-motion-supported-pilot-v1-reference.json"
    )
    require_governed(
        command_reference_path,
        "manifests/annotation/diagnostic-command-motion-supported-pilot-v1.json",
    )
    command_reference = load(command_reference_path)
    require_equal(
        pointer(command_reference, "/allowed_evidence/command_motion/command_sample_count"),
        376,
        "command samples",
    )
    require_equal(
        pointer(command_reference, "/allowed_evidence/command_motion/odometry_sample_count"),
        1598,
        "odometry samples",
    )
    checked_assertions += 2

    nominal_motion_reference_path = (
        "research/explanation_fidelity/annotations/development/"
        "diagnostic-command-motion-nominal-pilot-v1-reference.json"
    )
    require_governed(
        nominal_motion_reference_path,
        "manifests/annotation/diagnostic-command-motion-nominal-pilot-v1.json",
    )
    nominal_motion_reference = load(nominal_motion_reference_path)
    require_close(
        pointer(nominal_motion_reference, "/allowed_evidence/execution/displacement_m"),
        9.480303764343262,
        1e-12,
        "nominal command-motion displacement",
    )
    checked_assertions += 1

    compensated_path = (
        "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-compensated-001/"
        "evidence-and-diagnostic.json"
    )
    require_governed(
        compensated_path, "manifests/data/diagnostic-motion-development-cm-002.robot-visible.json"
    )
    compensated = load(compensated_path)
    require_interval(compensated, "discrepancy_commanded_planar_speed", [8.0, 18.0])
    require_interval(compensated, "recovered_measured_planar_speed", [20.0, 21.0])
    require_measurement(compensated, "sustained_discrepancy_duration", 10.0, 1e-12)
    require_measurement(compensated, "recovered_measured_planar_speed", 0.2597399950027466, 1e-12)
    checked_assertions += 4

    compensation_output_path = (
        "model_outputs/dev/diagnostic-command-motion-compensation-pilot-v1/"
        "diagnostic-motion-dev-cm-compensated-001/mechanism-recovery-success.json"
    )
    require_governed(
        compensation_output_path,
        "manifests/model_outputs/diagnostic-command-motion-compensation-pilot-v1.json",
    )
    compensation_output = load(compensation_output_path)
    r_outputs = [item for item in compensation_output["outputs"] if item["condition"] == "R"]
    require_equal(len(r_outputs), 1, "compensation R output count")
    require_equal("8–20 s" in r_outputs[0]["text"], True, "R output 8-20 second claim")
    require_equal("for 12 s" in r_outputs[0]["text"], True, "R output 12 second claim")
    checked_assertions += 3

    inventory_path = "manifests/annotation/diagnostic-development-pilot-v1.json"
    inventory = load(inventory_path)
    require_equal(inventory["responses"], 52, "diagnostic inventory responses")
    require_equal(inventory["statistical_clusters"], 9, "diagnostic inventory clusters")
    require_equal(len(inventory["packets"]), 13, "diagnostic inventory packets")
    checked_assertions += 3
    p_entries = []
    for specification in inventory["packets"]:
        key_path = specification["key"]
        require_equal(digest(key_path), specification["key_sha256"], f"key hash {key_path}")
        key = load(key_path)
        p_entries.extend(entry for entry in key["entries"] if entry["condition"] == "P")
    require_equal(len(p_entries), 13, "P response inventory")
    require_equal(sum(bool(entry["used_template_fallback"]) for entry in p_entries), 13, "P fallbacks")
    checked_assertions += 2
    paired_names = {
        "command-motion-supported",
        "command-motion-nominal",
        "command-motion-missing-odometry",
    }
    paired_specs = [item for item in inventory["packets"] if item["name"] in paired_names]
    require_equal(len(paired_specs), 3, "command-motion paired packet count")
    require_equal(
        len({item["statistical_cluster_id"] for item in paired_specs}),
        1,
        "command-motion paired cluster count",
    )
    paired_responses = sum(len(load(item["key"])["entries"]) for item in paired_specs)
    require_equal(paired_responses, 12, "command-motion paired response count")
    checked_assertions += 3

    primary_endpoints = load(
        "research/explanation_fidelity/experiment_configs/development/"
        "diagnostic-pilot-primary-endpoints-v1.json"
    )
    require_equal(len(primary_endpoints["selected"]), 6, "primary planning subset")
    require_equal(
        len({item["statistical_cluster_id"] for item in primary_endpoints["selected"]}),
        6,
        "primary planning subset clusters",
    )
    checked_assertions += 2

    luna_v2 = load("manifests/annotation/luna-model-judge-v1-development-v2.json")
    require_equal(luna_v2["status"], "NO_CONFIGURATION_QUALIFIED", "Luna v2 disposition")
    require_close(
        100 * pointer(luna_v2, "/efforts/medium/core_semantic_field_accuracy"),
        94.4,
        0.05,
        "Luna v2 medium core-field accuracy",
    )
    require_close(
        100 * pointer(luna_v2, "/efforts/medium/required_unit_accuracy"),
        93.75,
        0.001,
        "Luna v2 medium required-unit accuracy",
    )
    require_equal(pointer(luna_v2, "/efforts/medium/qualified"), False, "Luna v2 qualified")
    checked_assertions += 4

    require_paper_fragments(
        [
            "33 included episode clusters",
            "17 recovery-success and 16 terminal-abort",
            "minimum of 40 and target of 50",
            "198 one-shot responses",
            "46 of 66 responses (69.7%)",
            "0.3738 m goal error",
            "0.04861 m/s",
            "0.0262 m margin",
            "0.1876 m",
            "0.5614 m error",
            "18 m centerline",
            "cost-253 cell near x=8.45 m",
            "0.22 m robot radius and 0.55 m inflation",
            "x=6.949 m",
            "2.705 m laterally",
            "69 planning updates",
            "70.860 s under an exact 70 s",
            "1.699 m lateral deviation",
            "0.084 m maximum lateral deviation",
            "at least four source-qualified recovery invocations",
            "12,975 poses across 70 unique delivered plans",
            "-1.175 to +1.035 m",
            "376 command samples and 1,598 goal-interval odometry samples",
            "0.2597 m/s",
            "7--17 s",
            "0.800 m/s",
            "0.000 m/s",
            "9.480 m",
            "8--18 s",
            "20--21 s",
            "contain 12 blinded responses but form one paired/masked cluster",
            "52 responses in 13 packets over nine clusters",
            "13/13 development questions overall",
            "Primary planning subset & 6 clusters",
            "94.4% core; 93.75% units",
        ]
    )

    result = {
        "status": "PASS",
        "manuscript": PAPER.relative_to(ROOT).as_posix(),
        "empirical_assertions_checked": checked_assertions,
        "diagnostic_packets": len(inventory["packets"]),
        "diagnostic_responses": inventory["responses"],
        "diagnostic_clusters": inventory["statistical_clusters"],
        "note": "Pending result placeholders, bibliography years, equation notation, and LaTeX layout dimensions are outside the empirical-number audit.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
