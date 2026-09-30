#!/usr/bin/env python3
"""Verify mechanical blind packet assembly without model calls or semantic scoring."""

from __future__ import annotations

import json

from build_evidence_calibration_pilot_support_packets import BUNDLE, KEY, ROOT, build, digest
from evidence_calibration_io import canonical_json_bytes


def audit() -> dict:
    bundle, key = build()
    for path, value in ((ROOT / BUNDLE, bundle), (ROOT / KEY, key)):
        if path.read_bytes() != canonical_json_bytes(value) + b"\n":
            raise ValueError("retained support packet/key differs from pinned mechanical reconstruction")
    return {"schema": "crane-pilot-support-packet-audit/v1-development",
            "status": "PASS_MECHANICAL_BLIND_ASSEMBLY_NO_ANNOTATION",
            "bundle": {"path": BUNDLE, "raw_sha256": digest(ROOT / BUNDLE)},
            "separate_coordinator_key": {"path": KEY, "raw_sha256": digest(ROOT / KEY)},
            "responses": 114, "atomic_statements": 1084, "forms": 228,
            "top_level_episode_configuration_ids_removed": True,
            "evidence_fields_and_source_bytes_preserved": True,
            "atomic_level_anchors": 0, "highest_level_qualified": False,
            "annotator_method_join_key_access": False,
            "deterministic_packaging_key_access": True,
            "model_call_attempted": False, "pilot_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
