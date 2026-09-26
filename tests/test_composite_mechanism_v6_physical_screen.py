import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/composite-mechanism-v6-physical-screen-v1.json"
CATALOG = ROOT / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v6.json"
SCHEDULE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json"
AMENDMENT_1 = ROOT / "research/explanation_fidelity/experiment_configs/development/composite-mechanism-v6-physical-screen-v1-amendment-1.json"
AMENDMENT_2 = ROOT / "research/explanation_fidelity/experiment_configs/development/composite-mechanism-v6-physical-screen-v1-amendment-2.json"
RUN_001_DISPOSITION = ROOT / "manifests/data/cmcv6-dev-001-disposition.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_allocated_layouts_exist_and_do_not_overlap_frozen_schedules():
    declaration = _load(DECLARATION)
    catalog = _load(CATALOG)
    schedule = _load(SCHEDULE)

    catalog_by_id = {layout["id"]: layout for layout in catalog["layouts"]}
    allocated = {run["layout_id"] for run in declaration["fixed_runs"]}
    scheduled = {
        run["layout_id"]
        for cohort in schedule["cohorts"]
        for run in cohort["runs"]
    }

    assert len(allocated) == 7
    assert allocated.isdisjoint(scheduled)
    for run in declaration["fixed_runs"]:
        layout = catalog_by_id[run["layout_id"]]
        assert layout["seed"] == run["layout_seed"]
        assert layout["diagnosticMechanism"] == run["geometry"]
        assert layout["studySplit"] == declaration["allocation"]["source_split_label"]


def test_declaration_binds_current_catalog_schedule_and_implementation_bytes():
    declaration = _load(DECLARATION)
    assert declaration["allocation"]["catalog_sha256"] == _sha256(CATALOG)
    assert declaration["allocation"]["frozen_schedule_sha256"] == _sha256(SCHEDULE)

    paths = {
        "composer": ROOT / "analysis/compose_diagnostic_hypotheses_v2.py",
        "renderer": ROOT / "analysis/render_diagnostic_composition_v2.py",
        "geometric_adapter": ROOT / "analysis/build_geometric_composition_packet_v5.py",
        "command_motion_adapter": ROOT / "analysis/build_command_motion_composition_packet_v2.py",
    }
    for key, path in paths.items():
        assert declaration["candidate"]["implementation_hashes_at_declaration"][key] == _sha256(path)


def test_fixed_order_and_statistical_units_are_unique_and_fail_closed():
    declaration = _load(DECLARATION)
    runs = declaration["fixed_runs"]
    assert [run["order"] for run in runs] == list(range(1, 8))
    assert len({run["run_id"] for run in runs}) == len(runs)
    assert len({run["cluster_id"] for run in runs}) == len(runs)
    assert len({run["layout_seed"] for run in runs}) == len(runs)
    assert len({run["ros_domain_id"] for run in runs}) == len(runs)
    assert len({run["ros_tcp_port"] for run in runs}) == len(runs)
    assert declaration["scientific_boundary"]["one_attempt_per_configuration_no_replacement"] is True
    assert declaration["promotion_gate_to_a_later_prospective_protocol"]["required_consensus_p_win_clusters"] == 2
    assert all(mask["independent_cluster_increment"] == 0 for mask in declaration["planned_within_cluster_masks"])


def test_failed_preflight_does_not_count_as_a_physical_attempt():
    amendment = _load(AMENDMENT_1)
    assert amendment["status"] == "RECORDED_BEFORE_REBUILD_OR_PHYSICAL_LAUNCH"
    assert amendment["preflight_result"]["physical_attempt_increment"] == 0
    assert amendment["preflight_result"]["independent_cluster_increment"] == 0
    assert amendment["preflight_result"]["robot_episode_created"] is False
    assert amendment["preflight_result"]["model_or_judge_calls"] == 0
    assert amendment["prospective_resolution"]["source_commit"] == "05a1161e4b5a3ad6bbefe1c635507e7061ea8d58"


def test_rebuilt_player_is_pinned_before_first_physical_launch():
    amendment = _load(AMENDMENT_2)
    assert amendment["status"] == "FROZEN_BEFORE_FIRST_PHYSICAL_LAUNCH"
    assert amendment["build"]["source_dirty"] is False
    assert amendment["build"]["audit_accepted"] is True
    assert amendment["build"]["audit_failed_checks"] == []
    assert amendment["build"]["catalog_sha256"] == _sha256(CATALOG)
    assert amendment["build"]["large_player_retained_in_dvc"] is False


def test_run_001_retains_supported_execution_and_insufficient_geometry():
    result = _load(RUN_001_DISPOSITION)
    assert result["attempt_count"] == 1
    assert result["retry_or_replacement_performed"] is False
    assert result["admission"]["recording_valid_under_worker_result_gate"] is True
    assert result["command_motion_reference"]["independent_disposition"] == "supported"
    assert result["geometric_reference"]["proposed_disposition"] == "insufficient"
    assert result["geometric_reference"]["direct_route_fully_covered"] is False
    assert result["screen_consequence"]["composite_positive_clusters"] == 0
    assert result["screen_consequence"]["language_responses"] == 0
