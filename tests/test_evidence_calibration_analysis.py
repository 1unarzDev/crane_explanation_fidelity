import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from analyze_evidence_calibration import analyze, exact_mcnemar_p  # noqa: E402
from analyze_evidence_calibration_five_methods import analyze_five_methods, holm_adjusted_p  # noqa: E402
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
            "primary_families": ["command_motion"], "control_families": ["nominal"],
            "secondary_families": ["geometry"],
            "clustered_model": "LOGISTIC_CLUSTER_ROBUST_EPISODE",
            "minimum_practically_meaningful_reduction": 0.10,
            "bootstrap_seed": 7, "bootstrap_replicates": 200}


def five_method_dataset():
    data = dataset()
    for index, episode in enumerate(data["episodes"]):
        methods = episode["conditions"][0]["methods"]
        methods["B0"] = response(index != 3)
        methods["B1"] = response(index in (0, 1))
        methods["B3"] = response(index == 0)
    return data


def five_method_declaration():
    return {"schema": "crane-evidence-calibration-five-method-comparisons/v1-development",
            "methods": ["B0", "B1", "B2", "B3", "B4"],
            "primary_comparison": {"comparator": "B2"},
            "secondary_method_comparisons": {"comparators": ["B0", "B1", "B3"]},
            "confirmatory_semantic_output_authorized": False}


def test_five_method_pairs_keep_episode_n_and_report_every_secondary_contrast():
    data = five_method_dataset()
    extra = copy.deepcopy(data["episodes"][0]["conditions"][0])
    extra.update(condition_id="episode-0-e2", level_index=2)
    data["episodes"][0]["conditions"].append(extra)
    output = analyze_five_methods(data, plan(), five_method_declaration())
    assert output["primary_b2_vs_b4"]["independent_episode_count"] == 4
    assert set(output["secondary_method_family"]) == {"B0", "B1", "B3"}
    for row in output["secondary_method_family"].values():
        assert row["independent_paired_episode_count"] == 4
        assert sum(row[key] for key in ("neither_failure", "comparator_only_failure",
                                        "b4_only_failure", "both_failure")) == 4
        assert row["whole_episode_bootstrap_confidence_interval"] is not None
        assert row["holm_adjusted_p_across_three_method_contrasts"] >= row["exact_mcnemar_two_sided_p"]


def test_holm_step_down_and_five_method_parity_fail_closed():
    assert holm_adjusted_p({"B0": 0.01, "B1": 0.04, "B3": 0.03}) == {
        "B0": 0.03, "B3": 0.06, "B1": 0.06}
    data = five_method_dataset()
    del data["episodes"][0]["conditions"][0]["methods"]["B3"]
    with pytest.raises(ValueError, match="exactly B0"):
        analyze_five_methods(data, plan(), five_method_declaration())
    data = five_method_dataset()
    data["episodes"][0]["conditions"][0]["methods"]["B1"]["maximum_justified_rank"] = 2
    with pytest.raises(ValueError, match="same evaluator reference"):
        analyze_five_methods(data, plan(), five_method_declaration())


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


def test_control_and_secondary_episodes_cannot_change_primary_comparison():
    data = dataset()
    baseline = analyze(data, plan())
    for family, b2_failure, b4_failure in [("nominal", False, True), ("geometry", False, True)]:
        item = copy.deepcopy(data["episodes"][0])
        item["episode_id"] = family
        item["mechanism_family"] = family
        item["conditions"][0]["condition_id"] = family + "-e1"
        item["conditions"][0]["methods"] = {
            "B2": response(b2_failure), "B4": response(b4_failure),
        }
        data["episodes"].append(item)
    output = analyze(data, plan())
    assert output["paired_primary"] == baseline["paired_primary"]
    assert output["method_metrics"] == baseline["method_metrics"]
    assert output["independent_episode_count"] == 4
    assert output["total_independent_episode_count"] == 6
    assert output["primary_family_counts"] == {"command_motion": 4}
    assert output["primary_family_weighting"] == "OBSERVED_EPISODE_MIX_DEVELOPMENT_ONLY"
    assert output["nonprimary_family_descriptives"]["nominal"]["B4_episode_failures"] == 1
    assert output["nonprimary_family_descriptives"]["geometry"]["role"] == "secondary"


