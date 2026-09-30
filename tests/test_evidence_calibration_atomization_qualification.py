from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from run_evidence_calibration_atomization_qualification import call_once, load_freeze  # noqa: E402


def test_frozen_suite_is_disjoint_and_construction_defined() -> None:
    freeze, suite, _, _ = load_freeze()
    assert freeze["scope"].startswith("Synthetic extraction qualification only")
    cases = suite["cases"]
    assert len(cases) == 20
    assert sum(case["split"] == "heldout" for case in cases) == 16
    assert all(case["expected"] for case in cases)
    assert any("prompt_injection" in case["threat_tags"] for case in cases)
    assert all("cm-land-conf-" not in case["response_text"] for case in cases)


def test_one_retained_call_does_not_retry_or_claim_completeness(tmp_path: Path) -> None:
    freeze, _, prompt, schema = load_freeze()
    entry = {"opaque_response_id": "canary", "response_text": "The action succeeded."}
    returned = {
        "schema": "crane-evidence-calibration-atomization-return/v1",
        "opaque_response_id": "canary",
        "claims": [{"response_span": "The action succeeded.", "claim_text": "The action succeeded.",
                    "asserted_abstraction_level": "task_outcome"}],
        "unresolved_spans": [],
        "attestation": "METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT",
    }
    calls = []

    def fake_runner(command, **kwargs):
        calls.append(kwargs["input"])
        assert "cm-land-conf" not in kwargs["input"]
        Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(returned))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    output = tmp_path / "canary.json"
    first = call_once(entry=entry, role="atomizer-canary", freeze=freeze, prompt=prompt,
                      schema=schema, output=output, runner=fake_runner)
    second = call_once(entry=entry, role="atomizer-canary", freeze=freeze, prompt=prompt,
                       schema=schema, output=output, runner=fake_runner)
    assert len(calls) == 1
    assert first == second
    assert first["status"] == "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
    assert first["structural_validation"]["support_annotation_authorized"] is False


def test_forbidden_tool_event_is_retained_failure(tmp_path: Path) -> None:
    freeze, _, prompt, schema = load_freeze()
    entry = {"opaque_response_id": "canary", "response_text": "The action succeeded."}

    def fake_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout='{"item":{"type":"command_execution"}}', stderr="")

    result = call_once(entry=entry, role="atomizer-canary", freeze=freeze, prompt=prompt,
                       schema=schema, output=tmp_path / "failed.json", runner=fake_runner)
    assert result["status"] == "FAILED_NO_RETRY"
    assert result["attempt_count"] == 1
    assert result["invalid_event"] == "command_execution"
