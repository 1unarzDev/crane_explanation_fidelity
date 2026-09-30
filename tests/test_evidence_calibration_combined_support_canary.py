"""Synthetic offline gate checks. Mocked annotations are never observed evidence."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import run_evidence_calibration_combined_support_canary as module
import audit_evidence_calibration_combined_support_canary as auditor
from build_evidence_calibration_combined_support_canary import build
from adjudicate_evidence_calibration_annotations import compare
from evidence_calibration_support_execution import VALID, call_once
from evidence_calibration_io import canonical_sha256


def records(suite):
    return {slot: {"status": VALID, "parsed_final": copy.deepcopy(suite["support_references"][slot])} for slot in ("A", "B")} | {
        "C_CONSTRUCTED": {"status": VALID, "parsed_final": copy.deepcopy(suite["adjudication_reference"])}}


def test_frozen_components_reproduce_and_payloads_exclude_reference_answers():
    freeze, suite, _, a_schema, c_schema = module.load_bound()
    assert suite == build()
    tasks = module.requests(suite, a_schema, c_schema)
    assert [task["slot"] for task in tasks] == ["A", "B", "C_CONSTRUCTED"]
    for task in tasks:
        text = json.dumps(task["payload"])
        assert '"support_references"' not in text and '"adjudication_reference"' not in text
        assert '"method_id"' not in text and '"expected"' not in text
        assert all(atom["asserted_abstraction_level"] is None for atom in (
            task["payload"].get("form", task["payload"].get("blinded_form"))["atomic_statements"]))
    assert freeze["pilot_annotation_authorized"] is False
    assert len(suite["constructed_disagreement_report"]["disagreements"]) == 3
    assert compare(suite["packet"], *suite["support_references"].values())["disagreement_count"] == 0


def test_all_reference_fields_required_and_raw_level_never_scored():
    freeze, suite, *_ = module.load_bound()
    bank = records(suite)
    assert module.result_for(freeze, suite, bank, "offline")["status"].startswith("PASS_")
    bank["B"]["parsed_final"]["highest_asserted_abstraction_level"] = "NO_DIAGNOSTIC_ASSERTION"
    result = module.result_for(freeze, suite, bank, "offline")
    assert result["status"].startswith("PASS_") and result["highest_level_qualified"] is False
    assert result["actual_ab_disagreement_count_including_unqualified_raw_level"] == 1
    for field, key, value in (("atomic_labels", "label", "UNINTERPRETABLE"),
                              ("required_unit_coverage", "communicated", False),
                              ("limitation_preservation", "preserved", False)):
        bank = records(suite)
        bank["A"]["parsed_final"][field][0][key] = value
        assert module.result_for(freeze, suite, bank, "offline")["status"] == "FAILED_SYNTHETIC_REFERENCE_RETAIN_NO_RETRY"


def test_constructed_c_choice_error_is_retained_as_failure():
    freeze, suite, *_ = module.load_bound()
    bank = records(suite)
    row = suite["constructed_disagreement_report"]["disagreements"][0]
    item = next(item for item in bank["C_CONSTRUCTED"]["parsed_final"]["decisions"] if item["disagreement_id"] == row["disagreement_id"])
    item["selected_value"] = next(value for value in (row["annotator_a_value"], row["annotator_b_value"]) if value != item["selected_value"])
    assert module.result_for(freeze, suite, bank, "offline")["status"] == "FAILED_CONSTRUCTED_C_RETAIN_NO_RETRY"


def setup_mock_execution(tmp_path, monkeypatch, *, fail_slot=None, reference_error=False):
    bound = module.load_bound()
    freeze, suite = bound[:2]
    path = tmp_path / module.FREEZE
    path.parent.mkdir(parents=True)
    path.write_bytes((module.ROOT / module.FREEZE).read_bytes())
    monkeypatch.setattr(module, "load_bound", lambda root: bound)
    monkeypatch.setattr(auditor, "load_bound", lambda root: bound)
    monkeypatch.setattr(module, "transport_audit", lambda *args: {"status": "READY_FOR_SCHEMA_CANARY"})
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=freeze["cli_version"] + "\n"))
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    calls = []
    def invoke(**options):
        slot = options["output"].stem
        def run(command, **kw):
            calls.append(slot)
            if slot == fail_slot:
                return SimpleNamespace(returncode=1, stdout="", stderr="mock transport failure")
            value = copy.deepcopy(suite["adjudication_reference"] if slot == "C_CONSTRUCTED" else suite["support_references"][slot])
            if reference_error and slot == "A":
                value["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
            Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(value))
            return SimpleNamespace(returncode=0, stdout='{"type":"turn.completed"}', stderr="")
        return call_once(**options, runner=run)
    monkeypatch.setattr(module, "call_once", invoke)
    return freeze, calls


def test_one_shot_sequence_and_read_only_audit_reproduce(tmp_path, monkeypatch):
    _, calls = setup_mock_execution(tmp_path, monkeypatch)
    result = module.run(tmp_path)
    assert result["status"] == "PASS_COMBINED_SYNTHETIC_CANARY_PENDING_ARTIFACT_PUSH"
    assert calls == ["A", "B", "C_CONSTRUCTED"]
    assert module.run(tmp_path) == result and len(calls) == 3
    report = auditor.audit(tmp_path, process_terminal=True)
    assert report["counts"] == {"valid": 3, "failed": 0, "unknown_terminal": 0, "pending_live": 0, "never_launched": 0}
    assert report["result"] == result and len(report["bindings"]) == 7
    assert report["pilot_annotation_authorized"] is False


def test_first_technical_failure_stops_b_and_c_without_retry(tmp_path, monkeypatch):
    _, calls = setup_mock_execution(tmp_path, monkeypatch, fail_slot="A")
    result = module.run(tmp_path)
    assert result["status"] == "FAILED_TECHNICAL_RETAIN_NO_RETRY" and calls == ["A"]
    assert module.run(tmp_path) == result and calls == ["A"]
    report = auditor.audit(tmp_path, process_terminal=True)
    assert report["counts"]["failed"] == 1 and report["counts"]["never_launched"] == 2


def test_support_reference_failure_does_not_launch_constructed_c(tmp_path, monkeypatch):
    _, calls = setup_mock_execution(tmp_path, monkeypatch, reference_error=True)
    result = module.run(tmp_path)
    assert result["status"] == "FAILED_SYNTHETIC_REFERENCE_RETAIN_NO_RETRY" and calls == ["A", "B"]
    report = auditor.audit(tmp_path, process_terminal=True)
    assert report["counts"]["valid"] == 2 and report["counts"]["never_launched"] == 1


def test_unknown_intent_never_relaunches_and_audit_distinguishes_terminal(tmp_path, monkeypatch):
    freeze, calls = setup_mock_execution(tmp_path, monkeypatch)
    intent = tmp_path / freeze["output_root"] / "A.intent"
    intent.parent.mkdir(parents=True)
    intent.write_text("{}")
    with pytest.raises(RuntimeError, match="unknown.*intent"):
        module.run(tmp_path)
    assert calls == []
    assert auditor.audit(tmp_path)["counts"]["pending_live"] == 1
    assert auditor.audit(tmp_path, process_terminal=True)["counts"]["unknown_terminal"] == 1
