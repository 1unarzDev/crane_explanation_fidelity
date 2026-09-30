"""Offline execution integrity checks; mocked calls are not annotation evidence."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from test_evidence_calibration_pilot_support_packets import inputs
from build_evidence_calibration_pilot_support_packets import build_packet
from adjudicate_evidence_calibration_annotations import compare
from evidence_calibration_io import canonical_sha256
import evidence_calibration_support_execution as module


def fixture():
    args = list(inputs())
    args[2]["limitation_prompts"] = ["preserve evidence limitations"]
    packet, _ = build_packet(*args)
    return packet


def returned(packet, slot):
    form = next(item for item in packet["forms"] if item["annotator_slot"] == slot)
    return {"schema": "crane-blinded-atomic-annotation-return/v1",
            "packet_set_sha256": canonical_sha256(packet), "form_id": form["form_id"],
            "packet_id": form["packet_id"], "annotator_slot": slot,
            "annotator_id": f"agent-{slot}-offline", "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
            "atomic_labels": [{"item_id": item["item_id"], "label": "SUPPORTED_BY_VISIBLE_EVIDENCE",
                               "annotation_notes": None} for item in form["atomic_statements"]],
            "required_unit_coverage": [{"unit_prompt": item["unit_prompt"], "communicated": True,
                                        "response_span": packet["response_text"]}
                                       for item in form["required_unit_coverage"]],
            "limitation_preservation": [{"limitation_prompt": item["limitation_prompt"], "preserved": False,
                                        "response_span": None} for item in form["limitation_preservation"]],
            "highest_asserted_abstraction_level": "task_outcome", "false_premise_handling": "NOT_APPLICABLE"}


def kwargs(tmp_path, slot="A"):
    packet = fixture()
    return dict(output=tmp_path / f"{slot}.json", payload=module.annotation_payload(packet, slot, f"agent-{slot}-offline"),
                schema={}, prompt="offline prompt", freeze={"candidate": {"model": "gpt-6-astra", "reasoning_effort": "high"},
                "timeout_s": 1}, freeze_sha256="offline-freeze", cli_version="offline-cli",
                validate=lambda value: module.validate_support(packet, value, f"agent-{slot}-offline", slot))


def good_runner(workspaces):
    def run(command, **options):
        payload = json.loads(options["input"].split("UNTRUSTED_ANNOTATION_DATA_BEGIN\n", 1)[1]
                             .split("\nUNTRUSTED_ANNOTATION_DATA_END", 1)[0])
        slot = payload["form"]["annotator_slot"]
        workspace = Path(command[command.index("--cd") + 1])
        workspaces.append(workspace)
        assert set(path.name for path in workspace.iterdir()) == {"schema.json"}
        assert "--ephemeral" in command and "read-only" in command
        assert '"method_id"' not in options["input"]
        Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(returned(fixture(), slot)))
        return SimpleNamespace(returncode=0, stdout='{"type":"turn.completed"}\n', stderr="")
    return run


def test_intent_precedes_launch_failure_and_unknown_intent_are_not_retried(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    options = kwargs(tmp_path)
    calls = []
    def fail(*args, **kw):
        assert options["output"].with_suffix(".intent").is_file()
        calls.append(1)
        return SimpleNamespace(returncode=1, stdout="", stderr="mock transport failure")
    record = module.call_once(**options, runner=fail)
    assert record["status"] == "FAILED_NO_RETRY"
    assert module.call_once(**options, runner=fail) == record
    options["output"].unlink()
    with pytest.raises(RuntimeError, match="unknown.*intent"):
        module.call_once(**options, runner=fail)
    assert len(calls) == 1


def test_isolated_valid_returns_are_reused_and_tampering_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    workspaces = []
    runner = good_runner(workspaces)
    for slot in ("A", "B"):
        options = kwargs(tmp_path, slot)
        result = module.call_once(**options, runner=runner)
        assert result["status"] == module.VALID
        assert module.call_once(**options, runner=runner) == result
    assert len(workspaces) == 2 and workspaces[0] != workspaces[1]
    assert all(not workspace.exists() for workspace in workspaces)
    options = kwargs(tmp_path)
    result = json.loads(options["output"].read_text())
    result["parsed_final"]["atomic_labels"][0]["label"] = "UNINTERPRETABLE"
    options["output"].write_text(json.dumps(result))
    with pytest.raises(RuntimeError, match="differs from raw"):
        module.call_once(**options, runner=runner)
    assert len(workspaces) == 2


def test_disabled_network_writes_no_intent(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_SANDBOX_NETWORK_DISABLED", "1")
    with pytest.raises(RuntimeError, match="outbound sockets"):
        module.call_once(**kwargs(tmp_path), runner=lambda *a, **k: pytest.fail("must not launch"))
    assert not list(tmp_path.iterdir())


def test_support_rejects_wrong_slot_identity_and_schema_type_loopholes():
    packet = fixture()
    value = returned(packet, "B")
    value["annotator_id"] = "agent-A-offline"
    with pytest.raises(ValueError, match="identity"):
        module.validate_support(packet, value, "agent-A-offline", "A")
    for field, key in (("atomic_labels", "annotation_notes"), ("limitation_preservation", "response_span")):
        value = returned(packet, "A")
        value[field][0][key] = 1
        with pytest.raises(ValueError, match="schema"):
            module.validate_support(packet, value, "agent-A-offline", "A")
    with pytest.raises(ValueError, match="identity"):
        module.annotation_payload(packet, "B", "agent-A-offline")


def disagreement():
    packet = fixture()
    a, b = returned(packet, "A"), returned(packet, "B")
    b["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    b["required_unit_coverage"][0].update(communicated=False, response_span=None)
    b["limitation_preservation"][0].update(preserved=True, response_span=packet["response_text"])
    return packet, compare(packet, a, b)


def test_adjudication_has_full_answer_and_only_disputed_contexts_without_prior_identities():
    packet, report = disagreement()
    payload = module.adjudication_payload(packet, report, "agent-C-offline")
    assert payload["response_text"] == packet["response_text"]
    assert {row["decision_key"] for row in payload["disagreement_contexts"]} == {
        row["decision_key"] for row in report["disagreements"]}
    assert {row["kind"] for row in payload["disagreement_contexts"]} == {
        "atomic_label", "required_unit_coverage", "limitation_preservation"}
    serialized = json.dumps(payload)
    assert "agent-A-offline" not in serialized and "agent-B-offline" not in serialized
    assert '"agreed_decisions"' not in serialized and '"method_id"' not in serialized
    assert "unit_prompt" in serialized and "limitation_prompt" in serialized
    a, b = returned(packet, "A"), returned(packet, "B")
    with pytest.raises(ValueError, match="disagreements"):
        module.adjudication_payload(packet, compare(packet, a, b), "agent-C-offline")


def test_adjudication_rejects_invented_values_and_numeric_boolean_equivalence():
    _, report = disagreement()
    result = {"schema": "crane-blinded-atomic-annotation-adjudication/v1",
              "agreement_report_sha256": canonical_sha256(report), "adjudicator_id": "agent-C-offline",
              "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
              "decisions": [{"disagreement_id": row["disagreement_id"], "selected_value": row["annotator_a_value"],
                             "rationale": "offline synthetic choice"} for row in report["disagreements"]]}
    module.validate_adjudication(report, result, "agent-C-offline")
    for replacement in (1, "invented value"):
        changed = copy.deepcopy(result)
        index = next(i for i, row in enumerate(report["disagreements"]) if row["decision_key"].startswith("unit:"))
        changed["decisions"][index]["selected_value"] = replacement
        with pytest.raises(ValueError):
            module.validate_adjudication(report, changed, "agent-C-offline")


@pytest.mark.parametrize("event", ['{"type":"item.completed","item":{"type":"command_execution"}}',
                                   '{"type":"turn.failed"}', 'invalid json'])
def test_forbidden_tool_or_failed_events_retain_failure(tmp_path, monkeypatch, event):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    good = good_runner([])
    def run(command, **options):
        good(command, **options)
        return SimpleNamespace(returncode=0, stdout=event, stderr="")
    result = module.call_once(**kwargs(tmp_path), runner=run)
    assert result["status"] == "FAILED_NO_RETRY" and result["invalid_event"]


def test_timeout_is_terminal_and_never_retried(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    calls = []
    def run(command, **options):
        calls.append(command)
        raise module.subprocess.TimeoutExpired(command, options["timeout"], output=b"", stderr=b"mock timeout")
    options = kwargs(tmp_path)
    record = module.call_once(**options, runner=run)
    assert record["status"] == "FAILED_NO_RETRY" and record["timed_out"] is True
    assert module.call_once(**options, runner=run) == record
    assert len(calls) == 1


def test_raw_highest_disagreement_context_is_explicitly_unqualified():
    packet = fixture()
    a, b = returned(packet, "A"), returned(packet, "B")
    b["highest_asserted_abstraction_level"] = "specific_physical_cause"
    payload = module.adjudication_payload(packet, compare(packet, a, b), "agent-C-offline")
    assert len(payload["disagreement_contexts"]) == 1
    context = payload["disagreement_contexts"][0]
    assert context["kind"] == "raw_highest_level_unqualified" and context["endpoint_use_prohibited"] is True
