from __future__ import annotations

import json
from pathlib import Path

from analysis.build_contract_complete_annotation_reference import build_reference
from analysis.build_contract_complete_annotation_packet import decorate_pair
from analysis.build_diagnostic_annotation_packet import build_rows


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "data/robot_visible/dev/cc-pilot-001/command-motion-diagnostic-v3.json"
INDEPENDENT = ROOT / "data/evaluator_only/dev/cc-pilot-001/command-motion-independent-reference-v1.json"
PAIR = ROOT / "model_outputs/contract-complete-diagnostic-communication-v1-pilot/response-pairs/cc-pilot-001.json"
PERSISTENT_EXPORT = ROOT / "data/robot_visible/dev/cc-pilot-002/command-motion-diagnostic-v3.json"
PERSISTENT_INDEPENDENT = ROOT / "data/evaluator_only/dev/cc-pilot-002/command-motion-independent-reference-v1.json"


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
