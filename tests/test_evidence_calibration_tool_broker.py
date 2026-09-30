import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from evidence_calibration_io import canonical_sha256
from evidence_calibration_tool_broker import ToolBroker, tool_definitions, READ, COMPUTE
from stage_evidence_calibration_workspace import inventory


def broker(tmp_path, method="B2", max_calls=8):
    workspace = tmp_path / "job"
    workspace.mkdir()
    (workspace / "visible.json").write_text('{"unicode":"αβ", "speed":0.25}')
    identity = {"method_id": method, "inventory": inventory(workspace)}
    identity["workspace_sha256"] = canonical_sha256(identity)
    return ToolBroker(workspace, identity, tmp_path / "events", max_calls=max_calls, timeout_seconds=2)


def test_definitions_preserve_tool_parity_and_no_tool_baselines():
    assert tool_definitions("B0") == tool_definitions("B1") == []
    assert tool_definitions("B2") == tool_definitions("B3") == tool_definitions("B4")


def test_read_complete_and_explicit_chunks_reconstruct_unicode_with_hashes(tmp_path):
    b = broker(tmp_path)
    full = b.call("full", READ, {"path": "visible.json", "offset": 0, "length": None})["result"]
    chunks = []
    for offset in range(0, full["total_characters"], 7):
        r = b.call(f"chunk-{offset}", READ, {"path": "visible.json", "offset": offset, "length": 7})["result"]
        chunks.append(r["text"])
        assert r["file_sha256"] == full["file_sha256"]
    assert "".join(chunks) == full["text"]
    assert full["eof"]
    assert (b.events / "full.intent.json").exists()
    terminal = json.loads((b.events / "full.result.json").read_text())
    assert terminal["result"] == full


def test_local_computation_keeps_full_stream_access_and_denies_outside_read(tmp_path):
    b = broker(tmp_path)
    outside = tmp_path / "evaluator.json"
    outside.write_text("synthetic evaluator")
    code = "import json,pathlib; x=json.loads(pathlib.Path('visible.json').read_text()); print(x['speed']*2); print(pathlib.Path("+repr(str(outside))+").exists())"
    r = b.call("compute", COMPUTE, {"code": code})
    assert r["status"] == "RETURNED"
    assert r["result"]["stdout"] == "0.5\nFalse\n"


@pytest.mark.parametrize("path", ["../evaluator.json", "/etc/passwd", "unregistered.json"])
def test_unregistered_reads_retained_as_technical_failures(tmp_path, path):
    b = broker(tmp_path)
    with pytest.raises(ValueError): b.call("bad", READ, {"path": path, "offset": 0, "length": None})
    record = json.loads((b.events / "bad.result.json").read_text())
    assert record["status"] == "TECHNICAL_FAILURE" and record["result"] is None
    with pytest.raises(ValueError, match="no replay"): b.call("bad", READ, {"path": "visible.json", "offset": 0, "length": None})


@pytest.mark.parametrize("method", ["B0", "B1"])
def test_baseline_tool_attempts_denied_and_retained(tmp_path, method):
    b = broker(tmp_path, method)
    with pytest.raises(ValueError, match="not permitted"): b.call("denied", COMPUTE, {"code":"print(1)"})
    assert json.loads((b.events / "denied.result.json").read_text())["status"] == "TECHNICAL_FAILURE"


def test_unknown_intent_and_budget_cannot_be_replayed(tmp_path):
    b = broker(tmp_path,max_calls=1)
    (b.events / "unknown.intent.json").write_text("unknown disposition")
    with pytest.raises(ValueError,match="unknown intent"): b.call("unknown",COMPUTE,{"code":"print(1)"})
    b.call("first",COMPUTE,{"code":"print(1)"})
    with pytest.raises(ValueError,match="budget exhausted"): b.call("second",COMPUTE,{"code":"print(2)"})
    with pytest.raises(ValueError,match="fresh event namespace"):
        ToolBroker(b.workspace,b.identity,b.events,max_calls=1,timeout_seconds=2)


def test_runtime_error_is_retained_without_semantic_repair(tmp_path):
    b = broker(tmp_path)
    result = b.call("error",COMPUTE,{"code":"raise RuntimeError('synthetic')"})
    assert result["status"] == "TOOL_RUNTIME_FAILURE"
    assert result["result"]["return_code"] != 0
    assert "synthetic" in result["result"]["stderr"]


def test_actual_staged_primitive_tool_runs_through_broker(tmp_path):
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json").read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    entry = candidate.materialize(diagnostic,"test-configuration","measured_response_recovery",catalog)[-1]
    packets = build(entry,candidate.execution_contract(entry,diagnostic))
    packet = next(p for p in packets["method_packets"] if p["method_id"] == "B2")
    with staged_workspace(entry,packet) as (workspace,bound):
        b = ToolBroker(workspace,bound,tmp_path / "real-events",max_calls=2,timeout_seconds=2)
        r = b.call("tool",COMPUTE,{"code":"import runpy,sys; sys.argv=['inventory','robot_visible/evidence.json']; runpy.run_path('tools/inspect_evidence_calibration_packet.py',run_name='__main__')"})
        assert json.loads(r["result"]["stdout"]) == summarize(entry["method_packet"])
        with pytest.raises(ValueError):
            b.call("contract",READ,{"path":"contracts/claim_contracts.json","offset":0,"length":None})


def test_tool_timeout_retains_terminal_failure_and_blocks_same_identity(tmp_path):
    import subprocess
    b = broker(tmp_path)
    b.timeout_seconds = 1
    with pytest.raises(subprocess.TimeoutExpired):
        b.call("timeout",COMPUTE,{"code":"import time;time.sleep(30)"})
    record = json.loads((b.events / "timeout.result.json").read_text())
    assert record["status"] == "TECHNICAL_FAILURE"
    assert record["error_type"] == "TimeoutExpired"
    with pytest.raises(ValueError,match="no replay"):
        b.call("timeout",COMPUTE,{"code":"print(1)"})
