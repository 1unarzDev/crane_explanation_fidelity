#!/usr/bin/env python3
"""Claude Code CLI adapter for cached, single-sample model calls.

This is the Claude-family sibling of ``CodexCliCaller`` in ``run_llm_episode_pilot``. It produces
the same ``crane-explain-model-call/v1`` record so that existing manifest, resource, and summary
tooling reads either adapter without modification. Calls are never retried or resampled.

Three adapter differences from the Codex CLI adapter are unavoidable and are recorded inside every
retained request so that they can never be silently forgotten:

1. The Codex CLI enforces a read-only filesystem sandbox. The Claude Code CLI exposes no equivalent
   flag, so this adapter denies every mutating, network, and delegation tool, runs the agent only
   inside a throwaway extraction of the pinned checkout, and hashes the whole workspace before and
   after the call. A workspace whose hashes changed is retained and raised, never scored.
2. The Claude Code CLI reports provider monetary cost; the Codex ChatGPT-login path did not.

Schema delivery is *not* a difference: ``--json-schema`` is the direct analogue of the Codex CLI's
``--output-schema``, so the frozen prompt text reaches the model byte-unchanged in both arms. An
earlier revision of this adapter delivered the schema in-band as a prompt suffix instead; that was
abandoned during the development control because the model answered in prose often enough to fail
calls outright, and because an in-band suffix alters the prompt the frozen study pinned. Calls made
under that revision carry ``schema_delivery: "in_band_prompt_suffix"`` in their retained request and
are excluded from every summary.

A call that never produced a parsed answer -- a non-zero exit, a provider quota or transport error,
or a result that does not satisfy the schema -- is *not* an answer and is never written to the
answer cache. It is retained under ``_retained_failed_calls/`` and raised. The answer cache
guarantees that a successful call is never resampled; a failure that produced no sample carries no
such guarantee to protect, and caching one would permanently prevent the call from being made.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# Read-only tool surface. Everything that writes, reaches the network, or delegates is denied.
DENIED_TOOLS = (
    "Edit",
    "Write",
    "NotebookEdit",
    "WebFetch",
    "WebSearch",
    "Task",
    "Agent",
    "TodoWrite",
    "SlashCommand",
    "Skill",
)

# Recorded in every request so a cached record always states how its schema was delivered, and so
# a change of delivery mechanism changes the cache key instead of silently reusing a stale answer.
SCHEMA_DELIVERY = "out_of_band_json_schema_flag"

# Calls that never produced a parsed answer are retained here instead of in the answer cache. The
# answer cache exists to guarantee that a *successful* call is never resampled; a transport or
# quota failure produced no sample, so caching it would both misrepresent it as an answer and
# permanently prevent the call from ever being made. Records here are retained, never deleted.
FAILED_CALL_DIRECTORY = "_retained_failed_calls"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def workspace_digest(root: Path | None) -> dict[str, str] | None:
    """Hash every regular file under ``root`` so post-call mutation is detectable."""

    if root is None:
        return None
    digest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            digest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def extract_json_object(text: str) -> Any:
    """Parse the last complete top-level JSON object in a CLI result string.

    The Claude Code CLI returns the assistant's final message verbatim, which may be wrapped in a
    Markdown code fence. Fence stripping is textual only; no field is invented or repaired.
    """

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError("no JSON object found in result", stripped, 0)
    return json.loads(stripped[start : end + 1])


def usage_from_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Map Claude CLI usage onto the key names the retained Codex records already use."""

    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    cache_read = usage.get("cache_read_input_tokens") or 0
    cache_creation = usage.get("cache_creation_input_tokens") or 0
    uncached = usage.get("input_tokens") or 0
    details = usage.get("output_tokens_details") or {}
    return {
        "input_tokens": uncached + cache_creation + cache_read,
        "cached_input_tokens": cache_read,
        "output_tokens": usage.get("output_tokens") or 0,
        "reasoning_output_tokens": details.get("thinking_tokens") or 0,
        "uncached_input_tokens": uncached,
        "cache_creation_input_tokens": cache_creation,
    }


