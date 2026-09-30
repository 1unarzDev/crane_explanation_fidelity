#!/usr/bin/env python3
"""Revalidate only an existing continuation canary, without executing a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from continue_evidence_calibration_pilot_claim_roles import (
    CANARY, CONTINUATION, ROOT, digest, load_continuation,
)
from run_evidence_calibration_claim_role_v2r2_qualification import VALID_STATUS, call_once


def audit() -> dict:
    declaration, _, freeze, prompt, schema = load_continuation()
    output_root = ROOT / declaration["output_root"]
    output = output_root / "canary" / f"{CANARY['case_id']}.json"
    if not output.is_file():
        raise ValueError("continuation canary has no terminal record")
    def no_execution(*args, **kwargs):
        raise RuntimeError("read-only canary audit cannot execute a model")
    record = call_once(case=CANARY, slot="canary", freeze=freeze, prompt=prompt,
                       schema=schema, output_root=output_root,
                       cli_version=declaration["cli_version"], runner=no_execution)
    if record["status"] != VALID_STATUS or record.get("method_key_accessed") is not False:
        raise ValueError("continuation non-study schema canary did not pass")
    return {
        "schema": "crane-evidence-calibration-pilot-role-continuation-canary/v1",
        "recorded_date": "2026-09-30", "status": "PASS_BOUND_NON_STUDY_SCHEMA_CANARY",
        "declaration": {"path": str(CONTINUATION.relative_to(ROOT)), "raw_sha256": digest(CONTINUATION)},
        "auditor": {"path": "analysis/audit_evidence_calibration_pilot_role_continuation_canary.py",
                    "raw_sha256": digest(Path(__file__))},
        "call_record": {"path": str(output.relative_to(ROOT)), "raw_sha256": digest(output)},
        "intent": {"path": str(output.with_suffix('.intent').relative_to(ROOT)),
                   "raw_sha256": digest(output.with_suffix('.intent'))},
        "pilot_calls_in_canary_invocation": 0, "support_annotation_authorized": False,
        "endpoint_scoring_authorized": False, "p11_authorized": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.manifest and json.loads(args.manifest.read_text()) != result:
        raise ValueError("continuation canary differs from its bound manifest")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
