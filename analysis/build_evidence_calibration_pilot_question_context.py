#!/usr/bin/env python3
"""Expose the registered question for three blinded one-word answers only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evidence_calibration_io import canonical_json_bytes
from audit_evidence_calibration_pilot_remaining_complete_inventories import REVIEW as PRIOR, digest
from run_evidence_calibration_pilot_atomization import ROOT


BANK = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/atomization-bank.json"
VALIDATION = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json"
QUESTION_SOURCE = ROOT / "analysis/validate_evidence_calibration_pilot_inputs.py"
OUTPUT = ROOT / "manifests/annotation/evidence-calibration-pilot-question-only-context-v1.json"
QUESTION = (
    "The episode succeeded; was there nevertheless a navigation failure, "
    "and what does the evidence support?"
)


def build() -> dict:
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    target_ids = prior["remaining_question_dependent_response_ids"]
    if len(target_ids) != 3 or target_ids != sorted(set(target_ids)):
        raise ValueError("expected exactly three bound unresolved response IDs")
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    answers = {entry["opaque_response_id"]: entry["response_text"] for entry in bank["entries"]}
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if QUESTION not in QUESTION_SOURCE.read_text(encoding="utf-8").replace('\\\n', ''):
        # The exact string is defined in the original pilot-input builder. A source
        # change requires a new context handoff rather than a guessed question.
        raise ValueError("registered nominal question no longer matches its source")
    rows = []
    for response_id in target_ids:
        answer = answers[response_id]
        matches = []
        for episode in validation["episodes"]:
            for diagnostic in episode["diagnostics"]:
                condition_id = diagnostic["condition_id"]
                if diagnostic["b4_final_response"] == answer:
                    matches.append(episode["family"])
                b2_path = ROOT / f"model_outputs/evidence-calibration-b2-b4-pilot-v1/b2/{condition_id}.json"
                if b2_path.is_file() and json.loads(b2_path.read_text(encoding="utf-8"))["answer"] == answer:
                    matches.append(episode["family"])
        if matches != ["nominal_false_premise"]:
            raise ValueError(f"one-word answer has non-unique or non-nominal source: {response_id}")
        rows.append({
            "opaque_response_id": response_id,
            "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            "question_instruction": QUESTION,
        })
    return {
        "schema": "crane-evidence-calibration-pilot-question-only-context/v1-development",
        "recorded_date": "2026-09-30",
        "status": "QUESTION_ONLY_CONTEXT_NO_METHOD_JOIN",
        "previous_review_raw_sha256": digest(PRIOR),
        "blind_bank_raw_sha256": digest(BANK),
        "pilot_input_validation_raw_sha256": digest(VALIDATION),
        "question_source_raw_sha256": digest(QUESTION_SOURCE),
        "rows": rows,
        "evaluator_key_read": False,
        "method_identity_exposed_to_reviewer": False,
        "support_annotation_authorized": False,
        "endpoint_scoring_authorized": False,
        "p11_authorized": False,
        "confirmation_independent_n": 0,
        "replication_independent_n": 0,
    }


def audit(path: Path = OUTPUT) -> dict:
    actual = json.loads(path.read_text(encoding="utf-8"))
    expected = build()
    if actual != expected:
        raise ValueError("question-only context differs from exact blinded development sources")
    return {"status": "PASS_QUESTION_ONLY_NO_METHOD_JOIN", "response_count": 3,
            "support_annotation_authorized": False, "p11_authorized": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        data = canonical_json_bytes(build()) + b"\n"
        if OUTPUT.exists() and OUTPUT.read_bytes() != data:
            raise ValueError("refusing to overwrite changed question-only context")
        OUTPUT.write_bytes(data)
    print(json.dumps(audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
