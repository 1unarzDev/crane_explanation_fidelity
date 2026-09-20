#!/usr/bin/env python3
"""Run matched F/G/H development conditions for one retained provenance pilot.

The repository-agent workspaces contain only the exact Git checkout and the condition's allowed
robot-visible evidence. Evaluator-only files are never copied or mentioned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from crane_explain.io import episode_from_dict, provenance_from_dict
from crane_explain.provenance import resolve_provenance
from crane_explain.realize import render_template
from crane_explain.reasoning import plan_failure_cause, plan_recovery_mechanism
from crane_explain.verification import verify_final_text
from run_llm_episode_pilot import (
    ANSWER_SCHEMA,
    CodexCliCaller,
    realization_prompt,
    usage_from_events,
)

QUESTIONS = {
    "recovery-mechanism": "Why did the autonomy software enter recovery?",
    "failure-cause": "Did a physical obstacle cause the navigation failure?",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_repository(repository: Path, commit: str, destination: Path) -> None:
    destination.mkdir(parents=True)
    archive = subprocess.Popen(
        ("git", "-C", str(repository), "archive", commit), stdout=subprocess.PIPE
    )
    assert archive.stdout is not None
    extracted = subprocess.run(
        ("tar", "-x", "-C", str(destination)), stdin=archive.stdout, check=False
    )
    archive.stdout.close()
    return_code = archive.wait()
    if return_code or extracted.returncode:
        raise RuntimeError("failed to materialize exact repository checkout")


def agent_prompt(question: str, evidence_description: str, commit: str) -> str:
    return f"""You are a strong read-only coding agent explaining one robot navigation episode.
Inspect the allowed robot-visible evidence and the exact repository checkout in this workspace.
The repository is pinned to commit {commit}. Do not use outside knowledge or infer evaluator truth.
Distinguish what runtime evidence observed, what exact source/configuration defines, and what remains
unknown. Cite concrete runtime IDs/timestamps and exact repository paths/symbols when they support
the answer. Do not infer physical cause, consumed sensor input, complete history, or a
counterfactual unless the allowed evidence establishes it. Correct false premises. Give a concise,
substantive answer as JSON matching the supplied schema.

ALLOWED EVIDENCE
{evidence_description}

QUESTION
{question}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--provenance-dir", required=True, type=Path)
    parser.add_argument("--prior-a-e", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--question-kind", choices=tuple(QUESTIONS), required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="low")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")

    question = QUESTIONS[args.question_kind]
    episode_path = args.case_dir / "structured.json"
    episode = episode_from_dict(json.loads(episode_path.read_text(encoding="utf-8")))
    bundle = provenance_from_dict(
        json.loads(
            (args.provenance_dir / "provenance.json").read_text(encoding="utf-8")
        )
    )
    runtime_ids = {item.id for item in episode.evidence if item.kind == "bt_transition"}
    resolved = resolve_provenance(
        bundle,
        known_runtime_evidence_ids={item.id for item in episode.evidence},
        requested_runtime_evidence_ids=runtime_ids,
    )
    plan = (
        plan_recovery_mechanism(episode, resolved)
        if args.question_kind == "recovery-mechanism"
        else plan_failure_cause(episode)
    )
    caller = CodexCliCaller(args.cache, args.model, args.reasoning_effort)
    call_refs: list[dict[str, Any]] = []
    outputs = list(json.loads(args.prior_a_e.read_text(encoding="utf-8"))["outputs"])

    with tempfile.TemporaryDirectory(prefix="crane-provenance-agent-") as temporary:
        staging = Path(temporary)
        repository = staging / "repository"
        extract_repository(args.repository, args.commit, repository)
        workspace_identity = {
            "repository": args.repository_url,
            "commit": args.commit,
        }

        for condition in ("F", "H"):
            evidence = repository / "_robot_visible"
            if evidence.exists():
                shutil.rmtree(evidence)
            evidence.mkdir()
            if condition == "F":
                for name in ("events.jsonl", "manifest.json", "behavior_tree.xml"):
                    shutil.copy2(args.capture_dir / name, evidence / name)
                description = (
                    "Raw passive capture files are in _robot_visible/: events.jsonl, "
                    "manifest.json, and behavior_tree.xml. Treat repeated publications as repeated "
                    "messages, not new attempts."
                )
            else:
                shutil.copy2(episode_path, evidence / "structured.json")
                description = (
                    "Structured runtime evidence is in _robot_visible/structured.json."
                )
            record = caller.call(
                f"condition-{condition.lower()}-{args.question_kind}",
                agent_prompt(question, description, args.commit),
                ANSWER_SCHEMA,
                working_directory=repository,
                workspace_identity={
                    **workspace_identity,
                    "condition": condition,
                    "evidence_files": {
                        str(path.relative_to(repository)): sha256_file(path)
                        for path in sorted(evidence.iterdir())
                    },
                },
            )
            call_refs.append(
                {
                    "condition": condition,
                    "cache_key": record["cache_key"],
                    "latency_ms": record["latency_ms"],
                    "usage": usage_from_events(record["events"]),
                }
            )
            outputs.append(
                {
                    "condition": condition,
                    "text": record["parsed_final"]["answer"],
                    "disposition": "uncontrolled",
                    "verification_accepted": None,
                    "used_template_fallback": False,
                }
            )

    g_record = caller.call(
        f"condition-g-{args.question_kind}",
        realization_prompt(plan),
        ANSWER_SCHEMA,
        workspace_identity={
            "condition": "G",
            "bounded_provenance_sha256": sha256_file(
                args.provenance_dir / "bounded-source-context.json"
            ),
            "checked_plan_sha256": hashlib.sha256(
                json.dumps(plan.to_dict(), sort_keys=True).encode()
            ).hexdigest(),
        },
    )
    call_refs.append(
        {
            "condition": "G",
            "cache_key": g_record["cache_key"],
            "latency_ms": g_record["latency_ms"],
            "usage": usage_from_events(g_record["events"]),
        }
    )
    g_candidate = g_record["parsed_final"]["answer"]
    g_verification = verify_final_text(plan, g_candidate)
    outputs.append(
        {
            "condition": "G",
            "raw_candidate": g_candidate,
            "text": g_candidate if g_verification.accepted else render_template(plan),
            "disposition": plan.disposition,
            "verification_accepted": g_verification.accepted,
            "unsupported_sentences": g_verification.unsupported_sentences,
            "used_template_fallback": not g_verification.accepted,
            "checked_plan": plan.to_dict(),
        }
    )
    outputs.sort(key=lambda item: item["condition"])
    result = {
        "schema": "crane-explain-provenance-agent-pilot/v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": episode.episode_id,
        "question_kind": args.question_kind,
        "question": question,
        "conditions": [item["condition"] for item in outputs],
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "repository": args.repository_url,
        "repository_commit": args.commit,
        "evaluator_truth_available_to_methods": False,
        "calls": call_refs,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
