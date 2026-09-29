#!/usr/bin/env python3
"""Build the transport-only v2 qualification suite after v1's pre-inference 403."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from build_evidence_calibration_agent_qualification import build as build_v1
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def build() -> dict:
    prior = build_v1()
    cases = copy.deepcopy(prior["cases"])
    for case in cases:
        old = case["case_id"]
        new = old.replace("qa-", "qb-", 1)
        case["case_id"] = new
        case["form"]["robot_visible_evidence"]["qualification_fixture_version"] = "v2-login-transport"
        for item in case["form"]["atomic_statements"]:
            item["item_id"] = item["item_id"].replace(old, new, 1)
        for item in case["expected"]["atomic_labels"]:
            item["item_id"] = item["item_id"].replace(old, new, 1)
    return {
        "schema": "crane-evidence-calibration-agent-qualification-suite/v2",
        "suite_id": "evidence-calibration-agent-exact-task-v2-login",
        "predecessor_disposition": "v1 first call failed HTTP 403 before semantic output; retained and never retried",
        "construction": "construction-defined labels with new logical case identities; no prospective method output",
        "model_visible_gold": False,
        "case_count": len(cases),
        "split_counts": prior["split_counts"],
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v2.json")
    args = parser.parse_args()
    value = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(value) + b"\n")
    print(json.dumps({"output": str(args.output), "sha256": canonical_sha256(value), "case_count": value["case_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
