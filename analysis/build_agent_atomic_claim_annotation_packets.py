#!/usr/bin/env python3
"""Build the prospective automated-agent variant of blinded atomic packets.

The original human-oriented development exporter remains unchanged for provenance.  This adapter
changes only the prospective measurement metadata; packet contents and the separate join-key
boundary continue to come from the tested atomic packet builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_atomic_claim_annotation_packets import build as build_legacy_packet
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


PACKET_SCHEMA = "crane-blinded-agent-atomic-annotation-packet-set/v1"
KEY_SCHEMA = "crane-blinded-agent-atomic-annotation-key/v1"
BUILDER_ID = "blinded-agent-atomic-claim-annotation-builder"
BUILDER_VERSION = "v3-astra-response-text-parity"


def _validated_source_assets(source_assets: list[dict] | None) -> list[dict]:
    if source_assets is None:
        return []
    if not isinstance(source_assets, list):
        raise ValueError("source assets must be a list")
    result, seen = [], set()
    for asset in source_assets:
        if not isinstance(asset, dict) or set(asset) != {"asset_id", "sha256", "text"}:
            raise ValueError("source asset has missing or unknown fields")
        asset_id, expected_hash, value = asset["asset_id"], asset["sha256"], asset["text"]
        if not isinstance(asset_id, str) or not asset_id or asset_id in seen:
            raise ValueError("source asset identity is missing or duplicated")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or not isinstance(value, str):
            raise ValueError("source asset hash or text is invalid")
        if hashlib.sha256(value.encode("utf-8")).hexdigest() != expected_hash:
            raise ValueError("source asset bytes do not match their hash")
        if any(token in asset_id.lower() for token in ("evaluator", "gold", "intervention")):
            raise ValueError("source asset identity leaks evaluator context")
        seen.add(asset_id)
        result.append(dict(asset))
    return result


def build(condition_entry: dict, response: dict, rubric: dict, blinding_salt: str,
          source_assets: list[dict] | None = None):
    packet, key = build_legacy_packet(condition_entry, response, rubric, blinding_salt)
    validated_assets = _validated_source_assets(source_assets)
    if validated_assets:
        for form in packet["forms"]:
            form["robot_visible_evidence"] = {
                **form["robot_visible_evidence"],
                "exact_source_assets": validated_assets,
            }
        packet["annotation_source_assets_sha256"] = canonical_sha256(validated_assets)
    packet.update(
        {
            "schema": PACKET_SCHEMA,
            "builder_id": BUILDER_ID,
            "builder_version": BUILDER_VERSION,
            "response_text": response["final_response"],
            "annotation_origin": "automated_agent",
            "independent_agent_invocations_required": 2,
            "adjudication_agent_policy": "DISTINCT_DISAGREEMENT_ONLY_INVOCATION",
            "qualification_status": "EXACT_TASK_V4_ASTRA_QUALIFIED_AGENT_ASSESSED_ONLY",
            "qualification_disposition": "manifests/study/evidence-calibration-agent-qualification-disposition-v1.json",
        }
    )
    packet.pop("independent_annotator_count_required", None)
    packet.pop("automated_judge_role", None)
    key.update(
        {
            "schema": KEY_SCHEMA,
            "builder_id": BUILDER_ID,
            "builder_version": BUILDER_VERSION,
            "packet_set_sha256": canonical_sha256(packet),
            "annotation_origin": "automated_agent",
            "annotation_source_assets_sha256": canonical_sha256(validated_assets),
        }
    )
    return packet, key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-entry", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--blinding-salt-file", type=Path, required=True)
    parser.add_argument("--packet-output", type=Path, required=True)
    parser.add_argument("--key-output", type=Path, required=True)
    parser.add_argument("--source-asset-manifest", type=Path)
    args = parser.parse_args()
    packet, key = build(
        json.loads(args.condition_entry.read_text(encoding="utf-8")),
        json.loads(args.response.read_text(encoding="utf-8")),
        json.loads(args.rubric.read_text(encoding="utf-8")),
        args.blinding_salt_file.read_text(encoding="utf-8").strip(),
        None if args.source_asset_manifest is None else
        json.loads(args.source_asset_manifest.read_text(encoding="utf-8")),
    )
    args.packet_output.write_bytes(canonical_json_bytes(packet) + b"\n")
    args.key_output.write_bytes(canonical_json_bytes(key) + b"\n")


if __name__ == "__main__":
    main()
