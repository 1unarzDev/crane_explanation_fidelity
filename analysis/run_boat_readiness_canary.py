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
    export: dict[str, Any], independent: dict[str, Any], recomputed: dict[str, Any]
) -> dict[str, Any]:
    findings = independent["reference_findings"]
    if findings["full_terminal_margin_mechanism_supported"] is not True:
        raise ValueError("boat canary does not support the declared terminal-margin mechanism")
    if recomputed["final_text_verification"]["accepted"] is not True:
        raise ValueError("boat canary deterministic rendering did not verify")
    units = [
        {
            "unit_id": "mechanism-terminal-margin",
            "text": "The supported execution mechanism is insufficient terminal stopping margin for the observed post-result motion.",
        },
        {
            "unit_id": "return-state-comparison",
            "text": "At return, error was 0.3738 m and measured speed was 0.0486 m/s, within the configured 0.400 m and 0.050 m/s thresholds, leaving 0.0262 m task margin.",
        },
        {
            "unit_id": "outcome-comparison",
            "text": "Post-result displacement was 0.1876 m and settled error was 0.5614 m, outside the 0.400 m task tolerance.",
        },
        {
            "unit_id": "causal-limit",
            "text": "The evidence does not uniquely identify inertia, actuation, model mismatch, wind, current, waves, collision, or another physical source of residual motion.",
        },
    ]
    return {
        "schema": "crane-boat-readiness-annotation-reference/v1",
        "visibility": "robot_visible_reference",
        "reference_status": "DEVELOPMENT_CANARY_INDEPENDENT_COMPUTATION_NOT_HUMAN_GOLD",
        "episode_id": export["episode_id"],
        "question_id": "boat-readiness-terminal-margin-canary-v1",
        "diagnosable": True,
        "evidence_completeness": (
            "The packet contains the retained robot-visible return state, post-result motion, "
            "exact configuration thresholds, and a separately implemented reference calculation. "
            "It excludes simulator force decomposition, evaluator interventions, method identity, "
            "the proposed checked plan, verifier verdict, and the competing answer."
        ),
        "primary_endpoint_eligible": True,
        "mechanism_unit_id": "mechanism-terminal-margin",
        "complete_endpoint_unit_ids": [item["unit_id"] for item in units],
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

    freeze = json.loads(RESOURCE_FREEZE.read_text(encoding="utf-8"))
    baseline = freeze["baseline"]
    source = export["source"]
    config_bytes = exact_config(args.repository, source["config_commit"], source["config_path"])
    if hashlib.sha256(config_bytes).hexdigest() != source["config_sha256"]:
        raise ValueError("retained boat configuration hash mismatch")
    method_input = method_input_from_export(export)
    recomputed = build_result_from_config_bytes(method_input, config_bytes)
    independent = calculate_reference(export, config_bytes)
    reference = annotation_reference(export, independent, recomputed)

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
            "boat-readiness-terminal-margin-canary-R",
            load_prompt(PROMPT.name, {"QUESTION": QUESTION}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                "protocol": "roboboat-diagnostic-readiness-canary-v1",
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
        "schema": "crane-boat-readiness-response-pair/v1",
        "status": "DEVELOPMENT_ONLY_NOT_PROSPECTIVE_EVIDENCE",
        "protocol_id": "roboboat-diagnostic-readiness-canary-v1",
        "cluster_id": "boat-dev-terminal-margin-canary-001",
        "episode_id": export["episode_id"],
        "question_id": reference["question_id"],
        "question_kind": "complete-supported-diagnostic-communication-v1",
        "question": QUESTION,
        "provider": "mixed-deterministic-and-codex",
        "model": baseline["requested_model_id"],
        "evaluator_truth_available_to_methods": False,
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
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
