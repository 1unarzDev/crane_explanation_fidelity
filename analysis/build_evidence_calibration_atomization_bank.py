#!/usr/bin/env python3
"""Blind the retained paired development answers for a separately qualified atomizer.

This builder performs no semantic extraction or scoring. It does not read evaluator truth.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path

from evidence_calibration_io import canonical_json_bytes, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
PILOT = "evidence-calibration-b2-b4-pilot-v1"


def _opaque(secret: str, *parts: str) -> str:
    return hmac.new(secret.encode(), "\x1f".join(parts).encode(), hashlib.sha256).hexdigest()[:32]


def build(secret: str, root: Path = ROOT) -> tuple[dict, dict]:
    if len(secret) < 32:
        raise ValueError("blinding secret must contain at least 32 characters")
    validation_path = root / f"manifests/study/{PILOT}-input-validation.json"
    status_path = root / f"manifests/study/{PILOT}-execution-status.json"
    validation = json.loads(validation_path.read_text())
    status = json.loads(status_path.read_text())
    if validation["pilot_id"] != PILOT or status["pilot_id"] != PILOT:
        raise ValueError("pilot manifest identity mismatch")
    failed = set(status["b2"]["failed_conditions"])
    expected = {cid for episode in validation["episodes"] for cid in episode["condition_ids"]}
    if len(expected) != 60 or len(failed) != 3 or not failed <= expected:
        raise ValueError("fixed pilot condition/failure inventory changed")
    entries, key_rows = [], []
    for episode in validation["episodes"]:
        run_id = episode["run_id"]
        complete_ladder = all(cid not in failed for cid in episode["condition_ids"])
        for diagnostic in episode["diagnostics"]:
            condition_id = diagnostic["condition_id"]
            if condition_id in failed:
                continue
            if diagnostic.get("b4_audit_status") != "ACCEPTED":
                raise ValueError(f"B4 final answer was not accepted: {condition_id}")
            b2_path = root / f"model_outputs/{PILOT}/b2/{condition_id}.json"
            b2 = json.loads(b2_path.read_text())
            index = episode["condition_ids"].index(condition_id)
            if (b2.get("condition_id") != condition_id or b2.get("method") != "B2"
                    or b2.get("method_packet_sha256") != episode["condition_packet_sha256s"][index]
                    or not b2.get("single_call_no_retry") or not b2.get("development_only")):
                raise ValueError(f"B2 envelope differs from fixed pilot: {condition_id}")
            answers = [("B2", b2["answer"], str(b2_path.relative_to(root))),
                       ("B4", diagnostic["b4_final_response"], str(validation_path.relative_to(root)))]
            for method, answer, source_path in answers:
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError(f"empty retained answer: {condition_id} {method}")
                opaque_id = "ax-" + _opaque(secret, PILOT, condition_id, method)
                entries.append({"opaque_response_id": opaque_id, "response_text": answer})
                key_rows.append({
                    "opaque_response_id": opaque_id,
                    "condition_id": condition_id,
                    "episode_id": run_id,
                    "method_id": method,
                    "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                    "source_path": source_path,
                    "paired_episode_analysis_eligible": complete_ladder,
                })
    if len(entries) != 114 or len({row["opaque_response_id"] for row in entries}) != 114:
        raise ValueError("paired response inventory is incomplete or duplicated")
    entries.sort(key=lambda row: _opaque(secret, "order", row["opaque_response_id"]))
    bank = {
        "schema": "crane-evidence-calibration-blinded-atomization-bank/v1",
        "task": "ATOMIC_DECOMPOSITION_ONLY",
        "development_only": True,
        "response_count": len(entries),
        "entries": entries,
    }
    key = {
        "schema": "crane-evidence-calibration-atomization-key/v1",
        "bank_sha256": canonical_sha256(bank),
        "pilot_input_validation_sha256": hashlib.sha256(validation_path.read_bytes()).hexdigest(),
        "pilot_execution_status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
        "join_after_atomic_inventory_validation": True,
        "entries": sorted(key_rows, key=lambda row: row["opaque_response_id"]),
        "confirmatory_independent_n": 0,
    }
    return bank, key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blinding-salt-file", type=Path, required=True)
    parser.add_argument("--bank-output", type=Path, required=True)
    parser.add_argument("--key-output", type=Path, required=True)
    args = parser.parse_args()
    bank, key = build(args.blinding_salt_file.read_text().strip())
    args.bank_output.write_bytes(canonical_json_bytes(bank) + b"\n")
    args.key_output.write_bytes(canonical_json_bytes(key) + b"\n")


if __name__ == "__main__":
    main()
