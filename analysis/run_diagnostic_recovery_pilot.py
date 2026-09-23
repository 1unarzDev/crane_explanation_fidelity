#!/usr/bin/env python3
"""Run one no-retry R/P/T/N development pilot on a recovery-mechanism case."""

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

from claude_cli_caller import ClaudeCliCaller, usage_from_record  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA, CodexCliCaller  # noqa: E402
from run_provenance_agent_pilot import extract_repository  # noqa: E402


PROMPTS = ROOT / "research/explanation_fidelity/prompts"
QUESTION = (
    "Why did the autonomy software enter recovery, how many recovery invocations does the "
    "retained evidence support, and did recovery prevent task success? Identify the deepest "
    "supported mechanism and what physical cause remains unresolved."
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


def no_diagnostic_presentation(evidence: dict[str, Any]) -> dict[str, Any]:
    """Retain captured records while omitting the computed transition linkage."""

    bt = evidence["bt"]
    return {
        "schema": "crane-recovery-no-computation-presentation-v1",
        "visibility": "robot_visible",
        "episode_id": evidence["episodeId"],
        "action": evidence["action"],
        "feedback": evidence["feedback"],
        "behavior_tree": {
            "completeness": bt["completeness"],
            "recovery_node_classifier": bt["recoveryNodeClassifier"],
            "retained_recovery_invocations": bt["recoveryInvocations"],
            "retained_transition_count": bt["retainedTransitionCount"],
            "computed_planner_failure_to_recovery_linkage": None,
        },
        "trajectory_summary": evidence["trajectory"]["summary"],
        "costmap_delivery_summary": evidence["observations"]["costmap"],
        "runtime_hashes": evidence["runtime"],
        "withholding": evidence["withholding"],
        "limitations": [
            "The ordered transition computation linking planner failure, eligibility, and each recovery leaf is omitted.",
            "The feedback recovery count is not a unique invocation identity.",
            "Delivered costmaps do not prove exact planner consumption or a physical cause.",
        ],
    }


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


def run(args: argparse.Namespace, caller=None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    evidence_path = args.evidence.resolve(strict=True)
    diagnostic_path = args.diagnostic.resolve(strict=True)
    robot_root = (ROOT / "data/robot_visible").resolve(strict=True)
    if robot_root not in evidence_path.parents or robot_root not in diagnostic_path.parents:
        raise ValueError("evidence and diagnostic must be governed robot-visible artifacts")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    if evidence.get("schema") != "crane-ecological-robot-visible-evidence-v1":
        raise ValueError("unexpected ecological evidence schema")
    if diagnostic.get("visibility") != "robot_visible":
        raise ValueError("diagnostic export is not robot-visible")
    if diagnostic["source"]["robot_visible_evidence_sha256"] != sha256(evidence_path):
        raise ValueError("diagnostic export does not match the ecological evidence")
    if not diagnostic.get("final_text_verification", {}).get("accepted"):
        raise ValueError("checked diagnostic answer did not pass final-text verification")

    caller = caller or caller_for(
        args.provider, args.cache, args.model, args.reasoning_effort
    )
    calls: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    repository_identity = {"url": args.repository_url, "commit": args.repository_commit}
    adapter = ROOT / "analysis/export_recovery_execution_diagnostic.py"

    with tempfile.TemporaryDirectory(prefix="crane-diagnostic-recovery-r-") as temporary:
        workspace = Path(temporary) / "workspace"
        repository = workspace / "packages/crane_ml"
        core_repository = workspace / "packages/astro_dock/src/crane_explain"
        extract_repository(args.repository, args.repository_commit, repository)
        extract_repository(
            args.core_repository, args.core_repository_commit, core_repository
        )
        analysis_dir = workspace / "analysis"
        analysis_dir.mkdir()
        shutil.copy2(adapter, analysis_dir / adapter.name)
        visible = workspace / "_robot_visible"
        visible.mkdir()
        shutil.copy2(evidence_path, visible / "evidence.json")
        r_record = caller.call(
            "diagnostic-recovery-R",
            load_prompt(args.repository_prompt, {"QUESTION": QUESTION}),
            ANSWER_SCHEMA,
            working_directory=workspace,
            workspace_identity={
                **repository_identity,
                "condition": "R",
                "evidence_sha256": sha256(evidence_path),
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

    p_record = caller.call(
        "diagnostic-recovery-P-realization",
        load_prompt(
            "diagnostic_realization_dev_v1.txt",
            {
                "QUESTION": QUESTION,
                "DIAGNOSTIC_RESULT": json.dumps(
                    diagnostic["diagnostic_result"], indent=2, sort_keys=True
                ),
            },
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "P",
            "diagnostic_sha256": sha256(diagnostic_path),
            "diagnostic_adapter_sha256": sha256(adapter),
        },
    )
    calls.append(call_summary("P", p_record))
    candidate = p_record["parsed_final"]["answer"]
    template = diagnostic["final_answer"]
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

    presentation = no_diagnostic_presentation(evidence)
    n_record = caller.call(
        "diagnostic-recovery-N",
        load_prompt(
            "diagnostic_no_computation_dev_v1.txt",
            {"QUESTION": QUESTION, "PRESENTATION": json.dumps(presentation, indent=2)},
        ),
        ANSWER_SCHEMA,
        workspace_identity={
            **repository_identity,
            "condition": "N",
            "evidence_sha256": sha256(evidence_path),
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
        "schema": "crane-diagnostic-recovery-development-pilot-v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": diagnostic["episode_id"],
        "question_id": "diagnostic-recovery-sequence-v1",
        "question_kind": "recovery-mechanism-count-and-outcome-v1",
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
            "diagnostic_sha256": sha256(diagnostic_path),
            "diagnostic_adapter_sha256": sha256(adapter),
            "repository_prompt": args.repository_prompt,
            "repository_prompt_sha256": sha256(PROMPTS / args.repository_prompt),
            "core_repository_commit": args.core_repository_commit,
        },
        "comparison_scope": {
            "R": "repository-aware agent with raw robot-visible evidence, exact source, and the same executable recovery diagnostic as P",
            "P": "checked recovery diagnostic, model realization, exact final-text verification/fallback",
            "T": "deterministic rendering of the same checked diagnostic result",
            "N": "compact captured provenance without the transition-linkage computation",
            "primary_fair_comparison": "P versus tool-enabled R",
            "N_is_computation_ablation_not_tool_parity_baseline": True,
        },
        "information_parity": {
            "accepted": True,
            "primary_comparison": "P versus R",
            "shared_robot_visible_evidence_sha256": sha256(evidence_path),
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
    parser.add_argument("--diagnostic", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--core-repository", required=True, type=Path)
    parser.add_argument("--core-repository-commit", required=True)
    parser.add_argument(
        "--repository-prompt",
        default="diagnostic_repository_agent_recovery_dev_v1.txt",
    )
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
