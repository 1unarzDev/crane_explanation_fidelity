from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_boat_readiness_canary import annotation_reference, run
from run_luna_boat_canary import qualified_boat_release, reconcile


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json"


class FakeCaller:
    def call(self, *args, **kwargs):
        return {
            "cache_key": "fake-current-r",
            "latency_ms": 12.0,
            "cost_usd": None,
            "usage": {},
            "request": {
                "provider": "codex",
                "model": "gpt-6-sol",
                "reasoning_effort": "high",
            },
            "parsed_final": {"answer": "A bounded, qualified R answer."},
        }


def test_reference_declares_all_complete_endpoint_units():
    export = json.loads(EVIDENCE.read_text())
    independent = {
        "reference_findings": {"full_terminal_margin_mechanism_supported": True}
    }
    recomputed = {"final_text_verification": {"accepted": True}}
    reference = annotation_reference(export, independent, recomputed)
    assert reference["mechanism_unit_id"] == "mechanism-terminal-margin"
    assert reference["complete_endpoint_unit_ids"] == [
        item["unit_id"] for item in reference["required_units"]
    ]
    assert "waves" in " ".join(reference["prohibited_claims"])


def test_canary_uses_current_focused_r_and_two_arms(tmp_path: Path):
    result = run(
        argparse.Namespace(
            evidence=EVIDENCE,
            repository=ROOT / "packages/crane_ml",
            cache=tmp_path / "cache",
            output=tmp_path / "pair.json",
            reference_output=tmp_path / "reference.json",
        ),
        caller=FakeCaller(),
    )
    assert [item["condition"] for item in result["outputs"]] == ["P", "R"]
    assert result["outputs"][0]["provider"] == "deterministic"
    assert result["outputs"][1]["model"] == "gpt-6-sol"
    assert result["information_parity"]["same_executable_terminal_margin_adapter"] is True
    reference = json.loads((tmp_path / "reference.json").read_text())
    assert reference["primary_endpoint_eligible"] is True
    assert reference["reference_status"].startswith("DEVELOPMENT_CANARY")


def test_boat_judge_release_and_conservative_reconciliation():
    assert len(qualified_boat_release()["qualification_result_sha256"]) == 64
    report = {
        "conditions": ["P", "R"],
        "passes": {
            "pass-1": {
                "P": {"judgment_status": "valid", "supported_diagnostic_success": True, "material_error": False, "mechanism_identification": "correct"},
                "R": {"judgment_status": "valid", "supported_diagnostic_success": True, "material_error": False, "mechanism_identification": "correct"},
            },
            "pass-2": {
                "P": {"judgment_status": "valid", "supported_diagnostic_success": True, "material_error": False, "mechanism_identification": "correct"},
                "R": {"judgment_status": "valid", "supported_diagnostic_success": False, "material_error": False, "mechanism_identification": "correct"},
            },
        },
    }
    result = reconcile(report)
    assert result["status"] == "RECONCILED_WITH_UNRESOLVED_FIELDS"
    assert result["resolved"]["P"]["supported_diagnostic_success"] is True
    assert result["unresolved"]["R"] == ["supported_diagnostic_success"]
    assert result["prospective_boat_n_added"] == 0
