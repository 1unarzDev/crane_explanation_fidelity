#!/usr/bin/env python3
"""Export a checked recovery-mechanism diagnosis from ecological robot-visible evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
sys.path.insert(0, str(CORE))

from crane_explain.diagnostics import (  # noqa: E402
    BehaviorTreeTransition,
    RecoveryExecutionObservation,
    RecoveryInvocationRecord,
    diagnose_recovery_execution_sequence,
    render_diagnostic,
    verify_diagnostic_text,
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_export(evidence_path: Path, source_reference: str) -> dict[str, Any]:
    raw = evidence_path.read_bytes()
    evidence = json.loads(raw)
    if evidence.get("schema") != "crane-ecological-robot-visible-evidence-v1":
        raise ValueError("unexpected ecological robot-visible evidence schema")
    if evidence.get("withholding", {}).get("evaluatorTruthAvailableToMethods") is not False:
        raise ValueError("evaluator-only truth boundary is not explicitly closed")

    bt = evidence.get("bt") or {}
    runtime = evidence.get("runtime") or {}
    action = evidence.get("action") or {}
    policy_sha256 = str(runtime.get("btPolicySha256") or "")
    if not policy_sha256:
        raise ValueError("BT recovery policy SHA-256 is missing")

    transitions = tuple(
        BehaviorTreeTransition(
            record_id=str(item["recordId"]),
            node_name=str(item["nodeName"]),
            previous_status=str(item["previousStatus"]),
            current_status=str(item["currentStatus"]),
            goal_id=str(item["goalId"]),
        )
        for item in bt.get("transitionSequence") or ()
    )
    invocations = []
    for item in bt.get("recoveryInvocations") or ():
        qualification = item.get("sourceQualification") or {}
        observed_start = qualification.get("observedStartTransition") or {}
        invocations.append(
            RecoveryInvocationRecord(
                invocation_id=str(item["invocationId"]),
                node_name=str(item["nodeName"]),
                goal_id=str(item["goalId"]),
                start_transition_id=str(item["startTransitionId"]),
                end_transition_id=(
                    str(item["endTransitionId"])
                    if item.get("endTransitionId") is not None
                    else None
                ),
                complete=bool(item.get("complete", False)),
                terminal_status=(
                    str(item["terminalStatus"])
                    if item.get("terminalStatus") is not None
                    else None
                ),
                classifier_basis=str(qualification.get("classifierBasis") or ""),
                classifier_rule=str(qualification.get("classifierRule") or ""),
                policy_sha256=str(qualification.get("policySha256") or ""),
                observed_start_transition_id=str(observed_start.get("recordId") or ""),
            )
        )

    completeness = bt.get("completeness") or {}
    history_complete = (
        completeness.get("historyStatus") == "complete"
        and completeness.get("exactRecoveryCountEligible") is True
    )
    evidence_sha256 = sha256_bytes(raw)
    observation = RecoveryExecutionObservation(
        episode_id=str(evidence["episodeId"]),
        evidence_ids=(
            f"ecological-evidence-sha256:{evidence_sha256}",
            f"bt-policy-sha256:{policy_sha256}",
        ),
        action_status=str(action["terminalStatus"]),
        goal_id=str(action["goalId"]),
        transitions=transitions,
        recovery_invocations=tuple(invocations),
        recovery_policy_sha256=policy_sha256,
        whole_history_complete=history_complete,
        maximum_feedback_recovery_count=(
            int(evidence["feedback"]["maximumObservedRecoveryCount"])
            if evidence.get("feedback", {}).get("maximumObservedRecoveryCount") is not None
            else None
        ),
        physical_cause_established=bool(
            evidence.get("withholding", {}).get("physicalCauseEstablished", False)
        ),
        source_anchor_ids=(f"bt-policy-sha256:{policy_sha256}",),
    )
    result = diagnose_recovery_execution_sequence(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    if not verification.accepted:
        raise RuntimeError("deterministic recovery diagnosis failed final-text verification")

    return {
        "schema": "crane-recovery-execution-diagnostic-export-v1",
        "episode_id": observation.episode_id,
        "visibility": "robot_visible",
        "development_only": True,
        "source": {
            "robot_visible_evidence": source_reference,
            "robot_visible_evidence_sha256": evidence_sha256,
            "bt_policy_sha256": policy_sha256,
        },
        "method_input": {
            "action_status": observation.action_status,
            "goal_id": observation.goal_id,
            "transition_count": len(observation.transitions),
            "retained_recovery_invocation_count": len(
                observation.recovery_invocations
            ),
            "whole_history_complete": observation.whole_history_complete,
            "maximum_nav2_feedback_recovery_count": (
                observation.maximum_feedback_recovery_count
            ),
        },
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
        "evidence_boundary": {
            "included": [
                "goal-scoped BehaviorTreeLog transition sequence",
                "capture-side unique recovery invocation records",
                "bounded classifier rule and policy hash",
                "NavigateToPose terminal status",
                "Nav2 feedback recovery count as non-identity context only",
            ],
            "excluded": [
                "evaluator-only geometry and semantic obstacle identity",
                "claim that delivered costmaps were consumed by the planner",
                "physical cause of planner failure",
                "exact lifetime recovery count without whole-history completeness",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--source-reference", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_export(args.evidence, args.source_reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
