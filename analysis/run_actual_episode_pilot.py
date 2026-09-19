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


STATUS_NAMES = {4: "succeeded", 5: "canceled", 6: "aborted"}


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def derive_episode(capture: Path) -> tuple[dict, str, frozenset[str]]:
    records = load_records(capture / "events.jsonl")
    manifest = json.loads((capture / "manifest.json").read_text(encoding="utf-8"))
    harness = [item["event"] for item in records if item["type"] == "harness_event"]
    goals = [item for item in harness if item["type"] == "navigate_to_pose_goal"]
    if len(goals) != 1:
        raise ValueError(f"expected one accepted action goal, found {len(goals)}")
    goal_id = goals[0]["goal_id"]
    results = [item for item in harness if item["type"] == "navigate_to_pose_result"]
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
    if len(results) == 1:
        terminal_status = results[0]["status"]
        timestamp = results[0]["wall_time_ns"] / 1_000_000_000
        terminal_source = "harness_result"
    elif not results:
        statuses = [
            (record["received_wall_time_ns"], item["status"])
            for record in records if record["type"] == "action_status"
            for item in record["statuses"] if item["goal_id"] == goal_id
        ]
        terminal = next(
            ((wall, STATUS_NAMES[code]) for wall, code in reversed(statuses)
             if code in STATUS_NAMES), None)
        if terminal is None:
            raise ValueError("capture has neither a result payload nor a terminal action status")
        timestamp = terminal[0] / 1_000_000_000
        terminal_status = terminal[1]
        terminal_source = "action_status"
    else:
        raise ValueError(f"expected at most one action result, found {len(results)}")
    deadline_events = [item for item in harness if item["type"] == "client_deadline"]
    cancel_events = [item for item in harness if item["type"] == "client_cancel"]
    evidence = [
        {
            "id": "terminal-status",
            "kind": "navigate_to_pose_terminal_status",
            "value": terminal_status,
            "timestamp": timestamp,
            "source": terminal_source,
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
    ]
    outcome_events = []
    for event_id, kind, items in (
        ("client-deadline", "client_deadline", deadline_events),
        ("client-cancel", "client_cancel", cancel_events),
    ):
        if not items:
            continue
        event_timestamp = items[-1]["wall_time_ns"] / 1_000_000_000
        evidence.append({
            "id": event_id,
            "kind": kind,
            "value": True,
            "timestamp": event_timestamp,
            "source": "harness_event",
            "consumed": None,
        })
        outcome_events.append({
            "id": event_id,
            "kind": kind,
            "timestamp": event_timestamp,
            "evidence_ids": [event_id],
        })
    evidence_ids = [item["id"] for item in evidence]
    raw = {
        "schema_version": "crane-explain-episode/v1",
        "episode_id": manifest["episode_id"],
        "evidence": evidence,
        "decision": None,
        "outcome": {
            "terminal_status": terminal_status,
            "timestamp": timestamp,
            "events": outcome_events,
            "history_complete": True,
            "evidence_ids": evidence_ids,
        },
    }
    prose_parts = [
        f"The NavigateToPose action's recorded terminal status was {terminal_status}.",
        "Across the complete captured action history, feedback recorded zero recovery attempts.",
    ]
    if deadline_events:
        prose_parts.append("The experiment harness recorded a client deadline.")
    if cancel_events:
        prose_parts.append("The experiment harness requested cancellation.")
    prose_parts.append(
        "These records do not establish a Behavior Tree timeout or the physical cause of any "
        "navigation difficulty."
    )
    return raw, " ".join(prose_parts), frozenset(evidence_ids)


def direct_generator(evidence: str, question: str) -> str:
    if "terminate" in question.lower():
        if evidence.lstrip().startswith("{"):
            raw = json.loads(evidence)
            status = raw["outcome"]["terminal_status"]
            kinds = {event["kind"] for event in raw["outcome"]["events"]}
        else:
            lowered = evidence.lower()
            status = next(
                value for value in ("canceled", "aborted", "succeeded")
                if f"terminal status was {value}" in lowered)
            kinds = {
                kind for kind, phrase in (
                    ("client_deadline", "client deadline"),
                    ("client_cancel", "requested cancellation"),
                ) if phrase in lowered
            }
        sentences = [f"The recorded task outcome was {status}."]
        if "client_deadline" in kinds:
            sentences.append("The experiment harness recorded a client deadline.")
        if "client_cancel" in kinds:
            sentences.append("The experiment harness requested cancellation.")
        if kinds:
            sentences.append(
                "These client events do not establish that a Behavior Tree timeout or a physical "
                "navigation failure occurred."
            )
        return " ".join(sentences)
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
    parser.add_argument(
        "--question-kind", choices=("recovery-count", "terminal-status"),
        default="recovery-count",
    )
    args = parser.parse_args()
    raw, prose, fact_ids = derive_episode(args.capture)
    episode = episode_from_dict(raw)
    if args.question_kind == "terminal-status":
        question = "Why did the navigation task terminate?"
    else:
        question = "How many recovery attempts occurred?"
    case = BenchmarkCase(
        case_id=f"{episode.episode_id}-{args.question_kind}",
        episode=episode,
        prose=prose,
        question=question,
        question_kind=args.question_kind.replace("-", "_"),
        alternative_id=None,
        structured_fact_ids=fact_ids,
        prose_fact_ids=fact_ids,
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
        "fact_ids": sorted(fact_ids),
        "outputs": outputs,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
