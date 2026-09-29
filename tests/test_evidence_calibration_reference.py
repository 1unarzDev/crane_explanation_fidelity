import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_evidence_calibration_reference import build_reference  # noqa: E402
from build_nested_evidence_conditions import build_conditions  # noqa: E402
from evidence_calibration_io import canonical_json_bytes  # noqa: E402


ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
SHA = "2" * 64


def bundle():
    source = {
        "schema": "crane-normalized-method-evidence/v1", "episode_id": "episode-1",
        "configuration_id": "configuration-1", "question": "What is supported?",
        "evidence": {
            "navigate_to_pose_result": {"evidence_ids": ["action"], "status": "aborted"},
            "behavior_tree_transitions": {"evidence_ids": ["recovery"], "wait_count": 2},
            "source_anchors": {"evidence_ids": ["source"]},
            "delivered_command_stream": {"evidence_ids": ["command"], "median_mps": 0.26},
            "delivered_odometry_stream": {"evidence_ids": ["odometry"], "median_mps": 0.0},
            "command_motion_computation": {"evidence_ids": ["diagnostic"], "triggered": True},
            "validated_obstruction_evidence": {"evidence_ids": ["obstruction"], "validated": True},
        },
    }
    conditions = [
        ("e0", ["behavior_tree_transitions", "source_anchors", "delivered_command_stream", "delivered_odometry_stream", "command_motion_computation", "validated_obstruction_evidence"]),
        ("e1", ["delivered_command_stream", "delivered_odometry_stream", "command_motion_computation", "validated_obstruction_evidence"]),
        ("e2", ["delivered_odometry_stream", "command_motion_computation", "validated_obstruction_evidence"]),
        ("e3", ["validated_obstruction_evidence"]),
        ("e4", []),
    ]
    spec = {
        "schema": "crane-nested-evidence-mask-spec/v1", "ladder_id": "motion-v1",
        "condition_builder_id": "builder", "condition_builder_version": "v1",
        "condition_builder_sha256": SHA, "source_configuration_sha256": SHA,
        "runtime_manifest_sha256": SHA,
        "conditions": [
            {"condition_id": identifier, "level_index": index,
             "removed_json_pointers": [f"/evidence/{role}" for role in removed],
             "mask_id": None if not removed else f"mask-{identifier}",
             "mask_version": None if not removed else "v1"}
            for index, (identifier, removed) in enumerate(conditions)
        ],
    }
    return {"schema": "crane-nested-evidence-condition-bundle/v1",
            "conditions": build_conditions(source, spec)}


def reference_input(condition_bundle=None):
    condition_bundle = condition_bundle or bundle()
    requirement_ids = [item["requirement_id"] for item in ONTOLOGY["evidence_requirements"]]
    roles_by_condition = {
        item["condition"]["condition_id"]: set(item["condition"]["available_evidence_ids"])
        for item in condition_bundle["conditions"]
    }
    def evaluations(condition_id):
        available = roles_by_condition[condition_id]
        rows = []
        for identifier in requirement_ids:
            status, refs = "ABSENT", []
            if identifier in {"req-action-result-valid", "req-action-aborted"} and "action" in available:
                status, refs = "SATISFIED", ["action"]
            elif identifier == "req-action-succeeded" and "action" in available:
                status, refs = "CONTRADICTED", ["action"]
            elif identifier in {"req-recovery-trace-valid", "req-recovery-invoked"} and "recovery" in available:
                status, refs = "SATISFIED", ["recovery", "source"]
            elif identifier == "req-command-stream-valid" and "command" in available:
                status, refs = "SATISFIED", ["command"]
            elif identifier == "req-odometry-stream-valid" and "odometry" in available:
                status, refs = "SATISFIED", ["odometry"]
            elif identifier == "req-command-odometry-synchronized" and {"command", "odometry"}.issubset(available):
                status, refs = "SATISFIED", ["command", "odometry"]
            elif identifier in {"req-command-above-threshold", "req-interval-duration-sufficient", "req-measured-response-low"} and "diagnostic" in available:
                status, refs = "SATISFIED", ["diagnostic"]
            elif identifier in {"req-measured-response-recovered", "req-no-failure-triggered"} and "diagnostic" in available:
                status, refs = "CONTRADICTED", ["diagnostic"]
            elif identifier == "req-specific-cause-obstruction" and "obstruction" in available:
                status, refs = "SATISFIED", ["obstruction"]
            rows.append({"requirement_id": identifier, "status": status,
                         "support_references": refs, "detail": "development fixture"})
        return rows
    return {
        "schema": "crane-evidence-calibration-reference-input/v1",
        "reference_id": "reference-1", "reference_builder_id": "independent-reference",
        "reference_builder_version": "v1", "reference_builder_sha256": SHA,
        "physical_truth": {
            "physical_true_claim_ids": ["claim-task-abort", "claim-recovery-invoked",
                                        "claim-command-motion-discrepancy", "claim-external-obstruction"],
            "physical_false_claim_ids": ["claim-task-success", "claim-measured-response-recovered",
                                         "claim-false-premise-success"],
            "truth_assertions": [{"truth_id": "truth-hold", "description": "An obstruction was present."}],
            "truth_source_references": ["evaluator-intervention-manifest"],
        },
        "condition_assessments": [
            {"condition_id": item["condition"]["condition_id"],
             "requirement_evaluations": evaluations(item["condition"]["condition_id"]),
             "optional_supported_claim_ids": [], "ambiguity_claim_ids": [],
             "independent_computation_references": ["independent-computation"]}
            for item in condition_bundle["conditions"]
        ],
    }


