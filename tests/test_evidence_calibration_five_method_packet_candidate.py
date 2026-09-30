import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import build_evidence_calibration_five_method_packet_candidate as candidate  # noqa: E402
from build_evidence_calibration_method_packets import build as build_methods  # noqa: E402


def diagnostic(run):
    return json.loads((ROOT / f"data/robot_visible/dev/{run}/command-motion-diagnostic-v3.json").read_text())


def catalog():
    return json.loads((ROOT / candidate.CATALOG).read_text())


def test_fixed_population_and_all_five_packets_reproduce_snapshot():
    result = candidate.build()
    assert result == json.loads((ROOT / candidate.OUTPUT).read_text())
    assert result["inspected_development_episode_count"] == 16
    assert result["within_episode_condition_count"] == 60
    assert result["method_packet_count"] == 300
    assert "cm-land-conf-042" in {row["source_run_id"] for row in result["episodes"]}
    assert result["semantic_method_outputs_generated"] == 0
    assert result["model_calls_authorized"] is False
    assert result["confirmation_independent_n"] == 0


def test_raw_presentation_source_tools_and_verification_flags_preserve_parity():
    source = diagnostic("cm-land-conf-043")
    entries = candidate.materialize(source, "synthetic-configuration", "measured_response_recovery", catalog())
    for entry in entries:
        packets = build_methods(entry, candidate.execution_contract(entry, source))
        by_id = {packet["method_id"]: packet for packet in packets["method_packets"]}
        assert json.loads(by_id["B0"]["presentation"]) == by_id["B1"]["presentation"]
        assert {item["question_instruction"] for item in by_id.values()} == {entry["method_packet"]["question"]}
        for field in ("source_assets", "primitive_tools"):
            assert by_id["B2"][field] == by_id["B3"][field] == by_id["B4"][field]
        assert by_id["B2"]["contract_assets"] == []
        assert by_id["B3"]["contract_assets"] == by_id["B4"]["contract_assets"]
        assert by_id["B3"]["final_claim_verification"] is False
        assert by_id["B4"]["final_claim_verification"] is True


@pytest.mark.parametrize("run", ["cm-land-conf-054", "cm-land-conf-072"])
def test_nominal_projection_integrates_exact_scope_and_catalog_roles(run):
    entries = candidate.materialize(diagnostic(run), "synthetic-configuration", "nominal_false_premise", catalog())
    assert {entry["method_packet"]["question"] for entry in entries} == {candidate.QUESTION}
    for entry in entries:
        text = json.dumps(entry["method_packet"])
        assert "behavior_tree_transitions" not in text and "source_anchors" not in text
        assert "follow_path_failures" not in text and "source_qualified_wait_recoveries" not in text
        assert "five-method-aligned-v1" in entry["condition"]["condition_id"]


@pytest.mark.parametrize("run", ["cm-land-conf-041", "cm-land-conf-048"])
def test_missing_odom_has_no_odometry_or_odom_dependent_computation_at_any_level(run):
    entries = candidate.materialize(diagnostic(run), "synthetic-configuration", "missing_decisive_evidence", catalog())
    assert len(entries) == 3
    for entry in entries:
        assert "delivered_odometry_stream" not in entry["method_packet"]["evidence"]
        assert "command_motion_computation" not in entry["method_packet"]["evidence"]


def test_source_asset_mismatch_fails_closed():
    source = diagnostic("cm-land-conf-043")
    entry = candidate.materialize(source, "synthetic-configuration", "measured_response_recovery", catalog())[0]
    source["source"]["bt_policy_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="exact source/configuration"):
        candidate.execution_contract(entry, source)
