import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_v2r2_qualification import audit  # noqa: E402
from run_evidence_calibration_claim_role_v2r2_qualification import (  # noqa: E402
    VALID_STATUS, call_once, load_bound_freeze,
)


def test_absent_and_interrupted_calls_cannot_qualify(tmp_path):
    result = audit(tmp_path)
    assert result["canary_status"] == "UNCALLED"
    assert result["per_pass"]["A"]["uncalled"] == 24
    assert result["role_qualification_authorized"] is False
    intent = tmp_path / "A/rk2-ho-01.intent"
    intent.parent.mkdir(parents=True)
    intent.write_text("{}\n")
    result = audit(tmp_path)
    assert result["per_pass"]["A"]["interrupted_intents"] == 1
    assert result["exact_candidate"] is False
    assert result["model_calls_made_by_audit"] == 0


def test_exact_synthetic_records_still_require_semantic_review(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    freeze, cases, prompt, schema = load_bound_freeze()
    lookup = {case["case_id"]: case for case in cases}

    def gold_runner(command, **kwargs):
        payload = json.loads(kwargs["input"].split("UNTRUSTED_ROLE_INPUT_BEGIN\n", 1)[1]
                             .split("\nUNTRUSTED_ROLE_INPUT_END", 1)[0])
        case_id = payload["opaque_response_id"].rsplit("-", 1)[0]
        if case_id == "non-study-schema-canary":
            roles = [{"item_id": "c1", "stance": "ASSERTED_FACT", "claim_kind": "TASK_OUTCOME",
                      "polarity": "POSITIVE", "rationale_span": payload["claims"][0]["response_span"]}]
        else:
            roles = [{**gold, "rationale_span": claim["response_span"]}
                     for claim, gold in zip(lookup[case_id]["claims"], lookup[case_id]["expected"], strict=True)]
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps({
            "schema": "crane-evidence-calibration-claim-role-return/v2-development",
            "opaque_response_id": payload["opaque_response_id"], "claim_roles": roles,
            "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT",
        }))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    canary = {"case_id": "non-study-schema-canary", "response_text": "The recorded action succeeded.",
              "claims": [{"item_id": "c1", "response_span": "The recorded action succeeded.",
                          "claim_text": "The recorded action succeeded."}]}
    for slot, case in [("canary", canary)] + [(slot, case) for slot in ("A", "B") for case in cases]:
        assert call_once(case=case, slot=slot, freeze=freeze, prompt=prompt, schema=schema,
                         output_root=tmp_path, cli_version="codex-cli-test", runner=gold_runner)["status"] == VALID_STATUS
    result = audit(tmp_path)
    assert result["exact_candidate"] is True
    assert result["per_pass"]["A"]["heldout_exact_matches"] == 20
    assert result["per_pass"]["B"]["heldout_exact_matches"] == 20
    assert result["independent_semantic_review_complete"] is False
    assert result["pilot_role_annotation_authorized"] is False


def test_audit_refuses_orphan_record(tmp_path):
    path = tmp_path / "A/rk2-ho-01.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    with pytest.raises(ValueError, match="orphan role call record"):
        audit(tmp_path)
