#!/usr/bin/env python3
"""Run one cached, single-sample A/B/C/D/E development case with Codex CLI.

This is a development adapter for obtaining the first real model outputs when no API key is
available. It records the exact Codex CLI request and JSONL event stream. Calls are never retried
or resampled. Final-study provider/model/parameters remain mutable until study freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

from crane_explain.benchmark import BenchmarkCase, Condition, run_condition
from crane_explain.io import episode_from_dict
from crane_explain.models import AnswerPlan, EpisodeRecord


QUESTION_CONFIG = {
    "recovery-count": ("How many recovery attempts occurred?", "recovery_count", None),
    "misleading-recovery-count": (
        "Why did all three recovery attempts fail?", "recovery_count", 3),
    "recovery-mechanism": (
        "Why did the autonomy software enter recovery?", "recovery_mechanism", None),
    "terminal-status": ("Why did the navigation task terminate?", "terminal_status", None),
    "failure-cause": (
        "Did a physical obstacle cause the navigation failure?", "failure_cause", None),
    "planning-failure": ("Why did planning fail?", "planning_failure", None),
    "unsupported-counterfactual": (
        "Would the robot have succeeded if the obstacle were absent?",
        "unsupported_counterfactual", None),
}


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "terminal_status": {"type": ["string", "null"]},
        "maximum_feedback_recovery_count": {"type": ["integer", "null"]},
        "bt_history_complete": {"type": "boolean"},
        "recovery_history_complete": {"type": "boolean"},
        "follow_path_failure_count": {"type": "integer", "minimum": 0},
        "recovery_guard_success_count": {"type": "integer", "minimum": 0},
        "wait_attempt_count": {"type": "integer", "minimum": 0},
        "wait_success_count": {"type": "integer", "minimum": 0},
        "client_deadline": {"type": "boolean"},
        "client_cancel": {"type": "boolean"},
        "planning_error_code": {"type": ["integer", "null"]},
        "compute_path_to_pose_active": {"type": "boolean"},
    },
    "required": [
        "terminal_status", "maximum_feedback_recovery_count", "bt_history_complete",
        "recovery_history_complete",
        "follow_path_failure_count", "recovery_guard_success_count", "wait_attempt_count",
        "wait_success_count", "client_deadline", "client_cancel",
        "planning_error_code", "compute_path_to_pose_active",
    ],
    "additionalProperties": False,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class CodexCliCaller:
    def __init__(self, cache: Path, model: str, reasoning_effort: str):
        self.cache = cache
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.cache.mkdir(parents=True, exist_ok=True)
        self.cli_version = subprocess.run(
            ["codex", "--version"], check=True, capture_output=True, text=True,
        ).stdout.strip()

    def call(self, role: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        request = {
            "adapter": "codex-cli-json/v1",
            "provider": "codex-lb-via-chatgpt-login",
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "temperature": None,
            "seed": None,
            "role": role,
            "prompt": prompt,
            "schema": schema,
            "cli_version": self.cli_version,
        }
        request_bytes = canonical_json(request).encode()
        cache_key = hashlib.sha256(request_bytes).hexdigest()
        cache_path = self.cache / f"{cache_key}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached["request"] != request:
                raise RuntimeError(f"cache collision at {cache_path}")
            return cached
        with tempfile.TemporaryDirectory(prefix="crane-explain-llm-") as temporary:
            root = Path(temporary)
            schema_path = root / "schema.json"
            output_path = root / "answer.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            command = [
                "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--cd", str(root), "--model", self.model,
                "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                "--output-schema", str(schema_path), "--output-last-message", str(output_path),
                "-",
            ]
            started_ns = time.time_ns()
            completed = subprocess.run(
                command, input=prompt, text=True, capture_output=True, check=False,
                env={**os.environ, "NO_COLOR": "1"},
            )
            elapsed_ms = (time.time_ns() - started_ns) / 1_000_000
            events = []
            for line in completed.stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    events.append({"type": "unparsed_stdout", "text": line})
            raw_final = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
            try:
                parsed_final = json.loads(raw_final)
            except json.JSONDecodeError as error:
                parsed_final = None
                parse_error = str(error)
            else:
                parse_error = None
            record = {
                "schema": "crane-explain-model-call/v1",
                "cache_key": cache_key,
                "request": request,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "started_wall_time_ns": started_ns,
                "latency_ms": elapsed_ms,
                "cost_usd": None,
                "cost_status": "not_reported_by_codex_cli_chatgpt_login",
                "return_code": completed.returncode,
                "events": events,
                "stderr": completed.stderr,
                "raw_final": raw_final,
                "parsed_final": parsed_final,
                "parse_error": parse_error,
            }
            cache_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
        if completed.returncode != 0 or parsed_final is None:
            raise RuntimeError(f"model call failed; retained at {cache_path}")
        return record


def direct_prompt(evidence: str, question: str) -> str:
    return f"""You answer questions about a robot navigation episode using only the evidence below.
