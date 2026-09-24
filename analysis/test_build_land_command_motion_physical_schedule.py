import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "analysis/build_land_command_motion_physical_schedule.py"
SPEC = importlib.util.spec_from_file_location("physical_schedule", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CATALOG_PATH = (
    ROOT
    / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/"
    / "crane_land_proving_ground_v6.json"
)


def _schedule():
    raw = CATALOG_PATH.read_bytes()
    return MODULE.build(json.loads(raw), __import__("hashlib").sha256(raw).hexdigest())


def test_schedule_is_deterministic_and_disjoint():
    first = _schedule()
    assert first == _schedule()
    confirmation, replication = first["cohorts"]
    assert confirmation["fixed_cluster_count"] == 100
    assert replication["fixed_cluster_count"] == 100
    confirmation_ids = {run["layout_id"] for run in confirmation["runs"]}
    replication_ids = {run["layout_id"] for run in replication["runs"]}
    assert not confirmation_ids & replication_ids
    assert MODULE.QUALIFICATION_LAYOUT not in confirmation_ids | replication_ids


def test_tracked_schedule_is_byte_reproducible():
    tracked_path = (
        ROOT
        / "research/explanation_fidelity/experiment_configs/prospective/"
        / "land-command-motion-physical-schedule-v1.json"
    )
    expected = json.dumps(_schedule(), indent=2, sort_keys=True) + "\n"
    assert tracked_path.read_text(encoding="utf-8") == expected


def test_each_cohort_has_fixed_target_distribution():
    for cohort in _schedule()["cohorts"]:
        runs = cohort["runs"]
        families = [run["family"] for run in runs]
        assert families.count("persistent-discrepancy") == 35
        assert families.count("transient-compensation") == 35
        assert families.count("ambiguous-missing-odometry") == 15
        assert families.count("nominal-false-premise") == 15
        assert sum(run["geometry_mechanism"] == "connected-detour" for run in runs) == 50
        assert sum(run["geometry_mechanism"] == "nominal-clear-route" for run in runs) == 50


def test_interventions_and_masks_are_fail_closed():
    for cohort in _schedule()["cohorts"]:
        for run in cohort["runs"]:
            family = run["family"]
            if family == "nominal-false-premise":
                assert run["mobility_hold_after_s"] == -1.0
                assert run["mobility_release_after_s"] == -1.0
            else:
                assert run["mobility_hold_after_s"] in {18.0, 25.0}
                if family == "transient-compensation":
                    assert run["mobility_release_after_s"] == run["mobility_hold_after_s"] + 12.0
                else:
                    assert run["mobility_release_after_s"] == -1.0
            expected_mask = (
                "remove-delivered-odometry-v1"
                if family == "ambiguous-missing-odometry"
                else "none"
            )
            assert run["evidence_mask"] == expected_mask
