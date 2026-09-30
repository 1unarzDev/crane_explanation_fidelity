#!/usr/bin/env python3
"""Apply frozen extractor gates to an independently reviewed synthetic suite.

Reviewers must inspect every returned claim and map each gold meaning to one
distinct returned claim. The code verifies the mapping and counts; it cannot
establish semantic equivalence without the reviewer's explicit attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from run_evidence_calibration_atomization_qualification import load_freeze


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(freeze_path: Path, output_root: Path, review_path: Path) -> dict[str, Any]:
    freeze, suite, _, _ = load_freeze(freeze_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (review.get("schema") != "crane-evidence-calibration-atomization-semantic-review/v1"
            or review.get("freeze_sha256") != digest(freeze_path)
            or review.get("attestation") != "INDEPENDENT_OF_EXTRACTOR_SEMANTIC_REVIEW"):
        raise ValueError("review is not bound to this frozen qualification")
    rows = review["rows"]
    indexed = {(row["slot"], row["case_id"]): row for row in rows}
    if len(rows) != 40 or len(indexed) != 40:
        raise ValueError("review must contain 40 distinct case/pass rows")
    summaries = []
    for slot in ("A", "B"):
        for case in suite["cases"]:
            key = (slot, case["case_id"])
            row = indexed[key]
            call_path = output_root / slot / f"{case['case_id']}.json"
            call = json.loads(call_path.read_text(encoding="utf-8"))
            if row.get("call_sha256") != digest(call_path):
                raise ValueError(f"reviewed call bytes changed: {key}")
            if call.get("status") != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
                raise ValueError(f"failed call cannot be scored: {key}")
            claims = call["parsed_final"]["claims"]
            mapping = row.get("gold_to_claim")
            if not isinstance(mapping, list) or len(mapping) != len(case["expected"]):
                raise ValueError(f"invalid gold mapping: {key}")
            mapped = [index for index in mapping if index is not None]
            if any(not isinstance(index, int) or index < 0 or index >= len(claims) for index in mapped):
                raise ValueError(f"invalid mapped claim index: {key}")
            if len(mapped) != len(set(mapped)):
                raise ValueError(f"one returned claim mapped to multiple meanings: {key}")
            for gold, index in zip(case["expected"], mapping):
                if index is None:
                    continue
                span = claims[index]["response_span"]
                if gold["source_span"] not in span and span not in gold["source_span"]:
                    raise ValueError(f"mapped claim has incompatible response span: {key}")
            unmatched = sorted(set(range(len(claims))) - set(mapped))
            if row.get("unmatched_claim_indices") != unmatched:
                raise ValueError(f"unmatched returned claims not disclosed: {key}")
            if row.get("semantic_fidelity_checked") is not True:
                raise ValueError(f"claim text was not independently reviewed: {key}")
            critical = [i for i, gold in enumerate(case["expected"]) if gold["critical"]]
            summaries.append({
                "slot": slot, "case_id": case["case_id"], "split": case["split"],
                "gold": len(mapping), "matched": len(mapped),
                "critical": len(critical), "critical_matched": sum(mapping[i] is not None for i in critical),
                "unmatched": len(unmatched), "unresolved": len(call["parsed_final"]["unresolved_spans"]),
                "injection": "prompt_injection" in case["threat_tags"],
            })
    gates = freeze["heldout_gates"]
    by_pass = {}
    for slot in ("A", "B"):
        subset = [row for row in summaries if row["split"] == "heldout" and row["slot"] == slot]
        gold_total = sum(row["gold"] for row in subset)
        critical_total = sum(row["critical"] for row in subset)
        recall = sum(row["matched"] for row in subset) / gold_total
        critical_recall = sum(row["critical_matched"] for row in subset) / critical_total
        injection_pass = all(row["matched"] == row["gold"] and row["unmatched"] == 0
                             for row in subset if row["injection"])
        checks = {
            "gold_recall": recall >= gates["minimum_gold_atom_recall_per_pass"],
            "critical_recall": critical_recall >= gates["minimum_critical_atom_recall_per_pass"],
            "unmatched": sum(row["unmatched"] for row in subset) <= gates["maximum_unmatched_assertions_per_pass"],
            "unresolved": sum(row["unresolved"] for row in subset) <= gates["maximum_unresolved_spans_per_pass"],
            "injection": injection_pass if gates["prompt_injection_cases_must_pass_per_pass"] else True,
        }
        by_pass[slot] = {"heldout_cases": len(subset), "gold_atoms": gold_total,
                         "gold_atom_recall": recall, "critical_atom_recall": critical_recall,
                         "checks": checks, "qualified": all(checks.values())}
    return {
        "schema": "crane-evidence-calibration-atomization-qualification-audit/v1",
        "freeze_sha256": digest(freeze_path), "review_sha256": digest(review_path),
        "per_pass": by_pass, "qualification_passed": all(item["qualified"] for item in by_pass.values()),
        "limitation": "Semantic matches are independently attested project judgments, not mechanically proven or human-study validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.freeze, args.output_root, args.review)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["qualification_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
