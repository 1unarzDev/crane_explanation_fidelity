import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "process_annotation_returns.py"
SPEC = importlib.util.spec_from_file_location("process_annotation_returns", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def packet(identifier: str) -> dict:
    return {
        "schema": "crane-diagnostic-annotation-row/v1",
        "response_id": identifier,
        "question": "Why?",
        "question_kind": "diagnostic",
        "required_units": ["mechanism"],
        "response_text": "Answer.",
    }


def form(identifier: str, annotator: str, *, success: bool = True) -> dict:
    error = not success
    return {
        "response_id": identifier,
        "annotator_id": annotator,
        "supported_diagnostic_success": success,
        "material_error": error,
        "error_categories": ["incorrect_mechanism"] if error else [],
        "required_units_total": 1,
        "required_units_correct": int(success),
        "mechanism_correct": success,
        "failure_chain_correct": success,
        "qualification_correct": True,
        "causal_overclaim": False,
        "unnecessary_abstention": False,
        "evidence_citations_correct": True,
        "next_check_correct": True,
        "evidence_problem": False,
        "rationale": "Independent human judgment placeholder for integration test.",
    }


def setup_return(tmp_path: Path, name: str = "diagnostic-test.jsonl"):
    identifier = "a" * 24
    packets = tmp_path / "packets"
    forms_a = tmp_path / "a"
    forms_b = tmp_path / "b"
    write_jsonl(packets / name, [packet(identifier)])
    write_jsonl(forms_a / name, [form(identifier, "annotator-a")])
    write_jsonl(forms_b / name, [form(identifier, "annotator-b", success=False)])
    return packets, forms_a, forms_b, identifier


def test_processes_disagreement_transactionally_and_builds_blind_handoff(tmp_path):
    packets, forms_a, forms_b, identifier = setup_return(tmp_path)
    output = tmp_path / "processed"
    manifest = MODULE.process_returns(
        packet_dir=packets,
        annotator_a_dir=forms_a,
        annotator_b_dir=forms_b,
        output_dir=output,
        adjudicator_id="adjudicator-c",
        calibration_complete=False,
    )

    assert manifest["status"] == "AWAITING_ADJUDICATION"
    assert manifest["packet_count"] == 1
    assert manifest["response_count"] == 1
    assert manifest["condition_key_joined"] is False
    handoff = output / "adjudication-handoffs/diagnostic-test"
    assert json.loads((handoff / "packet.jsonl").read_text())["response_id"] == identifier
    combined = "\n".join(path.read_text() for path in handoff.iterdir())
    assert "annotator-a" not in combined
    assert "annotator-b" not in combined
    assert not any(path.name.endswith("key.json") for path in output.rglob("*"))


def test_complete_agreement_creates_no_adjudicator_handoff(tmp_path):
    packets, forms_a, forms_b, _ = setup_return(tmp_path)
    write_jsonl(forms_b / "diagnostic-test.jsonl", [form("a" * 24, "annotator-b")])
    output = tmp_path / "processed"
    manifest = MODULE.process_returns(
        packet_dir=packets,
        annotator_a_dir=forms_a,
        annotator_b_dir=forms_b,
        output_dir=output,
        adjudicator_id="adjudicator-c",
        calibration_complete=False,
    )
    assert manifest["status"] == "COMPLETE_AGREEMENT"
    assert manifest["packets_awaiting_adjudication"] == 0
    assert not any((output / "adjudication-handoffs").iterdir())


def test_requires_calibration_attestation_before_sealed_packet(tmp_path):
    packets, forms_a, forms_b, _ = setup_return(tmp_path, MODULE.SEALED_LEGACY)
    with pytest.raises(ValueError, match="calibration-complete"):
        MODULE.process_returns(
            packet_dir=packets,
            annotator_a_dir=forms_a,
            annotator_b_dir=forms_b,
            output_dir=tmp_path / "processed",
            adjudicator_id="adjudicator-c",
            calibration_complete=False,
        )


def test_calibration_disagreement_requires_discussion_not_third_person(tmp_path):
    packets, forms_a, forms_b, _ = setup_return(tmp_path, MODULE.LEGACY_CALIBRATION)
    output = tmp_path / "processed"
    manifest = MODULE.process_returns(
        packet_dir=packets,
        annotator_a_dir=forms_a,
        annotator_b_dir=forms_b,
        output_dir=output,
        adjudicator_id="adjudicator-c",
        calibration_complete=False,
    )
    assert manifest["status"] == "AWAITING_CALIBRATION_DISCUSSION"
    assert manifest["calibration_disagreements"] == 1
    assert manifest["packets_awaiting_adjudication"] == 0
    assert not any((output / "adjudication-handoffs").iterdir())


def test_invalid_form_inventory_leaves_no_partial_output(tmp_path):
    packets, forms_a, forms_b, _ = setup_return(tmp_path)
    write_jsonl(forms_b / "diagnostic-test.jsonl", [form("b" * 24, "annotator-b")])
    output = tmp_path / "processed"
    with pytest.raises(ValueError, match="inventory differs"):
        MODULE.process_returns(
            packet_dir=packets,
            annotator_a_dir=forms_a,
            annotator_b_dir=forms_b,
            output_dir=output,
            adjudicator_id="adjudicator-c",
            calibration_complete=False,
        )
    assert not output.exists()


def test_full_batch_rejects_extra_forms_but_only_selection_allows_them(tmp_path):
    packets, forms_a, forms_b, _ = setup_return(tmp_path)
    extra_name = "old-packet.jsonl"
    write_jsonl(forms_a / extra_name, [form("c" * 24, "annotator-a")])
    output = tmp_path / "processed"
    with pytest.raises(ValueError, match="unexpected returned forms"):
        MODULE.process_returns(
            packet_dir=packets,
            annotator_a_dir=forms_a,
            annotator_b_dir=forms_b,
            output_dir=output,
            adjudicator_id="adjudicator-c",
            calibration_complete=False,
        )

    manifest = MODULE.process_returns(
        packet_dir=packets,
        annotator_a_dir=forms_a,
        annotator_b_dir=forms_b,
        output_dir=output,
        adjudicator_id="adjudicator-c",
        calibration_complete=False,
        only=["diagnostic-test.jsonl"],
    )
    assert manifest["packet_count"] == 1
