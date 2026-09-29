#!/usr/bin/env python3
"""Export the exact source files available to both pilot methods for blinded annotation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evidence_calibration_io import canonical_json_bytes
from run_evidence_calibration_b2_pilot import _materialize


ROOT = Path(__file__).resolve().parents[1]


def build(condition_id: str, root: Path = ROOT) -> list[dict[str, str]]:
    pilot = json.loads((root / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
    schedule = json.loads((root / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    validation = json.loads((root / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json").read_text())
    entry, diagnostic, _ = _materialize(root, pilot, schedule, condition_id)
    expected = next(
        packet_hash
        for episode in validation["episodes"]
        for candidate_id, packet_hash in zip(episode["condition_ids"], episode["condition_packet_sha256s"], strict=True)
        if candidate_id == condition_id
    )
    if entry["condition"]["method_packet_sha256"] != expected:
        raise ValueError("condition packet differs from the pinned pilot")
    source = diagnostic["source"]
    b2_output_path = root / f"model_outputs/evidence-calibration-b2-b4-pilot-v1/b2/{condition_id}.json"
    if not b2_output_path.is_file():
        raise ValueError("source context requires a retained valid B2 response")
    b2_output = json.loads(b2_output_path.read_text())
    cache_path = root / f'research/explanation_fidelity/model_cache/evidence-calibration-b2-b4-pilot-v1/{b2_output["cache_key"]}.json'
    call = json.loads(cache_path.read_text())
    if call["request"]["workspace_identity"]["method_packet_sha256"] != expected:
        raise ValueError("B2 call workspace differs from the pinned condition packet")
    assets = [
        ("source/behavior_tree.xml", root / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml", source["bt_policy_sha256"]),
        ("source/nav2.yaml", root / "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml", source["nav2_config_sha256"]),
        ("source/diagnostic_config.json", root / "configs/diagnostic_command_motion_low_speed_v1.json", source["diagnostic_config_sha256"]),
        ("tools/inspect_evidence_calibration_packet.py", root / "analysis/inspect_evidence_calibration_packet.py", call["request"]["workspace_identity"]["tool_sha256"]),
    ]
    result = []
    for asset_id, path, expected_hash in assets:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError(f"source file differs from B2 pilot input: {asset_id}")
        result.append({"asset_id": asset_id, "sha256": expected_hash, "text": raw.decode("utf-8")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_bytes(canonical_json_bytes(build(args.condition_id)) + b"\n")


if __name__ == "__main__":
    main()
