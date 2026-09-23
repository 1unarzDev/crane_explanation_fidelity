import importlib.util
import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).parents[1] / "analysis" / "build_legacy_annotation_form.py"
SPEC = importlib.util.spec_from_file_location("build_legacy_annotation_form", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def packet_row(response_id="0123456789abcdef01234567"):
    return {
        "response_id": response_id,
        "question_kind": "recovery-mechanism",
        "question": "Why?",
        "gold_unit_inventory": ["a", "b"],
        "answerable_units_total": 2,
        "allowed_evidence": {"status": "aborted"},
        "response_text": "Answer.",
    }


def test_form_prefills_only_blinded_metadata_and_inventory():
    row = MODULE.build_form([packet_row()], "reviewer-a")[0]
    assert tuple(row) == MODULE.FORM_FIELDS
    assert row["response_id"] == "0123456789abcdef01234567"
    assert row["episode_id"] == MODULE.BLINDED_METADATA_SENTINEL
    assert row["scenario_family"] == MODULE.BLINDED_METADATA_SENTINEL
    assert row["condition_blinded_id"] == row["response_id"]
    assert row["question_kind"] == "recovery-mechanism"
    assert row["answerable_units_total"] == 2
    assert row["annotator_id"] == "reviewer-a"
    assert all(row[field] is None for field in set(MODULE.FORM_FIELDS) - MODULE.PREFILLED_FIELDS)
    assert "condition" not in row
    assert "response_text" not in row


def test_form_rejects_bad_id_duplicate_or_inventory():
    duplicate = packet_row()
    bad_inventory = packet_row("1123456789abcdef01234567")
    bad_inventory["answerable_units_total"] = 3
    for rows, message in (
        ([packet_row("condition-F")], "opaque"),
        ([duplicate, duplicate], "duplicate"),
        ([bad_inventory], "inventory"),
    ):
        try:
            MODULE.build_form(rows)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError(f"invalid packet accepted: {message}")


def test_cli_writes_all_required_fields(tmp_path):
    packet = tmp_path / "packet.jsonl"
    packet.write_text(json.dumps(packet_row()) + "\n", encoding="utf-8")
    output = tmp_path / "form.jsonl"
    subprocess.run(
        (
            sys.executable,
            str(SCRIPT),
            "--packet",
            str(packet),
            "--output",
            str(output),
            "--annotator-id",
            "reviewer-a",
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    row = json.loads(output.read_text(encoding="utf-8"))
    assert set(row) == set(MODULE.FORM_FIELDS)
    assert row["material_error"] is None