def test_reference_separates_truth_from_support_and_deepens_with_evidence():
    condition_bundle = bundle()
    first = build_reference(ONTOLOGY, condition_bundle, reference_input(condition_bundle))
    second = build_reference(ONTOLOGY, condition_bundle, reference_input(condition_bundle))
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["method_visible"] is False
    conditions = {item["condition_id"]: item for item in first["conditions"]}
    assert "claim-command-motion-discrepancy" in conditions["e0"]["physically_true_but_unsupported_claim_ids"]
    assert "claim-external-obstruction" in conditions["e3"]["physically_true_but_unsupported_claim_ids"]
    assert "claim-command-motion-discrepancy" in conditions["e3"]["supported_required_claim_ids"]
    assert "node-command-motion-discrepancy" in conditions["e3"]["highest_defensible_node_ids"]
    assert "node-external-obstruction" in conditions["e4"]["highest_defensible_node_ids"]
    assert conditions["e4"]["reference_state"] == "KNOWN"


def test_support_cannot_cite_evaluator_truth_or_evidence_absent_from_condition():
    condition_bundle = bundle()
    value = reference_input(condition_bundle)
    row = next(item for item in value["condition_assessments"] if item["condition_id"] == "e0")
    requirement = next(item for item in row["requirement_evaluations"] if item["requirement_id"] == "req-command-stream-valid")
    requirement.update(status="SATISFIED", support_references=["evaluator-intervention-manifest"])
    with pytest.raises(ValueError, match="not visible"):
        build_reference(ONTOLOGY, condition_bundle, value)


def test_every_condition_and_requirement_must_be_accounted_for():
    condition_bundle = bundle()
    missing_condition = reference_input(condition_bundle)
    missing_condition["condition_assessments"].pop()
    with pytest.raises(ValueError, match="every evidence condition"):
        build_reference(ONTOLOGY, condition_bundle, missing_condition)
    missing_requirement = reference_input(condition_bundle)
    missing_requirement["condition_assessments"][0]["requirement_evaluations"].pop()
    with pytest.raises(ValueError, match="every registered requirement"):
        build_reference(ONTOLOGY, condition_bundle, missing_requirement)


def test_physical_truth_sets_must_be_disjoint():
    condition_bundle = bundle()
    value = reference_input(condition_bundle)
    value["physical_truth"]["physical_false_claim_ids"].append("claim-task-abort")
    with pytest.raises(ValueError, match="overlap"):
        build_reference(ONTOLOGY, condition_bundle, value)


def test_reference_schema_is_closed_and_method_invisibility_is_constant():
    schema = json.loads((ROOT / "research/explanation_fidelity/schemas/evidence-calibration-reference-v1.schema.json").read_text())
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["method_visible"] == {"const": False}
    assert all(
        definition.get("additionalProperties") is False
        for definition in schema["$defs"].values()
        if definition.get("type") == "object"
    )
    labels = set(schema["$defs"]["claim_evaluation"]["properties"]["support_label"]["enum"])
    assert labels == {
        "SUPPORTED_BY_VISIBLE_EVIDENCE", "CONTRADICTED_BY_VISIBLE_EVIDENCE",
        "INSUFFICIENT_VISIBLE_EVIDENCE", "PHYSICALLY_TRUE_BUT_UNSUPPORTED",
    }
