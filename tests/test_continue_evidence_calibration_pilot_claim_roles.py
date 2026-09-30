from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import continue_evidence_calibration_pilot_claim_roles as continuation


def test_continuation_contains_only_158_never_launched_identities():
    declaration, tasks, _, _, _ = continuation.load_continuation()
    assert len(tasks) == 158
    assert sum(slot == "A" for slot, _ in tasks) == 44
    assert sum(slot == "B" for slot, _ in tasks) == 114
    quarantine = declaration["quarantined_requests"][0]
    assert (quarantine["slot"], quarantine["case_id"]) not in {
        (slot, case["case_id"]) for slot, case in tasks}
    assert declaration["endpoint_scoring_authorized"] is False


def test_continuation_rejects_substitution_of_unknown_request(tmp_path, monkeypatch):
    declaration = json.loads(continuation.CONTINUATION.read_text())
    quarantine = declaration["quarantined_requests"][0]
    declaration["tasks"][0] = {"slot": quarantine["slot"], "case_id": quarantine["case_id"]}
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(declaration))
    monkeypatch.setattr(continuation, "CONTINUATION", changed)
    with pytest.raises(ValueError, match="uncalled identities"):
        continuation.load_continuation()


def test_continuation_stops_at_first_failure_without_retry(tmp_path, monkeypatch):
    bound = continuation.load_continuation()
    declaration = bound[0]
    monkeypatch.setattr(continuation, "load_continuation", lambda: copy.deepcopy(bound))
    monkeypatch.setattr(continuation, "ROOT", tmp_path)
    monkeypatch.setattr(continuation, "transport_audit", lambda *args: {"status": "READY_FOR_SCHEMA_CANARY"})
    monkeypatch.setattr(continuation.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout=declaration["cli_version"]))
    canary = tmp_path / declaration["output_root"] / "canary" / f"{continuation.CANARY['case_id']}.json"
    canary.parent.mkdir(parents=True)
    canary.write_text("{}")
    calls = []
    def call(**kwargs):
        calls.append((kwargs["slot"], kwargs["case"]["case_id"]))
        return {"status": continuation.VALID_STATUS if kwargs["slot"] == "canary" else "FAILED_NO_RETRY"}
    monkeypatch.setattr(continuation, "call_once", call)
    result = continuation.run("pilot")
    assert result["status"] == "STOPPED_ON_RETAINED_FAILURE"
    assert result["valid_continuation_calls"] == 0
    assert len(calls) == 2
    assert calls[1] == (bound[1][0][0], bound[1][0][1]["case_id"])
