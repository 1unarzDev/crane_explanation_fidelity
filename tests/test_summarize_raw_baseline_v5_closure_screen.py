import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from summarize_raw_baseline_v5_screen import aggregate  # noqa: E402


ARM = "raw-baseline-v5-language-screen-v1-evidence-closure-v2"
PREDECLARATION = ROOT / f"manifests/annotation/luna-{ARM}-predeclaration.json"
ANNOTATION_ROOT = ROOT / f"model_outputs/automated_annotations/luna-model-judge-v1/{ARM}"
RESULT_PATH = ROOT / f"manifests/annotation/luna-{ARM}-result.json"


def test_closure_arm_retains_all_judgments_and_counts_only_five_clusters():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    assert result["valid_judgments"] == result["planned_judgments"] == 28
    assert result["retained_call_failures"] == []
    assert len(result["primary_endpoint_by_cluster"]) == 5
    assert result["confirmatory_semantic_n"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0


def test_systematic_closure_satisfies_declared_judge_evidence_parity():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    assert result["readiness_gates"]["judge_evidence_parity"] is True
    assert result["readiness_gates"]["information_parity"] is True


def test_written_closure_result_matches_recomputation_and_exact_gate_conjunction():
    expected = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    actual = json.loads(RESULT_PATH.read_text())
    assert actual == expected
    accepted = all(actual["readiness_gates"].values())
    assert actual["candidate_ready_for_prospective_freeze"] is accepted
    assert actual["status"] == (
        "DEVELOPMENT_ONLY_CANDIDATE_PASSED_FROZEN_GATE"
        if accepted
        else "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"
    )
