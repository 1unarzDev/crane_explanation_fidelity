#!/usr/bin/env python3
"""Run candidate-v3 P against one information-matched repository-agent R."""

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

from claude_cli_caller import usage_from_record  # noqa: E402
from recompute_command_motion_diagnostic import method_input_from_export  # noqa: E402
from render_command_motion_candidate_v3 import render  # noqa: E402
from run_diagnostic_command_motion_pilot import PROMPTS, caller_for, load_prompt, sha256_json  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA  # noqa: E402
from run_provenance_agent_pilot import extract_repository  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    evidence_path = args.evidence.resolve(strict=True)
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    if robot_root not in evidence_path.parents:
        raise ValueError("evidence must be a governed robot-visible artifact")
    for name in ("question", "question_id", "question_kind"):
        if not str(getattr(args, name, "")).strip():
            raise ValueError(f"candidate v3 requires explicit {name}")

    export = json.loads(evidence_path.read_text(encoding="utf-8"))
    method_payload = method_input_from_export(export)
    proposed = render(export)
    if proposed != render(export):
        raise AssertionError("candidate v3 rendering is not deterministic")
    permitted = sorted(export["diagnostic_result"]["supporting_evidence"])
    caller = caller or caller_for(args.provider, args.cache, args.model, args.reasoning_effort)
    adapter = ROOT / "analysis/recompute_command_motion_diagnostic.py"
    renderer = ROOT / "analysis/render_command_motion_candidate_v3.py"
    repository_identity = {"url": args.repository_url, "commit": args.repository_commit}

    with tempfile.TemporaryDirectory(prefix="crane-command-motion-candidate-v3-r-") as temporary:
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
        (visible / "command-motion-input.json").write_text(
            json.dumps(method_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        record = caller.call(
            "command-motion-candidate-v3-R",
            load_prompt(args.repository_prompt, {"QUESTION": args.question}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "method_input_sha256": sha256_json(method_payload),
                "diagnostic_adapter_sha256": sha256(adapter),
                "core_repository_commit": args.core_repository_commit,
                "candidate_version": "bounded-command-motion-candidate-v3",
            },
        )

    result = {
        "schema": "crane-command-motion-candidate-v3-development-result/v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "candidate": "bounded-command-motion-candidate-v3",
        "episode_id": export["episode_id"],
        "question_id": args.question_id,
        "question_kind": args.question_kind,
        "question": args.question,
        "conditions": ["P", "R"],
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "evaluator_truth_available_to_methods": False,
        "permitted_evidence_identifiers": permitted,
        "repository": repository_identity,
        "inputs": {
            "evidence_sha256": sha256(evidence_path),
            "method_input_sha256": sha256_json(method_payload),
            "diagnostic_adapter_sha256": sha256(adapter),
            "candidate_renderer_sha256": sha256(renderer),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "information_parity": {
            "accepted": True,
            "same_robot_visible_method_input": True,
            "same_executable_diagnostic": True,
            "same_exact_source_and_configuration_access": True,
            "p_model_calls": 0,
            "r_model_calls": 1,
            "resource_direction": "R receives strictly more language-model resource than P",
        },
        "calls": [{
            "condition": "R",
            "cache_key": record["cache_key"],
            "latency_ms": record["latency_ms"],
            "cost_usd": record.get("cost_usd"),
            "usage": usage_from_record(record),
        }],
        "outputs": [
            {
                "condition": "P",
                "text": proposed,
                "verification_accepted": True,
                "verification_policy": "exact-bounded-command-motion-candidate-v3",
                "used_template_fallback": False,
                "generation_method": "deterministic_checked_rendering",
            },
            {
                "condition": "R",
                "text": record["parsed_final"]["answer"],
                "verification_accepted": None,
                "used_template_fallback": False,
                "generation_method": "tool_enabled_repository_agent",
            },
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument("--repository-prompt", default="diagnostic_repository_agent_command_motion_dev_v2.txt")
    parser.add_argument("--question", required=True)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--question-kind", required=True)
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
