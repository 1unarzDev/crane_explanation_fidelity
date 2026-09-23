#!/usr/bin/env python3
"""Export a compact robot-visible diagnosis from a retained RoboBoat Nav2 grid.

The historical fixture predates goal coordinates in the fixture summary, so the exact commanded
goal is an explicit input.  The exporter does not read simulator geometry or the evaluator-only
interpretation of that goal.
"""

from __future__ import annotations

import argparse
import base64
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zlib


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
sys.path.insert(0, str(CORE))

from crane_explain.diagnostics import (  # noqa: E402
    GridDisconnectionObservation,
    diagnose_retained_grid_disconnection,
    render_diagnostic,
    verify_diagnostic_text,
)


PLANNER_FAILURE = re.compile(
    r'^\[(?P<level>[A-Z]+)\] \[(?P<stamp>[0-9.]+)\] \[planner_server\]: '
    r'GridBased plugin failed to plan from \((?P<start_x>-?[0-9.]+), '
    r'(?P<start_y>-?[0-9.]+)\) to \((?P<goal_x>-?[0-9.]+), '
    r'(?P<goal_y>-?[0-9.]+)\): "(?P<error>[^"]+)"$'
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stamp_seconds(stamp: dict) -> float:
    return float(stamp["sec"]) + float(stamp["nanosec"]) / 1_000_000_000.0


def _decode_grid(snapshot: dict) -> bytes:
    if snapshot.get("dataEncoding") != "base64+zlib+uint8-row-major":
        raise ValueError("unsupported or missing costmap encoding")
    cells = zlib.decompress(base64.b64decode(snapshot["data"], validate=True))
    expected = int(snapshot["sizeX"]) * int(snapshot["sizeY"])
    if len(cells) != expected:
        raise ValueError(f"costmap cell count {len(cells)} != declared {expected}")
    actual = hashlib.sha256(cells).hexdigest()
    if actual != snapshot["dataSha256"]:
        raise ValueError("decoded costmap SHA-256 does not match the retained declaration")
    return cells


def _cell(snapshot: dict, x_m: float, y_m: float) -> tuple[int, int]:
    resolution = float(snapshot["resolution"])
    origin = snapshot["origin"]
    return (
        math.floor((x_m - float(origin["x"])) / resolution),
        math.floor((y_m - float(origin["y"])) / resolution),
    )


def _cell_cost(snapshot: dict, cells: bytes, cell: tuple[int, int]) -> int:
    x, y = cell
    width = int(snapshot["sizeX"])
    height = int(snapshot["sizeY"])
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"pose cell {cell} is outside the retained costmap")
    return cells[y * width + x]


def _connected(
    snapshot: dict,
    cells: bytes,
    start: tuple[int, int],
    goal: tuple[int, int],
    threshold: int,
) -> tuple[bool, int]:
    if _cell_cost(snapshot, cells, start) >= threshold:
        return False, 0
    width = int(snapshot["sizeX"])
    height = int(snapshot["sizeY"])
    queue = deque([start])
    visited = {start}
    while queue:
        current_x, current_y = queue.popleft()
        if (current_x, current_y) == goal:
            return True, len(visited)
        for delta_x, delta_y in (
            (-1, -1), (-1, 0), (-1, 1), (0, -1),
            (0, 1), (1, -1), (1, 0), (1, 1),
        ):
            candidate = current_x + delta_x, current_y + delta_y
            if candidate in visited:
                continue
            x, y = candidate
            if not (0 <= x < width and 0 <= y < height):
                continue
            if _cell_cost(snapshot, cells, candidate) >= threshold:
                continue
            visited.add(candidate)
            queue.append(candidate)
    return False, len(visited)


