from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analysis.build_contract_complete_annotation_reference import build_reference
from analysis.build_contract_complete_annotation_reference_v2 import build_reference as build_reference_v2
from analysis.build_contract_complete_annotation_packet import decorate_pair
from analysis.build_diagnostic_annotation_packet import build_rows
from analysis.mask_command_motion_evidence_v2 import build_masked_export
from analysis.reference_command_motion_missing_odometry_v2 import build_reference as build_missing_reference

EXPORT = ROOT / "data/robot_visible/dev/cc-pilot-001/command-motion-diagnostic-v3.json"
INDEPENDENT = ROOT / "data/evaluator_only/dev/cc-pilot-001/command-motion-independent-reference-v1.json"
PAIR = ROOT / "model_outputs/contract-complete-diagnostic-communication-v1-pilot/response-pairs/cc-pilot-001.json"
PERSISTENT_EXPORT = ROOT / "data/robot_visible/dev/cc-pilot-002/command-motion-diagnostic-v3.json"
PERSISTENT_INDEPENDENT = ROOT / "data/evaluator_only/dev/cc-pilot-002/command-motion-independent-reference-v1.json"
CONTROL_EXPORT = ROOT / "data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json"
CONTROL_INDEPENDENT = ROOT / "data/evaluator_only/dev/cmv3-dev-003/command-motion-independent-reference-v1.json"


def artifacts() -> tuple[dict, dict]:
    export = json.loads(EXPORT.read_text())
    reference = build_reference(
        export,
        json.loads(INDEPENDENT.read_text()),
        family="measured_response_recovery",
        question_id="cc-measured-response-recovery-v1",
    )
    decorated = decorate_pair(
        json.loads(PAIR.read_text()), reference,
        question_id="cc-measured-response-recovery-v1",
    )
    return reference, decorated


def test_reference_is_exact_mqol_and_evidence_closed_for_both_answers() -> None:
    reference, _ = artifacts()
    units = {item["unit_id"]: item["text"] for item in reference["required_units"]}

    assert list(units) == ["M", "Q", "O", "L"]
    assert "0.260 m/s commanded and 0.2597 m/s measured" in units["Q"]
    assert "0.260 m/s commanded and 0.000 m/s measured" in units["Q"]
    assert "0.250 m/s commanded and 0.2497 m/s measured" in units["Q"]
    assert "Wait invocation caused recovery" in units["L"]
    assert "recovery caused the action outcome" in units["L"]
    supplemental = reference["allowed_evidence"]["independent_reference_computations"][1]
    assert supplemental["recovered_commanded_planar_speed_mps"] == 0.25
    assert supplemental["command_sample_count"] == 10
    assert reference["completeness_audit"]["valid_additional_claims_auditable"] is True


def test_packet_blinds_condition_and_preserves_verbatim_answers() -> None:
    reference, decorated = artifacts()
    rows, key = build_rows(decorated, reference, "fixed-test-secret")

    assert {item["condition"] for item in key} == {"P", "R"}
    assert all("condition" not in row for row in rows)
    assert all("provider" not in row for row in rows)
    assert all(row["complete_endpoint_unit_ids"] == ["M", "Q", "O", "L"] for row in rows)
    source_texts = {item["text"] for item in json.loads(PAIR.read_text())["outputs"]}
    assert {row["response_text"] for row in rows} == source_texts
    assert {item["response_id"] for item in key} == {row["response_id"] for row in rows}


def test_persistent_reference_has_exact_contract_units_and_comparisons() -> None:
    reference = build_reference(
        json.loads(PERSISTENT_EXPORT.read_text()),
        json.loads(PERSISTENT_INDEPENDENT.read_text()),
        family="persistent_command_motion_discrepancy",
        question_id="cc-persistent-command-motion-v1",
    )
    units = {item["unit_id"]: item["text"] for item in reference["required_units"]}

    assert list(units) == ["M", "Q", "O", "L"]
    assert "persistent command-to-measured-motion discrepancy" in units["M"]
    assert "0.260 m/s commanded and 0.2597 m/s measured" in units["Q"]
    assert "0.260 m/s commanded and 0.000 m/s measured" in units["Q"]
    assert "10.0--20.0 s" in units["Q"]
    assert "navigation action aborted" in units["O"]
    assert "does not uniquely identify" in units["L"]


