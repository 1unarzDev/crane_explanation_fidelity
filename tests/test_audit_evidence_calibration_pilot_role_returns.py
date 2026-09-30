from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import audit_evidence_calibration_pilot_role_returns as retained
from run_evidence_calibration_claim_role_v2r2_qualification import call_once


def setup_records(root: Path):
    def write(path: str, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))
        return {"path": path, "raw_sha256": retained.digest(target)}

    sentence = "The recorded action succeeded."
    entries = [{"case_id": f"case-{index:03}", "response_text": sentence,
                "claims": [{"item_id": f"c{n}", "response_span": sentence,
                            "claim_text": sentence} for n in range(10 if index < 58 else 9)]}
               for index in range(114)]
    prompt_path = root / "prompt.md"
    prompt_path.write_text("Synthetic offline test prompt.")
    freeze = {"candidate": {
        "model": "gpt-6-astra", "reasoning_effort": "high", "transport": "test-offline",
        "prompt": {"path": "prompt.md", "raw_sha256": retained.digest(prompt_path)},
        "return_schema": write("return-schema.json", {"type": "object"}),
    }}
    canary = {"case_id": "canary", "response_text": sentence, "claims": entries[0]["claims"][:1]}
    declaration = {
        "schema": "crane-evidence-calibration-pilot-claim-role-use/v1-development",
        "planned_call_count": 228, "isolated_passes": ["A", "B"], "quality_driven_retries": 0,
        "support_annotation_authorized": False, "endpoint_scoring_authorized": False,
        "p11_authorized": False, "development_pilot_role_calls_authorized": True,
        "confirmation_independent_n": 0, "replication_independent_n": 0,
        "model": "gpt-6-astra", "reasoning_effort": "high", "transport": "test-offline", "tools": "none",
        "freeze": write("freeze.json", freeze),
        "qualification": write("qualification.json", {"status": "PASS_SYNTHETIC_STANCE_KIND_POLARITY_ONLY"}),
        "input_bundle": write("input.json", {"entries": entries, "response_count": 114, "atomic_claim_count": 1084}),
        "runner": write("runner.json", {"test": True}),
        "output_root": "outputs", "canary": canary,
    }
    write(retained.DECLARATION, declaration)

    def call(case, slot, interrupted=False):
        def mock_runner(command, **kwargs):
            if interrupted:
                raise KeyboardInterrupt()
            result = {
                "schema": "crane-evidence-calibration-claim-role-return/v2-development",
                "opaque_response_id": f"{case['case_id']}-{slot}",
                "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT",
                "claim_roles": [{"item_id": claim["item_id"], "stance": "ASSERTED_FACT",
                                 "claim_kind": "TASK_OUTCOME", "polarity": "POSITIVE",
                                 "rationale_span": sentence} for claim in case["claims"]],
            }
            Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(result))
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return call_once(case=case, slot=slot, freeze=freeze, freeze_path=root / "freeze.json",
                         prompt=prompt_path.read_text(), schema={"type": "object"},
                         output_root=root / "outputs", cli_version="offline-test", runner=mock_runner)

    call(canary, "canary")
    call(entries[0], "A")
    with pytest.raises(KeyboardInterrupt):
        call(entries[1], "A", interrupted=True)
    return entries, call


def test_intent_without_terminal_record_remains_unknown_not_model_failure(tmp_path):
    setup_records(tmp_path)
    result = retained.audit(tmp_path)
    assert result["pilot_disposition_counts"] == {
        retained.VALID_STATUS: 1, "FAILED_NO_RETRY": 0,
        "UNKNOWN_DISPOSITION_NO_RETRY": 1, "NEVER_LAUNCHED": 226,
    }
    assert result["resume_authorized_by_audit"] is False
    assert result["support_labels_generated"] is False
    assert result["endpoint_scores_generated"] is False


def test_call_after_ambiguous_intent_fails_closed(tmp_path):
    entries, call = setup_records(tmp_path)
    call(entries[2], "A")
    with pytest.raises(ValueError, match="call after first"):
        retained.audit(tmp_path)


def test_altered_raw_return_fails_even_if_old_structural_status_is_valid(tmp_path):
    setup_records(tmp_path)
    path = tmp_path / "outputs/A/case-000.json"
    record = json.loads(path.read_text())
    changed = json.loads(record["raw_final"])
    changed["claim_roles"][0]["polarity"] = "NEGATIVE"
    record["raw_final"] = json.dumps(changed)
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="raw role return"):
        retained.audit(tmp_path)
