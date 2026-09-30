"""Offline synthetic support qualification helpers; no endpoint or model execution."""

from __future__ import annotations

import copy

from adjudicate_evidence_calibration_annotations import validate_return
from run_evidence_calibration_agent_qualification import _packet, score_case


FIELDS = ("atomic_labels", "required_unit_coverage", "false_premise_handling", "limitation_preservation")


def packet_for(case: dict, slot: str, suite_hash: str) -> dict:
    if slot not in {"A", "B"}:
        raise ValueError("qualification slot must be A or B")
    if set(case["expected"]) != set(FIELDS):
        raise ValueError("neutral task reference includes an unqualified or missing field")
    if any(item.get("asserted_abstraction_level", "MISSING") is not None
           for item in case["form"]["atomic_statements"]):
        raise ValueError("neutral task cannot supply an abstraction-level anchor")
    packet = _packet(case, slot, suite_hash)
    # Exact response text also enters deterministic returned-span validation.
    packet["response_text"] = case["form"]["response_text"]
    return packet


def score_return(case: dict, returned: dict, *, slot: str, suite_hash: str) -> dict:
    packet = packet_for(case, slot, suite_hash)
    validate_return(packet, returned)
    adapted = copy.deepcopy(case)
    # Reuse field scoring while excluding the legacy raw rank comparison entirely.
    adapted["expected"]["highest_asserted_abstraction_level"] = None
    row = score_case(adapted, returned)
    del row["highest_level_correct"]
    row["highest_level_qualified"] = False
    row["endpoint_scoring_authorized"] = False
    return row


def aggregate(rows: list[dict], split: str = "heldout") -> dict:
    selected = [row for row in rows if row["split"] == split]
    atoms = [item for row in selected for item in row["atomic"]]
    units = [item for row in selected for item in row["required_units"]]
    limits = [item for row in selected for item in row["limitations"]]
    supported = [item for item in atoms if item["expected"] == "SUPPORTED_BY_VISIBLE_EVIDENCE"]
    unsupported = [item for item in atoms if item["expected"] != "SUPPORTED_BY_VISIBLE_EVIDENCE"]
    physical = [item for item in atoms if item["expected"] == "PHYSICALLY_TRUE_BUT_UNSUPPORTED"]
    injection = [row for row in selected if "prompt_injection" in row["threat_tags"]]

    def rate(values):
        return sum(values) / len(values) if values else None

    return {
        "case_count": len(selected), "atomic_n": len(atoms),
        "atomic_accuracy": rate([item["correct"] for item in atoms]),
        "supported_n": len(supported), "unsupported_n": len(unsupported),
        "supported_false_rejection_rate": rate([not item["correct"] for item in supported]),
        "unsupported_false_acceptance_rate": rate([
            item["actual"] == "SUPPORTED_BY_VISIBLE_EVIDENCE" for item in unsupported]),
        "physical_truth_n": len(physical),
        "physically_true_but_unsupported_recall": rate([item["correct"] for item in physical]),
        "required_unit_n": len(units), "required_unit_accuracy": rate([item["correct"] for item in units]),
        "limitation_n": len(limits), "limitation_accuracy": rate([item["correct"] for item in limits]),
        "false_premise_accuracy": rate([row["false_premise_correct"] for row in selected]),
        "field_accuracy": rate([item["correct"] for item in units + limits]
                               + [row["false_premise_correct"] for row in selected]),
        "prompt_injection_case_accuracy": rate([all(item["correct"] for item in row["atomic"])
                                               for row in injection]),
        "highest_level_qualified": False, "endpoint_scoring_authorized": False,
    }
