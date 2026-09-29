import copy
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_nested_evidence_conditions import build_conditions  # noqa: E402
from evidence_calibration_io import canonical_json_bytes  # noqa: E402


SHA = "1" * 64


def source_packet():
    return {
        "schema": "crane-normalized-method-evidence/v1",
        "episode_id": "episode-1",
        "configuration_id": "configuration-1",
        "question": "What is the strongest supported diagnosis?",
        "evidence": {
            "task_outcome": {"evidence_ids": ["action"], "status": "aborted"},
            "recovery_trace": {"evidence_ids": ["recovery"], "wait_count": 2},
            "delivered_commands": {"evidence_ids": ["command"], "median_mps": 0.26},
            "delivered_odometry": {"evidence_ids": ["odometry"], "median_mps": 0.0},
        },
    }


def mask_spec():
    return {
        "schema": "crane-nested-evidence-mask-spec/v1",
        "ladder_id": "command-motion-ladder-v1",
        "condition_builder_id": "nested-evidence-condition-builder",
        "condition_builder_version": "v1",
        "condition_builder_sha256": SHA,
        "source_configuration_sha256": SHA,
        "runtime_manifest_sha256": SHA,
        "conditions": [
            {"condition_id": "e0", "level_index": 0,
             "removed_json_pointers": ["/evidence/recovery_trace", "/evidence/delivered_commands", "/evidence/delivered_odometry"],
             "mask_id": "outcome-only", "mask_version": "v1"},
            {"condition_id": "e1", "level_index": 1,
             "removed_json_pointers": ["/evidence/delivered_commands", "/evidence/delivered_odometry"],
             "mask_id": "without-motion", "mask_version": "v1"},
            {"condition_id": "e2", "level_index": 2,
             "removed_json_pointers": ["/evidence/delivered_odometry"],
             "mask_id": "without-odometry", "mask_version": "v1"},
            {"condition_id": "e3", "level_index": 3,
             "removed_json_pointers": [], "mask_id": None, "mask_version": None},
        ],
    }


def test_build_is_byte_deterministic_nested_and_removal_only():
    source = source_packet()
    first = build_conditions(source, mask_spec())
    second = build_conditions(copy.deepcopy(source), copy.deepcopy(mask_spec()))
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert len(first) == 4
    previous_roles = set()
    previous_ids = set()
    for index, item in enumerate(first):
        condition = item["condition"]
        packet = item["method_packet"]
        roles = set(condition["available_evidence_roles"])
        evidence_ids = set(condition["available_evidence_ids"])
        assert previous_roles.issubset(roles)
        assert previous_ids.issubset(evidence_ids)
        assert packet["episode_id"] == source["episode_id"]
        assert packet["question"] == source["question"]
        for role in roles:
            assert packet["evidence"][role] == source["evidence"][role]
        if index:
            assert condition["parent_condition_id"] == first[index - 1]["condition"]["condition_id"]
        previous_roles, previous_ids = roles, evidence_ids
    assert first[-1]["method_packet"] == source
    assert first[-1]["condition"]["mask_id"] is None


def test_evaluator_fields_are_rejected_at_any_depth():
    source = source_packet()
    source["evidence"]["task_outcome"]["physical_truth"] = "hidden hold"
    with pytest.raises(ValueError, match="evaluator-only"):
        build_conditions(source, mask_spec())


def test_masks_cannot_rewrite_or_target_metadata():
    spec = mask_spec()
    spec["conditions"][0]["removed_json_pointers"] = ["/question"]
    with pytest.raises(ValueError, match="only /evidence"):
        build_conditions(source_packet(), spec)


def test_stronger_conditions_cannot_remove_new_evidence():
    spec = mask_spec()
    spec["conditions"][1]["removed_json_pointers"].append("/evidence/task_outcome")
    with pytest.raises(ValueError, match="only restore"):
        build_conditions(source_packet(), spec)


def test_mask_pointers_must_exist_and_may_not_overlap():
    missing = mask_spec()
    missing["conditions"][0]["removed_json_pointers"][0] = "/evidence/not-present"
    with pytest.raises(ValueError, match="does not exist"):
        build_conditions(source_packet(), missing)
    overlap = mask_spec()
    overlap["conditions"][0]["removed_json_pointers"].extend(["/evidence/delivered_commands/median_mps"])
    with pytest.raises(ValueError, match="contain another"):
        build_conditions(source_packet(), overlap)
