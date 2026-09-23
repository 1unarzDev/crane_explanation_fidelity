#!/usr/bin/env python3
"""Run one cached R/P/T/N development pilot on governed RoboBoat evidence.

The script is separate from the frozen provenance study and never launches or modifies RoboBoat.
It gives R the same executable terminal-margin computation and exact pinned source/configuration
available to P.  The N arm receives the same observations and source text without that computed
diagnostic.  Every model arm is sampled once with no repair or retry.
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
    "Why did this docking attempt fail to remain within the declared task tolerance after the "
    "navigation action returned? Identify the deepest supported execution or physical mechanism, "
    "how it connects to the outcome, and what remains unresolved."
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


def method_input(export: dict[str, Any]) -> dict[str, Any]:
    """Expose observations and provenance, never the proposed method's derived answer."""

    return {
        "schema": "crane-terminal-margin-method-input-v1",
        "visibility": "robot_visible",
        "episode_id": export["episode_id"],
        "evidence_boundary": export["evidence_boundary"],
        "source": export["source"],
        "observation": export["observation"],
    }


def caller_for(provider: str, cache: Path, model: str, reasoning_effort: str):
    if provider == "codex":
        return CodexCliCaller(cache, model, reasoning_effort)
    if provider == "claude":
        return ClaudeCliCaller(cache, model, reasoning_effort)
    raise ValueError(f"unsupported provider: {provider}")


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    evidence_path = args.evidence.resolve(strict=True)
    robot_root = (ROOT / "data" / "robot_visible").resolve(strict=True)
    if robot_root not in evidence_path.parents:
        raise ValueError("evidence must be a governed robot-visible artifact")
    export = json.loads(evidence_path.read_text(encoding="utf-8"))
    if export.get("evidence_boundary", {}).get("classification") != (
        "robot_visible_declared_diagnostic_interface"
    ):
        raise ValueError("artifact does not declare the required robot-visible boundary")
    if not export.get("final_text_verification", {}).get("accepted"):
        raise ValueError("governed checked answer did not pass deterministic verification")

    source = export["source"]
    if source["config_commit"] != args.repository_commit:
        raise ValueError("requested CRANE commit does not match governed evidence")
    exact_config = subprocess_config(args.repository, args.repository_commit, source["config_path"])
    if hashlib.sha256(exact_config).hexdigest() != source["config_sha256"]:
        raise ValueError("governed configuration hash does not match the pinned commit")

    input_payload = method_input(export)
    input_bytes = (json.dumps(input_payload, indent=2, sort_keys=True) + "\n").encode()
    input_hash = hashlib.sha256(input_bytes).hexdigest()
    caller = caller or caller_for(args.provider, args.cache, args.model, args.reasoning_effort)
    calls: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    repository_identity = {"url": args.repository_url, "commit": args.repository_commit}
    adapter_path = ROOT / "analysis" / "recompute_terminal_margin_diagnostic.py"

    with tempfile.TemporaryDirectory(prefix="crane-diagnostic-boat-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages" / "crane_ml"
        core_repository = workspace / "packages" / "astro_dock" / "src" / "crane_explain"
        extract_repository(args.repository, args.repository_commit, repository)
        extract_repository(args.core_repository, args.core_repository_commit, core_repository)
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        shutil.copy2(adapter_path, analysis_dir / adapter_path.name)
        visible = workspace / "_robot_visible"
        visible.mkdir()
        (visible / "terminal-margin-input.json").write_bytes(input_bytes)
        r_record = caller.call(
            "diagnostic-boat-R",
            load_prompt(args.repository_prompt, {"QUESTION": QUESTION}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "method_input_sha256": input_hash,
                "diagnostic_adapter_sha256": sha256(adapter_path),
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

    p_record = caller.call(
        "diagnostic-boat-P-realization",
        load_prompt(
            "diagnostic_realization_dev_v1.txt",
            {
                "QUESTION": QUESTION,
                "DIAGNOSTIC_RESULT": json.dumps(
                    export["diagnostic_result"], indent=2, sort_keys=True
                ),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "P",
            "evidence_sha256": sha256(evidence_path),
            "diagnostic_adapter_sha256": sha256(adapter_path),
        },
    )
    calls.append(call_summary("P", p_record))
    candidate = p_record["parsed_final"]["answer"]
    template = export["checked_answer"]
    accepted = candidate == template
    outputs.append(
        {
            "condition": "P",
            "raw_candidate": candidate,
            "text": candidate if accepted else template,
            "verification_accepted": accepted,
            "used_template_fallback": not accepted,
            "verification_policy": "exact-checked-deterministic-rendering",
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

    presentation = dict(input_payload)
    presentation["exact_source_config"] = exact_config.decode("utf-8")
    n_record = caller.call(
        "diagnostic-boat-N",
        load_prompt(
            "diagnostic_no_computation_dev_v1.txt",
            {
                "QUESTION": QUESTION,
                "PRESENTATION": json.dumps(presentation, indent=2, sort_keys=True),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "N",
            "method_input_sha256": input_hash,
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
        "schema": "crane-diagnostic-boat-development-pilot-v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": export["episode_id"],
        "evidence_variant": args.variant,
        "question_id": f"diagnostic-terminal-margin-{args.variant}-v1",
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
            "evidence_sha256": sha256(evidence_path),
            "method_input_sha256": input_hash,
            "config_sha256": source["config_sha256"],
            "diagnostic_adapter_sha256": sha256(adapter_path),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "comparison_scope": {
            "R": "repository-aware agent with raw robot-visible observations, exact source, and the same executable terminal-margin computation as P",
            "P": "checked diagnostic result, model realization, exact final-text verification/fallback",
            "T": "deterministic rendering of the same checked diagnostic result",
            "N": "runtime/source presentation without the executable physical diagnostic computation",
            "primary_fair_comparison": "P versus tool-enabled R",
            "N_is_computation_ablation_not_tool_parity_baseline": True,
        },
        "information_parity": {
            "accepted": True,
            "primary_comparison": "P versus R",
            "shared_method_input_sha256": input_hash,
            "shared_diagnostic_adapter_sha256": sha256(adapter_path),
            "shared_crane_commit": args.repository_commit,
            "shared_core_commit": args.core_repository_commit,
            "n_is_predeclared_no-computation_ablation": True,
        },
        "calls": calls,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def subprocess_config(repository: Path, commit: str, path: str) -> bytes:
    import subprocess

    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout


def call_summary(condition: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition": condition,
        "cache_key": record["cache_key"],
        "latency_ms": record["latency_ms"],
        "cost_usd": record.get("cost_usd"),
        "usage": usage_from_record(record),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument(
        "--repository-prompt", default="diagnostic_repository_agent_boat_dev_v1.txt"
    )
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
