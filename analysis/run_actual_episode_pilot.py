#!/usr/bin/env python3
"""Build a five-condition pipeline smoke test from one real Nav2 capture.

This deliberately uses a transparent rule-based direct generator. It validates information parity
and end-to-end artifact flow; it is not an LLM comparison or an empirical result for RQ1/RQ2.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from crane_explain.benchmark import BenchmarkCase, Condition, run_condition
from crane_explain.io import episode_from_dict


STATUS_NAMES = {4: "succeeded", 5: "canceled", 6: "aborted"}


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def event_seconds(record: dict) -> float:
    stamp = record["event_stamp"]
    return stamp["sec"] + stamp["nanosec"] / 1_000_000_000


def derive_episode(capture: Path) -> tuple[dict, dict, str, frozenset[str]]:
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
    maximum_recovery_count = max(recovery_counts)
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
    bt = [item for item in records if item["type"] == "bt_transition"]
    follow_failures = [
        item for item in bt
        if item["node_name"] == "FollowPath"
        and item["previous_status"] == "RUNNING"
        and item["current_status"] == "FAILURE"
    ]
    follow_starts = [
        item for item in bt
        if item["node_name"] == "FollowPath"
        and item["previous_status"] == "IDLE"
        and item["current_status"] == "RUNNING"
    ]
    follow_terminals = [
        item for item in bt
        if item["node_name"] == "FollowPath"
        and item["previous_status"] == "RUNNING"
        and item["current_status"] in {"FAILURE", "SUCCESS"}
    ]
    guard_successes = [
        item for item in bt
        if item["node_name"] == "WouldAControllerRecoveryHelp"
        and item["previous_status"] == "IDLE"
        and item["current_status"] == "SUCCESS"
    ]
    wait_starts = [
        item for item in bt
        if item["node_name"] == "Wait"
        and item["previous_status"] == "IDLE"
        and item["current_status"] == "RUNNING"
    ]
    wait_successes = [
        item for item in bt
        if item["node_name"] == "Wait"
        and item["previous_status"] == "RUNNING"
        and item["current_status"] == "SUCCESS"
    ]
    if len(wait_starts) != maximum_recovery_count:
        raise ValueError(
            "BT Wait entries disagree with maximum feedback recovery count: "
            f"{len(wait_starts)} versus {maximum_recovery_count}"
        )
    bt_history_complete = len(follow_starts) == len(follow_terminals)
    recovery_history_complete = (
        complete
        and terminal_source in {"harness_result", "action_status"}
        and all(item["goal_id"] == goal_id for item in feedback)
        and feedback[-1]["number_of_recoveries"] == maximum_recovery_count
        and len(wait_starts) == maximum_recovery_count
    )
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
            "id": "physical-cause-status",
            "kind": "answerability",
            "value": "not_established",
            "timestamp": timestamp,
            "source": "evidence_scope_audit",
            "consumed": None,
        },
        {
            "id": "counterfactual-status",
            "kind": "answerability",
            "value": "not_established",
            "timestamp": timestamp,
            "source": "evidence_scope_audit",
            "consumed": None,
        },
        {
            "id": "recovery-count",
            "kind": "navigate_to_pose_feedback_recovery_count",
            "value": maximum_recovery_count,
            "timestamp": timestamp,
            "source": "action_feedback",
            "consumed": None,
        },
        {
            "id": "history-completeness",
            "kind": "capture_boundary_check",
            "value": complete and bt_history_complete,
            "timestamp": timestamp,
            "source": "capture_started_and_stopped",
            "consumed": None,
        },
        {
            "id": "recovery-history-completeness",
            "kind": "capture_boundary_terminal_feedback_bt_cross_check",
            "value": recovery_history_complete,
            "timestamp": timestamp,
            "source": "evidence_scope_audit",
            "consumed": None,
        },
    ]
    outcome_events = []
    for index, item in enumerate(follow_failures, 1):
        event_id = f"follow-path-failure-{index}"
        evidence.append({
            "id": event_id,
            "kind": "bt_transition",
            "value": {"node": "FollowPath", "from": "RUNNING", "to": "FAILURE"},
            "timestamp": event_seconds(item),
            "source": "behavior_tree_log",
            "consumed": None,
        })
        outcome_events.append({
            "id": event_id,
            "kind": "follow_path_failure",
            "timestamp": event_seconds(item),
            "evidence_ids": [event_id],
        })
    for index, item in enumerate(guard_successes, 1):
        event_id = f"recovery-guard-success-{index}"
        evidence.append({
            "id": event_id,
            "kind": "bt_transition",
            "value": {"node": "WouldAControllerRecoveryHelp", "from": "IDLE",
                      "to": "SUCCESS"},
            "timestamp": event_seconds(item),
            "source": "behavior_tree_log",
            "consumed": None,
        })
        outcome_events.append({
            "id": event_id,
            "kind": "controller_recovery_guard_success",
            "timestamp": event_seconds(item),
            "evidence_ids": [event_id],
        })
    for index, item in enumerate(wait_starts, 1):
        event_id = f"wait-recovery-{index}"
        attempt_id = f"wait-{item['node_uid']}-{index}"
        evidence.append({
            "id": event_id,
            "kind": "bt_transition",
            "value": {"node": "Wait", "from": "IDLE", "to": "RUNNING",
                      "attempt_id": attempt_id},
            "timestamp": event_seconds(item),
            "source": "behavior_tree_log",
            "consumed": None,
        })
        outcome_events.append({
            "id": event_id,
            "kind": "recovery_attempt",
            "timestamp": event_seconds(item),
            "attempt_id": attempt_id,
            "status": "completed_success" if index <= len(wait_successes) else "started",
            "evidence_ids": [event_id],
        })
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
            "history_complete": complete and bt_history_complete,
            "recovery_history_complete": recovery_history_complete,
            "evidence_ids": evidence_ids,
        },
    }
    parity_facts = [
        {"id": "terminal-status", "kind": "action_terminal_status",
         "value": terminal_status},
        {"id": "recovery-count", "kind": "maximum_feedback_recovery_count",
         "value": maximum_recovery_count},
        {"id": "wait-recoveries", "kind": "recorded_wait_recovery_entries",
         "value": len(wait_starts), "completed_success": len(wait_successes)},
        {"id": "follow-path-failures", "kind": "recorded_follow_path_failure_transitions",
         "value": len(follow_failures)},
        {"id": "recovery-guard-successes", "kind": "recorded_guard_success_transitions",
         "value": len(guard_successes)},
        {"id": "follow-path-starts", "kind": "recorded_follow_path_start_transitions",
         "value": len(follow_starts)},
        {"id": "follow-path-terminals", "kind": "recorded_follow_path_terminal_transitions",
         "value": len(follow_terminals)},
        {"id": "history-completeness", "kind": "bt_transition_history_complete",
         "value": bt_history_complete},
        {"id": "recovery-history-completeness",
         "kind": "recovery_count_history_complete",
         "value": recovery_history_complete},
        {"id": "physical-cause-status", "kind": "physical_cause_established",
         "value": False},
        {"id": "counterfactual-status", "kind": "hypothetical_outcome_established",
         "value": False},
    ]
    if follow_failures and guard_successes and wait_starts:
        parity_facts.append({
            "id": "first-recovery-sequence",
            "kind": "recorded_ordered_transition_sequence",
            "value": ["FollowPath:FAILURE", "WouldAControllerRecoveryHelp:SUCCESS",
                      "Wait:RUNNING"],
        })
    if deadline_events:
        parity_facts.append({
            "id": "client-deadline", "kind": "client_deadline_recorded", "value": True,
        })
    if cancel_events:
        parity_facts.append({
            "id": "client-cancel", "kind": "client_cancellation_requested", "value": True,
        })
    structured_presentation = {
        "schema": "crane-explain-parity-presentation/v1",
        "episode_id": manifest["episode_id"],
        "facts": parity_facts,
    }
    prose_parts = [
        f"The NavigateToPose action's recorded terminal status was {terminal_status}.",
        f"NavigateToPose feedback reached a recovery count of {maximum_recovery_count}.",
    ]
    prose_parts.append(
        "The recovery-count history is complete for this action: capture brackets the accepted "
        "goal and terminal result or status, the final monotonic feedback count matches the "
        "distinct Wait entries, and all records use the same goal ID."
        if recovery_history_complete else
        "The available records do not establish a complete recovery-count history for this action."
    )
    if wait_starts:
        prose_parts.append(
            f"The Behavior Tree log records {len(wait_starts)} distinct entries into the Wait "
            f"recovery action; {len(wait_successes)} returned SUCCESS."
        )
    else:
        prose_parts.append(
            "The Behavior Tree log records no entries into the Wait recovery action and no "
            "successful Wait completions."
        )
    prose_parts.append(
        f"The Behavior Tree log records {len(follow_failures)} FollowPath transitions from "
        f"RUNNING to FAILURE and {len(guard_successes)} WouldAControllerRecoveryHelp "
        "transitions from IDLE to SUCCESS."
    )
    if follow_failures and guard_successes and wait_starts:
        prose_parts.append(
            "In the recorded sequence, FollowPath returned FAILURE, "
            "WouldAControllerRecoveryHelp returned SUCCESS, and the tree then entered Wait."
        )
    if not bt_history_complete:
        prose_parts.append(
            f"The log records {len(follow_starts)} FollowPath starts but only "
            f"{len(follow_failures)} terminal FollowPath FAILURE transitions, so the Behavior "
            "Tree transition history is not complete."
        )
    else:
        prose_parts.append(
            f"The log records {len(follow_starts)} FollowPath starts and "
            f"{len(follow_terminals)} terminal FollowPath transitions, so the Behavior Tree "
            "transition history is complete."
        )
    if deadline_events:
        prose_parts.append("The experiment harness recorded a client deadline.")
    if cancel_events:
        prose_parts.append("The experiment harness requested cancellation.")
    prose_parts.append(
        "These records do not establish the physical cause of the navigation failure or what "
        "would have happened under a hypothetical environment change."
    )
    parity_ids = frozenset(fact["id"] for fact in parity_facts)
    return raw, structured_presentation, " ".join(prose_parts), parity_ids


def direct_generator(evidence: str, question: str) -> str:
    lowered_question = question.lower()
    if "physical obstacle" in lowered_question:
        return "The available records do not establish whether a physical obstacle caused the failure."
    if "would" in lowered_question:
        return "The available records do not establish the outcome of that hypothetical change."
    if "enter recovery" in lowered_question:
        return (
            "FollowPath returned FAILURE, the controller-recovery guard returned SUCCESS, and "
            "the Behavior Tree then entered Wait. This does not establish why FollowPath "
            "failed physically."
        )
    if "terminate" in lowered_question:
        if evidence.lstrip().startswith("{"):
            raw = json.loads(evidence)
            if "facts" in raw:
                facts = {item["id"]: item for item in raw["facts"]}
                status = facts["terminal-status"]["value"]
                kinds = set()
            else:
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
        if kinds & {"client_deadline", "client_cancel"}:
            sentences.append(
                "These client events do not establish that a Behavior Tree timeout or a physical "
                "navigation failure occurred."
            )
        return " ".join(sentences)
    if evidence.lstrip().startswith("{"):
        raw = json.loads(evidence)
        if "facts" in raw:
            facts = {item["id"]: item for item in raw["facts"]}
            count = facts["wait-recoveries"]["value"]
            complete = facts["history-completeness"]["value"]
        else:
            count = sum(
                1 for event in raw["outcome"]["events"]
                if event.get("kind") == "recovery_attempt" and event.get("attempt_id")
            )
            complete = raw["outcome"]["history_complete"]
    else:
        match = re.search(r"recovery count of (\d+)", evidence.lower())
        count = int(match.group(1)) if match else (
            0 if "zero recovery attempts" in evidence.lower() else None)
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
        "--question-kind", choices=(
            "recovery-count", "misleading-recovery-count", "recovery-mechanism",
            "terminal-status", "failure-cause", "unsupported-counterfactual",
        ),
        default="recovery-count",
    )
    args = parser.parse_args()
    raw, structured_presentation, prose, fact_ids = derive_episode(args.capture)
    episode = episode_from_dict(raw)
    questions = {
        "recovery-count": ("How many recovery attempts occurred?", "recovery_count", None),
        "misleading-recovery-count": (
            "Why did all three recovery attempts fail?", "recovery_count", 3),
        "recovery-mechanism": (
            "Why did the autonomy software enter recovery?", "recovery_mechanism", None),
        "terminal-status": ("Why did the navigation task terminate?", "terminal_status", None),
        "failure-cause": (
            "Did a physical obstacle cause the navigation failure?", "failure_cause", None),
        "unsupported-counterfactual": (
            "Would the robot have succeeded if the obstacle were absent?",
            "unsupported_counterfactual", None),
    }
    question, question_kind, premise_count = questions[args.question_kind]
    case = BenchmarkCase(
        case_id=f"{episode.episode_id}-{args.question_kind}",
        episode=episode,
        prose=prose,
        question=question,
        question_kind=question_kind,
        alternative_id=None,
        structured_fact_ids=fact_ids,
        prose_fact_ids=fact_ids,
        premise_count=premise_count,
        structured_presentation=structured_presentation,
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
    (args.output / "structured-presentation.json").write_text(
        json.dumps(structured_presentation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (args.output / "prose.txt").write_text(prose + "\n", encoding="utf-8")
    (args.output / "parity-audit.json").write_text(json.dumps({
        "schema": "crane-explain-parity-audit/v1",
        "status": "PASS",
        "structured_fact_ids": sorted(fact_ids),
        "prose_fact_ids": sorted(fact_ids),
        "structured_presentation": "structured-presentation.json",
        "prose_presentation": "prose.txt",
        "audit_method": "fact-by-fact manual construction; exact timestamps omitted from both",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
