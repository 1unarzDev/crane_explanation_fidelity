import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
SOURCE = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())


def test_pilot_selection_is_source_ordered_and_family_quota_complete():
    runs = [item for item in SOURCE["cohorts"][0]["runs"] if 41 <= item["order"] <= 100]
    invalid = set(PILOT["selection"]["retained_invalid_excluded_by_rule"])
    mapping = {
        "persistent_command_motion_discrepancy": "persistent-discrepancy",
        "measured_response_recovery": "transient-compensation",
        "missing_decisive_evidence": "ambiguous-missing-odometry",
        "nominal_false_premise": "nominal-false-premise",
    }
    expected = []
    for family, quota in PILOT["selection"]["family_quotas"].items():
        matches = [item["run_id"] for item in runs
                   if item["family"] == mapping[family] and item["run_id"] not in invalid]
        expected.extend(matches[:quota])
    assert PILOT["selection"]["episode_ids"] == expected
    assert len(expected) == PILOT["independent_episode_count"] == 16


def test_pilot_is_development_only_and_counts_ladders_within_episode():
    assert PILOT["status"] == "PREDECLARED_NOT_RUN"
    assert PILOT["confirmation_alpha"] == 0.0
    assert PILOT["annotation"]["independent_humans"] == 2
    assert not PILOT["annotation"]["pilot_significance_required"]
    assert PILOT["independent_unit"] == "episode_configuration"
    assert all(len(ladder) >= 3 for ladder in PILOT["evidence_ladders"].values())
