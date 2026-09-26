import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "measurement-complete-composition-v2-physical-screen-v1.json"
)
CATALOG = (
    ROOT
    / "packages/crane_ml/Assets/Resources/ReferenceEnvironments"
    / "crane_land_proving_ground_v5.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_physical_screen_is_frozen_and_clustered_by_scenario_configuration():
    contract = load_contract()
    runs = contract["physical_runs_in_fixed_order"]

    assert contract["status"] == "FROZEN_BEFORE_ANY_EPISODE_OR_MODEL_CALL"
    assert contract["scientific_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert contract["scientific_boundary"]["independent_unit"] == "scenario configuration"
    assert contract["scientific_boundary"]["independent_clusters_planned"] == 6
    assert [run["order"] for run in runs] == list(range(1, 7))
    assert len({run["run_id"] for run in runs}) == 6
    assert len({run["cluster_id"] for run in runs}) == 6
    assert len({run["layout_id"] for run in runs}) == 6
    assert contract["scientific_boundary"]["evidence_masks_add_clusters"] == 0
    assert contract["scientific_boundary"]["luna_passes_add_clusters"] == 0


def test_physical_screen_layouts_match_exact_fresh_v5_catalog_entries():
    contract = load_contract()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    layouts = {layout["id"]: layout for layout in catalog["layouts"]}

    assert sha256(CATALOG) == contract["pinned_software"]["catalog_sha256"]
    for run in contract["physical_runs_in_fixed_order"]:
        layout = layouts[run["layout_id"]]
        assert layout["seed"] == run["seed"]
        assert layout["studySplit"] == "candidate-v2-development"
        assert layout["diagnosticMechanism"] in {
            "connected-detour",
            "nominal-clear-route",
        }

    selected = {run["layout_id"] for run in contract["physical_runs_in_fixed_order"]}
    previously_allocated = {
        *(f"diagnostic-candidate-v2-development-connected-detour-{index:03d}" for index in range(1, 7)),
        "diagnostic-candidate-v2-development-nominal-clear-route-001",
        *(f"diagnostic-candidate-v2-development-nominal-clear-route-{index:03d}" for index in range(2, 8)),
    }
    assert selected.isdisjoint(previously_allocated)


def test_physical_screen_pins_current_treatment_and_capture_bytes():
    contract = load_contract()
    pinned = contract["pinned_software"]
    expected = {
        "capture_launcher_sha256": ROOT / "scripts/run_diagnostic_land_capture.sh",
        "command_motion_exporter_sha256": ROOT / "analysis/export_command_motion_diagnostic.py",
        "geometric_exporter_sha256": ROOT / "analysis/export_geometric_route_diagnostic.py",
        "command_motion_adapter_v2_sha256": ROOT / "analysis/build_command_motion_composition_packet_v2.py",
        "geometric_adapter_v2_sha256": ROOT / "analysis/build_geometric_composition_packet_v2.py",
        "composer_v2_sha256": ROOT / "analysis/compose_diagnostic_hypotheses_v2.py",
        "renderer_v2_sha256": ROOT / "analysis/render_diagnostic_composition_v2.py",
        "registry_sha256": ROOT / "configs/diagnostic_composition_registry_v1.json",
        "nav2_config_sha256": ROOT / "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        "bt_policy_sha256": ROOT / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml",
    }
    assert {name: sha256(path) for name, path in expected.items()} == {
        name: pinned[name] for name in expected
    }


def test_masks_and_calls_cannot_inflate_independent_cluster_count():
    contract = load_contract()
    run_ids = {run["run_id"] for run in contract["physical_runs_in_fixed_order"]}
    for mask in contract["paired_evidence_masks"]:
        assert mask["source_run_id"] in run_ids
        assert mask["independent_cluster_increment"] == 0
    assert contract["method_screen_boundary"]["response_generation_authorized_by_this_file"] is False
    assert contract["scientific_boundary"]["model_generations_add_clusters"] == 0
