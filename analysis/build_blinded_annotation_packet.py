#!/usr/bin/env python3
"""Build a blinded annotation packet and its evaluator-only key.

``docs/ANNOTATION_GUIDE.md`` requires that annotators receive an opaque response ID, the question,
the allowed robot-visible evidence packet, the gold proposition inventory, and the response text,
and nothing that reveals condition, model, prompt, arm, evaluator-only intervention, or expected
method behavior. This builds exactly that, plus the separate key needed to join labels back after
adjudication.

Three things make the blinding real rather than nominal:

1. Condition-revealing envelope fields are dropped, not merely reordered. A G output carries
   ``checked_plan``, ``verification_accepted``, ``unsupported_sentences``, and
   ``used_template_fallback``; an F/H output carries ``disposition: uncontrolled``. None of those
   reach the annotator.
2. Response IDs are HMACs under a per-packet secret, so they are stable and verifiable but reveal
   no ordering, arm, condition, or episode. Rows are shuffled with a seed derived from that same
   secret, so packet order carries no signal either.
3. The key is written under ``data/evaluator_only/``, which is untracked and physically separate
   from everything an annotator is given.

Both arms can be pooled into one packet. Pooling improves blinding, and the key still separates
them afterwards; it never licenses treating the two arms as independent observations.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent

# The frozen inventories from docs/ANNOTATION_GUIDE.md. Counts are asserted by the test suite.
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

QUESTION_TEXT = {
    "recovery-mechanism": "Why did the autonomy software enter recovery?",
    "failure-cause": "Did a physical obstacle cause the navigation failure?",
}

# Every output key that could betray which condition produced a response.
CONDITION_REVEALING_KEYS = (
    "condition",
    "checked_plan",
    "verification_accepted",
    "unsupported_sentences",
    "used_template_fallback",
    "raw_candidate",
    "disposition",
    "fact_ids",
)

# Conditions that are deterministic smoke outputs rather than model evaluations.
NON_MODEL_CONDITIONS = frozenset({"A", "B", "C", "D", "E"})


def response_id(
    secret: str, arm: str, episode_id: str, question_kind: str, condition: str
) -> str:
    # The unit separator cannot occur in any component, so the message is unambiguous.
    message = f"{arm}\x1f{episode_id}\x1f{question_kind}\x1f{condition}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()[:24]


def evidence_packet(result: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Describe the allowed robot-visible evidence without revealing which condition saw what.

    Every condition in this study is audited to the same information units, so the annotator is
    given the shared parity-audited runtime presentation and its hash, never the per-condition
    workspace description.
    """

    parity = result["information_parity"]
    presentation = None
    candidate = data_root / result["question_kind"] / "runtime-presentation.json"
    if candidate.is_file():
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest == parity["runtime_presentation_sha256"]:
            presentation = json.loads(candidate.read_text(encoding="utf-8"))
    return {
        "runtime_presentation_sha256": parity["runtime_presentation_sha256"],
        "information_parity_audit_sha256": parity["audit_sha256"],
        "information_parity_accepted": parity["accepted"],
        "answerable_unit_count": parity["unit_count"],
        "runtime_presentation": presentation,
    }


def blinded_rows(
    results: list[tuple[str, Path, dict[str, Any]]],
    secret: str,
    include_non_model: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for arm, path, result in results:
        question_kind = result["question_kind"]
        if QUESTION_TEXT[question_kind] != result["question"]:
            raise SystemExit(f"unexpected question text in {path}")
        data_root = (
            WORKSPACE / "data/robot_visible/final" / result["episode_id"].split("-worker-")[0]
            / "parity"
        )
        packet = evidence_packet(result, data_root)
        for output in result["outputs"]:
            condition = output["condition"]
            if condition in NON_MODEL_CONDITIONS and not include_non_model:
                continue
            identifier = response_id(
                secret, arm, result["episode_id"], question_kind, condition
            )
            rows.append(
                {
                    "response_id": identifier,
                    "question_kind": question_kind,
                    "question": result["question"],
                    "gold_unit_inventory": UNIT_INVENTORIES[question_kind],
                    "answerable_units_total": len(UNIT_INVENTORIES[question_kind]),
                    "allowed_evidence": packet,
                    "response_text": output["text"],
                }
            )
            key.append(
                {
                    "response_id": identifier,
                    "arm": arm,
                    "episode_id": result["episode_id"],
                    "question_kind": question_kind,
                    "condition": condition,
                    "is_model_condition": condition not in NON_MODEL_CONDITIONS,
                    "model": result["model"],
                    "result_path": path.relative_to(WORKSPACE).as_posix(),
                }
            )
    return rows, key


def collect(roots: list[tuple[str, Path]]) -> list[tuple[str, Path, dict[str, Any]]]:
    collected = []
    for arm, root in roots:
        resolved = (WORKSPACE / root).resolve()
        if not resolved.is_dir():
            raise SystemExit(f"missing result root: {root}")
        for path in sorted(resolved.rglob("*.json")):
            collected.append((arm, path, json.loads(path.read_text(encoding="utf-8"))))
    if not collected:
        raise SystemExit("no result files found")
    return collected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arm",
        action="append",
        required=True,
        metavar="NAME=ROOT",
        help="arm label and its result root, e.g. luna=model_outputs/final",
    )
    parser.add_argument("--packet", required=True, type=Path, help="blinded packet JSONL to write")
    parser.add_argument("--key", required=True, type=Path, help="evaluator-only key JSON to write")
    parser.add_argument(
        "--include-non-model-conditions",
        action="store_true",
        help="also package the deterministic A--E smoke outputs embedded in each envelope",
    )
    args = parser.parse_args()

    roots = []
    for item in args.arm:
        if "=" not in item:
            parser.error(f"--arm expects NAME=ROOT, got {item}")
        name, _, root = item.partition("=")
        roots.append((name, Path(root)))

    packet_path = (WORKSPACE / args.packet).resolve()
    key_path = (WORKSPACE / args.key).resolve()
    for path in (packet_path, key_path):
        if path.exists():
            raise SystemExit(f"refusing existing file: {path}")
    if (WORKSPACE / "data/evaluator_only").resolve() not in key_path.parents:
        parser.error("--key must live under data/evaluator_only/")
    if (WORKSPACE / "data/evaluator_only").resolve() in packet_path.parents:
        parser.error("--packet must not live under data/evaluator_only/")

    secret = secrets.token_hex(32)
    rows, key = blinded_rows(collect(roots), secret, args.include_non_model_conditions)
    random.Random(hashlib.sha256(secret.encode()).digest()).shuffle(rows)

    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    leaked = sorted(
        {field for row in rows for field in CONDITION_REVEALING_KEYS if field in row}
    )
    if leaked:
        packet_path.unlink()
        raise SystemExit(f"blinding failed; condition-revealing fields present: {leaked}")

    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(
        json.dumps(
            {
                "schema": "crane-explain-blinded-annotation-key/v1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "EVALUATOR_ONLY_DO_NOT_SHARE_WITH_ANNOTATORS",
                "packet": packet_path.relative_to(WORKSPACE).as_posix(),
                "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                "response_id_secret": secret,
                "arms": {name: str(root) for name, root in roots},
                "responses": len(rows),
                "annotators_required": 2,
                "adjudicator_required_on_disagreement": True,
                "entries": sorted(key, key=lambda item: item["response_id"]),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "packet": packet_path.relative_to(WORKSPACE).as_posix(),
                "key": key_path.relative_to(WORKSPACE).as_posix(),
                "responses": len(rows),
                "arms": sorted({name for name, _ in roots}),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
