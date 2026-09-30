#!/usr/bin/env python3
"""Reconstruct B0/B1 development inputs offline; retain hashes and byte sizes only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build as build_packets
from prepare_evidence_calibration_baselines import prepare

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "manifests/study/evidence-calibration-baseline-requests-v1-development.json"


def build() -> dict:
    source = candidate.build()
    if source != json.loads((ROOT / candidate.OUTPUT).read_text()):
        raise ValueError("source five-method packet candidate changed")
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    rows = []
    for episode in source["episodes"]:
        diagnostic = json.loads((ROOT / f"data/robot_visible/dev/{episode['source_run_id']}/command-motion-diagnostic-v3.json").read_text())
        entries = candidate.materialize(diagnostic, episode["configuration_id"], episode["family"], catalog)
        for entry, retained in zip(entries, episode["conditions"], strict=True):
            packets = build_packets(entry, candidate.execution_contract(entry, diagnostic))
            if {item["method_id"]: item["packet_sha256"] for item in packets["method_packets"]} != retained["method_packet_hashes"]:
                raise ValueError("reconstructed method packets differ from the retained source snapshot")
            requests = {method: prepare(method, entry, packets) for method in ("B0", "B1")}
            rows.append({"source_run_id": episode["source_run_id"], "configuration_id": episode["configuration_id"],
                         "condition_id": entry["condition"]["condition_id"], "level_index": entry["condition"]["level_index"],
                         "method_packet_sha256": entry["condition"]["method_packet_sha256"],
                         "requests": {method: {"request_sha256": request["request_sha256"],
                                               "presentation_sha256": request["presentation_sha256"],
                                               "prompt_utf8_bytes": len(request["prompt"].encode())}
                                      for method, request in requests.items()}})
    paths = ("analysis/prepare_evidence_calibration_baselines.py", "analysis/audit_evidence_calibration_baseline_requests.py",
             "tests/test_evidence_calibration_baselines.py",
             "research/explanation_fidelity/prompts/evidence_calibration_baseline_ordinary_development_v1.txt",
             candidate.OUTPUT, "docs/BASELINE_ORDINARY_INTERFACES_2026-09-30.md",
             "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json")
    return {"schema": "crane-baseline-request-audit/v1-development", "recorded_date": "2026-09-30",
            "status": "LOSSLESS_B0_B1_REQUESTS_AUDITED_EXECUTION_UNBOUND",
            "bindings": [{"path": path, "raw_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
            "inspected_development_episode_count": source["inspected_development_episode_count"],
            "within_episode_condition_count": len(rows), "baseline_request_count": len(rows) * 2,
            "prompt_utf8_byte_ranges": {method: {"minimum": min(row["requests"][method]["prompt_utf8_bytes"] for row in rows),
                                                 "maximum": max(row["requests"][method]["prompt_utf8_bytes"] for row in rows)}
                                        for method in ("B0", "B1")},
            "token_capacity_status": "UNVERIFIED_REQUIRES_MODEL_AND_TOKENIZER_BINDING_NO_TRUNCATION_AUTHORIZED",
            "requests": rows, "model_calls_authorized": False, "model_call_attempted": False,
            "semantic_method_outputs_generated": 0, "pilot_annotation_authorized": False,
            "old_packets_or_outputs_changed": False, "method_key_opened": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    result = build()
    if json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("baseline request audit differs from retained snapshot")
    print(json.dumps({key: value for key, value in result.items() if key not in ("requests", "bindings")},
                     indent=2, sort_keys=True))
