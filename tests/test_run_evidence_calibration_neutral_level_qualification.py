import copy
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from build_evidence_calibration_neutral_level_suite import build
from evidence_calibration_io import canonical_sha256
from evidence_calibration_neutral_level_qualification import packet_for
import run_evidence_calibration_neutral_level_qualification as module


def reference_return(case, slot, suite_hash):
    packet = packet_for(case, slot, suite_hash)
    form = packet["forms"][0]
    return {"schema": "crane-blinded-atomic-annotation-return/v1",
            "packet_set_sha256": canonical_sha256(packet), "form_id": form["form_id"],
            "packet_id": form["packet_id"], "annotator_slot": slot, "annotator_id": f"offline-{slot}",
            "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
            "atomic_labels": [{**item, "annotation_notes": "offline fixture"}
                              for item in case["expected"]["atomic_labels"]],
            "required_unit_coverage": copy.deepcopy(case["expected"]["required_unit_coverage"]),
            "limitation_preservation": copy.deepcopy(case["expected"]["limitation_preservation"]),
            "false_premise_handling": case["expected"]["false_premise_handling"],
            "highest_asserted_abstraction_level": "specific_physical_cause"}


def test_unknown_intent_and_terminal_failure_never_launch_again(tmp_path, monkeypatch):
    freeze, suite, prompt, schema = module.load_bound()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    case = suite["cases"][0]
    kwargs = dict(case=case, slot="A", suite_hash=canonical_sha256(suite), freeze=freeze,
                  prompt=prompt, schema=schema, cli_version=freeze["cli_version"])
    output = tmp_path / freeze["output_root"] / "A" / f"{case['case_id']}.json"
    calls = []

    def fail(command, **options):
        calls.append(command)
        assert output.with_suffix(".intent").is_file()
        assert '"expected"' not in options["input"]
        assert "--ephemeral" in command and "read-only" in command
        return SimpleNamespace(returncode=1, stdout="", stderr="synthetic transport failure")

    record = module.call_once(**kwargs, runner=fail)
    assert record["status"] == "FAILED_NO_RETRY"
    assert module.call_once(**kwargs, runner=fail) == record
    assert len(calls) == 1
    output.unlink()
    with pytest.raises(RuntimeError, match="do not retry"):
        module.call_once(**kwargs, runner=fail)
    assert len(calls) == 1


def test_valid_returns_bind_raw_bytes_and_isolated_slots(tmp_path, monkeypatch):
    freeze, suite, prompt, schema = module.load_bound()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    case = suite["cases"][0]
    calls = []
    kwargs = dict(case=case, suite_hash=canonical_sha256(suite), freeze=freeze,
                  prompt=prompt, schema=schema, cli_version=freeze["cli_version"])

    def good(command, **options):
        payload = json.loads(options["input"].split("UNTRUSTED_ANNOTATION_DATA_BEGIN\n", 1)[1]
                             .split("\nUNTRUSTED_ANNOTATION_DATA_END", 1)[0])
        slot = payload["form"]["annotator_slot"]
        raw = json.dumps(reference_return(case, slot, canonical_sha256(suite)))
        Path(command[command.index("--output-last-message") + 1]).write_text(raw)
        calls.append(slot)
        return SimpleNamespace(returncode=0, stdout='{"type":"turn.completed"}\n', stderr="")

    a = module.call_once(**kwargs, slot="A", runner=good)
    b = module.call_once(**kwargs, slot="B", runner=good)
    assert a["status"] == b["status"] == module.VALID
    assert a["request_identity"]["payload_sha256"] != b["request_identity"]["payload_sha256"]
    assert module.call_once(**kwargs, slot="A", runner=good) == a
    assert calls == ["A", "B"]
    output = tmp_path / freeze["output_root"] / "A" / f"{case['case_id']}.json"
    tampered = json.loads(output.read_text())
    tampered["parsed_final"]["atomic_labels"][0]["label"] = "UNINTERPRETABLE"
    output.write_text(json.dumps(tampered))
    with pytest.raises(RuntimeError, match="raw return"):
        module.call_once(**kwargs, slot="A", runner=good)
    assert calls == ["A", "B"]


def test_critical_negative_cause_error_cannot_hide_in_aggregate_accuracy():
    freeze, suite, _, _ = module.load_bound()
    records = {(slot, case["case_id"]): {"parsed_final": reference_return(case, slot, canonical_sha256(suite))}
               for slot in ("A", "B") for case in suite["cases"]}
    result = module.qualification_result(suite, records, freeze)
    assert result["status"] == "PASS_INPUT_EXTENSION_PENDING_DISPOSITION"
    records[("A", "nl-ho-08")]["parsed_final"]["atomic_labels"][0]["label"] = "UNINTERPRETABLE"
    result = module.qualification_result(suite, records, freeze)
    assert result["passes"][0]["metrics"]["atomic_accuracy"] >= .9
    assert result["passes"][0]["gate_checks"]["critical_reference_cases"] is False
    assert result["status"] == "FAILED_RETAIN_NO_RETRY"
    assert result["pilot_annotation_authorized"] is False
