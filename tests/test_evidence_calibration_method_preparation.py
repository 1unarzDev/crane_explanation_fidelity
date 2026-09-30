import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import audit_evidence_calibration_method_preparation as preparation
import build_evidence_calibration_five_method_packet_candidate as candidate
from evaluate_command_motion_requirements import evaluate


def test_complete_cohort_reproduces_hash_only_snapshot_and_preserves_boundaries():
    result = preparation.build()
    assert result == json.loads((ROOT / preparation.OUTPUT).read_text())
    assert result["inspected_development_episode_count"] == 16
    assert result["within_episode_condition_count"] == 60
    assert result["prepared_request_count"] == 240
    assert result["staged_workspace_count"] == 300
    assert result["b2_complete_request_bound"] is False
    assert result["harness_confinement_verified"] is False
    assert result["model_calls_authorized"] is False
    assert result["semantic_method_outputs_generated"] == 0
    assert "cm-land-conf-042" in {row["source_run_id"] for row in result["conditions"]}
    assert len({row["configuration_id"] for row in result["conditions"]}) == 16
    for row in result["conditions"]:
        assert set(row["requests"]) == {"B0", "B1", "B3", "B4"}
        assert {method: value["file_count"] for method, value in row["workspaces"].items()} == {
            "B0": 0, "B1": 0, "B2": 5, "B3": 6, "B4": 6}
        assert all(value["token_fit"] is None for value in row["requests"].values())
        assert all(set(value) == {"request_sha256", "prompt_utf8_bytes", "token_fit"} for value in row["requests"].values())


@pytest.mark.parametrize("run,family", [
    ("cm-land-conf-042", "persistent_command_motion_discrepancy"),
    ("cm-land-conf-043", "measured_response_recovery"),
    ("cm-land-conf-041", "missing_decisive_evidence"),
    ("cm-land-conf-054", "nominal_false_premise")])
def test_visible_plan_retains_each_family_evidence_boundary(run, family):
    ontology = json.loads((ROOT / candidate.ONTOLOGY).read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    diagnostic = json.loads((ROOT / f"data/robot_visible/dev/{run}/command-motion-diagnostic-v3.json").read_text())
    for entry in candidate.materialize(diagnostic, "test-configuration", family, catalog):
        question = {"question_id": "test", "failure_premise": True,
                    "required_mechanism_families": ["false_premise"] if family == "nominal_false_premise" else ["command_motion"]}
        facts = evaluate(ontology, entry, question)
        original = copy.deepcopy((ontology, entry, facts))
        result, plan = preparation.visible_plan(ontology, entry, facts)
        assert (ontology, entry, facts) == original
        level = entry["condition"]["level_index"]
        claims = set(plan["required_claim_ids"])
        assert ("claim-command-motion-discrepancy" in claims) == (level == 3)
        assert ("claim-measured-response-recovered" in claims) == (family == "measured_response_recovery" and level == 3)
        assert ("claim-false-premise-success" in claims) == (family == "nominal_false_premise" and level == 2)
        assert "claim-motor-failure" not in claims
        assert len(plan["approved_numeric_values"]) == (4 if level == 3 else 0)
        assert plan["required_non_entailment_ids"] == result["required_non_entailment_ids"]
        stale = copy.deepcopy(facts)
        stale["method_packet_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="bind"):
            preparation.visible_plan(ontology, entry, stale)
