#!/usr/bin/env python3
"""Run one no-retry R/P/T/N development comparison on a bounded composition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_cli_caller import ClaudeCliCaller, usage_from_record  # noqa: E402
from recompute_command_motion_diagnostic import method_input_from_export  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA, CodexCliCaller  # noqa: E402
from run_provenance_agent_pilot import extract_repository  # noqa: E402


PROMPTS = ROOT / "research/explanation_fidelity/prompts"
QUESTION = (
    "What is the deepest supported explanation for the robot's behavior during the retained "
    "observation window? Connect it to the recorded navigation behavior and state what remains "
    "unresolved, including the eventual outcome."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_prompt(name: str, replacements: dict[str, str]) -> str:
    text = (PROMPTS / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text or "}}" in text:
        raise ValueError(f"unresolved prompt placeholder in {name}")
    return text


def caller_for(provider: str, cache: Path, model: str, reasoning_effort: str):
    if provider == "codex":
        return CodexCliCaller(cache, model, reasoning_effort)
    if provider == "claude":
        return ClaudeCliCaller(cache, model, reasoning_effort)
    raise ValueError(f"unsupported provider: {provider}")


def _call_summary(condition: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition": condition,
        "cache_key": record["cache_key"],
        "latency_ms": record["latency_ms"],
        "cost_usd": record.get("cost_usd"),
        "usage": usage_from_record(record),
    }


def no_computation_presentation(
    command_export: dict[str, Any], geometry_export: dict[str, Any]
) -> dict[str, Any]:
    command = command_export["method_input"]
    geometry = geometry_export["method_input"]
    commands = command.get("command_samples") or []
    odometry = command.get("odometry_samples") or []
    command_speeds = [float(item["planar_speed_mps"]) for item in commands]
    motion_speeds = [float(item["planar_speed_mps"]) for item in odometry]
    plans = geometry.get("delivered_plan_geometry") or []
    return {
        "schema": "crane-land-composition-no-computation-presentation-v1",
        "visibility": "robot_visible",
        "episode_id": command_export["episode_id"],
        "action": {
            "status": command["action_status"],
            "terminal_result_observed": command["terminal_result_observed"],
            "analysis_duration_s": command["analysis_duration_s"],
        },
        "delivered_streams": {
            "command_sample_count": len(commands),
            "odometry_sample_count": len(odometry),
            "command_planar_speed_range_mps": (
                [min(command_speeds), max(command_speeds)] if command_speeds else None
            ),
            "odometry_planar_speed_range_mps": (
                [min(motion_speeds), max(motion_speeds)] if motion_speeds else None
            ),
            "time_aligned_command_motion_computation": None,
        },
        "execution_sequence": command["execution_sequence"],
        "route_delivery": {
            "plan_count": len(plans),
            "costmap_payload_available": geometry["costmap_payload_available"],
            "complete_route_coverage_computation": None,
            "route_classification": None,
        },
        "source": command_export["source"],
        "limitations": [
            "No time-aligned command-motion computation is supplied.",
            "No decoded route-coverage or connectivity computation is supplied.",
            "The action remained active at the declared observation cutoff.",
            "Evaluator intervention identity and simulator truth are unavailable.",
        ],
    }


def verify_realization(text: str) -> dict[str, Any]:
    normalized = text.replace("\u2013", "-").replace("\u2014", "-").lower()
    required_patterns = {
        "mechanism": r"command-to-motion discrepancy",
        "command_speed": r"0\.260 m/s",
        "measured_speed": r"0\.000 m/s",
        "healthy_speed": r"0\.25974 m/s",
        "interval": r"10\.0-{1,2}51\.0 s",
        "follow_path_failures": r"6 followpath failures",
        "wait_invocation": r"1 source-qualified wait invocation",
        "follow_path_attempts": r"11 followpath attempts",
        "nonterminal": r"no terminal result was observed",
        "unresolved_outcome": r"eventual action outcome is unresolved",
        "geometry_insufficient": r"geometric evidence is insufficient",
        "actuator_limit": r"commands do not prove actuator acceptance",
        "consumption_limit": r"odometry does not prove nav2 consumption",
    }
    required = {
        name: re.search(pattern, normalized) is not None
        for name, pattern in required_patterns.items()
    }
    forbidden_phrases = (
        "the action aborted",
        "the action failed",
        "recovery was exhausted",
        "geometry caused",
        "an obstacle caused",
        "motor failure caused",
        "mobility hold",
        "evaluator intervention",
    )
    forbidden = [phrase for phrase in forbidden_phrases if phrase in normalized]
    headings = tuple(
        heading in normalized
        for heading in (
            "diagnosis:",
            "decisive evidence:",
            "failure chain:",
            "limits and next check:",
        )
    )
    return {
        "accepted": all(required.values()) and all(headings) and not forbidden,
        "policy": "bounded-land-composition-language-v1",
        "required_checks": required,
        "four_sections_present": all(headings),
        "forbidden_findings": forbidden,
    }


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    paths = [args.fixture.resolve(strict=True), args.command.resolve(strict=True),
             args.geometry.resolve(strict=True), args.composition.resolve(strict=True)]
    if any(robot_root not in path.parents for path in paths):
        raise ValueError("all evidence inputs must be governed robot-visible artifacts")
    fixture_path, command_path, geometry_path, composition_path = paths
    command_export = json.loads(command_path.read_text(encoding="utf-8"))
    geometry_export = json.loads(geometry_path.read_text(encoding="utf-8"))
    composition = json.loads(composition_path.read_text(encoding="utf-8"))
    episode_id = composition["episode_id"]
    if {
        command_export.get("episode_id"), geometry_export.get("episode_id"), episode_id
    } != {episode_id}:
        raise ValueError("composition inputs do not share an episode ID")
    if any(item.get("visibility") != "robot_visible" for item in
           (command_export, geometry_export, composition)):
        raise ValueError("composition inputs must be robot-visible")
    if not composition.get("final_text_verification", {}).get("accepted"):
        raise ValueError("deterministic composition did not pass verification")
    source_hashes = composition["answer_plan"]["source_diagnostics"]
    if source_hashes["command_motion_sha256"] != sha256(command_path):
        raise ValueError("composition command input hash mismatch")
    if source_hashes["geometric_sha256"] != sha256(geometry_path):
        raise ValueError("composition geometry input hash mismatch")

    question = getattr(args, "question", QUESTION)
    caller = caller or caller_for(args.provider, args.cache, args.model, args.reasoning_effort)
    repository_identity = {"url": args.repository_url, "commit": args.repository_commit}
    command_method_input = method_input_from_export(command_export)
    calls: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="crane-land-composition-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages/crane_ml"
        core_repository = workspace / "packages/astro_dock/src/crane_explain"
        extract_repository(args.repository, args.repository_commit, repository)
        extract_repository(args.core_repository, args.core_repository_commit, core_repository)
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        for name in ("recompute_command_motion_diagnostic.py", "export_geometric_route_diagnostic.py"):
            shutil.copy2(ROOT / "analysis" / name, analysis_dir / name)
        visible = workspace / "_robot_visible"
        visible.mkdir()
        shutil.copy2(fixture_path, visible / "fixture-summary.json")
        (visible / "command-motion-input.json").write_text(
            json.dumps(command_method_input, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        r_record = caller.call(
            "land-diagnostic-composition-R",
            load_prompt(args.repository_prompt, {"QUESTION": question, "EPISODE_ID": episode_id}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "fixture_sha256": sha256(fixture_path),
                "command_method_input_sha256": sha256_json(command_method_input),
                "command_adapter_sha256": sha256(ROOT / "analysis/recompute_command_motion_diagnostic.py"),
                "geometry_adapter_sha256": sha256(ROOT / "analysis/export_geometric_route_diagnostic.py"),
                "core_repository_commit": args.core_repository_commit,
            },
        )
    calls.append(_call_summary("R", r_record))
    outputs.append({"condition": "R", "text": r_record["parsed_final"]["answer"],
                    "verification_accepted": None, "used_template_fallback": False})

    p_record = caller.call(
        "land-diagnostic-composition-P-realization",
        load_prompt(args.realization_prompt, {
            "QUESTION": question,
            "ANSWER_PLAN": json.dumps(composition["answer_plan"], indent=2, sort_keys=True),
        }),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "P",
            "composition_sha256": sha256(composition_path),
            "verification_policy": "bounded-land-composition-language-v1",
        },
    )
    calls.append(_call_summary("P", p_record))
    candidate = p_record["parsed_final"]["answer"]
    verification = verify_realization(candidate)
    template = composition["final_answer"]
    outputs.append({
        "condition": "P",
        "raw_candidate": candidate,
        "text": candidate if verification["accepted"] else template,
        "verification_accepted": verification["accepted"],
        "verification": verification,
        "used_template_fallback": not verification["accepted"],
    })
    outputs.append({"condition": "T", "text": template, "verification_accepted": True,
                    "used_template_fallback": False})

    presentation = no_computation_presentation(command_export, geometry_export)
    n_record = caller.call(
        "land-diagnostic-composition-N",
        load_prompt("diagnostic_no_computation_dev_v1.txt", {
            "QUESTION": question,
            "PRESENTATION": json.dumps(presentation, indent=2, sort_keys=True),
        }),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "N",
            "presentation_sha256": sha256_json(presentation),
            "physical_diagnostic_computation": False,
        },
    )
    calls.append(_call_summary("N", n_record))
    outputs.append({"condition": "N", "text": n_record["parsed_final"]["answer"],
                    "verification_accepted": None, "used_template_fallback": False})
    outputs.sort(key=lambda item: item["condition"])

    result = {
        "schema": "crane-land-diagnostic-composition-development-pilot/v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": episode_id,
        "question_id": args.question_id,
        "question_kind": args.question_kind,
        "question": question,
        "conditions": ["R", "P", "T", "N"],
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "evaluator_truth_available_to_methods": False,
        "repository": repository_identity,
        "inputs": {
            "fixture_sha256": sha256(fixture_path),
            "command_export_sha256": sha256(command_path),
            "geometry_export_sha256": sha256(geometry_path),
            "composition_sha256": sha256(composition_path),
            "command_adapter_sha256": sha256(ROOT / "analysis/recompute_command_motion_diagnostic.py"),
            "geometry_adapter_sha256": sha256(ROOT / "analysis/export_geometric_route_diagnostic.py"),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "realization_prompt": args.realization_prompt,
            "realization_prompt_sha256": sha256(PROMPTS / args.realization_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "information_parity": {
            "accepted": True,
            "primary_comparison": "P versus tool-enabled R",
            "same_robot_visible_inputs": True,
            "same_command_motion_computation_available": True,
            "same_geometric_computation_available": True,
            "same_source_and_configuration_access": True,
            "same_model_and_reasoning_effort": True,
            "one_call_each": True,
            "N_is_no_computation_ablation": True,
        },
        "calls": calls,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--command", required=True, type=Path)
    parser.add_argument("--geometry", required=True, type=Path)
    parser.add_argument("--composition", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument("--repository-prompt", default="diagnostic_repository_agent_composition_dev_v1.txt")
    parser.add_argument("--realization-prompt", default="diagnostic_composition_realization_dev_v1.txt")
    parser.add_argument("--question", default=QUESTION)
    parser.add_argument("--question-id", default="diagnostic-bounded-composition-v1")
    parser.add_argument("--question-kind", default="diagnostic-composition-and-causal-restraint-v1")
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
