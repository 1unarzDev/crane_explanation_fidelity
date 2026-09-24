import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective/"
    / "land-command-motion-physical-cohort-v1.json"
)
AMENDMENT = CONTRACT.with_name("land-command-motion-physical-cohort-v1-amendment-1.json")


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_contract_binds_schedule_and_runtime_sources():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schedule = contract["physical_schedule"]
    assert _sha256(schedule["path"]) == schedule["sha256"]
    assert _sha256(schedule["generator"]) == schedule["generator_sha256"]

    runtime = contract["pinned_runtime"]
    paths = {
        "capture_launcher_sha256": "scripts/run_diagnostic_land_capture.sh",
        "runtime_manifest_builder_sha256": "scripts/build_diagnostic_runtime_manifest.py",
        "player_auditor_sha256": "analysis/validate_diagnostic_player_build.py",
        "binding_auditor_sha256": "analysis/validate_land_scenario_binding.py",
        "nav2_config_sha256": "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        "bt_policy_sha256": "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml",
    }
    for field, path in paths.items():
        assert _sha256(path) == runtime[field]


def test_contract_binds_diagnostic_and_future_language_sources():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    diagnostic = contract["diagnostic_and_reference_freeze"]
    paths = {
        "diagnostic_config_sha256": diagnostic["diagnostic_config"],
        "exporter_sha256": "analysis/export_command_motion_diagnostic.py",
        "shared_recomputation_sha256": "analysis/recompute_command_motion_diagnostic.py",
        "independent_reference_sha256": "analysis/reference_command_motion.py",
        "complete_reference_builder_sha256": "analysis/build_command_motion_reference_v2.py",
        "mask_generator_sha256": "analysis/mask_command_motion_evidence.py",
    }
    for field, path in paths.items():
        assert _sha256(path) == diagnostic[field]

    language = contract["provisional_language_freeze_for_future_activation"]
    assert _sha256("analysis/render_command_motion_candidate_v3.py") == language["P_renderer_sha256"]
    assert _sha256("analysis/run_command_motion_candidate_v3.py") == language["P_R_runner_sha256"]
    assert _sha256(language["R_prompt"]) == language["R_prompt_sha256"]


def test_semantic_activation_and_replication_fail_closed():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "PHYSICAL_CAPTURE_FROZEN_SEMANTIC_ACTIVATION_BLOCKED"
    assert contract["relationship_to_registered_framework"]["semantic_campaign_active"] is False
    assert contract["relationship_to_registered_framework"]["alpha_allocation"] == "UNBOUND"
    assert contract["physical_schedule"]["replication_collection_authorized"] is False
    assert contract["physical_schedule"]["replacements_allowed"] is False


def test_independent_ambiguity_amendment_binds_versioned_adapters():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert amendment["timing"]["ambiguous_runs_already_attempted"] == []
    assert amendment["timing"]["ambiguous_outputs_or_labels_inspected"] is False
    resolution = amendment["resolution"]
    for path_field, hash_field in (
        ("mask", "mask_sha256"),
        ("independent_reference", "independent_reference_sha256"),
        ("complete_reference_builder", "complete_reference_builder_sha256"),
    ):
        assert _sha256(resolution[path_field]) == resolution[hash_field]
