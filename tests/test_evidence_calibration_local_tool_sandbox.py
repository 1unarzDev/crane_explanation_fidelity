import json
from pathlib import Path
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox import command, run
from stage_evidence_calibration_workspace import inventory, staged_workspace
import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build
from inspect_evidence_calibration_packet import summarize


def identity(workspace):
    result = {"inventory": inventory(workspace)}
    result["workspace_sha256"] = canonical_sha256(result)
    return result


def test_real_namespace_blocks_outside_reads_writes_environment_and_parent_network(tmp_path, monkeypatch):
    outside = tmp_path / "outside.json"
    outside.write_text('{"synthetic_evaluator_only":true}')
    workspace = tmp_path / "job"
    workspace.mkdir()
    (workspace / "visible.json").write_text('{"visible":true}')
    bound = identity(workspace)
    monkeypatch.setenv("CRANE_SYNTHETIC_SECRET", "synthetic-value")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        code = '''import json, os, pathlib, socket
checks = {}
checks["visible_read"] = json.loads(pathlib.Path("visible.json").read_text())["visible"]
checks["outside_absent"] = not pathlib.Path(OUTSIDE).exists()
checks["home_absent"] = not pathlib.Path("/home").exists()
checks["parent_root_absent"] = not pathlib.Path("/proc/1/root" + OUTSIDE).exists()
checks["environment_absent"] = "CRANE_SYNTHETIC_SECRET" not in os.environ
try:
    pathlib.Path("visible.json").write_text("changed")
    checks["visible_write_denied"] = False
except OSError:
    checks["visible_write_denied"] = True
pathlib.Path("/tmp/local-computation").write_text("scratch")
checks["scratch_available"] = True
try:
    with socket.create_connection(("127.0.0.1", PORT), timeout=1):
        checks["parent_network_denied"] = False
except OSError:
    checks["parent_network_denied"] = True
print(json.dumps(checks))
'''.replace("OUTSIDE", repr(str(outside))).replace("PORT", str(port))
        result = run(workspace, bound, ["-c", code])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {key: True for key in (
        "visible_read", "outside_absent", "home_absent", "parent_root_absent", "environment_absent",
        "visible_write_denied", "scratch_available", "parent_network_denied")}
    assert outside.read_text() == '{"synthetic_evaluator_only":true}'
    assert (workspace / "visible.json").read_text() == '{"visible":true}'


def test_actual_staged_inventory_tool_and_local_arithmetic_remain_usable():
    diagnostic = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json").read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    entry = candidate.materialize(diagnostic, "test-configuration", "measured_response_recovery", catalog)[-1]
    packets = build(entry, candidate.execution_contract(entry, diagnostic))
    packet = next(row for row in packets["method_packets"] if row["method_id"] == "B2")
    with staged_workspace(entry, packet) as (workspace, bound):
        result = run(workspace, bound, ["tools/inspect_evidence_calibration_packet.py", "robot_visible/evidence.json"])
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == summarize(entry["method_packet"])
        arithmetic = run(workspace, bound, ["-c", "import math; print(math.hypot(3,4))"])
        assert arithmetic.returncode == 0
        assert arithmetic.stdout.strip() == "5.0"


def test_runtime_failures_do_not_fallback_to_host_execution(tmp_path):
    result = run(tmp_path, identity(tmp_path), ["-c", "raise RuntimeError('synthetic failure')"])
    assert result.returncode != 0
    assert "synthetic failure" in result.stderr


@pytest.mark.parametrize("timeout", [0, 61, True, 1.5])
def test_invalid_timeouts_are_rejected(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        run(tmp_path, identity(tmp_path), ["-c", "pass"], timeout_seconds=timeout)


def test_workspace_tampering_rejected_before_process(tmp_path):
    bound = identity(tmp_path)
    (tmp_path / "unexpected.json").write_text("unexpected")
    with pytest.raises(ValueError, match="inventory changed"):
        command(tmp_path, bound, ["-c", "pass"])


def test_real_timeout_terminates_local_invocation_without_host_fallback(tmp_path):
    import subprocess
    with pytest.raises(subprocess.TimeoutExpired):
        run(tmp_path, identity(tmp_path), ["-c", "import time; time.sleep(30)"], timeout_seconds=1)
    assert inventory(tmp_path) == {"files": {}, "directories": []}
