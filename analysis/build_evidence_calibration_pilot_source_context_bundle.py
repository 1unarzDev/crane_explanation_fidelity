#!/usr/bin/env python3
"""Bind exact common source/tool context across all valid pilot B2 conditions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_evidence_calibration_pilot_source_context import build as build_assets
from evidence_calibration_io import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/source-assets-v1.json"
DEFAULT_AUDIT = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-source-context-v1.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(root: Path = ROOT) -> tuple[list[dict], dict]:
    b2_root = root / "model_outputs/evidence-calibration-b2-b4-pilot-v1/b2"
    outputs = sorted(b2_root.glob("*.json"))
    if len(outputs) != 57:
        raise ValueError("source context requires exactly 57 retained valid B2 outputs")
    shared = None
    rows = []
    for output in outputs:
        condition_id = output.stem
        assets = build_assets(condition_id, root)
        if shared is None:
            shared = assets
        elif assets != shared:
            raise ValueError(f"B2 source/tool context differs at {condition_id}")
        b2 = json.loads(output.read_text(encoding="utf-8"))
        cache_path = root / "research/explanation_fidelity/model_cache/evidence-calibration-b2-b4-pilot-v1" / f"{b2['cache_key']}.json"
        rows.append({
            "condition_id": condition_id,
            "b2_output_raw_sha256": sha256(output.read_bytes()),
            "b2_call_record_raw_sha256": sha256(cache_path.read_bytes()),
        })
    assert shared is not None
    asset_bytes = canonical_json_bytes(shared) + b"\n"
    result = {
        "schema": "crane-evidence-calibration-b2-b4-pilot-source-context-bundle/v1",
        "pilot_id": "evidence-calibration-b2-b4-pilot-v1",
        "development_only": True,
        "valid_b2_conditions": len(rows),
        "source_context_common_to_all_conditions": True,
        "source_asset_manifest_path": str(DEFAULT_ASSETS.relative_to(ROOT)),
        "source_asset_manifest_raw_sha256": sha256(asset_bytes),
        "asset_hashes": [{"asset_id": asset["asset_id"], "sha256": asset["sha256"]} for asset in shared],
        "method_answer_text_used_to_select_assets": False,
        "source_assets_derived_from_b2_accessible_files": True,
        "condition_bindings": rows,
        "annotation_performed": False,
    }
    return shared, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-output", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    assets, audit = build()
    args.assets_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.assets_output.write_bytes(canonical_json_bytes(assets) + b"\n")
    args.audit_output.write_bytes(canonical_json_bytes(audit) + b"\n")
    print(json.dumps({"status": "BOUND_COMMON_SOURCE_CONTEXT", "conditions": audit["valid_b2_conditions"],
                      "asset_count": len(assets), "asset_manifest_sha256": audit["source_asset_manifest_raw_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
