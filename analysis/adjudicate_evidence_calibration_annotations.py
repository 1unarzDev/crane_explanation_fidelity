#!/usr/bin/env python3
"""Validate, compare, and adjudicate blinded evidence-calibration annotations."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from evidence_calibration_io import canonical_json_bytes, canonical_sha256


RETURN_SCHEMA = "crane-blinded-atomic-annotation-return/v1"
REPORT_SCHEMA = "crane-blinded-atomic-annotation-agreement/v1"
ADJUDICATION_SCHEMA = "crane-blinded-atomic-annotation-adjudication/v1"
FINAL_SCHEMA = "crane-blinded-atomic-annotation-final/v1"
HANDOFF_SCHEMA = "crane-blinded-atomic-annotation-adjudication-handoff/v1"


def _item_id(prefix: str, text: str) -> str:
    return prefix + hashlib.sha256(text.encode()).hexdigest()[:24]


def _form(packet_set: dict[str, Any], form_id: str) -> dict[str, Any]:
    matches = [item for item in packet_set["forms"] if item["form_id"] == form_id]
    if len(matches) != 1:
        raise ValueError("annotation return does not name exactly one packet form")
    return matches[0]


def validate_return(packet_set: dict[str, Any], returned: dict[str, Any]) -> dict[str, Any]:
    response_text = packet_set.get("response_text")
    if "response_text" in packet_set and (not isinstance(response_text, str) or not response_text.strip()):
        raise ValueError("packet response text is invalid")
    required = {
        "schema", "packet_set_sha256", "form_id", "packet_id", "annotator_slot",
        "annotator_id", "atomic_labels", "required_unit_coverage",
        "highest_asserted_abstraction_level", "limitation_preservation",
        "false_premise_handling", "annotator_attestation",
    }
    if set(returned) != required or returned.get("schema") != RETURN_SCHEMA:
        raise ValueError("annotation return has missing or unknown fields")
    if returned["packet_set_sha256"] != canonical_sha256(packet_set):
        raise ValueError("annotation return packet hash mismatch")
    form = _form(packet_set, returned["form_id"])
    if returned["packet_id"] != form["packet_id"]:
        raise ValueError("annotation return packet ID mismatch")
    if returned["annotator_slot"] != form["annotator_slot"]:
        raise ValueError("annotation return slot mismatch")
    if not isinstance(returned["annotator_id"], str) or not returned["annotator_id"].strip():
        raise ValueError("annotator ID is required")
    if returned["annotator_attestation"] != "INDEPENDENT_BLINDED_COMPLETE":
        raise ValueError("independent blinded attestation is required")

    allowed_labels = set(form["allowed_claim_labels"])
    expected_claims = {item["item_id"] for item in form["atomic_statements"]}
    actual_claims = {item.get("item_id") for item in returned["atomic_labels"]}
    if actual_claims != expected_claims or len(actual_claims) != len(returned["atomic_labels"]):
        raise ValueError("claim annotations must cover every opaque item exactly once")
    for item in returned["atomic_labels"]:
        if set(item) != {"item_id", "label", "annotation_notes"}:
            raise ValueError("claim annotation has missing or unknown fields")
        if item["label"] not in allowed_labels:
            raise ValueError("claim annotation uses an undeclared label")

    expected_units = {item["unit_prompt"] for item in form["required_unit_coverage"]}
    actual_units = {item.get("unit_prompt") for item in returned["required_unit_coverage"]}
    if actual_units != expected_units or len(actual_units) != len(returned["required_unit_coverage"]):
        raise ValueError("required-unit annotations must cover every prompt exactly once")
    for item in returned["required_unit_coverage"]:
        if set(item) != {"unit_prompt", "communicated", "response_span"}:
            raise ValueError("required-unit annotation has missing or unknown fields")
        if not isinstance(item["communicated"], bool):
            raise ValueError("required-unit communicated must be boolean")
        if item["communicated"] and (not isinstance(item["response_span"], str) or not item["response_span"]):
            raise ValueError("communicated required unit needs an exact response span")
        if item["communicated"] and response_text is not None and item["response_span"] not in response_text:
            raise ValueError("required-unit response span is not in the exact response text")

    level = returned["highest_asserted_abstraction_level"]
    if level not in form["abstraction_level_options"]:
        raise ValueError("highest asserted abstraction level is outside the packet options")

    expected_limits = {item["limitation_prompt"] for item in form["limitation_preservation"]}
    actual_limits = {item.get("limitation_prompt") for item in returned["limitation_preservation"]}
    if actual_limits != expected_limits or len(actual_limits) != len(returned["limitation_preservation"]):
        raise ValueError("limitation annotations must cover every prompt exactly once")
    for item in returned["limitation_preservation"]:
        if set(item) != {"limitation_prompt", "preserved", "response_span"}:
            raise ValueError("limitation annotation has missing or unknown fields")
        if not isinstance(item["preserved"], bool):
            raise ValueError("limitation preserved must be boolean")
        if item["preserved"] and (not isinstance(item["response_span"], str) or not item["response_span"]):
            raise ValueError("preserved limitation needs an exact response span")
        if item["preserved"] and response_text is not None and item["response_span"] not in response_text:
            raise ValueError("limitation response span is not in the exact response text")

    false_premise = returned["false_premise_handling"]
    allowed_false_premise = {
        "NOT_APPLICABLE", "REJECTED_FALSE_PREMISE", "ACCEPTED_FALSE_PREMISE",
        "PARTIAL_OR_AMBIGUOUS", "UNINTERPRETABLE",
    }
    if false_premise not in allowed_false_premise:
        raise ValueError("false-premise label is invalid")
    if form["false_premise_handling"] == "NOT_APPLICABLE" and false_premise != "NOT_APPLICABLE":
        raise ValueError("false-premise label must remain not applicable")
    return returned


def _values(returned: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in returned["atomic_labels"]:
        values[f"claim:{item['item_id']}"] = item["label"]
    for item in returned["required_unit_coverage"]:
        values[f"unit:{_item_id('u-', item['unit_prompt'])}"] = item["communicated"]
    values["highest_asserted_abstraction_level"] = returned["highest_asserted_abstraction_level"]
    for item in returned["limitation_preservation"]:
        values[f"limitation:{_item_id('l-', item['limitation_prompt'])}"] = item["preserved"]
    values["false_premise_handling"] = returned["false_premise_handling"]
    return values


def _claim_kappa(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    a = {item["item_id"]: item["label"] for item in first["atomic_labels"]}
    b = {item["item_id"]: item["label"] for item in second["atomic_labels"]}
    count = len(a)
    observed = sum(a[key] == b[key] for key in a) / count
    first_counts, second_counts = Counter(a.values()), Counter(b.values())
    labels = set(first_counts) | set(second_counts)
    expected = sum(first_counts[label] * second_counts[label] for label in labels) / (count * count)
    kappa = None if abs(1.0 - expected) < 1e-12 else (observed - expected) / (1.0 - expected)
    return {"claim_count": count, "observed_agreement": observed,
            "expected_agreement": expected, "cohen_kappa": kappa}


def compare(packet_set: dict[str, Any], first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    validate_return(packet_set, first)
    validate_return(packet_set, second)
    if first["annotator_slot"] == second["annotator_slot"]:
        raise ValueError("independent returns must use different annotator slots")
    if first["annotator_id"] == second["annotator_id"]:
        raise ValueError("the same person cannot fill both independent returns")
    a, b = _values(first), _values(second)
    if set(a) != set(b):
        raise ValueError("annotation returns expose different decision inventories")
    disagreements = []
    for key in sorted(a):
        if a[key] != b[key]:
            disagreements.append({
                "disagreement_id": _item_id("d-", key), "decision_key": key,
                "annotator_a_value": a[key], "annotator_b_value": b[key],
            })
    return {
        "schema": REPORT_SCHEMA,
        "packet_set_sha256": canonical_sha256(packet_set),
        "packet_id": first["packet_id"],
        "annotator_ids": [first["annotator_id"], second["annotator_id"]],
        "decision_count": len(a),
        "agreement_count": len(a) - len(disagreements),
        "disagreement_count": len(disagreements),
        "claim_label_agreement": _claim_kappa(first, second),
        "agreed_decisions": {key: a[key] for key in sorted(a) if a[key] == b[key]},
        "disagreements": disagreements,
        "method_identity_visible": False,
        "condition_key_joined": False,
        "scientific_sample_count_increment": 0,
    }


def build_handoff(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("schema") != REPORT_SCHEMA:
        raise ValueError("unsupported agreement report schema")
    return {
        "schema": HANDOFF_SCHEMA,
        "agreement_report_sha256": canonical_sha256(report),
        "packet_set_sha256": report["packet_set_sha256"],
        "packet_id": report["packet_id"],
        "disagreement_count": report["disagreement_count"],
        "disagreements": report["disagreements"],
        "annotator_identities_visible": False,
        "agreed_decisions_visible": False,
        "method_identity_visible": False,
        "condition_key_joined": False,
    }


def finalize(report: dict[str, Any], adjudication: dict[str, Any]) -> dict[str, Any]:
    required = {"schema", "agreement_report_sha256", "adjudicator_id", "decisions", "attestation"}
    if set(adjudication) != required or adjudication.get("schema") != ADJUDICATION_SCHEMA:
        raise ValueError("adjudication has missing or unknown fields")
    if adjudication["agreement_report_sha256"] != canonical_sha256(report):
        raise ValueError("adjudication report hash mismatch")
    if adjudication["adjudicator_id"] in report["annotator_ids"]:
        raise ValueError("adjudicator must be distinct from both annotators")
    if adjudication["attestation"] != "DISAGREEMENT_ONLY_BLINDED_COMPLETE":
        raise ValueError("blinded disagreement-only attestation is required")
    expected = {item["disagreement_id"]: item for item in report["disagreements"]}
    supplied = {item.get("disagreement_id"): item for item in adjudication["decisions"]}
    if set(expected) != set(supplied) or len(supplied) != len(adjudication["decisions"]):
        raise ValueError("adjudication must cover exactly the disagreement inventory")
    final = dict(report["agreed_decisions"])
    for disagreement_id, source in expected.items():
        item = supplied[disagreement_id]
        if set(item) != {"disagreement_id", "selected_value", "rationale"}:
            raise ValueError("adjudication decision has missing or unknown fields")
        if item["selected_value"] not in (source["annotator_a_value"], source["annotator_b_value"]):
            raise ValueError("adjudicator must select one independently supplied value")
        if not isinstance(item["rationale"], str) or not item["rationale"].strip():
            raise ValueError("adjudication rationale is required")
        final[source["decision_key"]] = item["selected_value"]
    return {
        "schema": FINAL_SCHEMA,
        "packet_set_sha256": report["packet_set_sha256"],
        "packet_id": report["packet_id"],
        "agreement_report_sha256": canonical_sha256(report),
        "adjudicator_id": adjudication["adjudicator_id"],
        "final_decisions": {key: final[key] for key in sorted(final)},
        "original_disagreements_preserved": report["disagreements"],
        "method_identity_visible": False,
        "condition_key_joined": False,
        "ready_for_separate_key_join": True,
        "scientific_sample_count_increment": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-set", type=Path, required=True)
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--agreement-output", type=Path, required=True)
    parser.add_argument("--handoff-output", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--final-output", type=Path)
    args = parser.parse_args()
    packet_set = json.loads(args.packet_set.read_text(encoding="utf-8"))
    first = json.loads(args.annotator_a.read_text(encoding="utf-8"))
    second = json.loads(args.annotator_b.read_text(encoding="utf-8"))
    report = compare(packet_set, first, second)
    args.agreement_output.write_bytes(canonical_json_bytes(report) + b"\n")
    if args.handoff_output:
        args.handoff_output.write_bytes(canonical_json_bytes(build_handoff(report)) + b"\n")
    if args.adjudication:
        if not args.final_output:
            parser.error("--final-output is required with --adjudication")
        decision = json.loads(args.adjudication.read_text(encoding="utf-8"))
        args.final_output.write_bytes(canonical_json_bytes(finalize(report, decision)) + b"\n")
    elif args.final_output:
        parser.error("--final-output requires --adjudication")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
