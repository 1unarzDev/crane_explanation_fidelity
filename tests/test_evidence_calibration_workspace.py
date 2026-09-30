import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import REGISTRY, prepare_files, staged_workspace, verify


@pytest.fixture
def inputs():
    diagnostic = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json").read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    entry = candidate.materialize(diagnostic, "synthetic-configuration", "measured_response_recovery", catalog)[-1]
    packets = build(entry, candidate.execution_contract(entry, diagnostic))
    return entry, {p["method_id"]: p for p in packets["method_packets"]}


def rehash(packet):
    packet["packet_sha256"] = canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})


def test_five_method_inventory_parity_stability_and_cleanup(inputs):
    entry, packets = inputs
    identities = {}
    for method, packet in packets.items():
        with staged_workspace(entry, packet) as (path, identity):
            assert identity["model_calls_authorized"] is False
            assert identity["harness_confinement_verified"] is False
            assert len(identity["inventory"]["files"]) == {"B0": 0, "B1": 0, "B2": 5, "B3": 6, "B4": 6}[method]
            identities[method] = identity
            verify(path, identity)
        assert not path.exists()
        with staged_workspace(entry, packet) as (_, second):
            assert second == identity
    shared = identities["B2"]["inventory"]["files"]
    for method in ("B3", "B4"):
        assert all(identities[method]["inventory"]["files"][p] == h for p, h in shared.items())
    assert "contracts/claim_contracts.json" not in shared


@pytest.mark.parametrize("mutation", ["stale", "unknown", "missing", "category", "baseline_contract", "evidence"])
def test_invalid_inputs_fail_before_staging(inputs, mutation):
    entry, packets = copy.deepcopy(inputs)
    packet = packets["B2"]
    if mutation == "stale":
        packet["source_assets"][0]["sha256"] = "0" * 64
    elif mutation == "unknown":
        packet["source_assets"][0]["asset_id"] = "../evaluator/reference.json"
    elif mutation == "missing":
        packet["source_assets"].pop()
    elif mutation == "category":
        packet["primitive_tools"].append(packet["source_assets"].pop())
    elif mutation == "baseline_contract":
        packet = packets["B0"]
        packet["contract_assets"] = packets["B4"]["contract_assets"]
    else:
        entry["method_packet"]["question"] = "changed"
    rehash(packet)
    with pytest.raises(ValueError):
        prepare_files(entry, packet)


@pytest.mark.parametrize("mutation", ["changed", "added", "directory", "symlink", "identity"])
def test_post_stage_integrity_failure_and_cleanup(inputs, mutation):
    entry, packets = inputs
    with pytest.raises(ValueError, match="workspace"):
        with staged_workspace(entry, packets["B2"]) as (path, identity):
            if mutation == "changed":
                (path / "source/nav2.yaml").write_text("changed")
            elif mutation == "added":
                (path / "evaluator.json").write_text("unexpected")
            elif mutation == "directory":
                (path / "extra").mkdir()
            elif mutation == "symlink":
                (path / "outside").symlink_to(ROOT / "README.md")
            else:
                identity["method_id"] = "B4"
    assert not path.exists()


def test_source_symlinks_rejected(inputs, tmp_path):
    entry, packets = inputs
    for _, source, _, _ in REGISTRY.values():
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(ROOT / source)
    with pytest.raises(ValueError, match="source symlink"):
        prepare_files(entry, packets["B2"], root=tmp_path)


def test_staged_primitive_tool_remains_usable_without_inventory_change(inputs):
    import subprocess
    from inspect_evidence_calibration_packet import summarize
    entry, packets = inputs
    with staged_workspace(entry, packets["B2"]) as (path, identity):
        result = subprocess.run([sys.executable, "tools/inspect_evidence_calibration_packet.py",
                                 "robot_visible/evidence.json"], cwd=path, check=True,
                                capture_output=True, text=True)
        assert json.loads(result.stdout) == summarize(entry["method_packet"])
        verify(path, identity)


def test_packet_hash_and_condition_identity_are_bound(inputs):
    entry, packets = copy.deepcopy(inputs)
    packet = packets["B2"]
    packet["condition_id"] = "different-condition"
    with pytest.raises(ValueError, match="packet hash"):
        prepare_files(entry, packet)
    rehash(packet)
    with pytest.raises(ValueError, match="identity"):
        prepare_files(entry, packet)
