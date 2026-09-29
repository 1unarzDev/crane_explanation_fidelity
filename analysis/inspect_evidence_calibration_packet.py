#!/usr/bin/env python3
"""Primitive read-only inventory tool shared by evidence-calibration methods."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def summarize(packet: dict) -> dict:
    evidence = packet["evidence"]
    output = {"episode_id": packet["episode_id"], "configuration_id": packet["configuration_id"],
              "question": packet["question"], "roles": {}}
    for role, value in evidence.items():
        row = {"evidence_ids": value.get("evidence_ids", [])}
        if "samples" in value:
            row["sample_count"] = len(value["samples"])
        if "action_status" in value:
            row["action_status"] = value["action_status"]
        if "execution_sequence" in value:
            row["execution_sequence"] = value["execution_sequence"]
        if "diagnostic_disposition" in value:
            row["diagnostic_disposition"] = value["diagnostic_disposition"]
            row["measurements"] = value.get("measurements", [])
        output["roles"][role] = row
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.packet.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
