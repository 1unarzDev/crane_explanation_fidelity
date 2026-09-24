#!/usr/bin/env python3
"""Build a blinded development packet for the prospective diagnostic study."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import random
import re
import secrets
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PACKET_KEYS = {
    "condition",
    "model",
    "provider",
    "raw_candidate",
    "used_template_fallback",
    "verification_accepted",
    "verification_policy",
}
EVIDENCE_IDENTIFIER = re.compile(r"\b[a-z0-9-]+-sha256:[a-f0-9]{64}\b", re.IGNORECASE)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def identifier(secret: str, episode_id: str, question_id: str, condition: str) -> str:
    message = f"{episode_id}\0{question_id}\0{condition}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()[:24]


def build_rows(
    result: dict[str, Any], reference: dict[str, Any], secret: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if result.get("evaluator_truth_available_to_methods") is not False:
        raise ValueError("result does not attest exclusion of evaluator truth")
    if reference.get("visibility") != "robot_visible_reference":
        raise ValueError("reference must be explicitly robot-visible")
    if result["episode_id"] != reference["episode_id"]:
        raise ValueError("result/reference episode mismatch")
    if result["question_id"] != reference["question_id"]:
        raise ValueError("result/reference question mismatch")

    declared_identifiers = reference.get("allowed_evidence_identifiers")
    result_identifiers = result.get("permitted_evidence_identifiers")
    if (declared_identifiers is None) != (result_identifiers is None):
        raise ValueError("result/reference citation-identifier contracts differ")
    if declared_identifiers is not None:
        if (
            not isinstance(declared_identifiers, list)
            or not declared_identifiers
            or any(
                not isinstance(item, str) or not EVIDENCE_IDENTIFIER.fullmatch(item)
                for item in declared_identifiers
            )
            or len(declared_identifiers) != len(set(declared_identifiers))
        ):
            raise ValueError("reference has invalid allowed evidence identifiers")
        if set(declared_identifiers) != set(result_identifiers):
            raise ValueError("result/reference permitted evidence identifiers differ")

    rows: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    seen_conditions: set[str] = set()
    for output in result["outputs"]:
        condition = output["condition"]
        if condition in seen_conditions:
            raise ValueError(f"duplicate condition: {condition}")
        seen_conditions.add(condition)
        response_id = identifier(
            secret, result["episode_id"], result["question_id"], condition
        )
        cited_identifiers = set(EVIDENCE_IDENTIFIER.findall(output["text"]))
        if declared_identifiers is not None and not cited_identifiers <= set(declared_identifiers):
            raise ValueError(
                f"{condition}: response cites identifiers outside the declared robot-visible set"
            )
        allowed_evidence = reference["allowed_evidence"]
        if declared_identifiers is not None:
            if not isinstance(allowed_evidence, dict) or "evidence_identifiers" in allowed_evidence:
                raise ValueError("reference allowed evidence cannot carry citation identifiers twice")
            allowed_evidence = {
                **allowed_evidence,
                "evidence_identifiers": declared_identifiers,
            }
        rows.append(
            {
                "schema": "crane-diagnostic-annotation-row/v1",
                "response_id": response_id,
                "question": result["question"],
                "question_kind": result["question_kind"],
                "diagnosable": reference["diagnosable"],
                "reference_status": reference["reference_status"],
                "required_units": reference["required_units"],
                "prohibited_claims": reference["prohibited_claims"],
                "allowed_evidence": allowed_evidence,
                "response_text": output["text"],
            }
        )
        key.append(
            {
                "response_id": response_id,
                "episode_id": result["episode_id"],
                "question_id": result["question_id"],
                "condition": condition,
                "provider": result["provider"],
                "model": result["model"],
                "final_output": True,
                "used_template_fallback": output.get("used_template_fallback", False),
                "verification_accepted": output.get("verification_accepted"),
            }
        )

    random.Random(hashlib.sha256(secret.encode()).digest()).shuffle(rows)
    leaked = sorted({field for row in rows for field in FORBIDDEN_PACKET_KEYS if field in row})
    if leaked:
        raise ValueError(f"condition-revealing packet fields: {leaked}")
    return rows, sorted(key, key=lambda item: item["response_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    args = parser.parse_args()

    paths = {
        name: (ROOT / value).resolve()
        for name, value in vars(args).items()
        if isinstance(value, Path)
    }
    if paths["packet"].exists() or paths["key"].exists():
        raise SystemExit("refusing to overwrite an existing packet or key")
    evaluator_root = (ROOT / "data" / "evaluator_only").resolve()
    if evaluator_root not in paths["key"].parents:
        parser.error("--key must be under data/evaluator_only/")
    if evaluator_root in paths["packet"].parents:
        parser.error("--packet must not be under data/evaluator_only/")

    secret = secrets.token_hex(32)
    result = load(paths["result"])
    reference = load(paths["reference"])
    rows, entries = build_rows(result, reference, secret)
    paths["packet"].parent.mkdir(parents=True, exist_ok=True)
    paths["packet"].write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    paths["key"].parent.mkdir(parents=True, exist_ok=True)
    paths["key"].write_text(
        json.dumps(
            {
                "schema": "crane-diagnostic-annotation-key/v1",
                "status": "DEVELOPMENT_ONLY_EVALUATOR_ONLY",
                "packet": paths["packet"].relative_to(ROOT).as_posix(),
                "packet_sha256": hashlib.sha256(paths["packet"].read_bytes()).hexdigest(),
                "response_id_secret": secret,
                "reference": paths["reference"].relative_to(ROOT).as_posix(),
                "reference_sha256": hashlib.sha256(paths["reference"].read_bytes()).hexdigest(),
                "result": paths["result"].relative_to(ROOT).as_posix(),
                "result_sha256": hashlib.sha256(paths["result"].read_bytes()).hexdigest(),
                "annotators_required": 2,
                "adjudicator_required_on_disagreement": True,
                "entries": entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"packet": str(paths["packet"]), "key": str(paths["key"]), "responses": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
