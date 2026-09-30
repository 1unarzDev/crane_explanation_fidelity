import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_qualification import audit  # noqa: E402
from run_evidence_calibration_claim_role_qualification import call_once, load_bound_freeze  # noqa: E402


def _gold_runner(cases):
    lookup = {case["case_id"]: case for case in cases}

    def run(command, **kwargs):
        payload = json.loads(kwargs["input"].split("UNTRUSTED_ROLE_INPUT_BEGIN\n", 1)[1].split("\nUNTRUSTED_ROLE_INPUT_END", 1)[0])
        case_id = payload["opaque_response_id"].rsplit("-", 1)[0]
        if case_id == "non-study-schema-canary":
            roles = [{"item_id": "c1", "role": "AFFIRMATIVE_EPISODE_ASSERTION",
                      "asserted_diagnostic_level": "task_outcome",
                      "rationale_span": payload["claims"][0]["response_span"]}]
        else:
            case = lookup[case_id]
            roles = [{**gold, "rationale_span": claim["response_span"]}
                     for claim, gold in zip(case["claims"], case["expected"], strict=True)]
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps({"schema": "crane-evidence-calibration-claim-role-return/v1-development",
                                      "opaque_response_id": payload["opaque_response_id"],
                                      "claim_roles": roles,
                                      "attestation": "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT"}))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    return run


def test_absent_calls_are_uncalled_not_model_failures(tmp_path):
    result = audit(tmp_path)
    assert result["status"] == "INCOMPLETE_OR_RETAINED_FAILURE_NO_QUALIFICATION"
    assert result["canary_status"] == "UNCALLED"
    assert result["per_pass"]["A"]["uncalled"] == 24
    assert result["per_pass"]["B"]["retained_failures"] == 0
    assert result["model_calls_made_by_audit"] == 0


def test_exact_synthetic_returns_remain_review_candidates_only(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    freeze, cases, prompt, schema = load_bound_freeze()
    runner = _gold_runner(cases)
    canary = {"case_id": "non-study-schema-canary", "response_text": "The recorded action succeeded.",
              "claims": [{"item_id": "c1", "response_span": "The recorded action succeeded.",
                          "claim_text": "The recorded action succeeded."}]}
    for slot, case in [("canary", canary)] + [(slot, case) for slot in ("A", "B") for case in cases]:
        result = call_once(case=case, slot=slot, freeze=freeze, prompt=prompt, schema=schema,
                           output_root=tmp_path, cli_version="codex-cli-test", runner=runner)
        assert result["status"] == "STRUCTURALLY_VALID_ROLE_QUALIFICATION_UNSCORED"
    audited = audit(tmp_path)
    assert audited["exact_candidate"] is True
    assert audited["per_pass"]["A"]["heldout_exact_matches"] == 20
    assert audited["per_pass"]["B"]["heldout_exact_matches"] == 20
    assert audited["role_qualification_authorized"] is False
    assert audited["endpoint_scoring_authorized"] is False
    assert audited["model_calls_made_by_audit"] == 0


def test_audit_refuses_orphan_record(tmp_path):
    path = tmp_path / "A/role-ho-01.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    with pytest.raises(ValueError, match="orphan role call record"):
        audit(tmp_path)
