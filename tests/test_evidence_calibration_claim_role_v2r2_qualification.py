import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from run_evidence_calibration_claim_role_v2r2_qualification import (  # noqa: E402
    VALID_STATUS, call_once, load_bound_freeze,
)


def _case():
    return {"case_id": "synthetic-test", "response_text": "The action succeeded.",
            "claims": [{"item_id": "c1", "response_span": "The action succeeded.",
                        "claim_text": "The action succeeded."}]}


def _fake_success(command, **kwargs):
    output = Path(command[command.index("--output-last-message") + 1])
    payload = json.loads(kwargs["input"].split("UNTRUSTED_ROLE_INPUT_BEGIN\n", 1)[1].split("\nUNTRUSTED_ROLE_INPUT_END", 1)[0])
    output.write_text(json.dumps({
        "schema": "crane-evidence-calibration-claim-role-return/v2-development",
        "opaque_response_id": payload["opaque_response_id"],
        "claim_roles": [{"item_id": "c1", "stance": "ASSERTED_FACT", "claim_kind": "TASK_OUTCOME",
                         "polarity": "POSITIVE",
                         "rationale_span": "The action succeeded."}],
        "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT",
    }))
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def _inputs():
    freeze, _, prompt, schema = load_bound_freeze()
    return {"case": _case(), "slot": "canary", "freeze": freeze,
            "prompt": prompt, "schema": schema, "cli_version": "codex-cli-test"}


def test_structural_role_call_writes_intent_and_reuses_only_exact_request(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    arguments = {**_inputs(), "output_root": tmp_path}
    first = call_once(**arguments, runner=_fake_success)
    assert first["status"] == VALID_STATUS
    assert first["structural_validation"]["endpoint_scoring_authorized"] is False
    assert (tmp_path / "canary/synthetic-test.intent").is_file()
    def forbidden(*_args, **_kwargs):
        raise AssertionError("a retained request must not be called again")
    assert call_once(**arguments, runner=forbidden) == first
    changed = copy.deepcopy(arguments)
    changed["case"]["response_text"] = "The action failed."
    changed["case"]["claims"][0]["response_span"] = "The action failed."
    with pytest.raises(RuntimeError, match="differs from the frozen request"):
        call_once(**changed, runner=forbidden)


def test_prior_intent_without_terminal_record_prohibits_retry(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    path = tmp_path / "canary/synthetic-test.intent"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    with pytest.raises(RuntimeError, match="do not retry"):
        call_once(**_inputs(), output_root=tmp_path, runner=_fake_success)


def test_orphan_terminal_record_prohibits_reuse(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    path = tmp_path / "canary/synthetic-test.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    with pytest.raises(RuntimeError, match="orphan role call record"):
        call_once(**_inputs(), output_root=tmp_path, runner=_fake_success)


def test_failed_transport_is_retained_without_retry(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    def failed(command, **_kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="transport unavailable")
    arguments = {**_inputs(), "output_root": tmp_path}
    first = call_once(**arguments, runner=failed)
    assert first["status"] == "FAILED_NO_RETRY"
    assert first["attempt_count"] == 1
    def forbidden(*_args, **_kwargs):
        raise AssertionError("retained failure must not be retried")
    assert call_once(**arguments, runner=forbidden) == first


def test_retained_valid_record_must_match_raw_return_and_structural_check(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    arguments = {**_inputs(), "output_root": tmp_path}
    call_once(**arguments, runner=_fake_success)
    path = tmp_path / "canary/synthetic-test.json"
    retained = json.loads(path.read_text())
    retained["parsed_final"]["claim_roles"][0]["stance"] = "INFERENCE_LIMITATION"
    path.write_text(json.dumps(retained))
    with pytest.raises(RuntimeError, match="differs from its raw return"):
        call_once(**arguments, runner=_fake_success)


def test_retained_valid_record_rejects_corrupt_raw_final(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_SANDBOX_NETWORK_DISABLED", raising=False)
    arguments = {**_inputs(), "output_root": tmp_path}
    call_once(**arguments, runner=_fake_success)
    path = tmp_path / "canary/synthetic-test.json"
    retained = json.loads(path.read_text())
    retained["raw_final"] = "{"
    path.write_text(json.dumps(retained))
    with pytest.raises(RuntimeError, match="no longer validates"):
        call_once(**arguments, runner=_fake_success)


def test_managed_shell_rejects_call_before_writing_intent(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_SANDBOX_NETWORK_DISABLED", "1")
    with pytest.raises(RuntimeError, match="network-enabled host"):
        call_once(**_inputs(), output_root=tmp_path, runner=_fake_success)
    assert not list(tmp_path.rglob("*.intent"))