class ClaudeCliCaller:
    """Content-addressed, single-sample Claude Code CLI caller."""

    adapter = "claude-cli-json/v1"

    def __init__(self, cache: Path, model: str, reasoning_effort: str):
        self.cache = cache
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.cache.mkdir(parents=True, exist_ok=True)
        self.cli_version = subprocess.run(
            ["claude", "--version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def call(
        self,
        role: str,
        prompt: str,
        schema: dict[str, Any],
        *,
        working_directory: Path | None = None,
        workspace_identity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = {
            "adapter": self.adapter,
            "provider": "claude-code-cli",
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "temperature": None,
            "seed": None,
            "role": role,
            "prompt": prompt,
            "schema": schema,
            "cli_version": self.cli_version,
            "workspace_identity": workspace_identity,
            "schema_delivery": SCHEMA_DELIVERY,
            "denied_tools": list(DENIED_TOOLS),
        }
        request_bytes = canonical_json(request).encode()
        cache_key = hashlib.sha256(request_bytes).hexdigest()
        cache_path = self.cache / f"{cache_key}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached["request"] != request:
                raise RuntimeError(f"cache collision at {cache_path}")
            # A cached record must be a usable answer. Returning an unparsed or integrity-violating
            # record would surface later as an opaque error in the caller's own field access.
            if cached.get("parsed_final") is None:
                raise RuntimeError(
                    f"cached record has no parsed answer; retained at {cache_path}: "
                    f"{cached.get('parse_error')}"
                )
            if not cached.get("workspace_unmodified", False):
                raise RuntimeError(
                    f"read-only contract violated; workspace changed during {cache_path}"
                )
            return cached
        with tempfile.TemporaryDirectory(prefix="crane-explain-claude-") as temporary:
            root = Path(temporary)
            directory = working_directory or root
            before = workspace_digest(working_directory)
            command = [
                "claude",
                "--print",
                "--output-format",
                "json",
                "--model",
                self.model,
                "--effort",
                self.reasoning_effort,
                "--permission-mode",
                "bypassPermissions",
                "--permission-prompts",
                "none",
                "--strict-mcp-config",
                "--json-schema",
                json.dumps(schema, sort_keys=True),
                "--disallowedTools",
                " ".join(DENIED_TOOLS),
                "--add-dir",
                str(directory),
                "-",
            ]
            started_ns = time.time_ns()
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                check=False,
                cwd=str(directory),
                env={**os.environ, "NO_COLOR": "1"},
            )
            elapsed_ms = (time.time_ns() - started_ns) / 1_000_000
            after = workspace_digest(working_directory)
            try:
                envelope = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                envelope = None
                envelope_error: str | None = str(error)
            else:
                envelope_error = None
            raw_final = ""
            parsed_final = None
            parse_error: str | None = envelope_error
            usage = None
            cost_usd = None
            if isinstance(envelope, dict):
                raw_final = envelope.get("result") or ""
                usage = usage_from_result(envelope)
                cost_usd = envelope.get("total_cost_usd")
                if envelope.get("is_error"):
                    parse_error = f"cli reported error: {envelope.get('subtype')}"
                else:
                    try:
                        parsed_final = extract_json_object(raw_final)
                    except json.JSONDecodeError as error:
                        parse_error = str(error)
            record = {
                "schema": "crane-explain-model-call/v1",
                "cache_key": cache_key,
                "request": request,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "started_wall_time_ns": started_ns,
                "latency_ms": elapsed_ms,
                "cost_usd": cost_usd,
                "cost_status": (
                    "reported_by_claude_code_cli"
                    if cost_usd is not None
                    else "not_reported_by_claude_code_cli"
                ),
                "return_code": completed.returncode,
                "events": [envelope] if isinstance(envelope, dict) else [],
                "usage": usage,
                "stderr": completed.stderr,
                "raw_final": raw_final,
                "parsed_final": parsed_final,
                "parse_error": parse_error,
                "workspace_unmodified": before == after,
                "workspace_digest_before_sha256": (
                    hashlib.sha256(canonical_json(before).encode()).hexdigest()
                    if before is not None
                    else None
                ),
                "workspace_digest_after_sha256": (
                    hashlib.sha256(canonical_json(after).encode()).hexdigest()
                    if after is not None
                    else None
                ),
            }
            serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
            if completed.returncode != 0 or parsed_final is None:
                # The call produced no answer. Retain the whole record as evidence, but keep it out
                # of the content-addressed answer cache so the call is neither misreported as a
                # sample nor permanently blocked from being attempted again.
                failures = self.cache / FAILED_CALL_DIRECTORY
                failures.mkdir(parents=True, exist_ok=True)
                failure_path = failures / f"{cache_key}-{started_ns}.json"
                failure_path.write_text(serialized, encoding="utf-8")
                raise RuntimeError(
                    f"model call produced no answer; retained at {failure_path}: "
                    f"{parse_error}"
                )
            cache_path.write_text(serialized, encoding="utf-8")
        if not record["workspace_unmodified"]:
            raise RuntimeError(
                f"read-only contract violated; workspace changed during {cache_path}"
            )
        return record


def usage_from_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Usage accessor that works for either adapter's retained record."""

    if isinstance(record.get("usage"), dict):
        return record["usage"]
    usages = [
        event.get("usage")
        for event in record.get("events", [])
        if isinstance(event, dict) and isinstance(event.get("usage"), dict)
    ]
    return usages[-1] if usages else None
