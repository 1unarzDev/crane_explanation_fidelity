#!/usr/bin/env python3
"""Assemble reviewed method-blind atoms for development-only role classification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_manual_inventory import (
    BANK, RESPONSE_ID as MANUAL_ID, REVIEW as MANUAL_REVIEW, audit as audit_manual,
)
from audit_evidence_calibration_pilot_atomic_inventory_project_review_v2 import FORM_ROOT
from evidence_calibration_io import canonical_json_bytes
from run_evidence_calibration_pilot_atomization import ROOT


BASE = ROOT / "manifests/annotation"
REVIEW_PATHS = (
    BASE / "evidence-calibration-pilot-atomic-inventory-project-review-v2.json",
    BASE / "evidence-calibration-pilot-atomic-inventory-batch-9-review-v1.json",
    BASE / "evidence-calibration-pilot-remaining-complete-inventories-v1.json",
    BASE / "evidence-calibration-pilot-question-dependent-inventories-v1.json",
)
DEICTIC_REVIEW = BASE / "evidence-calibration-pilot-deictic-limitation-review-v1.json"
OUTPUT = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/claim-role-inputs-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atoms_from_row(form: dict, row: dict) -> list[dict]:
    candidates = form["atomic_claim_candidates"]
    replacements = row.get("approved_claim_text_replacements", {})
    atoms = []
    for index in row["accepted_candidate_indices"]:
        candidate = candidates[index]
        atoms.append({"candidate_index": index, "response_span": candidate["response_span"],
                      "claim_text": replacements.get(str(index), candidate["claim_text"])})
    for appended in row["appended_atomic_claims"]:
        atoms.append({"candidate_index": None, **appended})
    return atoms


def build() -> dict:
    audit_manual()
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    answers = {item["opaque_response_id"]: item["response_text"] for item in bank["entries"]}
    if len(answers) != 114:
        raise ValueError("blinded answer bank changed")
    atoms_by_id: dict[str, list[dict]] = {}
    for review_path in REVIEW_PATHS:
        review = json.loads(review_path.read_text(encoding="utf-8"))
        for row in review["rows"]:
            response_id = row["opaque_response_id"]
            if response_id in atoms_by_id:
                raise ValueError(f"overlapping base review: {response_id}")
            form = json.loads((FORM_ROOT / f"{response_id}.json").read_text(encoding="utf-8"))
            if form["response_text"] != answers[response_id]:
                raise ValueError(f"answer/form text mismatch: {response_id}")
            atoms_by_id[response_id] = _atoms_from_row(form, row)

    deictic = json.loads(DEICTIC_REVIEW.read_text(encoding="utf-8"))
    for row in deictic["rows"]:
        response_id = row["opaque_response_id"]
        form = json.loads((FORM_ROOT / f"{response_id}.json").read_text(encoding="utf-8"))
        if response_id not in atoms_by_id:
            if not row["newly_reviewed_response"]:
                raise ValueError(f"missing earlier reviewed deictic answer: {response_id}")
            atoms_by_id[response_id] = [
                {"candidate_index": item["candidate_index"], "response_span": item["response_span"],
                 "claim_text": item["claim_text"]} for item in form["atomic_claim_candidates"]
            ]
        else:
            if row["newly_reviewed_response"]:
                raise ValueError(f"deictic answer was reviewed twice: {response_id}")
        matching = [atom for atom in atoms_by_id[response_id]
                    if atom["candidate_index"] == row["deictic_candidate_index"]]
        if len(matching) != 1 or matching[0]["claim_text"] != row["original_candidate_claim_text"]:
            raise ValueError(f"deictic original claim changed: {response_id}")
        matching[0]["claim_text"] = row["reviewed_replacement_claim_text"]
        if row["append_delivery_atom"] is not None:
            atoms_by_id[response_id].append({"candidate_index": None, **row["append_delivery_atom"]})

    manual = json.loads(MANUAL_REVIEW.read_text(encoding="utf-8"))
    if MANUAL_ID in atoms_by_id:
        raise ValueError("manual answer overlaps extractor return")
    atoms_by_id[MANUAL_ID] = [
        {"candidate_index": None, **item} for item in manual["atomic_claims"]
    ]
    if set(atoms_by_id) != set(answers):
        raise ValueError("reviewed role inputs do not cover the complete blinded bank")

    entries = []
    for response_id in sorted(answers):
        response = answers[response_id]
        claims = []
        for index, atom in enumerate(atoms_by_id[response_id]):
            span, meaning = atom["response_span"], atom["claim_text"]
            if not span or span not in response or not meaning.strip():
                raise ValueError(f"reviewed role atom is absent or empty: {response_id}:{index}")
            item_id = "ri-" + hashlib.sha256(
                f"{response_id}\x1f{index}\x1f{span}\x1f{meaning}".encode("utf-8")
            ).hexdigest()[:20]
            claims.append({"item_id": item_id, "response_span": span, "claim_text": meaning})
        entries.append({"case_id": response_id, "response_text": response, "claims": claims})
    return {
        "schema": "crane-evidence-calibration-pilot-role-input-bundle/v1-development",
        "development_only": True,
        "task": "METHOD_BLIND_STANCE_KIND_POLARITY_ONLY",
        "blind_bank_raw_sha256": digest(BANK),
        "review_raw_sha256s": {str(path.relative_to(ROOT)): digest(path)
                               for path in (*REVIEW_PATHS, DEICTIC_REVIEW, MANUAL_REVIEW)},
        "response_count": len(entries),
        "atomic_claim_count": sum(len(entry["claims"]) for entry in entries),
        "manual_inventory_response_count": 1,
        "role_annotation_run_authorized": False,
        "endpoint_scoring_authorized": False,
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    raw = canonical_json_bytes(build()) + b"\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.read_bytes() != raw:
        raise ValueError("refusing to overwrite changed role input bundle")
    args.output.write_bytes(raw)
    print(json.dumps({"status": "ROLE_INPUTS_BUILT_NO_MODEL_CALL",
                      "output": str(args.output), "sha256": hashlib.sha256(raw).hexdigest()},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
