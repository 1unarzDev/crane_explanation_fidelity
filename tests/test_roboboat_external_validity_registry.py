import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research/explanation_fidelity/experiment_configs/prospective/roboboat-diagnostic-external-validity-v1-narrow-freeze.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_narrow_arm_is_exact_frozen_and_separate_from_land() -> None:
    value = load_registry()
    assert value["status"] == "NARROW_ARM_FROZEN"
    relation = value["relationship_to_land"]
    assert relation["counts_toward_land_n"] is False
    assert relation["reserved_land_replication"] is False
    assert relation["land_alpha_consumed"] == 0.0
    assert value["accounting"]["physical_configurations"] == 4
    assert value["accounting"]["masked_control_independent_n"] == 0


def test_configuration_and_cluster_identities_are_unique_and_ordered() -> None:
    value = load_registry()
    rows = value["ordered_configurations"]
    identifiers = [row["configuration_id"] for row in rows]
    assert len(identifiers) == len(set(identifiers)) == 4
    assert [row["order"] for row in rows] == [1, 2, 3, 4]
    assert identifiers == value["accounting"]["fixed_order"]
    assert all(row["cluster_id"] for row in rows)
    assert all(row["independent_physical_configuration"] is True for row in rows)


def test_masks_are_clustered_with_physical_parent_and_add_no_n() -> None:
    value = load_registry()
    rows = {row["configuration_id"]: row for row in value["ordered_configurations"]}
    for control in value["evidence_mask_controls"]:
        parent = rows[control["physical_parent"]]
        assert control["cluster_id"] == parent["cluster_id"]
        assert control["independent_n_added"] == 0


def test_frozen_source_inputs_match_declared_hashes() -> None:
    value = load_registry()["platform_identity"]
    for key in ("launcher", "fixture", "nav2_profile", "known_path"):
        item = value[key]
        assert sha256(ROOT / item["path"]) == item["sha256"]


def test_workers_have_distinct_domains_ports_roots_and_run_ids() -> None:
    rows = load_registry()["ordered_configurations"]
    for key in ("CRANE_ROS_DOMAIN_ID", "CRANE_ROS_PORT", "CRANE_RESULT_ROOT", "CRANE_RUN_ID"):
        values = [row["launch_values"][key] for row in rows]
        assert len(values) == len(set(values))
    assert all(0 <= int(row["launch_values"]["CRANE_ROS_DOMAIN_ID"]) <= 232 for row in rows)


def test_only_declared_terminal_margin_override_changes_profile() -> None:
    rows = {row["configuration_id"]: row for row in load_registry()["ordered_configurations"]}
    assert "CRANE_NAV2_CONTROLLER_EXTRA_ARGS" not in rows["boat-ext-narrow-002"]["launch_values"]
    assert rows["boat-ext-narrow-003"]["launch_values"]["CRANE_NAV2_CONTROLLER_EXTRA_ARGS"] == "-p goal_checker.xy_goal_tolerance:=0.40"
