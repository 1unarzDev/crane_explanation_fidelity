import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POPULATION = json.loads(
    (ROOT / "configs/evidence_calibration_population_v1_development.json").read_text()
)
LADDERS = json.loads(
    (ROOT / "configs/evidence_calibration_ladders_v1_development.json").read_text()
)


def test_population_weights_are_fixed_and_primary_is_balanced() -> None:
    rows = POPULATION["fixed_total_population_weights"]
    assert abs(sum(item["weight"] for item in rows) - 1.0) < 1e-12
    primary = [item for item in rows if item["analysis_role"] == "PRIMARY"]
    assert {item["stratum_id"] for item in primary} == {
        "persistent-command-motion-discrepancy", "measured-response-recovery"
    }
    assert POPULATION["primary_conditional_weights"] == {
        "persistent-command-motion-discrepancy": 0.5,
        "measured-response-recovery": 0.5,
    }


def test_every_population_stratum_uses_a_declared_ladder() -> None:
    ladder_ids = {item["ladder_id"] for item in LADDERS["ladders"]}
    assert all(
        item["ladder_id"] in ladder_ids
        for item in POPULATION["fixed_total_population_weights"]
    )
    assert POPULATION["secondary_geometry_arm"]["ladder_id"] in ladder_ids


def test_population_cannot_select_or_replace_by_semantic_outcome() -> None:
    eligibility = POPULATION["eligibility"]
    assert eligibility["uses_method_outputs"] is False
    assert eligibility["uses_semantic_labels"] is False
    assert eligibility["uses_observed_P_or_B2_performance"] is False
    assert eligibility["quality_driven_replacement"] is False
    assert POPULATION["stopping_candidate"]["semantic_looks"] == "ONE_FIXED_TERMINAL_LOOK"
    assert POPULATION["confirmation_authorized"] is False
