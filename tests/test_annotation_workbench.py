import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "annotation_workbench.py"
SPEC = importlib.util.spec_from_file_location("annotation_workbench", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def diagnostic_form(identifier="a" * 24):
    return {
        "response_id": identifier,
        "annotator_id": "ann-a",
        "supported_diagnostic_success": None,
        "material_error": None,
        "error_categories": None,
        "required_units_total": 2,
        "required_units_correct": None,
        "mechanism_correct": None,
        "failure_chain_correct": None,
        "qualification_correct": None,
        "causal_overclaim": None,
        "unnecessary_abstention": None,
        "evidence_citations_correct": None,
        "next_check_correct": None,
        "evidence_problem": None,
        "rationale": None,
    }


def diagnostic_packet(identifier="a" * 24):
    return {
        "schema": "crane-diagnostic-annotation-row/v1",
        "response_id": identifier,
        "question": "What happened?",
        "required_units": ["mechanism", "limit"],
        "response_text": "Bounded answer.",
    }


def test_diagnostic_entry_writes_complete_row_and_resumes_without_prompt(tmp_path):
    answers = iter(
        [
            "",  # open row
            "n",  # material error
            "2",  # units correct
            "y",  # mechanism
            "y",  # chain
            "y",  # qualification
            "n",  # causal overclaim
            "n",  # unnecessary abstention
            "y",  # citations
            "y",  # next check
            "n",  # evidence problem
            "y",  # supported success
            "Supported mechanism and limits.",
            "y",  # save
        ]
    )
    output = tmp_path / "completed.jsonl"
    completed, total = MODULE.run_workbench(
        [diagnostic_packet()],
        [diagnostic_form()],
        [],
        output=output,
        ask=lambda _: next(answers),
    )
    assert (completed, total) == (1, 1)
    row = json.loads(output.read_text())
    assert row["supported_diagnostic_success"] is True
    assert row["error_categories"] == []
    assert all(value is not None for value in row.values())

    def fail_prompt(_):
        raise AssertionError("completed row was prompted again")

    assert MODULE.run_workbench(
        [diagnostic_packet()],
        [diagnostic_form()],
        [row],
        output=output,
        ask=fail_prompt,
    ) == (1, 1)


def legacy_form(identifier="b" * 24):
    return {
        "response_id": identifier,
        "episode_id": "BLINDED_PENDING_KEY_JOIN",
        "scenario_family": "BLINDED_PENDING_KEY_JOIN",
        "question_kind": "recovery-mechanism",
        "condition_blinded_id": identifier,
        "material_error": None,
        "error_categories": None,
        "disposition": None,
        "substantive_answer": None,
        "requested_conclusion_answerable": None,
        "correct_abstention": None,
        "answerable_units_total": 2,
        "answerable_units_correct": None,
        "claim_count": None,
        "unsupported_claim_count": None,
        "source_reference_count": None,
        "correct_source_reference_count": None,
        "source_references_total_answerable": None,
        "physical_evidence_claim_count": None,
        "correct_physical_evidence_claim_count": None,
        "causal_overclaim": None,
        "qualification_correct": None,
        "evidence_problem": None,
        "annotator_id": "ann-a",
        "rationale": None,
    }


def test_legacy_entry_derives_substantive_answer_from_disposition(tmp_path):
    answers = iter(
        [
            "", "n", "full", "y", "n", "2", "2", "0", "1", "1", "1", "0", "0",
            "n", "y", "n", "Supported full answer.", "y",
        ]
    )
    packet = {
        "response_id": "b" * 24,
        "question_kind": "recovery-mechanism",
        "answerable_units_total": 2,
        "response_text": "Answer.",
    }
    output = tmp_path / "legacy.jsonl"
    MODULE.run_workbench(
        [packet], [legacy_form()], [], output=output, ask=lambda _: next(answers)
    )
    row = json.loads(output.read_text())
    assert row["disposition"] == "full"
    assert row["substantive_answer"] is True


def test_resume_rejects_prefilled_changes_and_partial_rows():
    template = diagnostic_form()
    changed = {**template, "annotator_id": "different"}
    changed.update({key: False for key, value in changed.items() if value is None})
    with pytest.raises(ValueError, match="annotator_id"):
        MODULE.validate_resume([template], [changed], "diagnostic")

    partial = dict(template)
    with pytest.raises(ValueError, match="incomplete"):
        MODULE.validate_resume([template], [partial], "diagnostic")


def test_resume_rejects_invalid_types_categories_and_counts():
    template = diagnostic_form()
    completed = {
        **template,
        "supported_diagnostic_success": True,
        "material_error": False,
        "error_categories": [],
        "required_units_correct": 2,
        "mechanism_correct": True,
        "failure_chain_correct": True,
        "qualification_correct": True,
        "causal_overclaim": False,
        "unnecessary_abstention": False,
        "evidence_citations_correct": True,
        "next_check_correct": True,
        "evidence_problem": False,
        "rationale": "Complete.",
    }
    bad_boolean = {**completed, "mechanism_correct": 1}
    with pytest.raises(ValueError, match="non-boolean"):
        MODULE.validate_resume([template], [bad_boolean], "diagnostic")

    bad_categories = {**completed, "material_error": True}
    with pytest.raises(ValueError, match="material-error categories"):
        MODULE.validate_resume([template], [bad_categories], "diagnostic")

    bad_count = {**completed, "required_units_correct": 3}
    with pytest.raises(ValueError, match="greater than"):
        MODULE.validate_resume([template], [bad_count], "diagnostic")


def test_run_rejects_mixed_rubrics_and_annotator_ids(tmp_path):
    with pytest.raises(ValueError, match="mixes"):
        MODULE.run_workbench(
            [diagnostic_packet(), {"response_id": "b" * 24}],
            [diagnostic_form(), legacy_form()],
            [],
            output=tmp_path / "mixed.jsonl",
            ask=lambda _: "q",
        )

    second = diagnostic_form("c" * 24)
    second["annotator_id"] = "ann-b"
    with pytest.raises(ValueError, match="multiple annotator"):
        MODULE.run_workbench(
            [diagnostic_packet(), diagnostic_packet("c" * 24)],
            [diagnostic_form(), second],
            [],
            output=tmp_path / "ids.jsonl",
            ask=lambda _: "q",
        )


def test_quit_before_first_row_does_not_create_output(tmp_path):
    output = tmp_path / "nothing.jsonl"
    assert MODULE.run_workbench(
        [diagnostic_packet()],
        [diagnostic_form()],
        [],
        output=output,
        ask=lambda _: "q",
    ) == (0, 1)
    assert not output.exists()
