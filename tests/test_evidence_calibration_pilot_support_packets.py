import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from build_evidence_calibration_agent_qualification import LEVELS
from build_evidence_calibration_pilot_support_packets import NON_RANK_OPTIONS, build_packet, write_once
from evidence_calibration_io import canonical_sha256


def inputs():
    evidence = {"schema": "crane-normalized-method-evidence/v1", "episode_id": "episode-17",
                "configuration_id": "configuration-17", "question": "What does the record support?",
                "evidence": {"navigate_to_pose_result": {"action_status": "SUCCEEDED",
                                                         "action_result_record_id": "record-19"}}}
    condition = {"condition": {"condition_id": "condition-17", "episode_id": "episode-17",
                               "configuration_id": "configuration-17",
                               "method_packet_sha256": canonical_sha256(evidence)},
                 "method_packet": evidence}
    response = {"response_id": "opaque-response", "method_id": "B2", "condition_id": "condition-17",
                "final_response": "The goal succeeded.", "method_configuration_sha256": None,
                "atomic_claims": [{"claim_id": "ri-opaque", "text": "The goal succeeded.",
                                   "response_span": "The goal succeeded.", "asserted_abstraction_level": None}]}
    rubric = {"rubric_id": "opaque-rubric", "question_text": evidence["question"],
              "required_unit_prompts": ["state the recorded outcome"],
              "abstraction_level_options": list(LEVELS), "limitation_prompts": [],
              "false_premise_applicable": False, "sanitized_physical_facts": [{"action_succeeded": True}]}
    text = "maximum_wait_invocations: 3\n"
    assets = [{"asset_id": "source/nav2.yaml", "text": text,
               "sha256": hashlib.sha256(text.encode()).hexdigest()}]
    return condition, response, rubric, "offline-blinding-salt-long-enough", assets


def test_exact_evidence_sources_and_text_preserved_without_metadata_or_rank_anchors():
    args = inputs()
    before = copy.deepcopy(args)
    packet, key = build_packet(*args)
    assert args == before
    assert packet["highest_level_qualified"] is False
    assert packet["raw_rank_endpoint_use_prohibited"] is True
    assert packet["response_text"] == args[1]["final_response"]
    for form in packet["forms"]:
        assert form["robot_visible_evidence"]["evidence"] == args[0]["method_packet"]["evidence"]
        assert form["robot_visible_evidence"]["exact_source_assets"] == args[-1]
        assert "episode_id" not in form["robot_visible_evidence"]
        assert "configuration_id" not in form["robot_visible_evidence"]
        assert form["abstraction_level_options"] == [*LEVELS, *NON_RANK_OPTIONS]
        assert form["atomic_statements"][0]["asserted_abstraction_level"] is None
    assert '"method_id"' not in json.dumps(packet)
    assert '"claim_id"' not in json.dumps(packet)
    assert key["method_id"] == "B2" and key["join_after_adjudication"] is True
    assert key["packet_set_sha256"] == canonical_sha256(packet)


def test_supplied_levels_invalid_source_bytes_and_changed_spans_fail_closed():
    condition, response, rubric, salt, assets = inputs()
    response["atomic_claims"][0]["asserted_abstraction_level"] = "task_outcome"
    with pytest.raises(ValueError, match="anchors"):
        build_packet(condition, response, rubric, salt, assets)
    response["atomic_claims"][0]["asserted_abstraction_level"] = None
    assets[0]["text"] += "different bytes"
    with pytest.raises(ValueError, match="their hash"):
        build_packet(condition, response, rubric, salt, assets)
    condition, response, rubric, salt, assets = inputs()
    response["atomic_claims"][0]["response_span"] = "invented motion diagnosis"
    with pytest.raises(ValueError, match="verbatim"):
        build_packet(condition, response, rubric, salt, assets)


def test_existing_packet_artifacts_are_never_overwritten(tmp_path):
    path = tmp_path / "packet.json"
    packet, _ = build_packet(*inputs())
    write_once(path, packet)
    original = path.read_bytes()
    write_once(path, packet)
    assert path.read_bytes() == original
    packet["response_text"] = "a different retained answer"
    with pytest.raises(ValueError, match="overwrite"):
        write_once(path, packet)
    assert path.read_bytes() == original
