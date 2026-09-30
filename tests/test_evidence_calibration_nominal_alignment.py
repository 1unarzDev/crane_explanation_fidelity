"""Prospective nominal packet integrity; no model output or old-response rescoring."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import build_evidence_calibration_nominal_alignment as module
from build_nested_evidence_conditions import _remove_pointer
from evidence_calibration_io import canonical_sha256
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from inspect_evidence_calibration_packet import summarize

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "configs/evidence_calibration_ladders_v1_development.json").read_text())
ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
CONTRACT = {"question_id": "nominal-check", "failure_premise": True, "required_mechanism_families": ["false_premise"]}


def diagnostic(episode="cm-land-conf-072"):
    return json.loads((ROOT / f"data/robot_visible/dev/{episode}/command-motion-diagnostic-v3.json").read_text())


def test_projection_removes_duplicate_trace_facts_and_preserves_every_surviving_value():
    source = diagnostic()
    before = copy.deepcopy(source)
    projected, removed, original = module.project(source, "configuration")
    assert source == before and len(removed) == 5
    replay = copy.deepcopy(original)
    for pointer in sorted(removed, key=lambda p: (p.rsplit("/", 1)[0], int(p.rsplit("/", 1)[1]) if p.rsplit("/", 1)[1].isdigit() else -1), reverse=True):
        _remove_pointer(replay, pointer)
    assert projected == replay
    for role in ("navigate_to_pose_result", "delivered_command_stream", "delivered_odometry_stream"):
        assert projected["evidence"][role] == original["evidence"][role]
    summary = summarize(projected)
    computation = summary["roles"]["command_motion_computation"]
    assert {item["id"] for item in computation["measurements"]} == module.NOMINAL_MEASUREMENTS
    assert "execution_sequence" not in json.dumps(summary)
    assert "follow_path_failures" not in json.dumps(summary) and "source_qualified_wait_recoveries" not in json.dumps(summary)


@pytest.mark.parametrize("episode", ["cm-land-conf-054", "cm-land-conf-072"])
def test_both_nominal_ladders_match_catalog_with_new_ids_and_invariant_question(episode):
    conditions, audit = module.materialize(diagnostic(episode), "configuration", CATALOG)
    assert audit["materialization_audit"]["status"] == "PASS_CATALOG_BOUND_DEVELOPMENT_ONLY"
    assert len(conditions) == 3 and {entry["method_packet"]["question"] for entry in conditions} == {module.QUESTION}
    assert [entry["condition"]["condition_id"] for entry in conditions] == [f"{diagnostic(episode)['episode_id']}-nominal-aligned-v1-E{i}" for i in range(3)]
    assert "succeeded" not in module.QUESTION.lower()
    for index, entry in enumerate(conditions):
        result = diagnose(ONTOLOGY, entry, evaluate(ONTOLOGY, entry, CONTRACT))
        assert "claim-task-success" in result["approved_claim_ids"]
        assert ("claim-false-premise-success" in result["approved_claim_ids"]) == (index == 2)
        assert "claim-command-motion-discrepancy" not in result["approved_claim_ids"]
        assert "claim-measured-response-recovered" not in result["approved_claim_ids"]


def test_removing_nontrigger_computation_removes_false_premise_license():
    conditions, _ = module.materialize(diagnostic(), "configuration", CATALOG)
    entry = copy.deepcopy(conditions[-1])
    del entry["method_packet"]["evidence"]["command_motion_computation"]
    entry["condition"]["available_evidence_roles"] = tuple(role for role in entry["condition"]["available_evidence_roles"] if role != "command_motion_computation")
    entry["condition"]["method_packet_sha256"] = canonical_sha256(entry["method_packet"])
    result = diagnose(ONTOLOGY, entry, evaluate(ONTOLOGY, entry, CONTRACT))
    assert "claim-false-premise-success" not in result["approved_claim_ids"]
    assert "claim-task-success" in result["approved_claim_ids"]


def test_projection_rejects_invalid_sources_and_unregistered_computation_shapes():
    for field in ("samples", "provenance"):
        data = diagnostic()
        data["method_input"]["odometry_" + field] = [] if field == "samples" else None
        with pytest.raises(ValueError, match="valid delivered"):
            module.project(data, "configuration")
    data = diagnostic()
    data["diagnostic_result"]["measurements"].append({"id": "undeclared_extra_trace_fact"})
    with pytest.raises(ValueError, match="inventory changed"):
        module.project(data, "configuration")
    data = diagnostic()
    data["diagnostic_result"]["disposition"] = "known"
    with pytest.raises(ValueError, match="nominal command-motion"):
        module.project(data, "configuration")
    with pytest.raises(ValueError, match="question scope"):
        module.project(diagnostic(), "configuration", "Was there any navigation failure?")


def test_saved_audit_reconstructs_old_hashes_and_preserves_all_six_mismatches():
    output = module.build()
    assert output == json.loads((ROOT / module.AUDIT).read_text())
    assert sum(row["old_role_mismatch_count"] for row in output["episodes"]) == 6
    assert output["semantic_method_outputs_generated"] == 0 and output["old_responses_rescored"] is False
    assert output["fresh_five_method_development_run_complete"] is False
    assert all(len(row["conditions"]) == 3 for row in output["episodes"])