def _planner_failures(controller_log: Path) -> list[dict]:
    records = []
    for line_number, raw_line in enumerate(
        controller_log.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = PLANNER_FAILURE.fullmatch(raw_line)
        if not match:
            continue
        values = match.groupdict()
        records.append(
            {
                "line_number": line_number,
                "timestamp_s": float(values["stamp"]),
                "start": {"x": float(values["start_x"]), "y": float(values["start_y"])},
                "goal": {"x": float(values["goal_x"]), "y": float(values["goal_y"])},
                "error": values["error"],
                "line_sha256": hashlib.sha256(raw_line.encode("utf-8")).hexdigest(),
            }
        )
    return records


def export(
    fixture_path: Path,
    controller_log: Path,
    *,
    episode_id: str,
    goal_x_m: float,
    goal_y_m: float,
    blocked_cost_threshold: int,
    committed_parent: str | None,
    source_state_note: str,
) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    snapshot = fixture["latestCostmapSnapshot"]
    cells = _decode_grid(snapshot)
    result_pose = fixture["actionResultPose"]
    start_cell = _cell(snapshot, float(result_pose["x"]), float(result_pose["y"]))
    goal_cell = _cell(snapshot, goal_x_m, goal_y_m)
    start_cost = _cell_cost(snapshot, cells, start_cell)
    goal_cost = _cell_cost(snapshot, cells, goal_cell)
    connected, reachable_cells = _connected(
        snapshot, cells, start_cell, goal_cell, blocked_cost_threshold
    )
    failures = _planner_failures(controller_log)
    matching_goal_failures = [
        record
        for record in failures
        if math.isclose(record["goal"]["x"], goal_x_m, abs_tol=0.01)
        and math.isclose(record["goal"]["y"], goal_y_m, abs_tol=0.01)
    ]
    unique_errors = sorted({record["error"] for record in matching_goal_failures})
    planner_error = unique_errors[0] if len(unique_errors) == 1 else None

    fixture_sha = sha256(fixture_path)
    log_sha = sha256(controller_log)
    evidence_ids = (
        f"fixture-summary-sha256:{fixture_sha}",
        f"controller-log-sha256:{log_sha}",
        f"costmap-data-sha256:{snapshot['dataSha256']}",
    )
    observation = GridDisconnectionObservation(
        episode_id=episode_id,
        evidence_ids=evidence_ids,
        frame=str(snapshot["frameId"]),
        action_status=str(fixture["status"]),
        start_x_m=float(result_pose["x"]),
        start_y_m=float(result_pose["y"]),
        goal_x_m=goal_x_m,
        goal_y_m=goal_y_m,
        start_cost=start_cost,
        goal_cost=goal_cost,
        blocked_cost_threshold=blocked_cost_threshold,
        grid_connected_below_threshold=connected,
        planner_failure_message_count=len(matching_goal_failures),
        planner_error_text=planner_error,
        action_wall_seconds=float(fixture["wallSeconds"]),
        costmap_resolution_m=float(snapshot["resolution"]),
        costmap_snapshot_sha256=str(snapshot["dataSha256"]),
        costmap_snapshot_timestamp_s=_stamp_seconds(snapshot["stamp"]),
        source_anchor_ids=(
            "navfn-gridbased-exact-runtime-error-text",
            "retained-global-costmap-service-snapshot",
        ),
    )
    result = diagnose_retained_grid_disconnection(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    if not verification.accepted:
        raise RuntimeError("deterministic diagnostic rendering failed verification")

    return {
        "schema": "crane-roboboat-grid-disconnection-export-v1",
        "episode_id": episode_id,
        "visibility": "robot_visible",
        "development_only": True,
        "confirmatory_eligibility": "ineligible_retrospective_and_incomplete_source_snapshot",
        "source_identity": {
            "committed_parent_at_run_from_local_reflog": committed_parent,
            "exact_dirty_worktree_diff_retained": False,
            "source_state_note": source_state_note,
            "fixture_summary_sha256": fixture_sha,
            "controller_log_sha256": log_sha,
        },
        "robot_visible_evidence": {
            "action": {
                "status": fixture["status"],
                "wall_seconds": fixture["wallSeconds"],
                "result_pose": result_pose,
                "requested_goal": {"x": goal_x_m, "y": goal_y_m, "frame": snapshot["frameId"]},
            },
            "costmap_snapshot": snapshot,
            "planner_failure_messages": matching_goal_failures,
        },
        "reference_computation": {
            "algorithm": "8-connected breadth-first search over decoded row-major uint8 cells",
            "blocked_cost_threshold": blocked_cost_threshold,
            "start_cell": {"x": start_cell[0], "y": start_cell[1], "cost": start_cost},
            "goal_cell": {"x": goal_cell[0], "y": goal_cell[1], "cost": goal_cost},
            "connected_below_threshold": connected,
            "reachable_cell_count": reachable_cells,
            "matching_planner_failure_message_count": len(matching_goal_failures),
            "unique_matching_error_texts": unique_errors,
        },
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
        "evidence_boundary": {
            "included": [
                "hash-checked delivered global costmap service snapshot",
                "recorded action result pose, status, and timing",
                "explicitly supplied recorded action goal",
                "exact retained Navfn failure log messages",
            ],
            "excluded": [
                "simulator geometry and obstacle semantic identity",
                "later corrected-goal outcome",
                "claims that the planner consumed this exact retained snapshot on every invocation",
                "global physical infeasibility or berth-width causation",
            ],
        },
    }


def recompute_compact(payload: dict) -> dict:
    """Recompute the checked result using only the governed compact robot-visible export."""

    if payload.get("schema") != "crane-roboboat-grid-disconnection-export-v1":
        raise ValueError("unsupported compact export schema")
    if payload.get("visibility") != "robot_visible":
        raise ValueError("compact input must be robot_visible")
    evidence = payload["robot_visible_evidence"]
    action = evidence["action"]
    snapshot = evidence["costmap_snapshot"]
    cells = _decode_grid(snapshot)
    result_pose = action["result_pose"]
    goal = action["requested_goal"]
    if goal.get("frame") != snapshot.get("frameId"):
        raise ValueError("goal and costmap frames differ")
    start_cell = _cell(snapshot, float(result_pose["x"]), float(result_pose["y"]))
    goal_cell = _cell(snapshot, float(goal["x"]), float(goal["y"]))
    threshold = int(payload["reference_computation"]["blocked_cost_threshold"])
    connected, reachable_cells = _connected(snapshot, cells, start_cell, goal_cell, threshold)
    failures = evidence["planner_failure_messages"]
    errors = sorted({str(record["error"]) for record in failures})
    planner_error = errors[0] if len(errors) == 1 else None
    source = payload["source_identity"]
    evidence_ids = (
        f"fixture-summary-sha256:{source['fixture_summary_sha256']}",
        f"controller-log-sha256:{source['controller_log_sha256']}",
        f"costmap-data-sha256:{snapshot['dataSha256']}",
    )
    observation = GridDisconnectionObservation(
        episode_id=str(payload["episode_id"]),
        evidence_ids=evidence_ids,
        frame=str(snapshot["frameId"]),
        action_status=str(action["status"]),
        start_x_m=float(result_pose["x"]),
        start_y_m=float(result_pose["y"]),
        goal_x_m=float(goal["x"]),
        goal_y_m=float(goal["y"]),
        start_cost=_cell_cost(snapshot, cells, start_cell),
        goal_cost=_cell_cost(snapshot, cells, goal_cell),
        blocked_cost_threshold=threshold,
        grid_connected_below_threshold=connected,
        planner_failure_message_count=len(failures),
        planner_error_text=planner_error,
        action_wall_seconds=float(action["wall_seconds"]),
        costmap_resolution_m=float(snapshot["resolution"]),
        costmap_snapshot_sha256=str(snapshot["dataSha256"]),
        costmap_snapshot_timestamp_s=_stamp_seconds(snapshot["stamp"]),
        source_anchor_ids=(
            "navfn-gridbased-exact-runtime-error-text",
            "retained-global-costmap-service-snapshot",
        ),
    )
    result = diagnose_retained_grid_disconnection(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    return {
        "schema": "crane-roboboat-grid-disconnection-recomputation-v1",
        "episode_id": payload["episode_id"],
        "input_artifact_sha256": hashlib.sha256(
            (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        ).hexdigest(),
        "reference_computation": {
            "start_cell": {"x": start_cell[0], "y": start_cell[1]},
            "goal_cell": {"x": goal_cell[0], "y": goal_cell[1]},
            "connected_below_threshold": connected,
            "reachable_cell_count": reachable_cells,
            "planner_failure_message_count": len(failures),
            "unique_error_texts": errors,
        },
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("controller_log", type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--goal-x", type=float, required=True)
    parser.add_argument("--goal-y", type=float, required=True)
    parser.add_argument("--blocked-cost-threshold", type=int, default=253)
    parser.add_argument("--committed-parent")
    parser.add_argument("--source-state-note", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = export(
        args.fixture,
        args.controller_log,
        episode_id=args.episode_id,
        goal_x_m=args.goal_x,
        goal_y_m=args.goal_y,
        blocked_cost_threshold=args.blocked_cost_threshold,
        committed_parent=args.committed_parent,
        source_state_note=args.source_state_note,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
