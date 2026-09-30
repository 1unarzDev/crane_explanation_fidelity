#!/usr/bin/env python3
"""Offline B2 request reconstruction on the unchanged inspected development cohort."""
import hashlib
import json
from pathlib import Path

import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build as build_packets
from prepare_evidence_calibration_b2_agent import prepare

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "manifests/study/evidence-calibration-b2-requests-v1-development.json"
PREPARATION = "manifests/study/evidence-calibration-method-preparation-v1-development.json"


def build():
    source = candidate.build()
    if source != json.loads((ROOT / candidate.OUTPUT).read_text()):
        raise ValueError("source packet snapshot changed")
    prior = json.loads((ROOT / PREPARATION).read_text())
    prior_rows = {row["condition_id"]: row for row in prior["conditions"]}
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    rows = []
    for episode in source["episodes"]:
        diagnostic = json.loads((ROOT / f"data/robot_visible/dev/{episode['source_run_id']}/command-motion-diagnostic-v3.json").read_text())
        entries = candidate.materialize(diagnostic, episode["configuration_id"], episode["family"], catalog)
        for entry, retained in zip(entries, episode["conditions"], strict=True):
            packets = build_packets(entry, candidate.execution_contract(entry, diagnostic))
            if {p["method_id"]:p["packet_sha256"] for p in packets["method_packets"]} != retained["method_packet_hashes"]:
                raise ValueError("method packet changed")
            request = prepare(entry, packets)
            workspace = request["workspace_identity"]
            if workspace["workspace_sha256"] != prior_rows[request["condition_id"]]["workspaces"]["B2"]["workspace_sha256"]:
                raise ValueError("prior staged B2 workspace changed")
            rows.append({"source_run_id": episode["source_run_id"], "configuration_id": episode["configuration_id"],
                         "condition_id": request["condition_id"], "level_index": entry["condition"]["level_index"],
                         "request_sha256": request["request_sha256"], "workspace_sha256": workspace["workspace_sha256"],
                         "prompt_utf8_bytes": len(request["prompt"].encode()), "token_fit": None})
    if len(rows) != 60 or {row["condition_id"] for row in rows} != set(prior_rows):
        raise ValueError("B2 condition coverage incomplete")
    paths = ["analysis/prepare_evidence_calibration_b2_agent.py", "analysis/audit_evidence_calibration_b2_requests.py",
             "tests/test_evidence_calibration_b2_agent.py", "tests/test_evidence_calibration_b2_requests.py",
             "research/explanation_fidelity/prompts/evidence_calibration_b2_development_v1.txt",
             "analysis/stage_evidence_calibration_workspace.py", candidate.OUTPUT, PREPARATION,
             "docs/B2_AGENT_INTERFACE_2026-09-30.md",
             "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json"]
    return {"schema": "crane-b2-request-audit/v1-development", "recorded_date": "2026-09-30",
            "status": "B2_REQUEST_CONTENT_AUDITED_HARNESS_AND_EXECUTION_UNBOUND",
            "bindings": [{"path":path,"raw_sha256":hashlib.sha256((ROOT/path).read_bytes()).hexdigest()} for path in paths],
            "inspected_development_episode_count": len({row["configuration_id"] for row in rows}),
            "within_episode_condition_count": len(rows), "b2_request_count": len(rows),
            "prompt_utf8_byte_range": {"minimum":min(row["prompt_utf8_bytes"] for row in rows),
                                       "maximum":max(row["prompt_utf8_bytes"] for row in rows)},
            "conditions": rows, "harness_permissions_enforced": False, "full_tool_surface_bound": False,
            "context_capacity_verified": False, "model_calls_authorized": False, "model_call_attempted": False,
            "semantic_method_outputs_generated": 0, "pilot_annotation_authorized": False, "method_key_opened": False,
            "old_packets_or_outputs_changed": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    result = build()
    if json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("B2 requests differ from retained snapshot")
    print(json.dumps({k:v for k,v in result.items() if k not in ("bindings","conditions")},indent=2,sort_keys=True))
