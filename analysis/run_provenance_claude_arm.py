#!/usr/bin/env python3
"""Run matched F/G/H conditions for the secondary Claude replication arm.

This is a deliberate sibling of the hash-frozen ``run_provenance_agent_pilot.py`` rather than an
edit of it. That file's SHA-256 is pinned by ``manifests/study/provenance-study-freeze-v1.json``
and amendment 3, so changing it would break the freeze for a purpose the freeze never covered. All
shared logic is imported from the frozen module; only the caller and the result envelope differ.

The arm is declared in ``manifests/study/provenance-claude-replication-arm-v1.json``. It reuses the
already-captured episodes exactly, makes no new capture, and writes into its own output, cache, and
manifest namespaces so that no Claude artifact can ever be mistaken for a frozen Luna artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from claude_cli_caller import ClaudeCliCaller
from crane_explain.io import episode_from_dict, provenance_from_dict
from crane_explain.provenance import resolve_provenance
from crane_explain.realize import render_template
from crane_explain.reasoning import plan_failure_cause, plan_recovery_mechanism
from crane_explain.runtime_presentation import (
    audit_fgh_information_parity,
    build_nav2_runtime_presentation,
    load_jsonl_records,
    validate_episode_projection,
)
from crane_explain.verification import verify_final_text
from run_llm_episode_pilot import ANSWER_SCHEMA
from run_provenance_agent_pilot import (
    QUESTIONS,
    agent_prompt,
    checked_realization_prompt,
    extract_repository,
    sha256_file,
)

ARM = "provenance-claude-replication-arm-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--provenance-dir", required=True, type=Path)
    parser.add_argument("--runtime-presentation", required=True, type=Path)
    parser.add_argument("--parity-audit", required=True, type=Path)
    parser.add_argument("--prior-a-e", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--question-kind", choices=tuple(QUESTIONS), required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument(
        "--study-status",
        choices=(
            "CLAUDE_ARM_DEVELOPMENT_MODEL_STRENGTH_CONTROL",
            "CLAUDE_ARM_SECONDARY_REPLICATION",
        ),
        required=True,
    )
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")

    question = QUESTIONS[args.question_kind]
    episode_path = args.case_dir / "structured.json"
    episode = episode_from_dict(json.loads(episode_path.read_text(encoding="utf-8")))
    runtime_presentation = json.loads(args.runtime_presentation.read_text(encoding="utf-8"))
    capture_records = load_jsonl_records(
        (args.capture_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    )
    capture_manifest = json.loads((args.capture_dir / "manifest.json").read_text(encoding="utf-8"))
    rebuilt_presentation = build_nav2_runtime_presentation(
        capture_records,
        capture_manifest,
        (args.capture_dir / "behavior_tree.xml").read_bytes(),
        episode,
        (args.capture_dir / "runtime_manifest.json").read_bytes()
        if (args.capture_dir / "runtime_manifest.json").is_file()
        else None,
    )
    if runtime_presentation != rebuilt_presentation:
        raise SystemExit("retained runtime presentation does not match the raw capture")
    retained_parity_audit = json.loads(args.parity_audit.read_text(encoding="utf-8"))
    computed_parity_audit = audit_fgh_information_parity(runtime_presentation, args.question_kind)
    if retained_parity_audit != computed_parity_audit:
        raise SystemExit("retained information-parity audit does not match the presentation")
    if not retained_parity_audit["accepted"]:
        raise SystemExit("F/G/H information-parity audit was not accepted")
    if runtime_presentation["episode_id"] != episode.episode_id:
        raise SystemExit("runtime presentation and structured episode IDs disagree")
    validate_episode_projection(runtime_presentation, episode)
    bundle = provenance_from_dict(
        json.loads((args.provenance_dir / "provenance.json").read_text(encoding="utf-8"))
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
    caller = ClaudeCliCaller(args.cache, args.model, args.reasoning_effort)
    call_refs: list[dict[str, Any]] = []
    outputs = list(json.loads(args.prior_a_e.read_text(encoding="utf-8"))["outputs"])

    with tempfile.TemporaryDirectory(prefix="crane-provenance-claude-") as temporary:
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
                raw_names = ["events.jsonl", "manifest.json", "behavior_tree.xml"]
                if (args.capture_dir / "runtime_manifest.json").is_file():
                    raw_names.append("runtime_manifest.json")
                for name in raw_names:
                    shutil.copy2(args.capture_dir / name, evidence / name)
                description = (
                    "Raw passive capture files are in _robot_visible/: events.jsonl, "
                    "manifest.json, behavior_tree.xml, and runtime_manifest.json when retained. "
                    "Treat repeated publications as repeated messages, not new attempts."
                )
            else:
                shutil.copy2(args.runtime_presentation, evidence / "runtime-presentation.json")
                description = (
                    "The deterministic structured runtime presentation is in "
                    "_robot_visible/runtime-presentation.json. It is derived only from the same "
                    "raw capture available to condition F and contains no source-provenance links."
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
                    "cost_usd": record["cost_usd"],
                    "workspace_unmodified": record["workspace_unmodified"],
                    "usage": record["usage"],
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
        checked_realization_prompt(plan, runtime_presentation),
        ANSWER_SCHEMA,
        workspace_identity={
            "condition": "G",
            "shared_runtime_presentation_sha256": sha256_file(args.runtime_presentation),
            "information_parity_audit_sha256": sha256_file(args.parity_audit),
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
            "cost_usd": g_record["cost_usd"],
            "workspace_unmodified": g_record["workspace_unmodified"],
            "usage": g_record["usage"],
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
        "schema": "crane-explain-provenance-claude-arm/v1",
        "arm": ARM,
        "status": args.study_status,
        "frozen_luna_arm_unchanged": True,
        "episode_id": episode.episode_id,
        "question_kind": args.question_kind,
        "question": question,
        "conditions": [item["condition"] for item in outputs],
        "adapter": caller.adapter,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "single_sample_no_retry": True,
        "repository": args.repository_url,
        "repository_commit": args.commit,
        "evaluator_truth_available_to_methods": False,
        "read_only_workspace_verified": all(
            call["workspace_unmodified"] for call in call_refs
        ),
        "information_parity": {
            "accepted": retained_parity_audit["accepted"],
            "runtime_presentation_sha256": sha256_file(args.runtime_presentation),
            "audit_sha256": sha256_file(args.parity_audit),
            "unit_count": len(retained_parity_audit["units"]),
            "provenance_is_treatment_not_shared_runtime_fact": True,
        },
        "calls": call_refs,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "outputs"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
