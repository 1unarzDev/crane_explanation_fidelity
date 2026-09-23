import importlib.util
import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).parents[1] / "analysis" / "build_diagnostic_annotation_form.py"
SPEC = importlib.util.spec_from_file_location("build_diagnostic_annotation_form", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def packet_row(response_id="0123456789abcdef01234567", units=None):
    return {
        "schema": "crane-diagnostic-annotation-row/v1",
        "response_id": response_id,
        "question": "Why?",
        "required_units": units or ["mechanism", "limit"],
        "allowed_evidence": {"status": "aborted"},
        "response_text": "A blinded response.",
    }


def test_form_preserves_only_opaque_id_count_and_unset_judgments():
    form = MODULE.build_form([packet_row()], "annotator-a")
    assert form[0]["response_id"] == "0123456789abcdef01234567"
    assert form[0]["annotator_id"] == "annotator-a"
    assert form[0]["required_units_total"] == 2
    assert all(form[0][field] is None for field in MODULE.JUDGMENT_FIELDS)
    assert set(form[0]) == set(MODULE.FORM_FIELDS)
    assert "question" not in form[0]
    assert "response_text" not in form[0]
    assert "condition" not in form[0]


def test_form_rejects_nonopaque_duplicate_or_invalid_inventory():
    for rows, message in (
        ([packet_row("condition-P")], "opaque"),
        ([packet_row(), packet_row()], "duplicate"),
        ([packet_row(units=[""])], "required_units"),
    ):
        try:
            MODULE.build_form(rows)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError(f"invalid packet accepted: {message}")


def test_cli_writes_a_validator_compatible_blank_form(tmp_path):
    packet = tmp_path / "packet.jsonl"
    packet.write_text(json.dumps(packet_row()) + "\n", encoding="utf-8")
    output = tmp_path / "annotator-a.jsonl"
    subprocess.run(
        (
            sys.executable,
            str(SCRIPT),
            "--packet",
            str(packet),
            "--output",
            str(output),
            "--annotator-id",
            "annotator-a",
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    row = json.loads(output.read_text(encoding="utf-8"))
    assert tuple(row) == MODULE.FORM_FIELDS
    assert row["required_units_total"] == 2
    assert row["mechanism_correct"] is None
