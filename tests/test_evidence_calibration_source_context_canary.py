from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from adjudicate_evidence_calibration_annotations import validate_return  # noqa: E402
from evidence_calibration_io import canonical_json_bytes, canonical_sha256  # noqa: E402
from run_evidence_calibration_agent_annotation import AMENDMENT, _annotation_payload, _canonical  # noqa: E402
from run_evidence_calibration_source_context_canary import (  # noqa: E402
    _retained_call, digest, load, packet_for, score, run,
)


def test_source_canary_uses_exact_qualified_binding_and_blind_synthetic_packet() -> None:
    freeze, case, _, _ = load()
    assert freeze["qualified_annotator"]["model"] == "gpt-6-astra"
    assert freeze["qualified_annotator"]["reasoning_effort"] == "high"
    packet = packet_for(case, "A")
    form = packet["forms"][0]
    assert "response_text" not in form
    assert packet["response_text"] == case["form"]["response_text"]
    assert len(form["robot_visible_evidence"]["exact_source_assets"]) == 1
    assert "method_id" not in str(packet)


def test_source_canary_expected_labels_require_visible_source_and_separate_truth() -> None:
    _, case, _, _ = load()
    packet = packet_for(case, "A")
    expected = case["expected"]
    returned = {
        "schema": "crane-blinded-atomic-annotation-return/v1",
        "packet_set_sha256": canonical_sha256(packet),
        "form_id": packet["forms"][0]["form_id"],
        "packet_id": case["canary_id"],
        "annotator_slot": "A",
        "annotator_id": "synthetic-test-agent",
        "atomic_labels": [{"item_id": item["item_id"], "label": item["label"], "annotation_notes": ""}
                          for item in expected["atomic_labels"]],
        "required_unit_coverage": expected["required_unit_coverage"],
        "highest_asserted_abstraction_level": expected["highest_asserted_abstraction_level"],
        "limitation_preservation": expected["limitation_preservation"],
        "false_premise_handling": expected["false_premise_handling"],
        "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
    }
    validate_return(packet, returned)
    assert score(case, returned)["passed"] is True
    returned["atomic_labels"][0]["label"] = "INSUFFICIENT_VISIBLE_EVIDENCE"
    assert score(case, returned)["passed"] is False


def test_managed_shell_blocks_canary_before_any_model_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODEX_SANDBOX_NETWORK_DISABLED", "1")
    with pytest.raises(RuntimeError, match="network-enabled host"):
        run(tmp_path / "canary")
    assert not (tmp_path / "canary").exists()


def test_retained_canary_call_must_match_exact_frozen_request(tmp_path: Path) -> None:
    freeze, case, schema, prompt = load()
    packet = packet_for(case, "A")
    payload = _annotation_payload(packet, packet["forms"][0], "A")
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN", _canonical(payload),
                             "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()
    identity = {
        "transport": freeze["qualified_annotator"]["transport"],
        "logical_role": "source-context-canary-A",
        "model": freeze["qualified_annotator"]["model"],
        "effort": freeze["qualified_annotator"]["reasoning_effort"],
        "cli_version": "fixture-cli",
        "prompt_sha256": prompt_hash,
        "schema_sha256": hashlib.sha256(canonical_json_bytes(schema)).hexdigest(),
        "payload": json.loads(json.dumps(payload)),
        "amendment_sha256": digest(AMENDMENT),
        "workspace": "empty-temporary-read-only",
    }
    cache_key = hashlib.sha256(_canonical(identity).encode()).hexdigest()
    path = tmp_path / f"{cache_key}.json"
    record = {"status": "VALID", "attempt_count": 1, "quality_driven_retries": 0,
              "credential_persisted": False, "request_identity": identity,
              "request_sha256": prompt_hash, "cache_key": cache_key}
    path.write_text(json.dumps(record), encoding="utf-8")
    assert _retained_call(path, freeze=freeze, slot="A", payload=payload,
                          schema=schema, prompt=prompt) == record
    record["request_identity"]["payload"]["response_text"] = "changed response"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not match the frozen request"):
        _retained_call(path, freeze=freeze, slot="A", payload=payload,
                       schema=schema, prompt=prompt)


def test_orphaned_canary_record_blocks_a_new_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    slot_dir = tmp_path / "canary/A"
    slot_dir.mkdir(parents=True)
    (slot_dir / "old.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="orphaned prior A canary call"):
        run(tmp_path / "canary")
