import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from analyze_evidence_calibration import analyze, exact_mcnemar_p  # noqa: E402
from simulate_evidence_calibration_power import simulate  # noqa: E402


def response(failure=False, emitted=1, available=1, rank=1, maximum=1, false_rejection=False):
    return {
        "claims": [{"claim_id": "c", "mechanistic": True,
                    "label": "INSUFFICIENT_VISIBLE_EVIDENCE" if failure else "SUPPORTED_BY_VISIBLE_EVIDENCE",
                    "required_minimum_level": 1}],
        "highest_asserted_rank": rank, "maximum_justified_rank": maximum,
        "supported_required_emitted": emitted, "supported_required_available": available,
        "false_premise_rejected": false_rejection,
    }


def dataset():
    patterns = [(True, False), (True, False), (False, True), (False, False)]
    episodes = []
    for index, (b2, b4) in enumerate(patterns):
        episodes.append({
            "episode_id": f"episode-{index}", "mechanism_family": "command_motion",
            "conditions": [{"condition_id": f"e{index}-1", "level_index": 1,
                            "evidence_insufficient": False, "false_premise": False,
                            "methods": {"B2": response(b2), "B4": response(b4)}}],
        })
    return {"schema": "crane-evidence-calibration-adjudicated-results/v1", "episodes": episodes}


def plan():
    return {"schema": "crane-evidence-calibration-analysis-plan/v1-development",
            "methods": ["B2", "B4"], "coverage_floor": 0.75, "alpha": 0.05,
            "clustered_model": "LOGISTIC_CLUSTER_ROBUST_EPISODE",
            "minimum_practically_meaningful_reduction": 0.10,
            "bootstrap_seed": 7, "bootstrap_replicates": 200}


def test_analysis_clusters_masks_and_reports_paired_discordances():
    output = analyze(dataset(), plan())
    assert output["independent_episode_count"] == 4
    assert output["paired_primary"]["b2_only_failure"] == 2
    assert output["paired_primary"]["b4_only_failure"] == 1
    assert output["paired_primary"]["b4_minus_b2_risk_difference"] == -0.25
    assert output["method_metrics"]["B2"]["usr_numerator"] == 2
    assert output["method_metrics"]["B2"]["usr_denominator"] == 4
    assert exact_mcnemar_p(2, 1) == 1.0
    assert output["clustered_response_model"]["status"] == "INSUFFICIENT_EPISODE_CLUSTERS"


def test_extra_condition_does_not_increment_independent_n():
    data = dataset()
    extra = copy.deepcopy(data["episodes"][0]["conditions"][0])
    extra.update(condition_id="episode-0-e2", level_index=2)
    data["episodes"][0]["conditions"].append(extra)
    output = analyze(data, plan())
    assert output["independent_episode_count"] == 4


def test_analysis_rejects_unpaired_condition():
    data = dataset()
    del data["episodes"][0]["conditions"][0]["methods"]["B4"]
    with pytest.raises(ValueError, match="paired"):
        analyze(data, plan())


def test_power_simulation_uses_acquired_episodes_and_invalid_rate():
    config = {
        "schema": "crane-evidence-calibration-power-scenarios/v1-development",
        "simulation_seed": 3, "replicates": 100, "alpha": 0.05,
        "acquired_episode_counts": [20],
        "scenarios": [{"scenario_id": "test", "neither": 0.4, "b2_only_failure": 0.4,
                       "b4_only_failure": 0.05, "both": 0.15, "invalid_episode_rate": 0.2}],
    }
    output = simulate(config)
    row = output["results"][0]
    assert row["mean_valid_independent_episodes"] < 20
    assert row["mean_discordant_independent_episodes"] < row["mean_valid_independent_episodes"]
    assert not output["masks_as_independent_samples"]
