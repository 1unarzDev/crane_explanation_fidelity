#!/usr/bin/env python3
"""Build a five-condition pipeline smoke test from one real Nav2 capture.

This deliberately uses a transparent rule-based direct generator. It validates information parity
and end-to-end artifact flow; it is not an LLM comparison or an empirical result for RQ1/RQ2.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crane_explain.benchmark import BenchmarkCase, Condition, run_condition
from crane_explain.io import episode_from_dict


FACT_IDS = frozenset({"terminal-status", "recovery-count", "history-completeness"})


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def derive_episode(capture: Path) -> tuple[dict, str]:
    records = load_records(capture / "events.jsonl")
    manifest = json.loads((capture / "manifest.json").read_text(encoding="utf-8"))
    harness = [item["event"] for item in records if item["type"] == "harness_event"]
    results = [item for item in harness if item["type"] == "navigate_to_pose_result"]
    if len(results) != 1:
        raise ValueError(f"expected one action result, found {len(results)}")
    feedback = [item for item in records if item["type"] == "navigate_to_pose_feedback"]
    if not feedback:
        raise ValueError("capture has no NavigateToPose feedback")
    recovery_counts = {item["number_of_recoveries"] for item in feedback}
    if recovery_counts != {0}:
        raise ValueError(
            "this first-pilot adapter only accepts the observed zero-recovery episode; "
            f"found {sorted(recovery_counts)}"
        )
    complete = (
        records[0].get("type") == "capture_started"
        and records[-1].get("type") == "capture_stopped"
    )
    if not complete:
        raise ValueError("capture boundaries are incomplete")
    result = results[0]
    timestamp = result["wall_time_ns"] / 1_000_000_000
    raw = {
        "schema_version": "crane-explain-episode/v1",
        "episode_id": manifest["episode_id"],
        "evidence": [
            {
                "id": "terminal-status",
                "kind": "navigate_to_pose_result",
                "value": result["status"],
                "timestamp": timestamp,
                "source": "harness_event",
                "consumed": None,
            },
            {
                "id": "recovery-count",
                "kind": "navigate_to_pose_feedback_recovery_count",
                "value": 0,
                "timestamp": timestamp,
                "source": "action_feedback",
                "consumed": None,
            },
            {
                "id": "history-completeness",
                "kind": "capture_boundary_check",
                "value": True,
                "timestamp": timestamp,
                "source": "capture_started_and_stopped",
                "consumed": None,
            },
        ],
        "decision": None,
        "outcome": {
            "terminal_status": result["status"],
            "timestamp": timestamp,
            "events": [],
            "history_complete": True,
            "evidence_ids": ["terminal-status", "recovery-count", "history-completeness"],
        },
    }
    prose = (
        "The NavigateToPose action succeeded. Across the complete captured action history, "
        "feedback recorded zero recovery attempts."
    )
    return raw, prose


def direct_generator(evidence: str, question: str) -> str:
    del question
    if evidence.lstrip().startswith("{"):
        raw = json.loads(evidence)
        count = sum(
            1 for event in raw["outcome"]["events"]
            if event.get("kind") == "recovery_attempt" and event.get("attempt_id")
        )
        complete = raw["outcome"]["history_complete"]
    else:
        count = 0 if "zero recovery attempts" in evidence.lower() else None
        complete = "complete captured action history" in evidence.lower()
    if count is None:
        return "The available record does not establish the recovery count."
    qualifier = "Exactly" if complete else "At least"
    return f"{qualifier} {count} recovery attempts occurred."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw, prose = derive_episode(args.capture)
    episode = episode_from_dict(raw)
    case = BenchmarkCase(
        case_id=f"{episode.episode_id}-recovery-count",
        episode=episode,
        prose=prose,
        question="How many recovery attempts occurred?",
        question_kind="recovery_count",
        alternative_id=None,
        structured_fact_ids=FACT_IDS,
        prose_fact_ids=FACT_IDS,
    )
    outputs = []
    for condition in Condition:
        kwargs = {}
        if condition in {Condition.A_PROSE_DIRECT, Condition.B_STRUCTURED_DIRECT}:
            kwargs["direct_generator"] = direct_generator
        elif condition == Condition.C_PROSE_EXTRACT_CHECKED:
            kwargs["extractor"] = lambda _: episode
        result = run_condition(case, condition, **kwargs)
        outputs.append({
            "condition": result.condition.value,
            "text": result.text,
            "disposition": result.disposition,
            "verification_accepted": result.verification_accepted,
            "used_template_fallback": result.used_template_fallback,
        })
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "structured.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "prose.txt").write_text(prose + "\n", encoding="utf-8")
    (args.output / "outputs.json").write_text(json.dumps({
        "schema": "crane-explain-actual-episode-pilot/v1",
        "status": "PIPELINE_SMOKE_NOT_LLM_EVALUATION",
        "generator": "transparent rule-based parity smoke",
        "question": case.question,
        "fact_ids": sorted(FACT_IDS),
        "outputs": outputs,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
