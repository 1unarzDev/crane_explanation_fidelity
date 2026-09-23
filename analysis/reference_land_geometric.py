#!/usr/bin/env python3
"""Independent development reference for the retained land geometric case.

This evaluator-side implementation imports neither CRANE's costmap-audit helper nor the proposed
diagnostic core.  It verifies and decodes the retained grid, rasterizes the requested start-goal
segment with integer Bresenham cells, checks connectivity with a separately implemented A* search,
and derives trajectory/deadline facts.  It does not identify evaluator-only obstacles or prove the
grid was consumed by a particular planner invocation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable
import zlib


BLOCKED_COST = 253


def decode_grid(snapshot: dict[str, Any]) -> bytes | None:
    encoded = snapshot.get("data")
    if encoded is None:
        return None
    if snapshot.get("dataEncoding") != "base64+zlib+uint8-row-major":
        raise ValueError("unsupported costmap encoding")
    raw = zlib.decompress(base64.b64decode(encoded))
    expected = int(snapshot["sizeX"]) * int(snapshot["sizeY"])
    if len(raw) != expected:
        raise ValueError(f"costmap size mismatch: {len(raw)} != {expected}")
    if hashlib.sha256(raw).hexdigest() != snapshot["dataSha256"]:
        raise ValueError("costmap cell hash mismatch")
    return raw


def world_to_cell(snapshot: dict[str, Any], point: tuple[float, float]) -> tuple[int, int]:
    origin = snapshot["origin"]
    dx = point[0] - float(origin["x"])
    dy = point[1] - float(origin["y"])
    yaw = float(origin["yaw"])
    local_x = math.cos(yaw) * dx + math.sin(yaw) * dy
    local_y = -math.sin(yaw) * dx + math.cos(yaw) * dy
    resolution = float(snapshot["resolution"])
    return math.floor(local_x / resolution), math.floor(local_y / resolution)


def cell_center(snapshot: dict[str, Any], cell: tuple[int, int]) -> tuple[float, float]:
    resolution = float(snapshot["resolution"])
    local_x = (cell[0] + 0.5) * resolution
    local_y = (cell[1] + 0.5) * resolution
    origin = snapshot["origin"]
    yaw = float(origin["yaw"])
    return (
        float(origin["x"]) + math.cos(yaw) * local_x - math.sin(yaw) * local_y,
        float(origin["y"]) + math.sin(yaw) * local_x + math.cos(yaw) * local_y,
    )


def bresenham(start: tuple[int, int], goal: tuple[int, int]) -> Iterable[tuple[int, int]]:
    x0, y0 = start
    x1, y1 = goal
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        yield x0, y0
        if (x0, y0) == (x1, y1):
            return
        twice = 2 * error
        if twice >= dy:
            error += dy
            x0 += sx
        if twice <= dx:
            error += dx
            y0 += sy


def cell_cost(snapshot: dict[str, Any], grid: bytes, cell: tuple[int, int]) -> int | None:
    width = int(snapshot["sizeX"])
    height = int(snapshot["sizeY"])
    x, y = cell
    if not (0 <= x < width and 0 <= y < height):
        return None
    return int(grid[y * width + x])


def connected_astar(
    snapshot: dict[str, Any], grid: bytes, start: tuple[int, int], goal: tuple[int, int]
) -> bool:
    if cell_cost(snapshot, grid, start) is None or cell_cost(snapshot, grid, goal) is None:
        return False
    if cell_cost(snapshot, grid, start) >= BLOCKED_COST or cell_cost(snapshot, grid, goal) >= BLOCKED_COST:
        return False
    frontier: list[tuple[float, int, tuple[int, int]]] = [(0.0, 0, start)]
    best = {start: 0.0}
    sequence = 0
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current == goal:
            return True
        current_cost = best[current]
        for dx, dy in (
            (-1, -1), (-1, 0), (-1, 1), (0, -1),
            (0, 1), (1, -1), (1, 0), (1, 1),
        ):
            neighbor = current[0] + dx, current[1] + dy
            cost = cell_cost(snapshot, grid, neighbor)
            if cost is None or cost >= BLOCKED_COST:
                continue
            candidate = current_cost + (math.sqrt(2.0) if dx and dy else 1.0)
            if candidate >= best.get(neighbor, math.inf):
                continue
            best[neighbor] = candidate
            heuristic = math.hypot(goal[0] - neighbor[0], goal[1] - neighbor[1])
            sequence += 1
            heapq.heappush(frontier, (candidate + heuristic, sequence, neighbor))
    return False


def timeout_seconds(bt_xml: bytes, explicit_deadline_seconds: float | None = None) -> float:
    if explicit_deadline_seconds is not None:
        if not math.isfinite(explicit_deadline_seconds) or explicit_deadline_seconds <= 0:
            raise ValueError("explicit deadline must be a finite positive number")
        return explicit_deadline_seconds
    match = re.search(rb"<Timeout\s+msec=\"([0-9]+)\"", bt_xml)
    if not match:
        raise ValueError(
            "literal BT Timeout msec value not found; provide explicit_deadline_seconds"
        )
    return int(match.group(1)) / 1000.0


def calculate(
    fixture: dict[str, Any],
    bt_xml: bytes,
    *,
    episode_id: str | None = None,
    explicit_deadline_seconds: float | None = None,
) -> dict[str, Any]:
    snapshot = fixture["latestCostmapSnapshot"]
    grid = decode_grid(snapshot)
    initial = (float(fixture["initialPose"]["x"]), float(fixture["initialPose"]["y"]))
    goal = (
        float(fixture["goal"]["position"]["x"]),
        float(fixture["goal"]["position"]["y"]),
    )
    result_pose = fixture.get("actionResultPose") or fixture["finalPose"]
    action_result = (float(result_pose["x"]), float(result_pose["y"]))
    deadline = timeout_seconds(bt_xml, explicit_deadline_seconds)
    action_seconds = float(fixture["wallSeconds"])
    action_status = str(fixture["status"]).lower()
    start_cell = world_to_cell(snapshot, initial)
    goal_cell = world_to_cell(snapshot, goal)
    result_cell = world_to_cell(snapshot, action_result)

    first_blocked = None
    direct_route_fully_covered = True
    grid_connected = None
    if grid is not None:
        for cell in bresenham(start_cell, goal_cell):
            cost = cell_cost(snapshot, grid, cell)
            if cost is None:
                direct_route_fully_covered = False
                continue
            if cost >= BLOCKED_COST:
                center = cell_center(snapshot, cell)
                first_blocked = {
                    "cell": list(cell),
                    "center_x_m": center[0],
                    "center_y_m": center[1],
                    "cost": cost,
                }
                break
        grid_connected = connected_astar(snapshot, grid, result_cell, goal_cell)

    route_dx = goal[0] - initial[0]
    route_dy = goal[1] - initial[1]
    route_length = math.hypot(route_dx, route_dy)
    lateral: list[float] = []
    forward: list[float] = []
    for sample in fixture.get("trajectory") or []:
        dx = float(sample["x"]) - initial[0]
        dy = float(sample["y"]) - initial[1]
        lateral.append(abs(route_dx * dy - route_dy * dx) / route_length)
        forward.append((dx * route_dx + dy * route_dy) / route_length)
    completeness = fixture.get("behaviorTreeCapture", {}).get("completeness", {})
    successful_plans = int(
        fixture.get("behaviorTreeTransitionCounts", {}).get(
            "ComputePathToPose:RUNNING->SUCCESS", 0
        )
    )
    direct_restriction = first_blocked is not None if grid is not None else None
    deadline_delta = abs(action_seconds - deadline)
    deadline_aligned_abort = action_status == "aborted" and deadline_delta <= 1.5
    return {
        "schema": "crane-land-geometric-independent-reference/v1",
        "status": "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY",
        "episode_id": episode_id or fixture.get("runId") or fixture.get("scope"),
        "implementation_independence": {
            "imports_crane_costmap_audit": False,
            "imports_proposed_diagnostic_core": False,
            "human_label": False,
            "route_algorithm": "integer_bresenham_cells",
            "connectivity_algorithm": "eight_neighbor_astar",
        },
        "measurements": {
            "costmap_payload_available": grid is not None,
            "costmap_data_sha256": snapshot["dataSha256"],
            "cost_threshold": BLOCKED_COST,
            "direct_route_first_blocked": first_blocked,
            "direct_route_fully_covered": (
                direct_route_fully_covered if grid is not None else None
            ),
            "connected_from_action_result_to_goal_below_threshold": grid_connected,
            "maximum_lateral_deviation_m": max(lateral) if lateral else None,
            "maximum_forward_progress_m": max(forward) if forward else None,
            "successful_planning_updates": successful_plans,
            "action_status": action_status,
            "action_wall_seconds": action_seconds,
            "configured_deadline_seconds": deadline,
            "deadline_alignment_delta_seconds": deadline_delta,
            "terminal_bt_transition_observed": bool(
                completeness.get("terminalTransitionObserved", False)
            ),
        },
        "reference_findings": {
            "direct_route_restriction_supported": direct_restriction,
            "retained_grid_has_connection": grid_connected,
            "substantial_route_deviation_observed": max(lateral, default=0.0) > 0.5,
            "deadline_aligned_abort_supported": deadline_aligned_abort,
            "global_physical_no_path_supported": False,
            "unique_physical_obstacle_supported": False,
            "terminal_timeout_tick_directly_observed": bool(
                completeness.get("terminalTransitionObserved", False)
            ),
        },
        "allowed_conclusions": [
            conclusion
            for conclusion, include in (
                (
                    "The requested direct route crosses a blocked cell in the retained planner grid.",
                    direct_restriction is True,
                ),
                (
                    "The retained grid still contains a connection from the action-result pose to the goal.",
                    grid_connected is True,
                ),
                (
                    "Delivered odometry records substantial lateral route deviation.",
                    max(lateral, default=0.0) > 0.5,
                ),
                (
                    "The abort time is aligned with the configured BT deadline.",
                    deadline_aligned_abort,
                ),
            )
            if include
        ],
        "required_withholding": [
            "The retained snapshot does not prove global physical no-path.",
            "Evaluator-only obstacle identity is not available to explanation methods.",
            "Delivered grid and odometry do not prove exact planner consumption.",
            *(
                ["The retained grid does not cover the complete requested route."]
                if grid is not None and not direct_route_fully_covered
                else []
            ),
            (
                "The terminal timeout tick was not directly observed."
                if not completeness.get("terminalTransitionObserved", False)
                else "No withholding is required for terminal-transition observation."
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--bt-xml", required=True, type=Path)
    parser.add_argument("--deadline-seconds", type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = calculate(
        json.loads(args.fixture.read_text(encoding="utf-8")),
        args.bt_xml.read_bytes(),
        episode_id=args.episode_id,
        explicit_deadline_seconds=args.deadline_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
