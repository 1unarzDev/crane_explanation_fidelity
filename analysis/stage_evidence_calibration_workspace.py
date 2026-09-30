#!/usr/bin/env python3
"""Offline temporary file staging; does not authorize calls or confine a harness."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile

from build_evidence_calibration_method_packets import _scan
from evidence_calibration_io import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = {
    "bt-policy": ("source_assets", "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml", "source/behavior_tree.xml", "retained-source-v1"),
    "nav2-config": ("source_assets", "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml", "source/nav2.yaml", "retained-source-v1"),
    "diagnostic-config": ("source_assets", "configs/diagnostic_command_motion_low_speed_v1.json", "source/diagnostic_config.json", "retained-source-v1"),
    "inspect-evidence-calibration-packet": ("primitive_tools", "analysis/inspect_evidence_calibration_packet.py", "tools/inspect_evidence_calibration_packet.py", "v1-development"),
    "claim-contracts": ("contract_assets", "configs/evidence_calibration_claim_contracts_v2_development.json", "contracts/claim_contracts.json", "v2-development"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(workspace: Path) -> dict:
    """Reject symlinks, special files, and unexpected empty directories too."""
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("invalid workspace root")
    files, directories = {}, []
    for path in sorted(workspace.rglob("*")):
        relative = path.relative_to(workspace).as_posix()
        if path.is_symlink():
            raise ValueError("workspace symlink prohibited")
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files[relative] = sha(path.read_bytes())
        else:
            raise ValueError("workspace special file prohibited")
    return {"files": files, "directories": directories}


def verify(workspace: Path, identity: dict) -> None:
    unsigned = {key: value for key, value in identity.items() if key != "workspace_sha256"}
    if canonical_sha256(unsigned) != identity.get("workspace_sha256"):
        raise ValueError("workspace identity hash mismatch")
    if inventory(workspace) != identity["inventory"]:
        raise ValueError("workspace inventory changed")


def prepare_files(entry: dict, packet: dict, *, root: Path = ROOT) -> dict[str, bytes]:
    """Resolve only registered assets; validate all inputs before creating files."""
    condition, evidence = entry["condition"], entry["method_packet"]
    if (condition.get("visibility") != "robot_visible" or not condition.get("evaluator_only_absent")
            or condition["method_packet_sha256"] != canonical_sha256(evidence)):
        raise ValueError("robot-visible evidence certification/hash mismatch")
    _scan(evidence)
    _scan(packet)
    unsigned = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if canonical_sha256(unsigned) != packet.get("packet_sha256"):
        raise ValueError("method packet hash mismatch")
    basis = {key: condition[key] for key in ("episode_id", "configuration_id", "condition_id",
             "method_packet_sha256", "available_evidence_ids", "source_configuration_sha256", "runtime_manifest_sha256")}
    if (any(packet[key] != condition[key] for key in ("episode_id", "condition_id", "method_packet_sha256", "available_evidence_ids"))
            or packet["evidence_basis_sha256"] != canonical_sha256(basis)
            or packet["question_instruction"] != evidence["question"]):
        raise ValueError("method/evidence identity mismatch")
    method = packet["method_id"]
    if method not in {"B0", "B1", "B2", "B3", "B4"}:
        raise ValueError("unknown method")
    presentation = json.loads(packet["presentation"]) if method == "B0" else packet["presentation"]
    if presentation != evidence:
        raise ValueError("source presentation differs from evidence")
    expected = set() if method in {"B0", "B1"} else set(REGISTRY) - {"claim-contracts"}
    if method in {"B3", "B4"}:
        expected.add("claim-contracts")
    files, seen = {}, set()
    for category in ("source_assets", "primitive_tools", "contract_assets"):
        for asset in packet[category]:
            identifier = asset["asset_id"]
            if identifier not in expected or identifier in seen or set(asset) != {"asset_id", "version", "sha256"}:
                raise ValueError("unknown, duplicate or prohibited asset")
            registered_category, source, target, version = REGISTRY[identifier]
            if category != registered_category or asset["version"] != version:
                raise ValueError("asset category/version mismatch")
            source_path = root / source
            if any((root / Path(*Path(source).parts[:index])).is_symlink() for index in range(1, len(Path(source).parts) + 1)):
                raise ValueError("source symlink prohibited")
            content = source_path.read_bytes()
            if sha(content) != asset["sha256"]:
                raise ValueError("source asset hash mismatch")
            files[target] = content
            seen.add(identifier)
    if seen != expected:
        raise ValueError("required asset missing")
    if expected:
        # Preserve the legacy B2 evidence serialization and filenames.
        files["robot_visible/evidence.json"] = (json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return files


@contextmanager
def staged_workspace(entry: dict, packet: dict, *, root: Path = ROOT):
    files = prepare_files(entry, packet, root=root)
    with tempfile.TemporaryDirectory(prefix="crane-ec-workspace-") as temporary:
        workspace = Path(temporary)
        for relative, content in files.items():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        identity = {"schema": "crane-evidence-calibration-workspace/v1-development",
                    "method_id": packet["method_id"], "condition_id": packet["condition_id"],
                    "packet_sha256": packet["packet_sha256"],
                    "evidence_basis_sha256": packet["evidence_basis_sha256"],
                    "inventory": inventory(workspace), "harness_confinement_verified": False,
                    "model_calls_authorized": False}
        identity["workspace_sha256"] = canonical_sha256(identity)
        verify(workspace, identity)
        try:
            yield workspace, identity
        finally:
            verify(workspace, identity)