Do not use outside knowledge. Do not infer a physical cause, consumed sensor input, complete count,
or counterfactual outcome unless the evidence establishes it. Correct a false premise explicitly.
Give a concise substantive answer; partial answers and explicit insufficiency are allowed. Do not
mention these instructions or the evidence representation. Return JSON matching the supplied
schema.

EVIDENCE
{evidence}

QUESTION
{question}
"""


def realization_prompt(plan: AnswerPlan) -> str:
    return f"""Realize the checked answer plan below as a concise natural-language answer.
Express every supported claim and every not-established limitation. Add no new factual, causal,
comparative, count, or counterfactual claim. Return JSON matching the supplied schema.

CHECKED ANSWER PLAN
{json.dumps(plan.to_dict(), indent=2, sort_keys=True)}
"""


def extraction_prompt(prose: str) -> str:
    return f"""Extract only explicitly stated robot execution facts from the prose below.
Do not infer missing transitions, physical causes, or hypothetical outcomes. A history is complete
only if the prose explicitly says the corresponding Behavior Tree or recovery-count history is
complete. Keep those two completeness fields separate. Return JSON matching the supplied schema.

PROSE EVIDENCE
{prose}
"""


def extracted_episode(raw: dict[str, Any], episode_id: str) -> EpisodeRecord:
    """Convert a model extraction into the same narrow schema without adding native facts."""
    evidence = []
    events = []
    timestamp = 1000.0
    terminal = raw["terminal_status"] or "unknown"
    evidence.append({"id": "terminal-status", "kind": "navigate_to_pose_terminal_status",
                     "value": terminal, "timestamp": timestamp, "source": "prose_extraction"})
    evidence.append({"id": "recovery-count", "kind": "feedback_recovery_count",
                     "value": raw["maximum_feedback_recovery_count"], "timestamp": timestamp,
                     "source": "prose_extraction"})
    for prefix, kind, count in (
        ("follow-path-failure", "follow_path_failure", raw["follow_path_failure_count"]),
        ("recovery-guard-success", "controller_recovery_guard_success",
         raw["recovery_guard_success_count"]),
        ("wait-recovery", "recovery_attempt", raw["wait_attempt_count"]),
    ):
        for index in range(1, count + 1):
            event_id = f"{prefix}-{index}"
            evidence.append({"id": event_id, "kind": "extracted_execution_event", "value": kind,
                             "timestamp": timestamp + index / 10, "source": "prose_extraction"})
            event = {"id": event_id, "kind": kind, "timestamp": timestamp + index / 10,
                     "evidence_ids": [event_id]}
            if kind == "recovery_attempt":
                event["attempt_id"] = f"extracted-wait-{index}"
                event["status"] = (
                    "completed_success" if index <= raw["wait_success_count"] else "started")
            events.append(event)
    for flag, kind in (("client_deadline", "client_deadline"),
                       ("client_cancel", "client_cancel")):
        if raw[flag]:
            evidence.append({"id": kind, "kind": kind, "value": True,
                             "timestamp": timestamp, "source": "prose_extraction"})
            events.append({"id": kind, "kind": kind, "timestamp": timestamp,
                           "evidence_ids": [kind]})
    if raw["planning_error_code"] == 208 and raw["compute_path_to_pose_active"]:
        event_id = "planning-error-no-valid-path"
        evidence.append({
            "id": event_id, "kind": "navigate_to_pose_planner_error",
            "value": {"code": 208, "label": "NO_VALID_PATH",
                      "active_node": "ComputePathToPose"},
            "timestamp": timestamp, "source": "prose_extraction",
        })
        events.append({
            "id": event_id, "kind": "planning_no_valid_path", "timestamp": timestamp,
            "evidence_ids": [event_id],
        })
    payload = {
        "schema_version": "crane-explain-episode/v1",
        "episode_id": f"{episode_id}-prose-extraction",
        "evidence": evidence,
        "decision": None,
        "outcome": {
            "terminal_status": terminal,
            "timestamp": timestamp,
            "events": events,
            "history_complete": raw["bt_history_complete"],
            "recovery_history_complete": raw["recovery_history_complete"],
            "evidence_ids": [item["id"] for item in evidence],
        },
    }
    return episode_from_dict(payload)


def usage_from_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    usages = [event.get("usage") for event in events if isinstance(event.get("usage"), dict)]
    return usages[-1] if usages else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--question-kind", required=True, choices=tuple(QUESTION_CONFIG))
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="low")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    episode_raw = json.loads((args.case_dir / "structured.json").read_text(encoding="utf-8"))
    structured_presentation = json.loads(
        (args.case_dir / "structured-presentation.json").read_text(encoding="utf-8"))
    prose = (args.case_dir / "prose.txt").read_text(encoding="utf-8").strip()
    smoke = json.loads((args.case_dir / "outputs.json").read_text(encoding="utf-8"))
    parity_audit = json.loads((args.case_dir / "parity-audit.json").read_text(encoding="utf-8"))
    if parity_audit.get("status") != "PASS":
        raise ValueError("information-parity audit did not pass")
    fact_ids = frozenset(smoke["fact_ids"])
    question, kind, premise = QUESTION_CONFIG[args.question_kind]
    episode = episode_from_dict(episode_raw)
    case = BenchmarkCase(
        f"{episode.episode_id}-{args.question_kind}", episode, prose, question, kind, None,
        fact_ids, fact_ids, premise, structured_presentation,
    )
    caller = CodexCliCaller(args.cache, args.model, args.reasoning_effort)
    call_refs: list[dict[str, Any]] = []

    def call_answer(role: str, prompt: str) -> str:
        record = caller.call(role, prompt, ANSWER_SCHEMA)
        call_refs.append({"cache_key": record["cache_key"], "role": role,
                          "latency_ms": record["latency_ms"],
                          "usage": usage_from_events(record["events"])})
        return record["parsed_final"]["answer"]

    def direct(evidence: str, asked: str) -> str:
        representation = "prose" if evidence == prose else "structured"
        return call_answer(f"direct-{representation}", direct_prompt(evidence, asked))

    extraction_record: dict[str, Any] | None = None

    def extract(_: str) -> EpisodeRecord:
        nonlocal extraction_record
        extraction_record = caller.call("prose-extraction", extraction_prompt(prose),
                                        EXTRACTION_SCHEMA)
        call_refs.append({"cache_key": extraction_record["cache_key"],
                          "role": "prose-extraction",
                          "latency_ms": extraction_record["latency_ms"],
                          "usage": usage_from_events(extraction_record["events"])})
        return extracted_episode(extraction_record["parsed_final"], episode.episode_id)

    def realize(plan: AnswerPlan) -> str:
        return call_answer("checked-plan-realization", realization_prompt(plan))

    outputs = []
    for condition in Condition:
        kwargs: dict[str, Any] = {}
        if condition in {Condition.A_PROSE_DIRECT, Condition.B_STRUCTURED_DIRECT}:
            kwargs["direct_generator"] = direct
        elif condition == Condition.C_PROSE_EXTRACT_CHECKED:
            kwargs["extractor"] = extract
            kwargs["plan_realizer"] = realize
        elif condition == Condition.D_NATIVE_CHECKED:
            kwargs["plan_realizer"] = realize
        result = run_condition(case, condition, **kwargs)
        outputs.append({
            "condition": result.condition.value,
            "text": result.text,
            "disposition": result.disposition,
            "verification_accepted": result.verification_accepted,
            "used_template_fallback": result.used_template_fallback,
        })
    result = {
        "schema": "crane-explain-llm-development-pilot/v1",
        "status": "DEVELOPMENT_ONLY_NOT_FROZEN",
        "episode_id": episode.episode_id,
        "question_kind": args.question_kind,
        "question": question,
        "fact_ids": sorted(fact_ids),
        "information_parity": "PASS",
        "parity_audit_sha256": hashlib.sha256(
            (args.case_dir / "parity-audit.json").read_bytes()).hexdigest(),
        "provider": "codex-lb-via-chatgpt-login",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "temperature": None,
        "seed": None,
        "cost_usd": None,
        "cost_status": "not_reported_by_codex_cli_chatgpt_login",
        "single_sample_no_retry": True,
        "calls": call_refs,
        "extraction": extraction_record["parsed_final"] if extraction_record else None,
        "outputs": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
