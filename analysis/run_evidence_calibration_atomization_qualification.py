#!/usr/bin/env python3
"""Run no-retry, method-blind atomization canary or synthetic qualification.

This runner deliberately makes no semantic pass decision. Exact-span structural
validation is necessary but an independent claim-completeness review is required.
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

from validate_evidence_calibration_atomization import validate


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-atomization-v1-freeze.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def bound_file(binding: dict[str, str]) -> Path:
    path = ROOT / binding["path"]
    if sha256(path.read_bytes()) != binding["raw_sha256"]:
        raise ValueError(f"frozen file hash mismatch: {binding['path']}")
    return path


def load_freeze(path: Path = FREEZE) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze["schema"] not in {"crane-evidence-calibration-atomization-qualification-freeze/v1",
                                "crane-evidence-calibration-atomization-qualification-freeze/v2"}:
        raise ValueError("unsupported atomization qualification freeze")
    suite = json.loads(bound_file(freeze["suite"]).read_text(encoding="utf-8"))
    if suite["schema"] not in {"crane-evidence-calibration-atomization-qualification-suite/v1",
                              "crane-evidence-calibration-atomization-qualification-suite/v2"}:
        raise ValueError("unsupported atomization qualification suite")
    prompt = bound_file(freeze["candidate"]["prompt"]).read_text(encoding="utf-8")
    schema = json.loads(bound_file(freeze["candidate"]["return_schema"]).read_text(encoding="utf-8"))
    cases = suite["cases"]
    if len(cases) != 20 or len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("qualification case count or uniqueness changed")
    for split, count in (("development", 4), ("heldout", 16)):
        if sum(case["split"] == split for case in cases) != count:
            raise ValueError("qualification split count changed")
    for case in cases:
        if not case["expected"] or any(item["source_span"] not in case["response_text"] for item in case["expected"]):
            raise ValueError(f"invalid construction-defined gold in {case['case_id']}")
    return freeze, suite, prompt, schema


def call_once(
    *, entry: dict[str, str], role: str, freeze: dict[str, Any], prompt: str,
    schema: dict[str, Any], output: Path, runner: Any = subprocess.run,
    freeze_path: Path = FREEZE,
) -> dict[str, Any]:
    candidate = freeze["candidate"]
    if candidate["transport"] != "codex-cli-chatgpt-login-ephemeral/v1" or candidate["tools"] != "none":
        raise ValueError("unapproved atomizer transport or tool configuration")
    model, effort = candidate["model"], candidate["reasoning_effort"]
    payload = {"opaque_response_id": entry["opaque_response_id"], "response_text": entry["response_text"]}
    full_prompt = "\n".join((
        prompt,
        "UNTRUSTED_EXPLANATION_DATA_BEGIN",
        canonical(payload).decode("utf-8"),
        "UNTRUSTED_EXPLANATION_DATA_END",
        "Return only the object required by the output schema. Do not use tools.",
    ))
    identity = {
        "role": role, "model": model, "reasoning_effort": effort,
        "transport": candidate["transport"], "freeze_sha256": sha256(freeze_path.read_bytes()),
        "payload_sha256": sha256(canonical(payload)),
        "prompt_sha256": sha256(full_prompt.encode("utf-8")),
        "schema_sha256": sha256(canonical(schema)),
        "workspace": "empty-temporary-read-only", "quality_driven_retries": 0,
    }
    if output.exists():
        retained = json.loads(output.read_text(encoding="utf-8"))
        if retained.get("request_identity") != identity:
            raise ValueError(f"immutable atomization call identity mismatch: {output}")
        return retained
    started = time.time_ns()
    with tempfile.TemporaryDirectory(prefix="crane-atomizer-") as temp:
        temporary = Path(temp)
        schema_path, final_path = temporary / "schema.json", temporary / "final.json"
        schema_path.write_bytes(canonical(schema) + b"\n")
        command = [
            "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
            "--sandbox", "read-only", "--cd", str(temporary), "--model", model,
            "--config", f'model_reasoning_effort="{effort}"',
            "--output-schema", str(schema_path), "--output-last-message", str(final_path), "-",
        ]
        try:
            done = runner(command, input=full_prompt, text=True, capture_output=True, check=False,
                          env={**os.environ, "NO_COLOR": "1"}, timeout=300)
            return_code, stdout, stderr, timed_out = done.returncode, done.stdout, done.stderr, False
        except subprocess.TimeoutExpired as error:
            return_code, timed_out = 124, True
            stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        final = final_path.read_text(encoding="utf-8") if final_path.exists() else ""
    invalid_event = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_event = "unparsed_stdout"
            break
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict) and item.get("type") not in {"agent_message", "reasoning"}:
            invalid_event = item.get("type")
        if isinstance(event, dict) and event.get("type") in {"error", "turn.failed"}:
            invalid_event = event.get("type")
    base = {
        "schema": "crane-evidence-calibration-atomization-call/v1",
        "request_identity": identity, "attempt_count": 1, "quality_driven_retries": 0,
        "return_code": return_code, "timed_out": timed_out,
        "latency_ms": (time.time_ns() - started) / 1_000_000,
        "stdout_sha256": sha256(stdout.encode("utf-8")), "stderr_sha256": sha256(stderr.encode("utf-8")),
        "invalid_event": invalid_event, "raw_final": final,
        "credential_persisted": False, "method_key_accessed": False,
    }
    try:
        if return_code or timed_out or invalid_event:
            raise ValueError("transport, timeout, or forbidden tool/event failure")
        parsed = json.loads(final)
        structural = validate(payload, parsed)
        result = {**base, "status": "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED",
                  "parsed_final": parsed, "structural_validation": structural}
    except (ValueError, json.JSONDecodeError, TypeError, KeyError) as error:
        result = {**base, "status": "FAILED_NO_RETRY", "failure": str(error)}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "qualification"), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=FREEZE)
    args = parser.parse_args()
    freeze, suite, prompt, schema = load_freeze(args.freeze)
    if args.mode == "canary":
        cases = [{"case_id": "non-study-schema-canary", "response_text": "The action succeeded."}]
        passes = ("canary",)
    else:
        canary_path = args.output_root / "canary" / "non-study-schema-canary.json"
        if not canary_path.is_file():
            raise ValueError("non-study atomization schema canary has not run")
        canary = json.loads(canary_path.read_text(encoding="utf-8"))
        if canary.get("status") != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            raise ValueError("non-study atomization schema canary did not pass")
        cases = suite["cases"]
        passes = ("A", "B")
    summary = []
    for slot in passes:
        for case in cases:
            entry = {"opaque_response_id": f"{case['case_id']}-{slot}", "response_text": case["response_text"]}
            output = args.output_root / slot / f"{case['case_id']}.json"
            result = call_once(entry=entry, role=f"atomizer-{slot}", freeze=freeze,
                               prompt=prompt, schema=schema, output=output, freeze_path=args.freeze)
            summary.append({"slot": slot, "case_id": case["case_id"], "status": result["status"]})
            if result["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
                print(json.dumps({"status": "STOPPED_ON_RETAINED_FAILURE", "calls": summary}, indent=2))
                return 1
    print(json.dumps({"status": "STRUCTURAL_RETURNS_ONLY_INDEPENDENT_SEMANTIC_REVIEW_REQUIRED",
                      "calls": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
