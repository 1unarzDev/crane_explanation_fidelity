#!/usr/bin/env python3
"""Run one no-retry R/P/T/N development pilot on blind command-motion evidence."""

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
sys.path.insert(0, str(ROOT / "packages/astro_dock/src/crane_explain/src"))

from audit_diagnostic_language_candidates import result_from_dict  # noqa: E402
from claude_cli_caller import ClaudeCliCaller, usage_from_record  # noqa: E402
from crane_explain.diagnostic_language import verify_bounded_diagnostic_text  # noqa: E402
from recompute_command_motion_diagnostic import method_input_from_export  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA, CodexCliCaller  # noqa: E402
from run_provenance_agent_pilot import extract_repository  # noqa: E402


PROMPTS = ROOT / "research/explanation_fidelity/prompts"
QUESTION = (
    "Did a command-to-motion discrepancy prevent the robot from continuing toward the goal? "
    "Identify the deepest supported mechanism or reject the premise, connect it to the outcome, "
    "and state what remains unresolved."
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


def call_summary(condition: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition": condition,
        "cache_key": record["cache_key"],
        "latency_ms": record["latency_ms"],
        "cost_usd": record.get("cost_usd"),
        "usage": usage_from_record(record),
    }


def no_computation_presentation(method_payload: dict[str, Any]) -> dict[str, Any]:
    method = method_payload["method_input"]
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    command_speeds = [float(item["planar_speed_mps"]) for item in commands]
    motion_speeds = [float(item["planar_speed_mps"]) for item in odometry]
    return {
        "schema": "crane-command-motion-no-computation-presentation-v1",
        "visibility": "robot_visible",
        "episode_id": method_payload["episode_id"],
        "action": {
            "status": method["action_status"],
            "error_code": method["action_error_code"],
            "analysis_duration_s": method["analysis_duration_s"],
        },
        "delivered_streams": {
            "command_provenance": method["command_provenance"],
            "odometry_provenance": method["odometry_provenance"],
            "command_sample_count": len(commands),
            "odometry_sample_count": len(odometry),
            "command_planar_speed_range_mps": (
                [min(command_speeds), max(command_speeds)] if command_speeds else None
            ),
            "odometry_planar_speed_range_mps": (
                [min(motion_speeds), max(motion_speeds)] if motion_speeds else None
            ),
            "time_aligned_window_computation": None,
        },
        "execution_sequence": method["execution_sequence"],
        "source": method_payload["source"],
        "limitations": [
            "No time-aligned healthy-response or sustained-discrepancy computation is supplied.",
            "Delivered command does not prove actuator acceptance.",
            "Delivered odometry does not prove Nav2 consumption.",
            "Evaluator intervention identity and simulator truth are unavailable.",
        ],
    }


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    evidence_path = args.evidence.resolve(strict=True)
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    if robot_root not in evidence_path.parents:
        raise ValueError("evidence must be a governed robot-visible artifact")
    export = json.loads(evidence_path.read_text(encoding="utf-8"))
    method_payload = method_input_from_export(export)
    question = getattr(args, "question", QUESTION)
    question_id = getattr(
        args, "question_id", "diagnostic-command-motion-mechanism-v1"
    )
    question_kind = getattr(
        args, "question_kind", "diagnostic-mechanism-or-false-premise-v1"
    )
    if not question.strip() or not question_id.strip() or not question_kind.strip():
        raise ValueError("question, question ID, and question kind must be non-empty")
    if not export.get("final_text_verification", {}).get("accepted"):
        raise ValueError("checked command-motion answer did not pass final-text verification")

    caller = caller or caller_for(
        args.provider, args.cache, args.model, args.reasoning_effort
    )
    calls: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    repository_identity = {"url": args.repository_url, "commit": args.repository_commit}
    adapter = ROOT / "analysis/recompute_command_motion_diagnostic.py"

    with tempfile.TemporaryDirectory(prefix="crane-diagnostic-command-motion-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages/crane_ml"
        core_repository = workspace / "packages/astro_dock/src/crane_explain"
        extract_repository(args.repository, args.repository_commit, repository)
        extract_repository(args.core_repository, args.core_repository_commit, core_repository)
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        shutil.copy2(adapter, analysis_dir / adapter.name)
        visible = workspace / "_robot_visible"
        visible.mkdir()
        method_path = visible / "command-motion-input.json"
        method_path.write_text(
            json.dumps(method_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        r_record = caller.call(
            "diagnostic-command-motion-R",
            load_prompt(args.repository_prompt, {"QUESTION": question}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "method_input_sha256": sha256_json(method_payload),
                "diagnostic_adapter_sha256": sha256(adapter),
                "core_repository_commit": args.core_repository_commit,
            },
        )
    calls.append(call_summary("R", r_record))
    outputs.append(
        {
            "condition": "R",
            "text": r_record["parsed_final"]["answer"],
            "verification_accepted": None,
            "used_template_fallback": False,
        }
    )

    diagnostic_result = export["diagnostic_result"]
    p_record = caller.call(
        "diagnostic-command-motion-P-realization",
        load_prompt(
            "diagnostic_realization_dev_v1.txt",
            {
                "QUESTION": question,
                "DIAGNOSTIC_RESULT": json.dumps(
                    diagnostic_result, indent=2, sort_keys=True
                ),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "P",
            "diagnostic_sha256": sha256(evidence_path),
            "bounded_verifier": "bounded-diagnostic-language-v2",
        },
    )
    calls.append(call_summary("P", p_record))
    candidate = p_record["parsed_final"]["answer"]
    verification = verify_bounded_diagnostic_text(
        result_from_dict(diagnostic_result), candidate
    )
    template = export["final_answer"]
    outputs.append(
        {
            "condition": "P",
            "raw_candidate": candidate,
            "text": verification.checked_text if verification.accepted else template,
            "verification_accepted": verification.accepted,
            "verification_repair_applied": verification.repair_applied,
            "verification_reasons": list(verification.reasons),
            "used_template_fallback": not verification.accepted,
            "verification_policy": verification.policy,
        }
    )
    outputs.append(
        {
            "condition": "T",
            "text": template,
            "verification_accepted": True,
            "used_template_fallback": False,
        }
    )

    presentation = no_computation_presentation(method_payload)
    n_record = caller.call(
        "diagnostic-command-motion-N",
        load_prompt(
            "diagnostic_no_computation_dev_v1.txt",
            {
                "QUESTION": question,
                "PRESENTATION": json.dumps(presentation, indent=2, sort_keys=True),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "N",
            "method_input_sha256": sha256_json(method_payload),
            "physical_diagnostic_computation": False,
        },
    )
    calls.append(call_summary("N", n_record))
    outputs.append(
        {
            "condition": "N",
            "text": n_record["parsed_final"]["answer"],
            "verification_accepted": None,
            "used_template_fallback": False,
        }
    )
    outputs.sort(key=lambda item: item["condition"])

    result = {
        "schema": "crane-diagnostic-command-motion-development-pilot-v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "question_kind": question_kind,
        "question": question,
        "conditions": ["R", "P", "T", "N"],
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "evaluator_truth_available_to_methods": False,
        "repository": repository_identity,
        "inputs": {
            "evidence_sha256": sha256(evidence_path),
            "method_input_sha256": sha256_json(method_payload),
            "diagnostic_adapter_sha256": sha256(adapter),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "comparison_scope": {
            "R": "repository-aware agent with the blind samples, exact source, and the same executable command-motion diagnostic as P",
            "P": "checked command-motion result, model realization, bounded final-text verification/fallback",
            "T": "deterministic rendering of the same checked diagnostic result",
            "N": "compact runtime/source presentation without time-aligned command-motion computation",
            "primary_fair_comparison": "P versus tool-enabled R",
            "N_is_computation_ablation_not_tool_parity_baseline": True,
        },
        "information_parity": {
            "accepted": True,
            "primary_comparison": "P versus R",
            "shared_method_input_sha256": sha256_json(method_payload),
            "shared_diagnostic_adapter_sha256": sha256(adapter),
            "shared_crane_commit": args.repository_commit,
            "shared_core_commit": args.core_repository_commit,
            "n_is_predeclared_no_computation_ablation": True,
        },
        "calls": calls,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument(
        "--repository-prompt",
        default="diagnostic_repository_agent_command_motion_dev_v1.txt",
    )
    parser.add_argument("--question", default=QUESTION)
    parser.add_argument(
        "--question-id", default="diagnostic-command-motion-mechanism-v1"
    )
    parser.add_argument(
        "--question-kind", default="diagnostic-mechanism-or-false-premise-v1"
    )
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
