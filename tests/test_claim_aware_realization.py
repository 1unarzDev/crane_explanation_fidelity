import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from evidence_calibration_io import canonical_sha256  # noqa: E402
from maximal_supported_diagnosis import diagnose  # noqa: E402
from realize_evidence_calibrated_explanation import realize  # noqa: E402


SPEC = importlib.util.spec_from_file_location(
    "diagnosis_fixtures", ROOT / "tests/test_maximal_supported_diagnosis.py"
)
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)
ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())


def diagnostic():
    current = FIXTURES.entry("e3")
    return diagnose(ONTOLOGY, current, FIXTURES.fact_packet(current))


def plan(result):
    evaluation = next(row for row in result["claim_evaluations"]
                      if row["claim_id"] == "claim-command-motion-discrepancy")
    reference = evaluation["support_references"][0]
    return {
        "schema": "crane-claim-realization-plan/v1",
        "plan_id": "plan-e3-v1",
        "diagnostic_result_sha256": canonical_sha256(result),
        "required_claim_ids": ["claim-task-abort", "claim-command-motion-discrepancy"],
        "optional_claim_ids": [],
        "required_non_entailment_ids": result["required_non_entailment_ids"],
        "approved_numeric_values": [
            {"claim_id": "claim-command-motion-discrepancy", "slot_id": slot,
             "value": value, "unit": unit, "support_reference": reference}
            for slot, value, unit in (
                ("commanded_speed", 0.25, "m/s"), ("measured_speed", 0.01, "m/s"),
                ("interval_start", 2.0, "s"), ("interval_end", 5.0, "s"),
            )
        ],
    }


def candidate(current_plan, clauses):
    return {"schema": "crane-claim-realization-candidate/v1", "response_id": "response-e3-P",
            "plan_sha256": canonical_sha256(current_plan), "clauses": clauses}


def test_valid_constrained_realization_preserves_claims_numbers_and_limits():
    result = diagnostic()
    current_plan = plan(result)
    clauses = [
        {"clause_id": "c1", "kind": "CLAIM", "contract_id": "claim-task-abort",
         "numeric_values": []},
        {"clause_id": "c2", "kind": "CLAIM", "contract_id": "claim-command-motion-discrepancy",
         "numeric_values": [{"slot_id": row["slot_id"], "value": row["value"], "unit": row["unit"]}
                            for row in current_plan["approved_numeric_values"]]},
    ] + [
        {"clause_id": f"limit-{identifier}", "kind": "NON_ENTAILMENT",
         "contract_id": identifier, "numeric_values": []}
        for identifier in current_plan["required_non_entailment_ids"]
    ]
    output = realize(ONTOLOGY, result, current_plan, candidate(current_plan, clauses))
    assert output["audit"]["status"] == "ACCEPTED"
    assert "0.25 m/s" in output["final_response"]
    assert set(output["audit"]["represented_required_claim_ids"]) == set(current_plan["required_claim_ids"])
    assert not output["audit"]["missing_limitation_ids"]


def test_bad_clause_is_removed_and_only_missing_content_is_reconstructed():
    result = diagnostic()
    current_plan = plan(result)
    clauses = [
        {"clause_id": "keep", "kind": "CLAIM", "contract_id": "claim-task-abort",
         "numeric_values": []},
        {"clause_id": "unsupported", "kind": "CLAIM", "contract_id": "claim-motor-failure",
         "numeric_values": []},
        {"clause_id": "wrong-number", "kind": "CLAIM",
         "contract_id": "claim-command-motion-discrepancy",
         "numeric_values": [{"slot_id": row["slot_id"],
                             "value": 99 if row["slot_id"] == "commanded_speed" else row["value"],
                             "unit": row["unit"]} for row in current_plan["approved_numeric_values"]]},
    ]
    output = realize(ONTOLOGY, result, current_plan, candidate(current_plan, clauses))
    assert output["audit"]["status"] == "REPAIRED"
    assert output["final_clauses"][0]["clause_id"] == "keep"
    assert "claim-motor-failure" not in output["final_response"]
    assert "claim-motor-failure" in output["audit"]["unapproved_claim_ids"]
    assert any(item.startswith("claim-command-motion-discrepancy:")
               for item in output["audit"]["numeric_mismatches"])
    assert any(item["clause_id"].startswith("repair-claim-") for item in output["final_clauses"])
    assert len(output["final_clauses"]) > 2


def test_plan_cannot_omit_numeric_slots_or_required_non_entailments():
    result = diagnostic()
    current_plan = plan(result)
    current_plan["approved_numeric_values"].pop()
    current_plan["diagnostic_result_sha256"] = canonical_sha256(result)
    with pytest.raises(ValueError, match="every numeric slot"):
        realize(ONTOLOGY, result, current_plan, candidate(current_plan, []))


def test_candidate_is_hash_bound_to_plan():
    result = diagnostic()
    current_plan = plan(result)
    draft = candidate(current_plan, [])
    draft["plan_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="not bound"):
        realize(ONTOLOGY, result, current_plan, draft)
