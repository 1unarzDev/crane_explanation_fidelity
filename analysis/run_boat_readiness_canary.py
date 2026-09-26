#!/usr/bin/env python3
"""Build the focused P/R pair and independent reference for a boat readiness canary.

This is a development-only adapter.  It deliberately does not alter the frozen land runner or
admit the retained episode to either prospective campaign.  P is recomputed and deterministically
rendered from robot-visible terminal-margin evidence.  R receives the same evidence, exact source
and configuration, and executable diagnostic adapter in an isolated checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_cli_caller import usage_from_record  # noqa: E402
from recompute_terminal_margin_diagnostic import (  # noqa: E402
    build_result_from_config_bytes,
    method_input_from_export,
)
from reference_terminal_margin import calculate as calculate_reference  # noqa: E402
from run_diagnostic_command_motion_pilot import caller_for, load_prompt  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA  # noqa: E402
from run_provenance_agent_pilot import extract_repository  # noqa: E402


RESOURCE_FREEZE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-resource-freeze.json"
)
PROMPT = ROOT / "research/explanation_fidelity/prompts/diagnostic_repository_agent_boat_dev_v1.txt"
ADAPTER = ROOT / "analysis/recompute_terminal_margin_diagnostic.py"
REFERENCE_IMPLEMENTATION = ROOT / "analysis/reference_terminal_margin.py"
QUESTION = (
    "Why did this docking attempt fail to remain within the declared task tolerance after the "
    "navigation action returned? Identify the deepest supported execution or physical mechanism, "
    "how it connects to the outcome, and what remains unresolved."
)
MASKED_QUESTION = (
    "Can the full terminal-margin mechanism be established from the retained evidence? State the "
    "supported positional failure chain, identify the missing stopped-state discriminator, and "
    "preserve the unresolved physical alternatives."
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def exact_config(repository: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout


def annotation_reference(
    export: dict[str, Any], independent: dict[str, Any], recomputed: dict[str, Any],
    *, question_id: str = "boat-readiness-terminal-margin-canary-v1",
    reference_status: str = "DEVELOPMENT_CANARY_INDEPENDENT_COMPUTATION_NOT_HUMAN_GOLD",
) -> dict[str, Any]:
    findings = independent["reference_findings"]
    if recomputed["final_text_verification"]["accepted"] is not True:
        raise ValueError("boat canary deterministic rendering did not verify")
    observation = export["observation"]
    measurements = independent.get("measurements") or {
        "return_error_m": observation["action_return_error_m"],
        "measured_speed_at_return_mps": observation["measured_speed_at_return_mps"],
        "goal_tolerance_m": observation["configured_goal_tolerance_m"],
        "stopped_speed_threshold_mps": observation["configured_stopped_speed_mps"],
        "position_margin_at_return_m": (
            observation["task_acceptance_tolerance_m"]
            - observation["action_return_error_m"]
        ),
        "post_result_displacement_m": observation["post_result_coast_m"],
        "settled_error_m": observation["settled_error_m"],
        "task_tolerance_m": observation["task_acceptance_tolerance_m"],
    }
    full_mechanism = findings["full_terminal_margin_mechanism_supported"] is True
    masked_speed = (
        findings.get("positional_failure_chain_supported") is True
        and findings.get("stopped_speed_state") == "unresolved_missing_measured_speed"
    )
    if not full_mechanism and not masked_speed:
        raise ValueError("boat evidence supports neither the full nor masked terminal-margin contract")
    if full_mechanism:
        units = [
            {
                "unit_id": "mechanism-terminal-margin",
                "text": "The supported execution mechanism is insufficient terminal stopping margin for the observed post-result motion.",
            },
            {
                "unit_id": "return-state-comparison",
                "text": (
                    f"At return, error was {measurements['return_error_m']:.4f} m and measured "
                    f"speed was {measurements['measured_speed_at_return_mps']:.4f} m/s, within the "
                    f"configured {measurements['goal_tolerance_m']:.3f} m and "
                    f"{measurements['stopped_speed_threshold_mps']:.3f} m/s thresholds, leaving "
                    f"{measurements['position_margin_at_return_m']:.4f} m task margin."
                ),
            },
            {
                "unit_id": "outcome-comparison",
                "text": (
                    f"Post-result displacement was {measurements['post_result_displacement_m']:.4f} m "
                    f"and settled error was {measurements['settled_error_m']:.4f} m, outside the "
                    f"{measurements['task_tolerance_m']:.3f} m task tolerance."
                ),
            },
            {
                "unit_id": "causal-limit",
                "text": "The evidence does not uniquely identify inertia, actuation, model mismatch, wind, current, waves, collision, or another physical source of residual motion.",
            },
        ]
    else:
        units = [
            {
                "unit_id": "supported-positional-failure-chain",
                "text": (
                    f"The action returned at {measurements['return_error_m']:.4f} m error with "
                    f"{measurements['position_margin_at_return_m']:.4f} m positional task margin; "
                    f"post-result displacement was {measurements['post_result_displacement_m']:.4f} m "
                    f"and settled error was {measurements['settled_error_m']:.4f} m, outside the "
                    f"{measurements['task_tolerance_m']:.3f} m task tolerance."
                ),
            },
            {
                "unit_id": "missing-stopped-state-discriminator",
                "text": (
                    "Independently measured speed at action return is missing, so whether the "
                    f"platform physically met the configured {measurements['stopped_speed_threshold_mps']:.3f} m/s "
                    "stopped-speed threshold is unresolved."
                ),
            },
            {
                "unit_id": "full-mechanism-withheld",
                "text": "The complete terminal-margin mechanism must remain qualified because its stopped-state discriminator is unavailable.",
            },
            {
                "unit_id": "causal-limit",
                "text": "The evidence does not uniquely identify inertia, actuation, model mismatch, wind, current, waves, collision, or another physical source of residual motion.",
            },
        ]
    result = {
        "schema": "crane-boat-readiness-annotation-reference/v1",
        "visibility": "robot_visible_reference",
        "reference_status": reference_status,
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "diagnosable": full_mechanism,
        "evidence_completeness": (
            "The packet contains the retained robot-visible return state, post-result motion, "
            "exact configuration thresholds, and a separately implemented reference calculation. "
            "It excludes simulator force decomposition, evaluator interventions, method identity, "
            "the proposed checked plan, verifier verdict, and the competing answer."
        ),
        "primary_endpoint_eligible": full_mechanism,
        "required_units": units,
        "prohibited_claims": [
            "Wind, current, waves, collision, inertia, or actuator failure uniquely caused the residual motion.",
            "Delivered odometry proves every value consumed internally by Nav2.",
            "This retrospective episode proves a tighter tolerance would correct future outcomes.",
        ],
        "allowed_evidence": {
            "robot_visible_export": {
                "episode_id": export["episode_id"],
                "observation": export["observation"],
                "source": export["source"],
                "evidence_boundary": export["evidence_boundary"],
            },
            "independent_reference_computation": independent,
        },
        "reference_provenance": {
            "implementation": str(REFERENCE_IMPLEMENTATION.relative_to(ROOT)),
            "implementation_sha256": digest(REFERENCE_IMPLEMENTATION),
            "imports_proposed_diagnostic_core": False,
            "imports_proposed_adapter": False,
            "human_gold": False,
        },
    }
    if full_mechanism:
        result["mechanism_unit_id"] = "mechanism-terminal-margin"
        result["complete_endpoint_unit_ids"] = [item["unit_id"] for item in units]
    return result


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    output = args.output.resolve()
    reference_output = args.reference_output.resolve()
    if output.exists() or reference_output.exists():
        raise FileExistsError("refusing to overwrite boat canary output or reference")
    evidence = args.evidence.resolve(strict=True)
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    if robot_root not in evidence.parents:
        raise ValueError("boat canary evidence must be governed robot-visible data")
    export = json.loads(evidence.read_text(encoding="utf-8"))
    if export.get("evidence_boundary", {}).get("classification") != (
        "robot_visible_declared_diagnostic_interface"
    ):
        raise ValueError("boat canary evidence boundary is not robot-visible")
    prospective_configuration_id = getattr(args, "prospective_configuration_id", None)
    prospective = prospective_configuration_id is not None
    if prospective and (
        export.get("study_status") != "PROSPECTIVE_EXTERNAL_VALIDITY_ARM"
        or export.get("configuration_id") != prospective_configuration_id
        or export.get("land_n_added") != 0
    ):
        raise ValueError("prospective boat response identity differs from the governed export")
    masked_speed_control = export.get("evidence_boundary", {}).get("masked_fields") == [
        "measured_speed_at_return"
    ]
    question = MASKED_QUESTION if masked_speed_control else QUESTION

    freeze = json.loads(RESOURCE_FREEZE.read_text(encoding="utf-8"))
    baseline = freeze["baseline"]
    source = export["source"]
    config_bytes = exact_config(args.repository, source["config_commit"], source["config_path"])
    if hashlib.sha256(config_bytes).hexdigest() != source["config_sha256"]:
        raise ValueError("retained boat configuration hash mismatch")
    method_input = method_input_from_export(export)
    recomputed = build_result_from_config_bytes(method_input, config_bytes)
    independent = calculate_reference(export, config_bytes)
    reference = annotation_reference(
        export,
        independent,
        recomputed,
        question_id=(export["question_id"] if prospective else "boat-readiness-terminal-margin-canary-v1"),
        reference_status=(
            "PROSPECTIVE_EXTERNAL_VALIDITY_INDEPENDENT_REFERENCE_NOT_HUMAN_GOLD"
            if prospective
            else "DEVELOPMENT_CANARY_INDEPENDENT_COMPUTATION_NOT_HUMAN_GOLD"
        ),
    )

    caller = caller or caller_for(
        "codex", args.cache, baseline["requested_model_id"], baseline["reasoning_effort"]
    )
    with tempfile.TemporaryDirectory(prefix="crane-boat-readiness-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        crane_ml = workspace / "packages/crane_ml"
        core = workspace / "packages/astro_dock/src/crane_explain"
        extract_repository(args.repository, source["config_commit"], crane_ml)
        core_spec = freeze["repositories"]["astro_dock_diagnostic_core"]
        extract_repository(ROOT / core_spec["path"], core_spec["commit"], core)
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        shutil.copy2(ADAPTER, analysis_dir / ADAPTER.name)
        visible = workspace / "_robot_visible"
        visible.mkdir()
        method_bytes = (json.dumps(method_input, indent=2, sort_keys=True) + "\n").encode()
        (visible / "terminal-margin-input.json").write_bytes(method_bytes)
        record = caller.call(
            (
                f"roboboat-prospective-{export['configuration_id']}"
                f"{'-missing-return-speed' if masked_speed_control else ''}-R"
                if prospective
                else "boat-readiness-terminal-margin-canary-R"
            ),
            load_prompt(PROMPT.name, {"QUESTION": question}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                "protocol": (
                    "roboboat-diagnostic-external-validity-v1-narrow"
                    if prospective
                    else "roboboat-diagnostic-readiness-canary-v1"
                ),
                "condition": "R",
                "episode_id": export["episode_id"],
                "resource_freeze_sha256": digest(RESOURCE_FREEZE),
                "method_input_sha256": hashlib.sha256(method_bytes).hexdigest(),
                "diagnostic_adapter_sha256": digest(ADAPTER),
                "source_commit": source["config_commit"],
                "core_commit": core_spec["commit"],
            },
        )
    request = record.get("request", {})
    if request.get("model") != baseline["requested_model_id"] or request.get(
        "reasoning_effort"
    ) != baseline["reasoning_effort"]:
        raise ValueError("boat canary R configuration differs from the focused freeze")

    result = {
        "schema": (
            "crane-roboboat-prospective-response-pair/v1"
            if prospective
            else "crane-boat-readiness-response-pair/v1"
        ),
        "status": (
            "PROSPECTIVE_EXTERNAL_VALIDITY_ARM_RESPONSE_PAIR"
            if prospective
            else "DEVELOPMENT_ONLY_NOT_PROSPECTIVE_EVIDENCE"
        ),
        "protocol_id": (
            "roboboat-diagnostic-external-validity-v1-narrow"
            if prospective
            else "roboboat-diagnostic-readiness-canary-v1"
        ),
        "cluster_id": (
            export["cluster_id"] if prospective else "boat-dev-terminal-margin-canary-001"
        ),
        "episode_id": export["episode_id"],
        "question_id": reference["question_id"],
        "question_kind": (
            "missing_decisive_or_ambiguous_evidence"
            if masked_speed_control
            else "complete-supported-diagnostic-communication-v1"
        ),
        "question": question,
        "provider": "mixed-deterministic-and-codex",
        "model": baseline["requested_model_id"],
        "evaluator_truth_available_to_methods": False,
        "configuration_id": export.get("configuration_id"),
        "independent_physical_configuration": bool(
            export.get("independent_physical_configuration", False)
        ),
        "land_n_added": 0,
        "prospective_boat_n_added": int(prospective and not masked_speed_control),
        "evidence_mask_control": (
            "boat-ext-narrow-003-missing-return-speed" if masked_speed_control else None
        ),
        "resource_freeze_sha256": digest(RESOURCE_FREEZE),
        "inputs": {
            "robot_visible_evidence_sha256": digest(evidence),
            "method_input_sha256": canonical_digest(method_input),
            "diagnostic_adapter_sha256": digest(ADAPTER),
            "reference_implementation_sha256": digest(REFERENCE_IMPLEMENTATION),
            "prompt_sha256": digest(PROMPT),
            "config_sha256": source["config_sha256"],
        },
        "information_parity": {
            **freeze["information_parity"],
            "boat_adapter_scope": "terminal-margin-v2",
            "same_robot_visible_method_input_sha256": canonical_digest(method_input),
            "same_executable_terminal_margin_adapter": True,
        },
        "outputs": [
            {
                "condition": "P",
                "text": recomputed["checked_answer"],
                "provider": "deterministic",
                "model": None,
                "model_calls": 0,
                "verification_accepted": True,
                "used_template_fallback": False,
            },
            {
                "condition": "R",
                "text": record["parsed_final"]["answer"],
                "provider": request["provider"],
                "model": request["model"],
                "model_calls": 1,
                "verification_accepted": None,
                "used_template_fallback": False,
            },
        ],
        "calls": [
            {
                "condition": "R",
                "cache_key": record["cache_key"],
                "latency_ms": record["latency_ms"],
                "cost_usd": record.get("cost_usd"),
                "usage": usage_from_record(record),
            }
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    reference_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reference_output.write_text(
        json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-output", required=True, type=Path)
    parser.add_argument("--prospective-configuration-id")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
