import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREDECL = ROOT / "research/explanation_fidelity/experiment_configs/development/contract-complete-concise-v1-inspected-screen-predeclaration.json"


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_concise_screen_pins_methods_before_new_outputs():
    value = json.loads(PREDECL.read_text())
    assert value["status"] == "FROZEN_BEFORE_R_CONCISE_OR_LUNA_OUTPUTS"
    assert digest(value["candidate"]["renderer"]) == value["candidate"]["sha256"]
    assert digest(value["baseline"]["prompt"]) == value["baseline"]["prompt_sha256"]
    assert digest(value["runner"]["path"]) == value["runner"]["sha256"]
    assert digest(value["runner"]["base_path"]) == value["runner"]["base_sha256"]
    assert digest(value["question_contract"]["path"]) == value["question_contract"]["sha256"]
    assert digest(value["population"]["source_schedule"]) == value["population"]["source_schedule_sha256"]
    assert value["communication_budget"]["maximum_words"] == 120
    assert value["alpha_consumed"] == 0
    assert value["confirmation"]["independent_n"] == 0


def test_concise_screen_keeps_failures_and_controls_in_denominator_accounting():
    value = json.loads(PREDECL.read_text())
    population = value["population"]
    assert population == {
        "source_schedule": "research/explanation_fidelity/experiment_configs/prospective/explicit-causal-restraint-successor-v1-schedule.json",
        "source_schedule_sha256": "576872bb8e749dc372553be2630a76d904721ba3de157ee4a0736d8cc49e71f0",
        "scheduled": 20,
        "valid_reused": 18,
        "primary": 14,
        "controls": 4,
        "retained_technical_failures": ["cr-pilot-007", "cr-pilot-017"],
        "freshness": "All physical outcomes and previous answers are inspected; only P-v5 text, R-concise responses, and their judgments are new.",
    }
