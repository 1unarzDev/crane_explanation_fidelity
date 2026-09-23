import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "build_adjudication_handoff.py"
SPEC = importlib.util.spec_from_file_location("build_adjudication_handoff", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def diagnostic_row(identifier: str) -> dict:
    return {
        "schema": "crane-diagnostic-annotation-row/v1",
        "response_id": identifier,
        "required_units": ["mechanism", "limit"],
        "response_text": f"response {identifier}",
    }


def legacy_row(identifier: str) -> dict:
    return {
        "response_id": identifier,
        "question_kind": "recovery-mechanism",
        "gold_unit_inventory": ["mechanism", "limit"],
        "answerable_units_total": 2,
        "response_text": f"response {identifier}",
    }


def agreement(packet: Path, rubric: str, disagreements: list[str]) -> dict:
    return {
        "schema": MODULE.SCHEMAS[rubric],
        "status": "AWAITING_ADJUDICATION",
        "packet": str(packet.resolve()),
        "disagreements": disagreements,
        "unresolved_disagreements": disagreements,
        "condition_key_joined": False,
        "labels": None,
        # These sensitive fields may exist in the project-side report but must not be copied.
        "annotators": ["private-a", "private-b"],
    }


@pytest.mark.parametrize(
    ("rubric", "row_builder"),
    (("diagnostic", diagnostic_row), ("legacy", legacy_row)),
)
def test_builds_only_disagreements_without_prior_identities(tmp_path, rubric, row_builder):
    ids = ["1" * 24, "2" * 24, "3" * 24]
    packet = tmp_path / "packet.jsonl"
    write_jsonl(packet, [row_builder(identifier) for identifier in ids])
    report = tmp_path / "private-a-private-b-agreement.json"
    report.write_text(json.dumps(agreement(packet, rubric, [ids[1]])), encoding="utf-8")
    output = tmp_path / "handoff"

    manifest = MODULE.build_handoff(
        rubric=rubric,
        packet_path=packet.resolve(),
        agreement_path=report.resolve(),
        output_dir=output.resolve(),
        adjudicator_id="third-person",
    )

    packet_rows = MODULE.read_diagnostic_packet(output / "packet.jsonl") if rubric == "diagnostic" else MODULE.read_legacy_packet(output / "packet.jsonl")
    form_rows = [json.loads(line) for line in (output / "form.jsonl").read_text().splitlines()]
    assert [row["response_id"] for row in packet_rows] == [ids[1]]
    assert [row["response_id"] for row in form_rows] == [ids[1]]
    assert form_rows[0]["annotator_id"] == "third-person"
    combined = "\n".join(path.read_text() for path in output.iterdir())
    assert "private-a" not in combined
    assert "private-b" not in combined
    assert manifest["condition_key_included"] is False
    assert manifest["prior_annotator_labels_included"] is False
    assert manifest["prior_annotator_identities_included"] is False


def test_rejects_complete_report_unknown_id_and_existing_output(tmp_path):
    identifier = "a" * 24
    packet = tmp_path / "packet.jsonl"
    write_jsonl(packet, [diagnostic_row(identifier)])
    report = tmp_path / "agreement.json"
    payload = agreement(packet, "diagnostic", [identifier])
    payload["status"] = "COMPLETE"
    report.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="not awaiting"):
        MODULE.build_handoff(
            rubric="diagnostic",
            packet_path=packet.resolve(),
            agreement_path=report.resolve(),
            output_dir=(tmp_path / "complete").resolve(),
            adjudicator_id="third",
        )

    payload = agreement(packet, "diagnostic", ["b" * 24])
    report.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown responses"):
        MODULE.build_handoff(
            rubric="diagnostic",
            packet_path=packet.resolve(),
            agreement_path=report.resolve(),
            output_dir=(tmp_path / "unknown").resolve(),
            adjudicator_id="third",
        )

    payload = agreement(packet, "diagnostic", [identifier])
    report.write_text(json.dumps(payload), encoding="utf-8")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="overwrite"):
        MODULE.build_handoff(
            rubric="diagnostic",
            packet_path=packet.resolve(),
            agreement_path=report.resolve(),
            output_dir=existing.resolve(),
            adjudicator_id="third",
        )


def test_rejects_packet_report_mismatch_and_evaluator_output(tmp_path):
    identifier = "c" * 24
    packet = tmp_path / "packet.jsonl"
    other = tmp_path / "other.jsonl"
    write_jsonl(packet, [diagnostic_row(identifier)])
    write_jsonl(other, [diagnostic_row(identifier)])
    report = tmp_path / "agreement.json"
    report.write_text(
        json.dumps(agreement(other, "diagnostic", [identifier])), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="paths differ"):
        MODULE.build_handoff(
            rubric="diagnostic",
            packet_path=packet.resolve(),
            agreement_path=report.resolve(),
            output_dir=(tmp_path / "mismatch").resolve(),
            adjudicator_id="third",
        )

    evaluator_output = (MODULE.ROOT / "data/evaluator_only/adjudication-test-output").resolve()
    with pytest.raises(ValueError, match="must not be under"):
        MODULE.build_handoff(
            rubric="diagnostic",
            packet_path=packet.resolve(),
            agreement_path=report.resolve(),
            output_dir=evaluator_output,
            adjudicator_id="third",
        )
