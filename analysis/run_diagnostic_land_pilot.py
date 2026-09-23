#!/usr/bin/env python3
"""Run one cached R/P/T/N development pilot on governed land evidence.

This is deliberately separate from the frozen provenance study.  It does not create gold labels,
freeze a protocol, or call development outputs held-out evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"))

from claude_cli_caller import ClaudeCliCaller, usage_from_record
from run_llm_episode_pilot import ANSWER_SCHEMA, CodexCliCaller
from run_provenance_agent_pilot import extract_repository


PROMPTS = ROOT / "research" / "explanation_fidelity" / "prompts"
QUESTION = (
    "Why did this navigation action fail? Identify the deepest supported physical or execution "
    "mechanism, how it connects to the outcome, and what remains unresolved."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prompt(name: str, replacements: dict[str, str]) -> str:
    text = (PROMPTS / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text or "}}" in text:
        raise ValueError(f"unresolved prompt placeholder in {name}")
    return text


def no_diagnostic_presentation(fixture: dict[str, Any], nav2_config: Path, bt_xml: Path) -> dict:
    """Build the N input without decoding or classifying the compressed costmap."""

    trajectory = fixture.get("trajectory") or []
    x_values = [float(item["x"]) for item in trajectory]
    y_values = [float(item["y"]) for item in trajectory]
    snapshot = dict(fixture.get("latestCostmapSnapshot") or {})
    snapshot.pop("data", None)
    return {
        "schema": "crane-diagnostic-no-computation-presentation-v1",
        "action": {
            "status": fixture.get("status"),
            "wall_seconds": fixture.get("wallSeconds"),
            "goal": fixture.get("goal"),
            "initial_pose": fixture.get("initialPose"),
            "action_result_pose": fixture.get("actionResultPose"),
        },
        "execution": {
            "controller_commands": fixture.get("controllerCommands"),
            "successful_plan_updates": fixture.get("behaviorTreeTransitionCounts", {}).get(
                "ComputePathToPose:RUNNING->SUCCESS"
            ),
            "maximum_recovery_feedback": fixture.get("maximumRecoveryCount"),
            "trajectory_samples": len(trajectory),
            "trajectory_bounds": {
                "min_x": min(x_values) if x_values else None,
                "max_x": max(x_values) if x_values else None,
                "min_y": min(y_values) if y_values else None,
                "max_y": max(y_values) if y_values else None,
            },
        },
        "costmap_delivery": {
            "provenance": fixture.get("costmapProvenance"),
            "observations": fixture.get("costmapObservations"),
            "maximum_occupied_cells": fixture.get("maximumOccupiedCostmapCells"),
            "latest_snapshot_metadata": snapshot,
            "decoded_route_or_connectivity_computation": None,
        },
        "behavior_tree_capture": fixture.get("behaviorTreeCapture", {}).get("completeness"),
        "source": {
            "nav2_config_sha256": sha256(nav2_config),
            "nav2_config": nav2_config.read_text(encoding="utf-8"),
            "bt_xml_sha256": sha256(bt_xml),
            "bt_xml": bt_xml.read_text(encoding="utf-8"),
        },
        "limitations": [
            "The compressed costmap was delivered but no geometric route computation is supplied.",
            "Delivered odometry and costmap state are not proof of every value consumed by Nav2.",
            "Evaluator-only geometry and scenario identity are unavailable.",
        ],
    }


def caller_for(provider: str, cache: Path, model: str, reasoning_effort: str):
    if provider == "codex":
        return CodexCliCaller(cache, model, reasoning_effort)
    if provider == "claude":
        return ClaudeCliCaller(cache, model, reasoning_effort)
    raise ValueError(f"unsupported provider: {provider}")


def run(args: argparse.Namespace, caller=None) -> dict:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    fixture_path = args.fixture.resolve(strict=True)
    diagnostic_path = args.diagnostic.resolve(strict=True)
    robot_root = (ROOT / "data" / "robot_visible").resolve(strict=True)
    if robot_root not in fixture_path.parents or robot_root not in diagnostic_path.parents:
        raise ValueError("fixture and diagnostic must both be governed robot-visible artifacts")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    diagnostic_export = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    if diagnostic_export.get("visibility") != "robot_visible":
        raise ValueError("diagnostic export is not robot-visible")
    if diagnostic_export["method_input"]["fixture_summary_sha256"] != sha256(fixture_path):
        raise ValueError("diagnostic export does not match the fixture")

    caller = caller or caller_for(
        args.provider, args.cache, args.model, args.reasoning_effort
    )
    call_records: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    repository_identity = {
        "url": args.repository_url,
        "commit": args.repository_commit,
    }

    with tempfile.TemporaryDirectory(prefix="crane-diagnostic-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages" / "crane_ml"
        core_repository = workspace / "packages" / "astro_dock" / "src" / "crane_explain"
        extract_repository(args.repository, args.repository_commit, repository)
        extract_repository(args.core_repository, args.core_repository_commit, core_repository)
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        shutil.copy2(
            ROOT / "analysis" / "export_geometric_route_diagnostic.py",
            analysis_dir / "export_geometric_route_diagnostic.py",
        )
        evidence = workspace / "_robot_visible"
        evidence.mkdir()
        shutil.copy2(fixture_path, evidence / "fixture-summary.json")
        r_record = caller.call(
            "diagnostic-land-R",
            load_prompt(
                args.repository_prompt,
                {
                    "QUESTION": QUESTION,
                    "EPISODE_ID": diagnostic_export["episode_id"],
                },
            ),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "fixture_sha256": sha256(fixture_path),
                "diagnostic_wrapper_sha256": sha256(
                    ROOT / "analysis" / "export_geometric_route_diagnostic.py"
                ),
                "costmap_audit_sha256": sha256(
                    args.repository / "Tools/Performance/audit_nav2_costmap_clearance.py"),
                "core_repository_commit": args.core_repository_commit,
            },
        )
    call_records.append({
        "condition": "R",
        "cache_key": r_record["cache_key"],
        "latency_ms": r_record["latency_ms"],
        "cost_usd": r_record.get("cost_usd"),
        "usage": usage_from_record(r_record),
    })
    outputs.append({
        "condition": "R",
        "text": r_record["parsed_final"]["answer"],
        "verification_accepted": None,
        "used_template_fallback": False,
    })

    diagnostic_result = diagnostic_export["diagnostic_result"]
    p_record = caller.call(
        "diagnostic-land-P-realization",
        load_prompt(
            "diagnostic_realization_dev_v1.txt",
            {
                "QUESTION": QUESTION,
                "DIAGNOSTIC_RESULT": json.dumps(diagnostic_result, indent=2, sort_keys=True),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            "condition": "P",
            "diagnostic_sha256": sha256(diagnostic_path),
            **repository_identity,
        },
    )
    call_records.append({
        "condition": "P",
        "cache_key": p_record["cache_key"],
        "latency_ms": p_record["latency_ms"],
        "cost_usd": p_record.get("cost_usd"),
        "usage": usage_from_record(p_record),
    })
    candidate = p_record["parsed_final"]["answer"]
    template = diagnostic_export["final_answer"]
    accepted = candidate == template
    outputs.append({
        "condition": "P",
        "raw_candidate": candidate,
        "text": candidate if accepted else template,
        "verification_accepted": accepted,
        "used_template_fallback": not accepted,
        "verification_policy": "exact-checked-deterministic-rendering",
    })
    outputs.append({
        "condition": "T",
        "text": template,
        "verification_accepted": True,
        "used_template_fallback": False,
    })

    presentation = no_diagnostic_presentation(fixture, args.nav2_config, args.bt_xml)
    n_record = caller.call(
        "diagnostic-land-N",
        load_prompt(
            "diagnostic_no_computation_dev_v1.txt",
            {
                "QUESTION": QUESTION,
                "PRESENTATION": json.dumps(presentation, indent=2, sort_keys=True),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            "condition": "N",
            "fixture_sha256": sha256(fixture_path),
            "physical_diagnostic_computation": False,
            **repository_identity,
        },
    )
    call_records.append({
        "condition": "N",
        "cache_key": n_record["cache_key"],
        "latency_ms": n_record["latency_ms"],
        "cost_usd": n_record.get("cost_usd"),
        "usage": usage_from_record(n_record),
    })
    outputs.append({
        "condition": "N",
        "text": n_record["parsed_final"]["answer"],
        "verification_accepted": None,
        "used_template_fallback": False,
    })
    outputs.sort(key=lambda item: item["condition"])

    result = {
        "schema": "crane-diagnostic-land-development-pilot-v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": diagnostic_export["episode_id"],
        "question_id": "diagnostic-mechanism-and-outcome-v1",
        "question_kind": "diagnostic-mechanism-and-outcome-v1",
        "question": QUESTION,
        "conditions": ["R", "P", "T", "N"],
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "evaluator_truth_available_to_methods": False,
        "repository": repository_identity,
        "inputs": {
            "fixture_sha256": sha256(fixture_path),
            "diagnostic_sha256": sha256(diagnostic_path),
            "nav2_config_sha256": sha256(args.nav2_config),
            "bt_xml_sha256": sha256(args.bt_xml),
            "diagnostic_wrapper_sha256": sha256(
                ROOT / "analysis" / "export_geometric_route_diagnostic.py"
            ),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "comparison_scope": {
            "R": "repository-aware agent with raw fixture, exact source, and the same executable diagnostic wrapper as P",
            "P": "checked diagnostic result, model realization, exact final-text verification/fallback",
            "T": "deterministic rendering of the same checked diagnostic result",
            "N": "runtime/source presentation without decoded geometric diagnostic computation",
            "primary_fair_comparison": "P versus tool-enabled R",
            "N_is_computation_ablation_not_tool_parity_baseline": True,
        },
        "information_parity": {
            "accepted": True,
            "primary_comparison": "P versus R",
            "shared_robot_visible_fixture_sha256": sha256(fixture_path),
            "shared_diagnostic_wrapper_sha256": sha256(
                ROOT / "analysis" / "export_geometric_route_diagnostic.py"
            ),
            "shared_crane_commit": args.repository_commit,
            "shared_core_commit": args.core_repository_commit,
            "n_is_predeclared_no_computation_ablation": True,
        },
        "calls": call_records,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--diagnostic", required=True, type=Path)
    parser.add_argument("--nav2-config", required=True, type=Path)
    parser.add_argument("--bt-xml", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument(
        "--repository-prompt",
        default="diagnostic_repository_agent_dev_v1.txt",
        help="prompt filename below research/explanation_fidelity/prompts",
    )
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    payload = run(parse_args())
    print(json.dumps(payload, indent=2, sort_keys=True))
