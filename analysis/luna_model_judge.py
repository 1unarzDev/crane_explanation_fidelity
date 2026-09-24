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
import shutil
import subprocess
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


def parse_sse_response(payload: bytes) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Extract a completed Responses object or a sanitized terminal failure from SSE."""
    completed: dict[str, Any] | None = None
    terminal = {"event": None, "response_id": None, "error": None}
    for block in payload.decode("utf-8", errors="replace").split("\n\n"):
        event_name: str | None = None
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").lstrip())
        if not data_lines or data_lines == ["[DONE]"]:
            continue
        try:
            data = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        event_type = data.get("type", event_name)
        if event_type == "response.completed" and isinstance(data.get("response"), dict):
            completed = data["response"]
            terminal = {
                "event": "response.completed",
                "response_id": completed.get("id"),
                "error": None,
            }
        elif event_type == "response.failed":
            failed = data.get("response") if isinstance(data.get("response"), dict) else {}
            error = failed.get("error") if isinstance(failed.get("error"), dict) else {}
            terminal = {
                "event": "response.failed",
                "response_id": failed.get("id"),
                "error": {
                    "type": error.get("type"),
                    "code": error.get("code"),
                    "message": error.get("message"),
                },
            }
    return completed, terminal


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
            "caller_source_sha256": digest_path(Path(__file__)),
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
        last_terminal: dict[str, Any] | None = None
        max_attempts = self.manifest["retry_policy"]["maximum_transport_retries"] + 1
        for attempt in range(1, max_attempts + 1):
            started_ns = time.time_ns()
            request = urllib.request.Request(
                f"{self.base_url}/responses",
                data=encoded,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "text/event-stream, application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "crane-explain-luna-judge/1",
                },
                method="POST",
            )
            try:
                with self.opener(request, timeout=self.timeout_s) as result:
                    payload = result.read()
                    http_status = getattr(result, "status", 200)
            except urllib.error.HTTPError as error:
                payload = error.read()
                http_status = error.code
                try:
                    error_value = json.loads(payload)
                except json.JSONDecodeError:
                    error_value = None
                last_terminal = {
                    "event": "http_error",
                    "http_status": http_status,
                    "error": error_value.get("error") if isinstance(error_value, dict) else None,
                }
                attempts.append(
                    {
                        "attempt": attempt,
                        "started_wall_time_ns": started_ns,
                        "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                        "transport_status": f"HTTP_{http_status}",
                        "response_body_sha256": digest_bytes(payload),
                    }
                )
                if (
                    http_status not in {408, 409, 429, 500, 502, 503, 504}
                    or attempt >= max_attempts
                ):
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
                if attempt >= max_attempts:
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
                decoded = None
            if isinstance(decoded, dict):
                response = decoded
                break
            response, terminal = parse_sse_response(payload)
            last_terminal = terminal
            attempts[-1]["response_event"] = terminal.get("event")
            attempts[-1]["provider_response_id"] = terminal.get("response_id")
            if response is not None:
                break
            retryable_stream_failure = (
                terminal.get("event") == "response.failed"
                and isinstance(terminal.get("error"), dict)
                and terminal["error"].get("type") == "server_error"
            )
            if retryable_stream_failure and attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))
                continue
            break  # Returned unusable content is retained and not retried.

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
                "terminal_failure": last_terminal,
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


class LunaIsolatedCodexCaller:
    """Run one ephemeral Codex turn in an OS namespace containing no project files."""

    def __init__(
        self,
        *,
        cache: Path,
        effort: str,
        base_url: str | None = None,
        api_key_env: str = "CODEX_LB_API_KEY",
        timeout_s: float = 300.0,
        runner: Any = subprocess.run,
    ) -> None:
        self.manifest, self.prompt, self.schema, self.rubrics = load_arm()
        self.cache = cache
        self.effort = effort
        self.base_url = resolve_base_url(base_url)
        self.api_key_env = api_key_env
        self.timeout_s = timeout_s
        self.runner = runner
        binary = shutil.which("codex")
        bwrap = shutil.which("bwrap")
        if binary is None or bwrap is None:
            raise RuntimeError("isolated judge requires codex and bwrap")
        self.binary = Path(binary).resolve()
        self.bwrap = Path(bwrap).resolve()
        self.cli_version = subprocess.run(
            [str(self.binary), "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()

    def _config(self) -> str:
        return "\n".join(
            (
                f'model = "{MODEL_ID}"',
                'model_provider = "judge-provider"',
                f'model_reasoning_effort = "{self.effort}"',
                '[model_providers.judge-provider]',
                'name = "openai"',
                f'base_url = "{self.base_url}"',
                f'env_key = "{self.api_key_env}"',
                'wire_api = "responses"',
                'supports_websockets = true',
                'requires_openai_auth = false',
                '[shell_environment_policy]',
                'inherit = "none"',
                '[features]',
                'apps = false',
                'browser_use = false',
                'computer_use = false',
                'image_generation = false',
                'plugins = false',
                'shell_tool = false',
                'sleep_tool = false',
                'unified_exec = false',
                '',
            )
        )

    def _events(self, stdout: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError("Codex CLI emitted non-JSON output") from error
            if not isinstance(event, dict):
                raise ValueError("Codex CLI event is not an object")
            events.append(event)
        return events

    def call(self, envelope: dict[str, Any]) -> dict[str, Any]:
        if envelope["rubric"] not in self.rubrics:
            raise ValueError("unknown rubric")
        full_prompt = "\n".join(
            (
                self.prompt,
                render_user_input(envelope, self.rubrics[envelope["rubric"]]),
            )
        )
        source_hash = digest_path(Path(__file__))
        identity = {
            "adapter": "codex-cli-bwrap-json/v1",
            "arm_manifest_sha256": digest_path(MANIFEST_PATH),
            "caller_source_sha256": source_hash,
            "model": MODEL_ID,
            "reasoning_effort": self.effort,
            "cli_version": self.cli_version,
            "base_url": self.base_url,
            "prompt_sha256": digest_bytes(full_prompt.encode("utf-8")),
            "schema_sha256": digest_bytes(canonical_json(self.schema).encode("utf-8")),
            "envelope": envelope,
            "filesystem_view": "bwrap-system-runtime-plus-empty-workdir-v1",
            "tools_policy": "features-disabled-and-any-tool-event-rejected",
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

        attempts: list[dict[str, Any]] = []
        max_attempts = self.manifest["retry_policy"]["maximum_transport_retries"] + 1
        last_stdout = ""
        last_stderr = ""
        for attempt in range(1, max_attempts + 1):
            with tempfile.TemporaryDirectory(prefix="crane-luna-isolated-") as temporary:
                root = Path(temporary)
                codex_home = root / "codex-home"
                work = root / "work"
                codex_home.mkdir()
                work.mkdir()
                (codex_home / "config.toml").write_text(self._config(), encoding="utf-8")
                host_codex_home = Path(
                    os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
                )
                model_cache = host_codex_home / "models_cache.json"
                if model_cache.is_file():
                    shutil.copyfile(model_cache, codex_home / "models_cache.json")
                schema_path = work / "schema.json"
                output_path = work / "judgment.json"
                schema_path.write_text(json.dumps(self.schema), encoding="utf-8")
                command = [
                    str(self.bwrap),
                    "--unshare-all",
                    "--share-net",
                    "--ro-bind",
                    str(self.binary),
                    "/codex",
                    "--ro-bind",
                    "/usr",
                    "/usr",
                    "--symlink",
                    "usr/bin",
                    "/bin",
                    "--ro-bind",
                    "/etc",
                    "/etc",
                    "--proc",
                    "/proc",
                    "--dev",
                    "/dev",
                    "--tmpfs",
                    "/tmp",
                    "--dir",
                    "/home",
                    "--dir",
                    "/home/lunarz",
                    "--bind",
                    str(codex_home),
                    "/home/lunarz/.codex",
                    "--bind",
                    str(work),
                    "/work",
                    "--chdir",
                    "/work",
                    "--clearenv",
                    "--setenv",
                    "HOME",
                    "/home/lunarz",
                    "--setenv",
                    "CODEX_HOME",
                    "/home/lunarz/.codex",
                    "--setenv",
                    "PATH",
                    "/usr/bin:/bin",
                    "--setenv",
                    "NO_COLOR",
                    "1",
                    "--setenv",
                    self.api_key_env,
                    api_key,
                    "/codex",
                    "exec",
                    "--json",
                    "--ephemeral",
                    "--ignore-rules",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "read-only",
                    "--cd",
                    "/work",
                    "--model",
                    MODEL_ID,
                    "--config",
                    f'model_reasoning_effort="{self.effort}"',
                    "--output-schema",
                    "/work/schema.json",
                    "--output-last-message",
                    "/work/judgment.json",
                    "-",
                ]
                started_ns = time.time_ns()
                try:
                    completed = self.runner(
                        command,
                        input=full_prompt,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=self.timeout_s,
                    )
                except subprocess.TimeoutExpired:
                    attempts.append(
                        {
                            "attempt": attempt,
                            "started_wall_time_ns": started_ns,
                            "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                            "transport_status": "TIMEOUT",
                        }
                    )
                    if attempt < max_attempts:
                        continue
                    break
                attempts.append(
                    {
                        "attempt": attempt,
                        "started_wall_time_ns": started_ns,
                        "latency_ms": (time.time_ns() - started_ns) / 1_000_000,
                        "transport_status": f"EXIT_{completed.returncode}",
                        "stdout_sha256": digest_bytes(completed.stdout.encode("utf-8")),
                        "stderr_sha256": digest_bytes(completed.stderr.encode("utf-8")),
                    }
                )
                last_stdout = completed.stdout
                last_stderr = completed.stderr
                if completed.returncode != 0 or not output_path.is_file():
                    if attempt < max_attempts:
                        continue
                    break
                try:
                    events = self._events(completed.stdout)
                    forbidden_items = []
                    client_warnings = []
                    for event in events:
                        item = event.get("item")
                        if event.get("type") == "item.completed" and isinstance(item, dict):
                            if item.get("type") == "error" and str(item.get("message", "")).startswith(
                                f"Model metadata for `{MODEL_ID}` not found."
                            ):
                                client_warnings.append(item["message"])
                            elif item.get("type") not in {"agent_message", "reasoning"}:
                                forbidden_items.append(item.get("type"))
                    raw_final = output_path.read_text(encoding="utf-8")
                    if forbidden_items:
                        raise ValueError(f"model used or emitted forbidden tool/items: {forbidden_items}")
                    judgment = json.loads(raw_final)
                    if not isinstance(judgment, dict):
                        raise ValueError("final judgment is not an object")
                    validate_judgment(judgment, envelope)
                except (ValueError, json.JSONDecodeError) as error:
                    failure = {
                        "schema": "crane-luna-model-judge-call/v1",
                        "status": "INVALID_JUDGMENT_NO_RETRY",
                        "cache_key": cache_key,
                        "request_identity": identity,
                        "attempts": attempts,
                        "raw_final": locals().get("raw_final"),
                        "validation_error": str(error),
                    }
                    atomic_write_json(cache_path, failure)
                    raise RuntimeError(f"invalid Luna judgment; retained at {cache_path}") from error
                record = {
                    "schema": "crane-luna-model-judge-call/v1",
                    "status": "VALID",
                    "cache_key": cache_key,
                    "request_identity": identity,
                    "model": MODEL_ID,
                    "reasoning_effort": self.effort,
                    "temperature": None,
                    "seed": None,
                    "tools_exposed": [],
                    "tool_events_observed": 0,
                    "client_warnings": client_warnings,
                    "attempts": attempts,
                    "events": events,
                    "raw_final": raw_final,
                    "judgment": judgment,
                }
                atomic_write_json(cache_path, record)
                return record
        failure = {
            "schema": "crane-luna-model-judge-call/v1",
            "status": "TRANSPORT_FAILURE",
            "cache_key": cache_key,
            "request_identity": identity,
            "attempts": attempts,
            "stdout_events": (
                self._events(last_stdout) if last_stdout.strip() else []
            ),
            "stderr": last_stderr,
        }
        atomic_write_json(cache_path, failure)
        raise RuntimeError(f"isolated Luna call failed; retained at {cache_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--input-kind", choices=("qualification", "packet"), required=True)
    parser.add_argument("--rubric", choices=("legacy", "diagnostic"))
    parser.add_argument("--pass-id", choices=("pass-1", "pass-2", "qualification"), required=True)
    parser.add_argument("--effort", choices=("low", "medium", "high"), required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--base-url")
    parser.add_argument(
        "--transport", choices=("isolated-codex-cli", "direct-responses"), default="isolated-codex-cli"
    )
    args = parser.parse_args()
    value = load_json(args.input)
    if args.input_kind == "qualification":
        envelope = qualification_envelope(value, args.pass_id)
    else:
        if args.rubric is None:
            parser.error("--rubric is required for packet input")
        envelope = packet_envelope(value, args.rubric, args.pass_id)
    caller_class = LunaIsolatedCodexCaller if args.transport == "isolated-codex-cli" else LunaResponsesCaller
    record = caller_class(
        cache=args.cache, effort=args.effort, base_url=args.base_url
    ).call(envelope)
    print(json.dumps({"cache_key": record["cache_key"], "status": record["status"]}))


if __name__ == "__main__":
    main()
