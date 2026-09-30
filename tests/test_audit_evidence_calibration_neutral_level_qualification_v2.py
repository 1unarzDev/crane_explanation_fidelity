import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import audit_evidence_calibration_neutral_level_qualification_v2 as module
from evidence_calibration_io import canonical_sha256
from evidence_calibration_neutral_level_qualification_v2 import packet_for


def bank(tmp_path, monkeypatch, count):
    freeze, suite, prompt, schema = module.load_bound()
    freeze_path = tmp_path / module.FREEZE.relative_to(module.ROOT)
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_bytes(module.FREEZE.read_bytes())
    monkeypatch.setattr(module, "FREEZE", freeze_path)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    records = {}
    for slot, case in [(slot, case) for slot in ("A", "B") for case in suite["cases"]][:count]:
        packet = packet_for(case, slot, canonical_sha256(suite))
        form = packet["forms"][0]
        returned = {"schema": "crane-blinded-atomic-annotation-return/v1",
                    "packet_set_sha256": canonical_sha256(packet), "form_id": form["form_id"],
                    "packet_id": form["packet_id"], "annotator_slot": slot,
                    "annotator_id": f"agent-{slot}-offline-test",
                    "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
                    "atomic_labels": [{**item, "annotation_notes": "offline structural fixture"}
                                      for item in case["expected"]["atomic_labels"]],
                    "required_unit_coverage": copy.deepcopy(case["expected"]["required_unit_coverage"]),
                    "limitation_preservation": copy.deepcopy(case["expected"]["limitation_preservation"]),
                    "false_premise_handling": case["expected"]["false_premise_handling"],
                    "highest_asserted_abstraction_level": "UNINTERPRETABLE"}
        identity = module.request_identity(case, slot, freeze, suite, prompt, schema)
        record = {"schema": "crane-neutral-support-call/v2", "request_identity": identity,
                  "status": module.VALID, "attempt_count": 1, "quality_driven_retries": 0,
                  "credential_persisted": False, "method_key_accessed": False,
                  "study_answers_included": False, "return_code": 0, "timed_out": False,
                  "invalid_event": None, "raw_final": json.dumps(returned), "parsed_final": returned}
        path = tmp_path / freeze["output_root"] / slot / f"{case['case_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))
        path.with_suffix(".intent").write_text(json.dumps({
            "schema": "crane-neutral-support-call-intent/v2", "request_identity": identity,
            "terminal_record_pending": True}))
        records[(slot, case["case_id"])] = record
    return freeze, suite, records


def test_prefix_never_scores_and_unknown_intent_requires_terminal_assertion(tmp_path, monkeypatch):
    freeze, suite, _ = bank(tmp_path, monkeypatch, 1)
    path = tmp_path / freeze["output_root"] / "A" / f"{suite['cases'][0]['case_id']}.json"
    path.unlink()
    monkeypatch.setattr(module, "qualification_result", lambda *args: pytest.fail("prefix must not score"))
    live = module.audit()
    assert live["counts"]["pending_live"] == 1 and live["counts"]["unknown_terminal"] == 0
    terminal = module.audit(process_terminal=True)
    assert terminal["counts"]["unknown_terminal"] == 1 and terminal["counts"]["pending_live"] == 0
    assert terminal["counts"]["never_launched"] == 39
    assert terminal["accuracy_reproduced"] is False
    assert terminal["status"] == "TERMINAL_INCOMPLETE_NOT_QUALIFIED"


def test_complete_score_reproduces_without_activating_pilot_or_increasing_n(tmp_path, monkeypatch):
    freeze, suite, records = bank(tmp_path, monkeypatch, 40)
    path = tmp_path / freeze["output_root"] / "qualification-result.json"
    with pytest.raises(ValueError, match="lacks retained score"):
        module.audit(process_terminal=True)
    result = module.qualification_result(suite, records, freeze)
    path.write_text(json.dumps(result))
    verified = module.audit(process_terminal=True)
    assert verified["counts"]["valid"] == 40
    assert verified["status"] == "PASS_INPUT_EXTENSION_PENDING_DISPOSITION"
    assert verified["accuracy_reproduced"] is True
    assert verified["pilot_annotation_authorized"] is False
    assert verified["confirmation_independent_n"] == verified["replication_independent_n"] == 0
    result["passes"][0]["metrics"]["atomic_accuracy"] = 0.5
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="frozen reproduction"):
        module.audit(process_terminal=True)


def test_requests_after_unknown_frontier_and_raw_return_tampering_fail_closed(tmp_path, monkeypatch):
    freeze, suite, _ = bank(tmp_path, monkeypatch, 2)
    path = tmp_path / freeze["output_root"] / "A" / f"{suite['cases'][0]['case_id']}.json"
    original = path.read_text()
    path.unlink()
    with pytest.raises(ValueError, match="stop frontier"):
        module.audit(process_terminal=True)
    path.write_text(original)
    record = json.loads(original)
    record["parsed_final"]["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="differs from raw return"):
        module.audit()
