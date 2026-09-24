#!/usr/bin/env python3
"""Isolated, condition-blind Luna evidence-auditor caller.

The coordinator reads one already-blinded packet row, serializes only its allowed contents into a
fresh Responses API request, exposes no tools, and retains an immutable request/response record.
Evaluator keys are deliberately unsupported by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import tomllib
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
ARM_ID = "luna-model-judge-v1"
MODEL_ID = "gpt-6-luna"
MANIFEST_PATH = ROOT / "manifests/annotation/luna-model-judge-v1.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_path(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def load_arm() -> tuple[dict[str, Any], str, dict[str, Any], dict[str, str]]:
    manifest = load_json(MANIFEST_PATH)
    if manifest.get("arm_id") != ARM_ID:
        raise ValueError("automated annotation arm ID mismatch")
    prompt_spec = manifest["prompt"]
    schema_spec = manifest["output_schema"]
    prompt_path = ROOT / prompt_spec["path"]
    schema_path = ROOT / schema_spec["path"]
    if digest_path(prompt_path) != prompt_spec["sha256"]:
        raise ValueError("judge prompt differs from predeclared hash")
    if digest_path(schema_path) != schema_spec["sha256"]:
        raise ValueError("judge output schema differs from predeclared hash")
    rubrics: dict[str, str] = {}
    for name, spec in manifest["rubrics"].items():
        path = ROOT / spec["path"]
        if digest_path(path) != spec["sha256"]:
            raise ValueError(f"{name} rubric differs from declared hash")
        rubrics[name] = path.read_text(encoding="utf-8")
    return (
        manifest,
        prompt_path.read_text(encoding="utf-8"),
        load_json(schema_path),
        rubrics,
    )


def resolve_base_url(explicit: str | None) -> str:
    base = explicit or os.environ.get("CRANE_MODEL_BASE_URL")
    if base is None:
        config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
        if not config_path.is_file():
            raise ValueError("no --base-url, CRANE_MODEL_BASE_URL, or Codex config.toml")
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        provider_name = config.get("model_provider")
        provider = config.get("model_providers", {}).get(provider_name, {})
        base = provider.get("base_url")
    if not isinstance(base, str) or not base.startswith("https://"):
        raise ValueError("model base URL must be an explicit HTTPS URL")
    return base.rstrip("/")


def qualification_envelope(case: dict[str, Any], pass_id: str) -> dict[str, Any]:
    required = {
        "case_id",
        "rubric",
        "question",
        "evidence_completeness",
        "allowed_evidence",
        "required_units",
        "candidate_answer",
    }
    missing = sorted(required - set(case))
    if missing:
        raise ValueError(f"qualification case is missing {missing}")
    return {
        "arm_id": ARM_ID,
        "opaque_response_id": case["case_id"],
        "pass_id": pass_id,
        "rubric": case["rubric"],
        "question": case["question"],
        "evidence_completeness": case["evidence_completeness"],
        "allowed_robot_visible_evidence": case["allowed_evidence"],
        "answerable_or_required_units": case["required_units"],
        "approved_deterministic_calculations": case.get("deterministic_calculations", []),
        "candidate_final_answer": case["candidate_answer"],
    }


def packet_envelope(row: dict[str, Any], rubric: str, pass_id: str) -> dict[str, Any]:
    allowed_fields = {
        "response_id",
        "question",
        "question_kind",
        "allowed_evidence",
        "gold_unit_inventory",
        "answerable_units_total",
        "required_units",
        "diagnosable",
        "prohibited_claims",
        "reference_status",
        "response_text",
        "evidence_completeness",
    }
    unexpected = sorted(set(row) - allowed_fields - {"schema"})
    if unexpected:
        raise ValueError(f"blinded packet row has unsupported fields: {unexpected}")
    if not isinstance(row.get("response_id"), str) or not row["response_id"]:
        raise ValueError("packet row has no opaque response_id")
    if not isinstance(row.get("response_text"), str):
        raise ValueError("packet row has no response_text")
    units = row.get("required_units", row.get("gold_unit_inventory", []))
    completeness = row.get(
        "evidence_completeness",
        "Use evidence_problem if the supplied blinded packet is internally incomplete or inconsistent; do not infer omitted repository data.",
    )
    return {
        "arm_id": ARM_ID,
        "opaque_response_id": row["response_id"],
        "pass_id": pass_id,
        "rubric": rubric,
        "question": row.get("question"),
        "question_kind": row.get("question_kind"),
        "evidence_completeness": completeness,
        "allowed_robot_visible_evidence": row.get("allowed_evidence"),
        "answerable_or_required_units": units,
        "answerable_units_total": row.get("answerable_units_total"),
        "diagnosable": row.get("diagnosable"),
        "prohibited_claims": row.get("prohibited_claims", []),
        "reference_status": row.get("reference_status"),
        "candidate_final_answer": row["response_text"],
    }


def render_user_input(envelope: dict[str, Any], rubric_text: str) -> str:
    return "\n".join(
        (
            "APPLICABLE_RUBRIC_BEGIN",
            rubric_text,
            "APPLICABLE_RUBRIC_END",
            "UNTRUSTED_CASE_DATA_BEGIN",
            canonical_json(envelope),
            "UNTRUSTED_CASE_DATA_END",
            "Return only the structured judgment required by the output schema.",
        )
    )


def request_body(
    *, prompt: str, rubric_text: str, envelope: dict[str, Any], schema: dict[str, Any], effort: str
) -> dict[str, Any]:
    if effort not in {"low", "medium", "high"}:
        raise ValueError("judge reasoning effort must be low, medium, or high")
    return {
        "model": MODEL_ID,
        "input": [
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": prompt}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": render_user_input(envelope, rubric_text),
                    }
                ],
            },
        ],
        "reasoning": {"effort": effort},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "crane_luna_model_judge_v1",
                "strict": True,
                "schema": schema,
            }
        },
        "store": False,
        "stream": False,
        "tools": [],
    }


def extract_output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    texts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(
                content.get("text"), str
            ):
                texts.append(content["text"])
    if not texts:
        raise ValueError("Responses payload has no final output text")
    return "".join(texts)


def validate_judgment(value: dict[str, Any], envelope: dict[str, Any]) -> None:
    required = {
        "schema",
        "annotation_origin",
        "arm_id",
        "opaque_response_id",
        "pass_id",
        "rubric",
        "judgment_status",
        "answerability",
        "material_error",
        "material_error_categories",
        "claims",
        "required_units",
        "disposition",
        "mechanism_identification",
        "correct_abstention",
        "causal_overclaim",
        "evidence_problem",
        "evidence_problem_detail",
        "unresolved_fields",
        "rationale",
    }
    if set(value) != required:
        raise ValueError(f"judgment fields differ from schema: {sorted(set(value) ^ required)}")
    constants = {
        "schema": "crane-luna-model-judge-output/v1",
        "annotation_origin": "automated",
        "arm_id": ARM_ID,
        "opaque_response_id": envelope["opaque_response_id"],
        "pass_id": envelope["pass_id"],
        "rubric": envelope["rubric"],
    }
    for field, expected in constants.items():
        if value[field] != expected:
            raise ValueError(f"judgment {field} does not match request")
    categories = value["material_error_categories"]
    if not isinstance(categories, list) or len(categories) != len(set(categories)):
        raise ValueError("material_error_categories must be a unique list")
    if value["material_error"] is True and not categories:
        raise ValueError("material error requires at least one category")
    if value["material_error"] is False and categories:
        raise ValueError("non-error judgment cannot carry material-error categories")
    if value["material_error"] is None and value["judgment_status"] == "resolved":
        raise ValueError("resolved judgment requires a material-error label")
    if value["evidence_problem"] != (value["judgment_status"] == "evidence_problem"):
        raise ValueError("evidence_problem must match judgment_status")
    if value["evidence_problem"] != (value["evidence_problem_detail"] is not None):
        raise ValueError("evidence_problem detail is inconsistent")
    if not isinstance(value["rationale"], str) or not value["rationale"].strip():
        raise ValueError("judgment rationale is empty")


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


class LunaResponsesCaller:
    def __init__(
        self,
        *,
        cache: Path,
        effort: str,
        base_url: str | None = None,
        api_key_env: str = "CODEX_LB_API_KEY",
        timeout_s: float = 300.0,
        opener: Any = urllib.request.urlopen,
    ) -> None:
        self.manifest, self.prompt, self.schema, self.rubrics = load_arm()
        self.cache = cache
        self.effort = effort
        self.base_url = resolve_base_url(base_url)
        self.api_key_env = api_key_env
        self.timeout_s = timeout_s
        self.opener = opener

    def call(self, envelope: dict[str, Any]) -> dict[str, Any]:
        if envelope["rubric"] not in self.rubrics:
            raise ValueError("unknown rubric")
        body = request_body(
            prompt=self.prompt,
            rubric_text=self.rubrics[envelope["rubric"]],
            envelope=envelope,
            schema=self.schema,
            effort=self.effort,
        )
        identity = {
            "arm_manifest_sha256": digest_path(MANIFEST_PATH),
            "request_body": body,
            "endpoint": f"{self.base_url}/responses",
        }
        cache_key = digest_bytes(canonical_json(identity).encode("utf-8"))
        cache_path = self.cache / f"{cache_key}.json"
        if cache_path.exists():
            cached = load_json(cache_path)
            if cached.get("request_identity") != identity:
                raise RuntimeError(f"cache collision at {cache_path}")
            if cached.get("status") != "VALID":
                raise RuntimeError(f"cached call is not a valid judgment: {cache_path}")
            validate_judgment(cached["judgment"], envelope)
            return cached

        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        encoded = canonical_json(body).encode("utf-8")
        attempts: list[dict[str, Any]] = []
        response: dict[str, Any] | None = None
        last_payload: bytes | None = None
        for attempt in range(1, self.manifest["retry_policy"]["maximum_transport_retries"] + 2):
            started_ns = time.time_ns()
            request = urllib.request.Request(
                f"{self.base_url}/responses",
                data=encoded,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "crane-explain-luna-judge/1",
                },
                method="POST",
            )
            try:
                with self.opener(request, timeout=self.timeout_s) as result:
                    payload = result.read()
                    last_payload = payload
                    http_status = getattr(result, "status", 200)
            except urllib.error.HTTPError as error:
                payload = error.read()
                last_payload = payload
                http_status = error.code
                attempts.append(
                    {
                        "attempt": attempt,
                        "started_wall_time_ns": started_ns,
                        "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                        "transport_status": f"HTTP_{http_status}",
                        "response_body_sha256": digest_bytes(payload),
                    }
                )
                if http_status not in {408, 409, 429, 500, 502, 503, 504} or attempt >= 3:
                    break
                time.sleep(2 ** (attempt - 1))
                continue
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                attempts.append(
                    {
                        "attempt": attempt,
                        "started_wall_time_ns": started_ns,
                        "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                        "transport_status": type(error).__name__,
                    }
                )
                if attempt >= 3:
                    break
                time.sleep(2 ** (attempt - 1))
                continue
            attempts.append(
                {
                    "attempt": attempt,
                    "started_wall_time_ns": started_ns,
                    "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                    "transport_status": f"HTTP_{http_status}",
                    "response_body_sha256": digest_bytes(payload),
                }
            )
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                break  # A returned but malformed payload is retained and is not retried.
            if not isinstance(decoded, dict):
                break
            response = decoded
            break

        base_record = {
            "schema": "crane-luna-model-judge-call/v1",
            "cache_key": cache_key,
            "request_identity": identity,
            "request_sha256": digest_bytes(encoded),
            "model": MODEL_ID,
            "reasoning_effort": self.effort,
            "temperature": None,
            "seed": None,
            "tools_exposed": [],
            "attempts": attempts,
        }
        if response is None:
            failure = {
                **base_record,
                "status": "TRANSPORT_OR_RESPONSE_FAILURE",
                "response_body_text": (
                    last_payload.decode("utf-8", errors="replace")
                    if last_payload is not None
                    else None
                ),
            }
            atomic_write_json(cache_path, failure)
            raise RuntimeError(f"Luna call failed; retained at {cache_path}")
        try:
            raw_final = extract_output_text(response)
            judgment = json.loads(raw_final)
            if not isinstance(judgment, dict):
                raise ValueError("final judgment is not an object")
            validate_judgment(judgment, envelope)
        except (ValueError, json.JSONDecodeError) as error:
            failure = {
                **base_record,
                "status": "INVALID_JUDGMENT_NO_RETRY",
                "provider_response_id": response.get("id"),
                "returned_model": response.get("model"),
                "usage": response.get("usage"),
                "raw_final": locals().get("raw_final"),
                "validation_error": str(error),
            }
            atomic_write_json(cache_path, failure)
            raise RuntimeError(f"invalid Luna judgment; retained at {cache_path}") from error
        record = {
            **base_record,
            "status": "VALID",
            "provider_response_id": response.get("id"),
            "returned_model": response.get("model"),
            "usage": response.get("usage"),
            "raw_final": raw_final,
            "judgment": judgment,
        }
        atomic_write_json(cache_path, record)
        return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--input-kind", choices=("qualification", "packet"), required=True)
    parser.add_argument("--rubric", choices=("legacy", "diagnostic"))
    parser.add_argument("--pass-id", choices=("pass-1", "pass-2", "qualification"), required=True)
    parser.add_argument("--effort", choices=("low", "medium", "high"), required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    value = load_json(args.input)
    if args.input_kind == "qualification":
        envelope = qualification_envelope(value, args.pass_id)
    else:
        if args.rubric is None:
            parser.error("--rubric is required for packet input")
        envelope = packet_envelope(value, args.rubric, args.pass_id)
    record = LunaResponsesCaller(
        cache=args.cache, effort=args.effort, base_url=args.base_url
    ).call(envelope)
    print(json.dumps({"cache_key": record["cache_key"], "status": record["status"]}))


if __name__ == "__main__":
    main()
