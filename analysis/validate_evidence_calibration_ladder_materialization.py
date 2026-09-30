#!/usr/bin/env python3
"""Check prospective condition packets against the declared development ladder roles."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from evidence_calibration_io import canonical_sha256
from validate_evidence_calibration_ladders import ROOT, validate as validate_catalog


DEFAULT_CATALOG = ROOT / "configs/evidence_calibration_ladders_v1_development.json"


def validate_materialization(catalog: dict[str, Any], ladder_id: str,
                             bundle: list[dict[str, Any]]) -> dict[str, Any]:
    validate_catalog(ROOT, catalog)
    matches = [item for item in catalog["ladders"] if item["ladder_id"] == ladder_id]
    if len(matches) != 1:
        raise ValueError("materialized ladder has no unique catalog entry")
    ladder = matches[0]
    levels = ladder["levels"]
    if len(bundle) != len(levels):
        raise ValueError("materialized ladder level count differs from catalog")
    terminal = bundle[-1]["method_packet"]
    terminal_evidence = terminal["evidence"]
    if set(terminal_evidence) != set(ladder["terminal_evidence_roles"]):
        raise ValueError("unmasked source roles differ from catalog terminal roles")
    source_hash = canonical_sha256(terminal)
    previous_id = None
    for index, (entry, level) in enumerate(zip(bundle, levels)):
        condition, packet = entry["condition"], entry["method_packet"]
        expected_roles = set(level["available_evidence_roles"])
        if (condition["ladder_id"] != ladder_id or condition["level_index"] != index
                or not condition["condition_id"].endswith(f"-{level['condition_id_suffix']}")
                or condition["parent_condition_id"] != previous_id
                or set(condition["available_evidence_roles"]) != expected_roles
                or set(packet["evidence"]) != expected_roles):
            raise ValueError(f"materialized E{index} roles or condition identity differ from catalog")
        expected_packet = copy.deepcopy(terminal)
        expected_packet["evidence"] = {
            role: value for role, value in terminal_evidence.items() if role in expected_roles
        }
        expected_removed = {f"/evidence/{role}" for role in terminal_evidence if role not in expected_roles}
        if (condition["source_packet_sha256"] != source_hash
                or condition["method_packet_sha256"] != canonical_sha256(packet)
                or set(condition["removed_json_pointers"]) != expected_removed
                or packet != expected_packet):
            raise ValueError(f"materialized E{index} is not a byte-preserving removal from one source")
        previous_id = condition["condition_id"]
    return {
        "schema": "crane-evidence-calibration-ladder-materialization-audit/v1",
        "status": "PASS_CATALOG_BOUND_DEVELOPMENT_ONLY",
        "ladder_id": ladder_id,
        "levels": len(levels),
        "terminal_roles": sorted(terminal_evidence),
        "source_packet_sha256": source_hash,
        "confirmation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--ladder-id", required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    source = json.loads(args.bundle.read_text(encoding="utf-8"))
    bundle = source["conditions"] if isinstance(source, dict) else source
    print(json.dumps(validate_materialization(catalog, args.ladder_id, bundle), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
