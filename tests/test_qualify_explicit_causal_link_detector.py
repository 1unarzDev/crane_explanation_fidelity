import json
from pathlib import Path

from analysis.qualify_explicit_causal_link_detector import evaluate


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "explicit-causal-link-detector-qualification-v1.json"
)


def test_frozen_qualification_suite_is_bounded_and_has_no_duplicate_cases():
    value = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = value["cases"]
    assert len(cases) == 24
    assert len({item["id"] for item in cases}) == 24
    assert len({item["text"] for item in cases}) == 24
    assert sum(bool(item["relations"]) for item in cases) == 13
    assert sum(not item["relations"] for item in cases) == 11
    assert value["acceptance"] == {
        "case_polarity_accuracy": 1.0,
        "relation_set_accuracy": 1.0,
        "exact_span_accuracy": 1.0,
        "execution_failures": 0,
    }


def test_qualification_evaluator_reports_failure_without_repairing_expected_data():
    value = json.loads(SUITE.read_text(encoding="utf-8"))
    value["cases"][0]["relations"] = []
    result = evaluate(value)
    assert result["passed"] is False
    assert result["metrics"]["case_polarity_accuracy"] < 1.0
