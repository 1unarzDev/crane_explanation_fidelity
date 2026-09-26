#!/usr/bin/env python3
"""Build the exact pre-response P/R resource freeze for the focused campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS = {
    "protocol": "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1.json",
    "schedule": "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-schedule.json",
    "question_registry": "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-questions.json",
    "candidate_registry": "configs/diagnostic_composition_registry_v1.json",
    "candidate_composer": "analysis/compose_diagnostic_hypotheses_v2.py",
    "candidate_composer_base": "analysis/compose_diagnostic_hypotheses.py",
    "candidate_command_adapter": "analysis/build_command_motion_composition_packet_v2.py",
    "candidate_command_adapter_base": "analysis/build_command_motion_composition_packet.py",
    "candidate_geometry_adapter": "analysis/build_geometric_composition_packet_v3.py",
    "candidate_geometry_adapter_v2": "analysis/build_geometric_composition_packet_v2.py",
    "candidate_geometry_adapter_base": "analysis/build_geometric_composition_packet.py",
    "candidate_renderer": "analysis/render_diagnostic_composition_v2.py",
    "focused_command_reference_builder": "analysis/build_focused_command_motion_reference.py",
    "independent_command_reference": "analysis/reference_command_motion.py",
    "independent_geometry_reference": "analysis/reference_land_geometric.py",
    "independent_plan_geometry_reference": "analysis/reference_land_plan_geometry.py",
    "command_recomputation_tool": "analysis/recompute_command_motion_diagnostic.py",
    "command_diagnostic_config": "configs/diagnostic_command_motion_low_speed_v1.json",
    "baseline_prompt": "research/explanation_fidelity/prompts/diagnostic_repository_agent_measurement_complete_v2.txt",
    "baseline_caller": "analysis/run_llm_episode_pilot.py",
    "baseline_caller_dispatch": "analysis/run_diagnostic_command_motion_pilot.py",
    "model_usage_parser": "analysis/claude_cli_caller.py",
    "repository_snapshot_helper": "analysis/run_provenance_agent_pilot.py",
    "response_pair_runner": "analysis/run_focused_response_pair.py",
    "annotation_packet_builder": "analysis/build_diagnostic_annotation_packet.py",
    "annotation_packet_runner": "analysis/run_luna_single_diagnostic_packet.py",
    "judge_prompt": "research/explanation_fidelity/prompts/luna-model-judge-v5.md",
    "judge_schema": "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json",
    "judge_caller": "analysis/luna_model_judge.py",
    "judge_freeze": "research/explanation_fidelity/experiment_configs/prospective/luna-model-judge-v12-final-freeze.json",
    "judge_endpoint_extension_freeze": "research/explanation_fidelity/experiment_configs/prospective/luna-model-judge-v12-complete-endpoint-extension-v1-freeze.json",
    "judge_endpoint_extension_result": "manifests/annotation/luna-model-judge-v12-complete-endpoint-extension-v1.json",
    "focused_monitor": "analysis/focused_sequential_monitor.py",
    "focused_results_schema": "research/explanation_fidelity/schemas/focused-supported-diagnostic-results-v1.schema.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def build() -> dict:
    missing = [value for value in ARTIFACTS.values() if not (ROOT / value).is_file()]
    if missing:
        raise FileNotFoundError("missing focused resource artifacts: " + ", ".join(missing))
    cli_version = subprocess.run(
        ["codex", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "schema": "crane-focused-supported-diagnostic-resource-freeze/v1",
        "freeze_id": "focused-supported-diagnostic-communication-v1-resources",
        "declared_date": "2026-09-26",
        "status": "FROZEN_BEFORE_CONFIRMATORY_RESPONSE",
        "candidate": {
            "id": "measurement-complete-checked-composition-v2",
            "generation": "deterministic_checked_rendering",
            "model_calls_per_response": 0,
            "artifacts": [name for name in ARTIFACTS if name.startswith("candidate_")],
        },
        "baseline": {
            "id": "R-strong-repository-tool-enabled-measurement-complete-v2",
            "provider_interface": "codex-cli-json/v1 via codex-lb-via-chatgpt-login",
            "requested_model_id": "gpt-6-sol",
            "provider_model_version_exposed": None,
            "substitution_allowed": False,
            "reasoning_effort": "high",
            "temperature": None,
            "seed": None,
            "model_calls_per_response": 1,
            "usable_answer_retries": 0,
            "codex_cli_version": cli_version,
            "tool_policy": "read-only isolated workspace; exact listed primitive tools; scripts and templates permitted",
        },
        "information_parity": {
            "same_robot_visible_evidence": True,
            "same_independent_reference_computations": True,
            "same_exact_source_and_configuration": True,
            "same_primitive_calculation_tools": True,
            "p_checked_certificate_plan_verifier_and_final_hidden_from_R": True,
            "evaluator_truth_hidden_from_both": True,
            "audit_result": "PASS",
        },
        "resource_accounting": {
            "R_input_or_output_token_cap": None,
            "R_wall_time_cap_s": None,
            "interpretation": "The interface exposes no enforceable token or wall-time cap. Actual tokens, cached tokens, latency, tool events, and failures are retained per call; this limitation is reported rather than inventing a cap.",
            "P_preprocessing_and_rendering_time_retained": True,
        },
        "repositories": {
            "crane_ml": {"path": "packages/crane_ml", "commit": git_head(ROOT / "packages/crane_ml")},
            "astro_dock_diagnostic_core": {"path": "packages/astro_dock/src/crane_explain", "commit": git_head(ROOT / "packages/astro_dock/src/crane_explain")},
        },
        "artifact_sha256": {name: digest(ROOT / path) for name, path in sorted(ARTIFACTS.items())},
        "artifact_paths": dict(sorted(ARTIFACTS.items())),
        "activation_boundary": "No confirmatory response may be opened until this freeze, the monitor dry run, and atomic alpha binding are committed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing resource freeze: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
