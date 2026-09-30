"""Offline tool dispatch with immutable intents/results; no provider transport or activation."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re
import subprocess

from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox import run
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once
from stage_evidence_calibration_workspace import verify

READ = "read_staged_file"
COMPUTE = "compute_visible_python"


def tool_definitions(method: str) -> list[dict]:
    if method not in {"B0", "B1", "B2", "B3", "B4"}:
        raise ValueError("unknown method")
    if method in {"B0", "B1"}:
        return []
    return [
        {"name": READ, "description": "Read exact staged file text using explicit Unicode character offsets; no inferred summary.",
         "inputSchema": {"type": "object", "properties": {"path": {"type": "string"},
            "offset": {"type": "integer", "minimum": 0}, "length": {"type": ["integer", "null"], "minimum": 1}},
            "required": ["path", "offset", "length"], "additionalProperties": False}},
        {"name": COMPUTE, "description": "Run local Python calculations over full staged visible records/source in an isolated namespace.",
         "inputSchema": {"type": "object", "properties": {"code": {"type": "string", "minLength": 1}},
                         "required": ["code"], "additionalProperties": False}},
    ]


class ToolBroker:
    def __init__(self, workspace: Path, identity: dict, event_directory: Path, *, max_calls: int, timeout_seconds: int):
        verify(workspace, identity)
        if type(max_calls) is not int or max_calls < 1 or type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
            raise ValueError("explicit positive call budget and 1–60 second timeout required")
        if event_directory.resolve() == workspace.resolve() or workspace.resolve() in event_directory.resolve().parents:
            raise ValueError("event records must be outside method workspace")
        if event_directory.exists():
            raise ValueError("fresh event namespace required; existing intents must be quarantined")
        event_directory.mkdir(parents=True)
        self.workspace, self.identity, self.events = workspace, deepcopy(identity), event_directory
        self.max_calls, self.timeout_seconds, self.calls = max_calls, timeout_seconds, 0
        self.definitions = tool_definitions(identity["method_id"])

    def call(self, event_id: str, name: str, arguments: dict) -> dict:
        if not isinstance(event_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", event_id):
            raise ValueError("invalid tool event ID")
        intent, terminal = self.events / (event_id + ".intent.json"), self.events / (event_id + ".result.json")
        if intent.exists() or terminal.exists():
            raise ValueError("retained tool event/unknown intent; no replay or retry")
        if self.calls >= self.max_calls:
            raise ValueError("tool call budget exhausted")
        request = {"schema": "crane-tool-event-request/v1-development", "event_id": event_id,
                   "method_id": self.identity["method_id"], "workspace_sha256": self.identity["workspace_sha256"],
                   "name": name, "arguments": arguments, "timeout_seconds": self.timeout_seconds,
                   "max_calls": self.max_calls, "ordinal": self.calls + 1}
        _write_once(intent, {"request": request, "request_sha256": canonical_sha256(request), "terminal_record_pending": True})
        self.calls += 1
        result = None
        try:
            verify(self.workspace, self.identity)
            if name not in {row["name"] for row in self.definitions}:
                raise ValueError("tool not permitted for this method")
            if name == READ:
                if (not isinstance(arguments, dict) or set(arguments) != {"path", "offset", "length"}
                        or not isinstance(arguments["path"], str)
                        or arguments["path"] not in self.identity["inventory"]["files"]
                        or type(arguments["offset"]) is not int or arguments["offset"] < 0
                        or (arguments["length"] is not None and (type(arguments["length"]) is not int or arguments["length"] < 1))):
                    raise ValueError("read requires a registered path and valid explicit character range")
                content = (self.workspace / arguments["path"]).read_bytes()
                file_sha = hashlib.sha256(content).hexdigest()
                if file_sha != self.identity["inventory"]["files"][arguments["path"]]:
                    raise ValueError("staged file hash changed during read")
                text = content.decode("utf-8")
                start = arguments["offset"]
                if start > len(text):
                    raise ValueError("read offset exceeds file length")
                end = len(text) if arguments["length"] is None else min(len(text), start + arguments["length"])
                result = {"text": text[start:end], "file_sha256": file_sha, "total_characters": len(text),
                          "start_character": start, "end_character": end, "eof": end == len(text)}
            else:
                if not isinstance(arguments, dict) or set(arguments) != {"code"} or not isinstance(arguments["code"], str) or not arguments["code"].strip():
                    raise ValueError("computation requires nonempty Python code")
                completed = run(self.workspace, self.identity, ["-c", arguments["code"]], timeout_seconds=self.timeout_seconds)
                result = {"return_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
            verify(self.workspace, self.identity)
        except (ValueError, OSError, subprocess.TimeoutExpired) as error:
            # Full technical error retained; no replacement, host fallback or fabricated output.
            record = {"request": request, "status": "TECHNICAL_FAILURE", "result": None,
                      "error_type": type(error).__name__, "error": str(error)}
            _write_once(terminal, record)
            raise
        record = {"request": request, "status": "RETURNED" if name == READ or result["return_code"] == 0 else "TOOL_RUNTIME_FAILURE",
                  "result": result, "error_type": None, "error": None}
        _write_once(terminal, record)
        return deepcopy(record)
