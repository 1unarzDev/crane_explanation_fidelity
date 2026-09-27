#!/usr/bin/env python3
"""Build contract-complete references for either prospectively missing decisive stream."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import build_contract_complete_annotation_reference as v1


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _missing_command_reference(
    export: dict[str, Any], independent: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    if independent.get("schema") != "crane-command-motion-missing-command-reference/v1":
        raise ValueError("missing-command contract requires its independent masked reference")
    if export.get("episode_id") != independent.get("episode_id"):
        raise ValueError("contract export/reference episode mismatch")
    if independent.get("independent_of_proposed_diagnostic_result") is not True:
        raise ValueError("masked independent reference identity is not established")
    mask = export.get("evidence_mask") or {}
    if (
        mask.get("mask_id") != "remove-delivered-command-v1"
        or mask.get("paired_unmasked_export_available_to_methods") is not False
        or mask.get("independent_scenario_increment") != 1
    ):
        raise ValueError("missing-command export does not carry the frozen independent mask")
    diagnostic = export.get("diagnostic_result") or {}
    if diagnostic.get("disposition") != "insufficient":
        raise ValueError("missing-command diagnostic did not withhold the mechanism")
    observations = independent.get("observations") or {}
    answerability = independent.get("answerability") or {}
    commands = observations.get("delivered_command_sample_count")
    odometry = observations.get("independent_odometry_sample_count")
    status = observations.get("action_status")
    if (
        commands != 0
        or not isinstance(odometry, int)
        or isinstance(odometry, bool)
        or odometry <= 0
        or not isinstance(status, str)
        or answerability.get("command_motion_discrepancy") != "insufficient"
        or answerability.get("recorded_execution_sequence") != "answerable"
        or answerability.get("unique_physical_cause") != "insufficient"
    ):
        raise ValueError("masked independent reference has inconsistent answerability facts")
    values = {
        item.get("id"): item.get("value")
        for item in diagnostic.get("measurements", [])
        if isinstance(item, dict)
    }
    if (
        values.get("delivered_command_sample_count") != 0
        or values.get("independent_odometry_sample_count") != odometry
        or values.get("action_status") != status
    ):
        raise ValueError("masked production and independent facts disagree")
    texts = {
        "M": "A command-to-measured-motion mechanism cannot be established from the retained evidence.",
        "Q": (
            f"The record contains 0 delivered command samples and {odometry} independent "
            "odometry samples; delivered command is the decisive missing discriminator."
        ),
        "O": f"The recorded navigation action {status}.",
        "L": (
            "Without the missing delivered-command stream, measured motion and the recorded "
            "execution sequence cannot establish a requested-to-delivered-to-measured response "
            "chain, actuator acceptance, or a unique physical cause."
        ),
    }
    return {
        "schema": "crane-checked-composition-annotation-reference/v1",
        "visibility": "robot_visible_reference",
        "reference_status": "CONTRACT_COMPLETE_V2_INDEPENDENT_MISSING_COMMAND_REFERENCE_NOT_HUMAN_GOLD",
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "question": v1._question("missing_decisive_or_ambiguous_evidence")["text"],
        "diagnosable": False,
        "primary_endpoint_eligible": True,
        "mechanism_unit_id": "M",
        "complete_endpoint_unit_ids": ["M", "Q", "O", "L"],
        "required_units": [
            {"unit_id": code, "text": texts[code]} for code in ("M", "Q", "O", "L")
        ],
        "prohibited_claims": list(independent.get("prohibited_claims") or ()),
        "allowed_evidence_identifiers": v1._supporting_ids(export),
        "evidence_completeness": (
            "Complete for auditing the missing-command M/Q/O/L contract and additional claims "
            "available from the sole masked robot-visible export."
        ),
        "allowed_evidence": {
            "primitive_diagnostic": v1._blind(export),
            "independent_reference_computations": [v1._visible_independent(independent)],
            "reference_boundary": (
                "The independent calculation verifies absent delivered commands, retained odometry, "
                "and the execution outcome; it cannot establish the masked mechanism or unique cause."
            ),
        },
        "completeness_audit": {
            "accepted": True,
            "question_specific_MQOL_units": True,
            "full_robot_visible_method_evidence_included": True,
            "valid_additional_claims_auditable": True,
            "independent_quantities_checked": True,
            "evaluator_truth_excluded": True,
            "paired_unmasked_export_excluded": True,
        },
    }


def build_reference(
    export: dict[str, Any], independent: dict[str, Any], *, family: str, question_id: str
) -> dict[str, Any]:
    if independent.get("schema") == "crane-command-motion-missing-command-reference/v1":
        if family != "missing_decisive_or_ambiguous_evidence":
            raise ValueError("missing-command reference requires the evidence-limited family")
        return _missing_command_reference(export, independent, question_id=question_id)
    result = v1.build_reference(export, independent, family=family, question_id=question_id)
    if family == "missing_decisive_or_ambiguous_evidence":
        result = copy.deepcopy(result)
        result["primary_endpoint_eligible"] = True
        result["mechanism_unit_id"] = "M"
        result["complete_endpoint_unit_ids"] = ["M", "Q", "O", "L"]
        result["reference_status"] = (
            "CONTRACT_COMPLETE_V2_INDEPENDENT_MISSING_MOTION_REFERENCE_NOT_HUMAN_GOLD"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--family", required=True)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    result = build_reference(
        json.loads(args.export.read_text(encoding="utf-8")),
        json.loads(args.independent_reference.read_text(encoding="utf-8")),
        family=args.family,
        question_id=args.question_id,
    )
    result["inputs"] = {
        "robot_visible_export_sha256": _digest(args.export),
        "independent_reference_sha256": _digest(args.independent_reference),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
