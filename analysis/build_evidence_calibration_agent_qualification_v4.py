#!/usr/bin/env python3
"""Build the final bounded Astra qualification after invalidating Luna v3 gold."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from build_evidence_calibration_agent_qualification_v3 import build as build_v3
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def build() -> dict:
    prior = build_v3()
    cases = copy.deepcopy(prior["cases"])
    for case in cases:
        old = case["case_id"]
        new = old.replace("qc-", "qd-", 1)
        case["case_id"] = new
        case["form"]["robot_visible_evidence"]["qualification_fixture_version"] = "v4-astra-final"
        for item in case["form"]["atomic_statements"]:
            item["item_id"] = item["item_id"].replace(old, new, 1)
        for item in case["expected"]["atomic_labels"]:
            item["item_id"] = item["item_id"].replace(old, new, 1)
        if new == "qd-ho-14":
            case["form"]["false_premise_handling"] = None
            case["expected"]["false_premise_handling"] = "REJECTED_FALSE_PREMISE"
            case["threat_tags"].append("false_premise")
    return {
        "schema": "crane-evidence-calibration-agent-qualification-suite/v4",
        "suite_id": "evidence-calibration-agent-exact-task-v4-astra-final",
        "predecessor_disposition": "v3 invalidated by prospectively relevant reference-contract defect; raw outputs retained",
        "reference_correction": "The global-no-path geometry question is explicitly false-premise applicable; no Luna v3 score is reused.",
        "candidate_family_freshness": "gpt-6-astra has not received these qualification cases",
        "construction": "construction-defined labels; no prospective method output",
        "model_visible_gold": False,
        "case_count": len(cases),
        "split_counts": prior["split_counts"],
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v4.json")
    args = parser.parse_args()
    value = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(value) + b"\n")
    print(json.dumps({"output": str(args.output), "sha256": canonical_sha256(value), "case_count": value["case_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
