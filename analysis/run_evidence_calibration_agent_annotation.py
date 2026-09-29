#!/usr/bin/env python3
"""Run two blinded agent annotations and disagreement-only agent adjudication.

This runner uses the frozen v4 Astra exact-task qualification. It makes
one no-tool Responses request per logical agent identity, retains failures without quality-driven
retry, and never reads the evaluator join key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import subprocess
import time
from typing import Any
import urllib.error
import urllib.request

from adjudicate_evidence_calibration_annotations import build_handoff, compare, finalize, validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from luna_model_judge import extract_output_text, parse_sse_response, resolve_base_url


ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-astra"
EFFORT = "high"
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md"
RETURN_SCHEMA = ROOT / "research/explanation_fidelity/schemas/blinded-agent-atomic-annotation-return-v2.schema.json"
ADJUDICATION_SCHEMA = ROOT / "research/explanation_fidelity/schemas/blinded-agent-atomic-adjudication-v2.schema.json"
AMENDMENT = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-agent-annotation-amendment-v2.json"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(canonical_json_bytes(value) + b"\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


class StructuredAgentCaller:
    def __init__(self, cache: Path, *, opener: Any = urllib.request.urlopen, timeout_s: float = 300.0):
        self.cache = cache
        self.opener = opener
        self.timeout_s = timeout_s
        self.base_url = resolve_base_url(None)

    def call(self, *, logical_role: str, payload: dict[str, Any], schema: dict[str, Any], prompt: str) -> dict[str, Any]:
        body = {
            "model": MODEL,
            "input": [
                {"role": "developer", "content": [{"type": "input_text", "text": prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": _canonical(payload)}]},
            ],
            "reasoning": {"effort": EFFORT},
            "text": {"format": {"type": "json_schema", "name": logical_role.replace("-", "_"), "strict": True, "schema": schema}},
            "store": False,
            "stream": False,
            "tools": [],
        }
        identity = {
            "transport": "codex-lb-responses-no-tools/v1",
            "logical_role": logical_role,
            "model": MODEL,
            "effort": EFFORT,
            "endpoint": f"{self.base_url}/responses",
            "prompt_sha256": _digest(prompt.encode()),
            "schema_sha256": _digest(canonical_json_bytes(schema)),
            "payload": payload,
            "amendment_sha256": _digest(AMENDMENT.read_bytes()),
        }
        cache_key = _digest(_canonical(identity).encode())
        path = self.cache / f"{cache_key}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("request_identity") != identity:
                raise RuntimeError(f"cache collision at {path}")
            if record.get("status") != "VALID":
                raise RuntimeError(f"retained agent failure at {path}")
            return record
        key = os.environ.get("CODEX_LB_API_KEY")
        if not key:
            raise RuntimeError("Codex LB credential is unavailable")
        encoded = _canonical(body).encode()
        started = time.time_ns()
        request = urllib.request.Request(
            f"{self.base_url}/responses",
            data=encoded,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            method="POST",
        )
        response = None
        failure: dict[str, Any] | None = None
        try:
            with self.opener(request, timeout=self.timeout_s) as result:
                raw = result.read()
                http_status = getattr(result, "status", 200)
            try:
                response = json.loads(raw)
            except json.JSONDecodeError:
                response, terminal = parse_sse_response(raw)
                if response is None:
                    failure = {"terminal": terminal, "response_body_sha256": _digest(raw)}
        except urllib.error.HTTPError as error:
            raw = error.read()
            http_status = error.code
            failure = {"http_status": http_status, "response_body_sha256": _digest(raw)}
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            http_status = None
            failure = {"transport_error": type(error).__name__}
        base = {
            "schema": "crane-evidence-calibration-agent-call/v1",
            "cache_key": cache_key,
            "request_identity": identity,
            "request_sha256": _digest(encoded),
            "latency_ms": (time.time_ns() - started) / 1_000_000,
            "http_status": http_status,
            "attempt_count": 1,
            "quality_driven_retries": 0,
            "credential_persisted": False,
        }
        if response is None:
            record = {**base, "status": "TRANSPORT_OR_RESPONSE_FAILURE", "failure": failure}
            _atomic_write(path, record)
            raise RuntimeError(f"agent call failed; retained at {path}")
        try:
            raw_final = extract_output_text(response)
            parsed = json.loads(raw_final)
            if not isinstance(parsed, dict):
                raise ValueError("structured return is not an object")
        except (ValueError, json.JSONDecodeError) as error:
            record = {**base, "status": "INVALID_RETURN_NO_RETRY", "validation_error": str(error), "raw_final": locals().get("raw_final")}
            _atomic_write(path, record)
            raise RuntimeError(f"invalid agent return; retained at {path}") from error
        record = {**base, "status": "VALID", "provider_response_id": response.get("id"), "returned_model": response.get("model"), "usage": response.get("usage"), "parsed_final": parsed}
        _atomic_write(path, record)
        return record


class StructuredCodexCliAgentCaller:
    """Login-backed, ephemeral structured caller with an empty read-only workspace."""

    def __init__(self, cache: Path, *, model: str = MODEL, effort: str = EFFORT,
                 timeout_s: float = 300.0, runner: Any = subprocess.run):
        self.cache = cache
        self.model = model
        self.effort = effort
        self.timeout_s = timeout_s
        self.runner = runner
        self.cli_version = subprocess.run(
            ["codex", "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()

    def call(self, *, logical_role: str, payload: dict[str, Any], schema: dict[str, Any], prompt: str) -> dict[str, Any]:
        full_prompt = "\n".join((
            prompt,
            "UNTRUSTED_ANNOTATION_DATA_BEGIN",
            _canonical(payload),
            "UNTRUSTED_ANNOTATION_DATA_END",
            "Return only the object required by the output schema. Do not use tools.",
        ))
        identity = {
            "transport": "codex-cli-chatgpt-login-ephemeral/v1",
            "logical_role": logical_role,
            "model": self.model,
            "effort": self.effort,
            "cli_version": self.cli_version,
            "prompt_sha256": _digest(full_prompt.encode()),
            "schema_sha256": _digest(canonical_json_bytes(schema)),
            "payload": payload,
            "amendment_sha256": _digest(AMENDMENT.read_bytes()),
            "workspace": "empty-temporary-read-only",
        }
        cache_key = _digest(_canonical(identity).encode())
        path = self.cache / f"{cache_key}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("request_identity") != identity:
                raise RuntimeError(f"cache collision at {path}")
            if record.get("status") != "VALID":
                raise RuntimeError(f"retained agent failure at {path}")
            return record
        started = time.time_ns()
        with tempfile.TemporaryDirectory(prefix="crane-agent-cli-") as temporary:
            root = Path(temporary)
            schema_path = root / "schema.json"
            output_path = root / "output.json"
            schema_path.write_bytes(canonical_json_bytes(schema) + b"\n")
            command = [
                "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--cd", str(root), "--model", self.model,
                "--config", f'model_reasoning_effort="{self.effort}"',
                "--output-schema", str(schema_path), "--output-last-message", str(output_path), "-",
            ]
            try:
                completed = self.runner(
                    command, input=full_prompt, text=True, capture_output=True, check=False,
                    env={**os.environ, "NO_COLOR": "1"}, timeout=self.timeout_s,
                )
                return_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
                timed_out = False
            except subprocess.TimeoutExpired as error:
                return_code, timed_out = 124, True
                stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
                stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
            events = []
            invalid_event = None
            for line in stdout.splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    event = {"type": "unparsed_stdout", "text_sha256": _digest(line.encode())}
                events.append(event)
                item = event.get("item") if isinstance(event, dict) else None
                if isinstance(item, dict) and item.get("type") not in {"agent_message", "reasoning"}:
                    invalid_event = item.get("type")
                if isinstance(event, dict) and event.get("type") in {"error", "turn.failed"}:
                    invalid_event = event.get("type")
            raw_final = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        base = {
            "schema": "crane-evidence-calibration-agent-call/v1",
            "cache_key": cache_key,
            "request_identity": identity,
            "request_sha256": _digest(full_prompt.encode()),
            "latency_ms": (time.time_ns() - started) / 1_000_000,
            "return_code": return_code,
            "timed_out": timed_out,
            "attempt_count": 1,
            "quality_driven_retries": 0,
            "credential_persisted": False,
            "stderr_sha256": _digest(stderr.encode()),
            "event_types": [event.get("type") for event in events if isinstance(event, dict)],
        }
        if return_code != 0 or invalid_event is not None or not raw_final:
            record = {**base, "status": "TRANSPORT_OR_TOOL_POLICY_FAILURE", "invalid_event": invalid_event}
            _atomic_write(path, record)
            raise RuntimeError(f"agent CLI call failed; retained at {path}")
        try:
            parsed = json.loads(raw_final)
            if not isinstance(parsed, dict):
                raise ValueError("structured return is not an object")
        except (ValueError, json.JSONDecodeError) as error:
            record = {**base, "status": "INVALID_RETURN_NO_RETRY", "validation_error": str(error), "raw_final_sha256": _digest(raw_final.encode())}
            _atomic_write(path, record)
            raise RuntimeError(f"invalid agent return; retained at {path}") from error
        record = {**base, "status": "VALID", "parsed_final": parsed}
        _atomic_write(path, record)
        return record


def _annotation_payload(packet: dict[str, Any], form: dict[str, Any], slot: str) -> dict[str, Any]:
    return {
        "task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION",
        "annotation_origin": "automated_agent",
        "agent_identity": f"agent-{slot}-astra-v4",
        "packet_set_sha256": canonical_sha256(packet),
        "form": form,
        "required_attestation": "INDEPENDENT_BLINDED_COMPLETE",
    }


def run(packet_path: Path, output_root: Path, *, caller: Any | None = None) -> dict[str, Any]:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("schema") != "crane-blinded-agent-atomic-annotation-packet-set/v1":
        raise ValueError("runner requires the prospective automated-agent packet schema")
    forms = {item["annotator_slot"]: item for item in packet.get("forms", [])}
    if set(forms) != {"A", "B"}:
        raise ValueError("packet must contain exactly agent slots A and B")
    def caller_for(slot: str) -> Any:
        if caller is not None:
            return caller
        return StructuredCodexCliAgentCaller(
            output_root / f"pass-{slot}" / "calls", model=MODEL, effort=EFFORT
        )
    prompt = PROMPT.read_text(encoding="utf-8")
    schema = json.loads(RETURN_SCHEMA.read_text(encoding="utf-8"))
    returned: dict[str, dict[str, Any]] = {}
    cache_keys: dict[str, str] = {}
    for slot in ("A", "B"):
        record = caller_for(slot).call(logical_role=f"atomic-agent-{slot}", payload=_annotation_payload(packet, forms[slot], slot), schema=schema, prompt=prompt)
        value = record["parsed_final"]
        validate_return(packet, value)
        expected_id = f"agent-{slot}-astra-v4"
        if value["annotator_id"] != expected_id:
            raise ValueError("agent return changed its assigned opaque annotator identity")
        returned[slot] = value
        cache_keys[slot] = record["cache_key"]
        _atomic_write(output_root / f"annotation-{slot}.json", value)
    report = compare(packet, returned["A"], returned["B"])
    _atomic_write(output_root / "agreement.json", report)
    handoff = build_handoff(report)
    _atomic_write(output_root / "adjudication-handoff.json", handoff)
    final = None
    adjudication_cache_key = None
    if report["disagreement_count"]:
        adjudication_schema = json.loads(ADJUDICATION_SCHEMA.read_text(encoding="utf-8"))
        adjudication_payload = {
            "task": "BLINDED_DISAGREEMENT_ONLY_ADJUDICATION",
            "annotation_origin": "automated_agent",
            "agent_identity": "agent-C-astra-v4",
            "blinded_form": forms["A"],
            "handoff": handoff,
            "required_attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
        }
        record = caller_for("C").call(logical_role="atomic-agent-C", payload=adjudication_payload, schema=adjudication_schema, prompt=prompt)
        adjudication = record["parsed_final"]
        final = finalize(report, adjudication)
        adjudication_cache_key = record["cache_key"]
        _atomic_write(output_root / "adjudication.json", adjudication)
        _atomic_write(output_root / "final.json", final)
    else:
        coordinator_close = {
            "schema": "crane-blinded-atomic-annotation-adjudication/v1",
            "agreement_report_sha256": canonical_sha256(report),
            "adjudicator_id": "coordinator-no-disagreements",
            "decisions": [],
            "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
        }
        final = finalize(report, coordinator_close)
        _atomic_write(output_root / "final.json", final)
    summary = {
        "schema": "crane-evidence-calibration-agent-annotation-run/v1",
        "status": "DEVELOPMENT_AGENT_ASSESSED_V4_QUALIFIED",
        "qualification_disposition": "manifests/study/evidence-calibration-agent-qualification-disposition-v1.json",
        "packet_sha256": _digest(packet_path.read_bytes()),
        "agent_assessed": True,
        "human_annotations_collected": 0,
        "independent_agent_invocations": 2,
        "adjudication_agent_invoked": report["disagreement_count"] > 0,
        "agreement_report_sha256": canonical_sha256(report),
        "finalized": final is not None,
        "cache_keys": {**cache_keys, "C": adjudication_cache_key},
        "confirmation_independent_n": 0,
        "replication_independent_n": 0,
        "confirmatory_alpha_consumed": 0.0,
    }
    _atomic_write(output_root / "development-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--phase", choices=["development"], default="development")
    args = parser.parse_args()
    if (args.output_root / "development-summary.json").exists():
        raise SystemExit("refusing to overwrite a completed annotation run")
    print(json.dumps(run(args.packet.resolve(strict=True), args.output_root.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
