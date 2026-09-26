import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from summarize_raw_baseline_v5_screen import aggregate  # noqa: E402


PREDECLARATION = (
    ROOT / "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-predeclaration.json"
)
ANNOTATION_ROOT = (
    ROOT
    / "model_outputs/automated_annotations/luna-model-judge-v1"
    / "raw-baseline-v5-language-screen-v1"
)


def test_aggregate_retains_all_planned_judgments_and_no_failures():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    assert result["planned_judgments"] == 28
    assert result["valid_judgments"] == 28
    assert result["retained_call_failures"] == []
    assert len(result["judgments"]) == 28
    assert result["confirmatory_semantic_n"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0


def test_cluster_endpoint_uses_two_pass_consensus_without_inflating_n():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    clusters = result["primary_endpoint_by_cluster"]
    assert len(clusters) == 5
    assert len({item["cluster_id"] for item in clusters}) == 5
    for item in clusters:
        assert len(item["P_pass_values"]) == 2
        assert len(item["R_pass_values"]) == 2
        for condition in ("P", "R"):
            values = item[f"{condition}_pass_values"]
            expected = values[0] if len(set(values)) == 1 else None
            assert item[condition] == expected


def test_readiness_status_is_exact_conjunction_of_frozen_gates():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    accepted = all(result["readiness_gates"].values())
    assert result["candidate_ready_for_prospective_freeze"] is accepted
    assert result["status"] == (
        "DEVELOPMENT_ONLY_CANDIDATE_PASSED_FROZEN_GATE"
        if accepted
        else "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"
    )


def test_compact_binding_fails_closed_for_judge_evidence_parity():
    result = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    assert result["readiness_gates"]["judge_evidence_parity"] is False
    assert result["candidate_ready_for_prospective_freeze"] is False


def test_written_result_matches_recomputed_summary():
    path = (
        ROOT / "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-result.json"
    )
    expected = aggregate(PREDECLARATION, ANNOTATION_ROOT)
    assert json.loads(path.read_text()) == expected
