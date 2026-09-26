import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "coverage-complete-v4-physical-screen-v1.json"
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


def test_successor_screen_is_fixed_development_only_and_clustered() -> None:
    contract = load_contract()
    boundary = contract["scientific_boundary"]
    runs = contract["physical_runs_in_fixed_order"]

    assert contract["status"] == "FROZEN_BEFORE_ANY_EPISODE_OR_MODEL_CALL"
    assert boundary["confirmatory"] is False
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0
    assert boundary["confirmation_or_replication_reserves_consumed"] is False
    assert boundary["independent_unit"] == "scenario configuration"
    assert boundary["independent_clusters_planned"] == 5
    assert [run["order"] for run in runs] == list(range(1, 6))
    assert len({run["run_id"] for run in runs}) == 5
    assert len({run["cluster_id"] for run in runs}) == 5
    assert len({run["layout_id"] for run in runs}) == 5
    for field in (
        "question_variants_add_clusters",
        "evidence_masks_add_clusters",
        "model_generations_add_clusters",
        "luna_passes_add_clusters",
    ):
        assert boundary[field] == 0


def test_successor_screen_uses_only_declared_fresh_v5_layouts() -> None:
    contract = load_contract()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    layouts = {layout["id"]: layout for layout in catalog["layouts"]}
    assert sha256(CATALOG) == contract["pinned_software"]["catalog_sha256"]

    expected = {
        *(f"diagnostic-candidate-v2-development-connected-detour-{i:03d}" for i in range(10, 13)),
        *(f"diagnostic-candidate-v2-development-nominal-clear-route-{i:03d}" for i in range(11, 13)),
    }
    selected = {run["layout_id"] for run in contract["physical_runs_in_fixed_order"]}
    assert selected == expected
    for run in contract["physical_runs_in_fixed_order"]:
        layout = layouts[run["layout_id"]]
        assert layout["seed"] == run["seed"]
        assert layout["studySplit"] == "candidate-v2-development"
        assert layout["diagnosticMechanism"] in {"connected-detour", "nominal-clear-route"}


def test_successor_screen_pins_current_capture_treatment_and_mask_bytes() -> None:
    pinned = load_contract()["pinned_software"]
    expected = {
        "capture_launcher_sha256": ROOT / "scripts/run_diagnostic_land_capture.sh",
        "command_motion_exporter_sha256": ROOT / "analysis/export_command_motion_diagnostic.py",
        "geometric_exporter_sha256": ROOT / "analysis/export_geometric_route_diagnostic.py",
        "command_motion_adapter_v2_sha256": ROOT / "analysis/build_command_motion_composition_packet_v2.py",
        "geometric_adapter_v4_sha256": ROOT / "analysis/build_geometric_composition_packet_v4.py",
        "composer_v2_sha256": ROOT / "analysis/compose_diagnostic_hypotheses_v2.py",
        "renderer_v2_sha256": ROOT / "analysis/render_diagnostic_composition_v2.py",
        "registry_sha256": ROOT / "configs/diagnostic_composition_registry_v1.json",
        "geometric_masker_sha256": ROOT / "analysis/mask_geometric_costmap_evidence.py",
        "command_motion_masker_v2_sha256": ROOT / "analysis/mask_command_motion_evidence_v2.py",
        "nav2_config_sha256": ROOT / "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        "bt_policy_sha256": ROOT / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml",
    }
    assert {name: sha256(path) for name, path in expected.items()} == {
        name: pinned[name] for name in expected
    }


def test_successor_masks_do_not_inflate_cluster_count() -> None:
    contract = load_contract()
    run_ids = {run["run_id"] for run in contract["physical_runs_in_fixed_order"]}
    assert len(contract["paired_evidence_masks"]) == 2
    for mask in contract["paired_evidence_masks"]:
        assert mask["source_run_id"] in run_ids
        assert mask["independent_cluster_increment"] == 0
    assert contract["method_screen_boundary"]["response_generation_authorized_by_this_file"] is False
