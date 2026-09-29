#!/usr/bin/env python3
"""Build the prospective automated-agent variant of blinded atomic packets.

The original human-oriented development exporter remains unchanged for provenance.  This adapter
changes only the prospective measurement metadata; packet contents and the separate join-key
boundary continue to come from the tested atomic packet builder.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_atomic_claim_annotation_packets import build as build_legacy_packet
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


PACKET_SCHEMA = "crane-blinded-agent-atomic-annotation-packet-set/v1"
KEY_SCHEMA = "crane-blinded-agent-atomic-annotation-key/v1"
BUILDER_ID = "blinded-agent-atomic-claim-annotation-builder"
BUILDER_VERSION = "v1-development"


def build(condition_entry: dict, response: dict, rubric: dict, blinding_salt: str):
    packet, key = build_legacy_packet(condition_entry, response, rubric, blinding_salt)
    packet.update(
        {
            "schema": PACKET_SCHEMA,
            "builder_id": BUILDER_ID,
            "builder_version": BUILDER_VERSION,
            "annotation_origin": "automated_agent",
            "independent_agent_invocations_required": 2,
            "adjudication_agent_policy": "DISTINCT_DISAGREEMENT_ONLY_INVOCATION",
            "qualification_status": "EXACT_TASK_QUALIFICATION_REQUIRED_BEFORE_PRIMARY_SCORING",
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
    args = parser.parse_args()
    packet, key = build(
        json.loads(args.condition_entry.read_text(encoding="utf-8")),
        json.loads(args.response.read_text(encoding="utf-8")),
        json.loads(args.rubric.read_text(encoding="utf-8")),
        args.blinding_salt_file.read_text(encoding="utf-8").strip(),
    )
    args.packet_output.write_bytes(canonical_json_bytes(packet) + b"\n")
    args.key_output.write_bytes(canonical_json_bytes(key) + b"\n")


if __name__ == "__main__":
    main()
