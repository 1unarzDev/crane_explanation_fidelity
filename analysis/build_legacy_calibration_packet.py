#!/usr/bin/env python3
"""Build the frozen-rubric calibration packet from development-only responses."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import random
import secrets
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SOURCE = (
    ROOT / "model_outputs" / "dev" / "runtime-provenance-repilot-e043"
).resolve()
EVIDENCE_ROOT = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "land-nav-20260919-e043"
    / "runtime-provenance-repilot"
)
CONDITIONS = ("F", "G", "H")
UNIT_INVENTORIES = {
    "recovery-mechanism": [
        "concrete FollowPath failure transition(s)",
        "concrete recovery guard success(es)",
        "concrete Wait invocation(s)",
        "their order",
        "exact retained BT artifact identity",
        "relevant retry/Wait configuration",
        "physical cause remains unknown",
        "guard success is software eligibility rather than physical diagnosis",
    ],
    "failure-cause": [
        "terminal outcome",
        "recorded intermediate FollowPath failure(s)",
        "recorded Wait recovery invocation(s)",
        "absence of robot-visible physical-cause evidence",
        "obstacle or other physical causality remains unknown",
    ],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def opaque_id(secret: str, question_kind: str, condition: str) -> str:
    return hmac.new(
        secret.encode(), f"e043\0{question_kind}\0{condition}".encode(), hashlib.sha256
    ).hexdigest()[:24]


def build(
    results: list[dict[str, Any]], secret: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for result in results:
        if result.get("episode_id") != "land-nav-20260919-e043-worker-0":
            raise ValueError("calibration source is not the retained e043 development episode")
        if result.get("evaluator_truth_available_to_methods") is not False:
            raise ValueError("development result does not attest evaluator-truth exclusion")
        question_kind = result.get("question_kind")
        if question_kind not in UNIT_INVENTORIES:
            raise ValueError("unsupported calibration question")
        presentation_path = EVIDENCE_ROOT / question_kind / "runtime-presentation.json"
        expected_hash = result["information_parity"]["runtime_presentation_sha256"]
        if digest(presentation_path) != expected_hash:
            raise ValueError("calibration runtime presentation hash mismatch")
        outputs = {output["condition"]: output for output in result["outputs"]}
        if not set(CONDITIONS).issubset(outputs):
            raise ValueError("calibration result is missing F/G/H")
        allowed_evidence = {
            "runtime_presentation_sha256": expected_hash,
            "information_parity_audit_sha256": result["information_parity"]["audit_sha256"],
            "information_parity_accepted": result["information_parity"]["accepted"],
            "answerable_unit_count": len(UNIT_INVENTORIES[question_kind]),
            "runtime_presentation": json.loads(presentation_path.read_text(encoding="utf-8")),
        }
        for condition in CONDITIONS:
            identifier = opaque_id(secret, question_kind, condition)
            rows.append(
                {
                    "response_id": identifier,
                    "question_kind": question_kind,
                    "question": result["question"],
                    "gold_unit_inventory": UNIT_INVENTORIES[question_kind],
                    "answerable_units_total": len(UNIT_INVENTORIES[question_kind]),
                    "allowed_evidence": allowed_evidence,
                    "response_text": outputs[condition]["text"],
                }
            )
            key.append(
                {
                    "response_id": identifier,
                    "episode_id": result["episode_id"],
                    "question_kind": question_kind,
                    "condition": condition,
                    "model": result["model"],
                    "status": "DEVELOPMENT_CALIBRATION_ONLY",
                }
            )
    random.Random(hashlib.sha256(secret.encode()).digest()).shuffle(rows)
    return rows, sorted(key, key=lambda item: item["response_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    args = parser.parse_args()
    source = (ROOT / args.result_root).resolve(strict=True)
    if source != ALLOWED_SOURCE:
        parser.error("--result-root must be the retained development-only e043 source")
    packet = (ROOT / args.packet).resolve()
    key_path = (ROOT / args.key).resolve()
    if packet.exists() or key_path.exists():
        raise SystemExit("refusing to overwrite an existing calibration packet or key")
    evaluator_root = (ROOT / "data" / "evaluator_only").resolve()
    if evaluator_root not in key_path.parents or evaluator_root in packet.parents:
        parser.error("key must be evaluator-only and packet must be robot-visible")

    paths = sorted(source.glob("*.json"))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if len(results) != 2:
        raise SystemExit("expected exactly two retained e043 question results")
    secret = secrets.token_hex(32)
    rows, entries = build(results, secret)
    packet.parent.mkdir(parents=True, exist_ok=True)
    packet.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(
        json.dumps(
            {
                "schema": "crane-explain-legacy-calibration-key/v1",
                "status": "DEVELOPMENT_ONLY_REVEAL_AFTER_INDEPENDENT_CALIBRATION_PASSES",
                "packet": packet.relative_to(ROOT).as_posix(),
                "packet_sha256": digest(packet),
                "response_id_secret": secret,
                "source": source.relative_to(ROOT).as_posix(),
                "responses": len(rows),
                "entries": entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"packet": str(packet), "key": str(key_path), "responses": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
