import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v2-multiconfiguration-pilot-v1.json"
AMENDMENT = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v2-multiconfiguration-pilot-v1-amendment-1.json"
AMENDMENT_2 = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v2-multiconfiguration-pilot-v1-amendment-2.json"
AMENDMENT_3 = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v2-multiconfiguration-pilot-v1-amendment-3.json"


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_candidate_v2_pilot_is_bounded_balanced_and_disjoint_from_smoke():
    value = json.loads(DECLARATION.read_text(encoding="utf-8"))
    runs = value["physical_runs_in_fixed_order"]

    assert value["status"] == "PREDECLARED_DEVELOPMENT_ONLY_NOT_RUN"
    assert len(runs) == 6
    assert [run["order"] for run in runs] == list(range(1, 7))
    assert len({run["run_id"] for run in runs}) == 6
    assert len({run["cluster_id"] for run in runs}) == 6
    assert len({run["layout_id"] for run in runs}) == 6
    assert len({run["seed"] for run in runs}) == 6
    assert len({run["ros_domain_id"] for run in runs}) == 6
    assert len({run["ros_port"] for run in runs}) == 6
    assert "diagnostic-candidate-v2-development-nominal-clear-route-001" not in {
        run["layout_id"] for run in runs
    }
    assert sorted(run["family"] for run in runs) == sorted(
        ["persistent-discrepancy"] * 2
        + ["transient-compensation"] * 2
        + ["nominal-false-premise"] * 2
    )
    assert value["paired_ambiguous_variant"]["independent_cluster_increment"] == 0
    assert value["scientific_boundary"]["alpha_consumed"] == 0.0
    assert value["run_contract"]["no_layout_or_run_replacement"] is True


def test_candidate_v2_pilot_hashes_live_inputs_and_keeps_strong_r():
    value = json.loads(DECLARATION.read_text(encoding="utf-8"))
    pinned = value["pinned_software"]
    expected = {
        "candidate_runner_sha256": "analysis/run_command_motion_candidate_v2.py",
        "independent_reference_sha256": "analysis/reference_command_motion.py",
        "shared_diagnostic_adapter_sha256": "analysis/recompute_command_motion_diagnostic.py",
        "repository_agent_prompt_sha256": "research/explanation_fidelity/prompts/diagnostic_repository_agent_command_motion_dev_v2.txt",
        "diagnostic_config_sha256": "configs/diagnostic_command_motion_low_speed_v1.json",
        "catalog_sha256": "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v5.json",
        "nav2_config_sha256": "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        "bt_policy_sha256": "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml",
    }
    for key, relative in expected.items():
        assert pinned[key] == sha256(relative)
    assert pinned["complete_reference_builder_sha256"] == (
        "d7a08fcf03c313c1c15e171ab005a766c6f0987dbe60286a41ce5de7d8efaa98"
    )

    assert value["methods"]["R"].startswith("gpt-6-sol high")
    assert value["methods"]["reasoning_effort"] == "high"
    assert value["methods"]["maximum_calls_per_valid_primary_case"] == 1
    assert value["development_readiness_gate"][
        "required_each_luna_pass_net_p_minus_r_successes"
    ] == 2


def test_pre_run_amendment_binds_actual_launcher_and_parent():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert amendment["parent_declaration_sha256"] == sha256(
        DECLARATION.relative_to(ROOT).as_posix()
    )
    assert amendment["correction"]["launcher_sha256"] == (
        "0629f7bff592fc286954c9cbe92409aaca196289c89ce449c742097752382bb0"
    )
    assert amendment["outcomes_inspected_before_amendment"] is False
    assert amendment["timing"].startswith("before any declared physical run")


def test_post_run_amendment_preserves_run_one_and_pins_future_launcher():
    amendment = json.loads(AMENDMENT_2.read_text(encoding="utf-8"))
    assert amendment["parent_amendment_sha256"] == sha256(
        AMENDMENT.relative_to(ROOT).as_posix()
    )
    assert amendment["correction"]["launcher_sha256"] == sha256(
        "scripts/run_diagnostic_land_capture.sh"
    )
    assert amendment["applies_to_run_ids"] == [
        "cmv2-dev-002",
        "cmv2-dev-003",
        "cmv2-dev-004",
        "cmv2-dev-005",
        "cmv2-dev-006",
    ]
    assert amendment["run_001_disposition"]["rerun_authorized"] is False
    assert amendment["run_001_disposition"]["scenario_binding_postprocessed"] is True


def test_reference_builder_amendment_adds_only_declared_config_provenance():
    amendment = json.loads(AMENDMENT_3.read_text(encoding="utf-8"))
    assert amendment["parent_amendment_sha256"] == sha256(
        AMENDMENT_2.relative_to(ROOT).as_posix()
    )
    assert amendment["correction"]["complete_reference_builder_sha256"] == sha256(
        "analysis/build_command_motion_reference_v2.py"
    )
    assert amendment["model_or_luna_calls_before_amendment"] == 0
    assert amendment["failed_reference_retained"] is True