def test_nominal_control_reference_is_mqol_but_not_primary_eligible() -> None:
    reference = build_reference(
        json.loads(CONTROL_EXPORT.read_text()),
        json.loads(CONTROL_INDEPENDENT.read_text()),
        family="nominal_false_premise_or_irrelevant_obstacle",
        question_id="cc-nominal-false-premise-v1",
    )
    units = {item["unit_id"]: item["text"] for item in reference["required_units"]}

    assert list(units) == ["M", "Q", "O", "L"]
    assert reference["primary_endpoint_eligible"] is False
    assert "complete_endpoint_unit_ids" not in reference
    assert "does not support" in units["M"]
    assert "0.260 m/s commanded" in units["Q"]
    assert "succeeded" in units["O"]
    assert "obstacle visibility" in units["L"]


def test_missing_evidence_control_uses_only_masked_independent_facts(tmp_path: Path) -> None:
    source = json.loads(PERSISTENT_EXPORT.read_text())
    masked = build_masked_export(source, "contract-missing-control-test")
    masked_path = tmp_path / "masked.json"
    masked_path.write_text(json.dumps(masked))
    missing = build_missing_reference(masked, masked_path)
    reference = build_reference(
        masked,
        missing,
        family="missing_decisive_or_ambiguous_evidence",
        question_id="cc-missing-decisive-evidence-v1",
    )
    units = {item["unit_id"]: item["text"] for item in reference["required_units"]}

    assert list(units) == ["M", "Q", "O", "L"]
    assert reference["primary_endpoint_eligible"] is False
    assert "complete_endpoint_unit_ids" not in reference
    assert "cannot be established" in units["M"]
    assert "0 independent odometry samples" in units["Q"]
    assert "recorded navigation action" in units["O"]
    assert "cannot establish a command-to-motion discrepancy" in units["L"]
    audit = reference["completeness_audit"]
    assert audit["paired_unmasked_export_excluded"] is True
    primitive = reference["allowed_evidence"]["primitive_diagnostic"]
    assert primitive["method_input"]["odometry_samples"] == []


def test_v2_missing_evidence_reference_builds_primary_mqol_packet(tmp_path: Path) -> None:
    source = json.loads(PERSISTENT_EXPORT.read_text())
    masked = build_masked_export(source, "contract-missing-primary-test")
    masked_path = tmp_path / "masked.json"
    masked_path.write_text(json.dumps(masked))
    missing = build_missing_reference(masked, masked_path)
    reference = build_reference_v2(
        masked,
        missing,
        family="missing_decisive_or_ambiguous_evidence",
        question_id="cc-missing-decisive-evidence-v1",
    )
    pair = json.loads(PAIR.read_text())
    pair["episode_id"] = masked["episode_id"]
    pair["family"] = "missing_decisive_or_ambiguous_evidence"
    for output in pair["outputs"]:
        output["text"] = "A bounded answer without governed citation identifiers."
    decorated = decorate_pair(
        pair,
        reference,
        question_id="cc-missing-decisive-evidence-v1",
    )

    rows, _ = build_rows(decorated, reference, "fixed-test-secret")

    assert reference["primary_endpoint_eligible"] is True
    assert reference["mechanism_unit_id"] == "M"
    assert reference["complete_endpoint_unit_ids"] == ["M", "Q", "O", "L"]
    assert all(row["mechanism_unit_id"] == "M" for row in rows)
    assert all(row["complete_endpoint_unit_ids"] == ["M", "Q", "O", "L"] for row in rows)
