#!/usr/bin/env python3
"""Reproduce the frozen synthetic stop frontier and references without model execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_calibration_support_execution import call_once, VALID
from run_evidence_calibration_combined_support_canary import ROOT, FREEZE, digest, load_bound, requests, result_for
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once


def audit(root: Path = ROOT, *, process_terminal: bool = False) -> dict:
    freeze, suite, prompt, annotation_schema, adjudication_schema = load_bound(root)
    output_root = root / freeze["output_root"]
    freeze_hash = digest(root / FREEZE)
    tasks = requests(suite, annotation_schema, adjudication_schema)
    records, bindings, counts = {}, {}, {"valid": 0, "failed": 0, "unknown_terminal": 0, "pending_live": 0, "never_launched": 0}
    stopped = False
    allowed = {"canary-result.json"}
    for task in tasks:
        allowed.update({f"{task['slot']}.json", f"{task['slot']}.intent"})
    if output_root.exists() and any(path.name not in allowed for path in output_root.iterdir()):
        raise ValueError("unexpected artifact in three-call canary directory")
    for task in tasks:
        slot = task["slot"]
        output, intent = output_root / f"{slot}.json", output_root / f"{slot}.intent"
        if stopped and (output.exists() or intent.exists()):
            raise ValueError("canary call exists beyond the frozen stop frontier")
        if slot == "C_CONSTRUCTED" and {"A", "B"}.issubset(records):
            if result_for(freeze, suite, records, freeze_hash)["status"] != "SUPPORT_PASS_C_NOT_RUN":
                stopped = True
                if output.exists() or intent.exists():
                    raise ValueError("constructed C launched after support reference failure")
        for name, path in ((f"{slot}_record", output), (f"{slot}_intent", intent)):
            if path.exists():
                bindings[name] = {"path": str(path.relative_to(root)), "raw_sha256": digest(path)}
        if not output.exists():
            counts[("unknown_terminal" if process_terminal else "pending_live") if intent.exists() else "never_launched"] += 1
            stopped = True
            continue
        if not intent.exists():
            raise ValueError("orphan retained canary return")
        def forbid(*args, **kwargs):
            raise RuntimeError("read-only canary audit attempted model execution")
        record = call_once(output=output, payload=task["payload"], schema=task["schema"], prompt=prompt,
                           freeze=freeze, freeze_sha256=freeze_hash, cli_version=freeze["cli_version"],
                           validate=task["validate"], runner=forbid)
        records[slot] = record
        if record["status"] == VALID:
            counts["valid"] += 1
        else:
            counts["failed"] += 1
            stopped = True
    result = result_for(freeze, suite, records, freeze_hash)
    result_path = output_root / "canary-result.json"
    if result_path.exists():
        if json.loads(result_path.read_text()) != result:
            raise ValueError("retained combined canary result does not reproduce")
        bindings["result"] = {"path": str(result_path.relative_to(root)), "raw_sha256": digest(result_path)}
    elif process_terminal and records and not counts["unknown_terminal"]:
        raise ValueError("terminal canary lacks summary; inspect terminal process before disposition")
    return {"schema": "crane-combined-support-canary-audit/v1", "freeze_raw_sha256": freeze_hash,
            "process_terminal_asserted": process_terminal, "status": result["status"], "counts": counts,
            "bindings": bindings, "result": result, "model_call_attempted": False,
            "pilot_annotation_authorized": False, "endpoint_scoring_authorized": False, "p11_authorized": False,
            "highest_level_qualified": False, "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-terminal", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and not args.process_terminal:
        parser.error("terminal snapshot requires explicitly verified process termination")
    report = audit(process_terminal=args.process_terminal)
    if args.output:
        _write_once(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
