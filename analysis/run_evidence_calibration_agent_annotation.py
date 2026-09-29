#!/usr/bin/env python3
"""Run two blinded agent annotations and disagreement-only agent adjudication.

This runner is development-only until an exact-task qualification manifest is frozen.  It makes
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
import time
from typing import Any
import urllib.error
import urllib.request

from adjudicate_evidence_calibration_annotations import build_handoff, compare, finalize, validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from luna_model_judge import extract_output_text, parse_sse_response, resolve_base_url


ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-luna"
EFFORT = "high"
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md"
RETURN_SCHEMA = ROOT / "research/explanation_fidelity/schemas/blinded-agent-atomic-annotation-return-v1.schema.json"
ADJUDICATION_SCHEMA = ROOT / "research/explanation_fidelity/schemas/blinded-agent-atomic-adjudication-v1.schema.json"
AMENDMENT = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-agent-annotation-amendment-v1.json"


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


def _annotation_payload(packet: dict[str, Any], form: dict[str, Any], slot: str) -> dict[str, Any]:
    return {
        "task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION",
        "annotation_origin": "automated_agent",
        "agent_identity": f"agent-{slot}-luna-v1",
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
    caller = caller or StructuredAgentCaller(output_root / "calls")
    prompt = PROMPT.read_text(encoding="utf-8")
    schema = json.loads(RETURN_SCHEMA.read_text(encoding="utf-8"))
    returned: dict[str, dict[str, Any]] = {}
    cache_keys: dict[str, str] = {}
    for slot in ("A", "B"):
        record = caller.call(logical_role=f"atomic-agent-{slot}", payload=_annotation_payload(packet, forms[slot], slot), schema=schema, prompt=prompt)
        value = record["parsed_final"]
        validate_return(packet, value)
        expected_id = f"agent-{slot}-luna-v1"
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
            "agent_identity": "agent-C-luna-v1",
            "blinded_form": forms["A"],
            "handoff": handoff,
            "required_attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
        }
        record = caller.call(logical_role="atomic-agent-C", payload=adjudication_payload, schema=adjudication_schema, prompt=prompt)
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
        "status": "DEVELOPMENT_ONLY_EXACT_TASK_QUALIFICATION_PENDING",
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