def test_undeclared_family_cannot_enter_primary_by_default():
    data = dataset()
    data["episodes"][0]["mechanism_family"] = "unregistered"
    with pytest.raises(ValueError, match="no declared analysis role"):
        analyze(data, plan())


def test_missing_required_evidence_fails_even_if_agent_labels_claim_supported():
    data = dataset()
    target = data["episodes"][3]["conditions"][0]["methods"]["B2"]["claims"][0]
    assert target["label"] == "SUPPORTED_BY_VISIBLE_EVIDENCE"
    target["required_minimum_level"] = 2
    output = analyze(data, plan())
    assert output["paired_primary"]["b2_only_failure"] == 3
    assert output["method_metrics"]["B2"]["usr_numerator"] == 3
    assert output["method_metrics"]["B2"]["emvr_numerator"] == 1


def test_paired_methods_cannot_use_different_evaluator_references():
    data = dataset()
    b4 = data["episodes"][0]["conditions"][0]["methods"]["B4"]
    b4["maximum_justified_rank"] = 2
    with pytest.raises(ValueError, match="same evaluator reference"):
        analyze(data, plan())
    b4["maximum_justified_rank"] = 1
    b4["supported_required_available"] = 2
    with pytest.raises(ValueError, match="same evaluator reference"):
        analyze(data, plan())


def test_cluster_model_reports_rank_deficiency_instead_of_fake_level_coefficients():
    data = dataset()
    for index in (0, 2):
        item = copy.deepcopy(data["episodes"][index])
        item["episode_id"] += "-copy"
        item["conditions"][0]["condition_id"] += "-copy"
        data["episodes"].append(item)
    model = analyze(data, plan())["clustered_response_model"]
    assert model["status"] == "RANK_DEFICIENT_DESIGN"
    assert model["design_rank"] == 2
    assert model["required_rank"] == 4
    assert "coefficients" not in model


def test_analysis_rejects_unpaired_condition():
    data = dataset()
    del data["episodes"][0]["conditions"][0]["methods"]["B4"]
    with pytest.raises(ValueError, match="paired"):
        analyze(data, plan())


def test_analysis_rejects_unreviewed_truthy_mechanistic_flags():
    data = dataset()
    data["episodes"][0]["conditions"][0]["methods"]["B2"]["claims"][0]["mechanistic"] = "false"
    with pytest.raises(ValueError, match="mechanistic claim flag"):
        analyze(data, plan())


def test_analysis_rejects_invalid_coverage_and_abstraction_values():
    data = dataset()
    response = data["episodes"][0]["conditions"][0]["methods"]["B2"]
    response["supported_required_available"] = -1
    with pytest.raises(ValueError, match="supported required counts"):
        analyze(data, plan())
    response["supported_required_available"] = 1
    response["highest_asserted_rank"] = True
    with pytest.raises(ValueError, match="diagnostic abstraction ranks"):
        analyze(data, plan())


def test_analysis_rejects_duplicate_ladder_levels_with_distinct_condition_ids():
    data = dataset()
    extra = copy.deepcopy(data["episodes"][0]["conditions"][0])
    extra["condition_id"] = "second-mask-at-same-level"
    data["episodes"][0]["conditions"].append(extra)
    with pytest.raises(ValueError, match="distinct ordered ladder levels"):
        analyze(data, plan())


def test_analysis_does_not_silently_map_uninterpretable_claims_to_nonfailure():
    data = dataset()
    data["episodes"][0]["conditions"][0]["methods"]["B2"]["claims"][0]["label"] = "UNINTERPRETABLE"
    with pytest.raises(ValueError, match="no prospectively bound endpoint mapping"):
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
