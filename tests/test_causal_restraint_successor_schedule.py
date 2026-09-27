import json
from pathlib import Path

from analysis.build_causal_restraint_successor_schedule import build


ROOT = Path(__file__).resolve().parents[1]
V6 = ROOT / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v6.json"
V8 = ROOT / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v8.json"
OLD = ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_successor_schedule_is_disjoint_balanced_and_preserves_original_replication():
    value = build(load(V6), load(V8), load(OLD), {})
    assert value["stage_counts"] == {
        "pilot": {"total": 20, "primary": 16, "controls": 4},
        "discovery": {"total": 60, "primary": 48, "controls": 12},
        "replication": {"total": 60, "primary": 48, "controls": 12},
    }
    old_replication = {
        item["layout_id"] for item in load(OLD)["cohorts"][1]["runs"]
    }
    pilot = value["stages"]["pilot"]
    assert not old_replication.intersection(item["layout_id"] for item in pilot)
    all_layouts = [
        item["layout_id"]
        for stage in value["stages"].values()
        for item in stage
    ]
    assert len(all_layouts) == len(set(all_layouts)) == 140


def test_each_successor_stage_balances_geometry_family_and_timing():
    value = build(load(V6), load(V8), load(OLD), {})
    expected = {
        "pilot": {"persistent_command_motion_discrepancy": 4, "measured_response_recovery": 4,
                  "missing_decisive_or_ambiguous_evidence": 1,
                  "nominal_false_premise_or_irrelevant_obstacle": 1},
        "discovery": {"persistent_command_motion_discrepancy": 12, "measured_response_recovery": 12,
                      "missing_decisive_or_ambiguous_evidence": 3,
                      "nominal_false_premise_or_irrelevant_obstacle": 3},
        "replication": {"persistent_command_motion_discrepancy": 12, "measured_response_recovery": 12,
                        "missing_decisive_or_ambiguous_evidence": 3,
                        "nominal_false_premise_or_irrelevant_obstacle": 3},
    }
    for stage, rows in value["stages"].items():
        for geometry in ("connected-detour", "nominal-clear-route"):
            selected = [item for item in rows if item["geometry_mechanism"] == geometry]
            assert {family: sum(item["family"] == family for item in selected)
                    for family in expected[stage]} == expected[stage]
        for item in rows:
            if item["family"] == "measured_response_recovery":
                assert item["mobility_release_after_s"] == item["mobility_hold_after_s"] + 12.0
            elif item["family"] == "nominal_false_premise_or_irrelevant_obstacle":
                assert item["mobility_hold_after_s"] == item["mobility_release_after_s"] == -1.0


def test_successor_schedule_generation_is_deterministic():
    left = build(load(V6), load(V8), load(OLD), {})
    right = build(load(V6), load(V8), load(OLD), {})
    assert left == right
