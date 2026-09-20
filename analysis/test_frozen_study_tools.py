from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def annotation_row(episode: str, condition: str, error: bool) -> dict:
    return {
        "episode_id": episode,
        "question_kind": "failure-cause",
        "condition": condition,
        "material_error": error,
        "substantive_answer": True,
        "answerable_units_correct": 5,
        "answerable_units_total": 5,
        "disposition": "full",
        "causal_overclaim": error,
        "unsupported_claim_count": int(error),
        "claim_count": 3,
        "source_reference_count": 1,
        "correct_source_reference_count": 1,
        "source_references_total_answerable": 1,
        "physical_evidence_claim_count": 1,
        "correct_physical_evidence_claim_count": int(not error),
        "qualification_correct": not error,
        "requested_conclusion_answerable": False,
        "correct_abstention": not error,
    }


def test_frozen_analyzer_preserves_pairing(tmp_path: Path) -> None:
    rows = [
        annotation_row(episode, condition, condition == "F")
        for episode in ("pn-0001", "pn-0002")
        for condition in ("F", "G", "H")
    ]
    annotations = tmp_path / "annotations.jsonl"
    annotations.write_text("".join(json.dumps(row) + "\n" for row in rows))
    output = tmp_path / "result.json"
    subprocess.run(
        (
            str(ROOT / "analysis/analyze_provenance_study.py"),
            str(annotations),
            "--output",
            str(output),
            "--simulations",
            "100",
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(output.read_text())
    assert result["episodes"] == 2
    assert result["primary_comparison"]["risk_difference_method_minus_baseline"] == -1.0
    assert result["primary_comparison"]["coverage_difference_method_minus_baseline"] == 0.0
    assert result["conditions"]["G"]["correct_abstention_rate_on_unanswerable"] == 1.0


def test_leakage_scanner_rejects_forbidden_json_key(tmp_path: Path) -> None:
    (tmp_path / "episode.json").write_text(json.dumps({"fault_injection": "hidden"}))
    completed = subprocess.run(
        (str(ROOT / "analysis/scan_robot_visible_leakage.py"), str(tmp_path)),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "fault_injection" in completed.stderr


def test_leakage_scanner_accepts_negative_evaluator_truth_attestation(tmp_path: Path) -> None:
    (tmp_path / "audit.json").write_text(
        json.dumps({"evaluator_truth_available_to_methods": False})
    )
    completed = subprocess.run(
        (str(ROOT / "analysis/scan_robot_visible_leakage.py"), str(tmp_path)),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
