import importlib.util
import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).parents[1] / "analysis" / "adjudicate_diagnostic_annotations.py"
SPEC = importlib.util.spec_from_file_location("adjudicate_diagnostic_annotations", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def row(response_id="r1", annotator="a", **overrides):
    value = {
        "response_id": response_id,
        "annotator_id": annotator,
        "supported_diagnostic_success": True,
        "material_error": False,
        "error_categories": [],
        "required_units_total": 2,
        "required_units_correct": 2,
        "mechanism_correct": True,
        "failure_chain_correct": True,
        "qualification_correct": True,
        "causal_overclaim": False,
        "unnecessary_abstention": False,
        "evidence_citations_correct": True,
        "next_check_correct": True,
        "evidence_problem": False,
        "rationale": "Supported mechanism and limits.",
    }
    value.update(overrides)
    return value


def test_validate_complete_consistent_pass():
    inventory = {"r1": 2, "r2": 2}
    rows = [row(), row("r2")]
    assert MODULE.validate_rows(rows, inventory, "a", expected_ids=set(inventory)) == "a"


def test_validate_rejects_success_with_material_error():
    bad = row(
        material_error=True,
        error_categories=["unsupported_causal_claim"],
    )
    try:
        MODULE.validate_rows([bad], {"r1": 2}, "a", expected_ids={"r1"})
    except ValueError as error:
        assert "supported success" in str(error)
    else:
        raise AssertionError("inconsistent supported success was accepted")


def test_validate_rejects_wrong_inventory_and_incomplete_pass():
    try:
        MODULE.validate_rows([row(required_units_total=1)], {"r1": 2, "r2": 2}, "a", expected_ids={"r1", "r2"})
    except ValueError as error:
        assert "packet has 2" in str(error)
        assert "incomplete" in str(error)
    else:
        raise AssertionError("wrong and incomplete pass was accepted")


def test_cli_completes_without_third_annotator_when_passes_agree(tmp_path):
    packet = tmp_path / "packet.jsonl"
    packet.write_text(json.dumps({"response_id": "r1", "required_units": ["a", "b"]}) + "\n")
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_text(json.dumps(row(annotator="a")) + "\n")
    second.write_text(json.dumps(row(annotator="b")) + "\n")
    output = tmp_path / "agreement.json"

    subprocess.run(
        (
            sys.executable,
            str(SCRIPT),
            "--packet", str(packet),
            "--annotator-a", str(first),
            "--annotator-b", str(second),
            "--output", str(output),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(output.read_text())
    assert payload["status"] == "COMPLETE"
    assert payload["condition_key_joined"] is False
    assert payload["labels"]["r1"]["annotator_id"] == "a"
