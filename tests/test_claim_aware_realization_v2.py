from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from realize_evidence_calibrated_explanation import realize as realize_v1  # noqa: E402
from realize_evidence_calibrated_explanation_v2 import realize as realize_v2  # noqa: E402
from audit_claim_aware_realization_v2 import MANIFEST, audit  # noqa: E402

SPEC = importlib.util.spec_from_file_location("realization_fixtures", ROOT / "tests/test_claim_aware_realization.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURES)


def example():
    result = FIXTURES.diagnostic()
    plan = FIXTURES.plan(result)
    clauses = [
        {"clause_id": "keep-outcome", "kind": "CLAIM", "contract_id": "claim-task-abort", "numeric_values": []},
        {"clause_id": "candidate-discrepancy", "kind": "CLAIM", "contract_id": "claim-command-motion-discrepancy",
         "numeric_values": [{"slot_id": item["slot_id"], "value": item["value"], "unit": item["unit"]}
                            for item in plan["approved_numeric_values"]]},
    ] + [{"clause_id": f"keep-limit-{identifier}", "kind": "NON_ENTAILMENT",
          "contract_id": identifier, "numeric_values": []} for identifier in plan["required_non_entailment_ids"]]
    return result, plan, FIXTURES.candidate(plan, clauses)


def test_preserve_v1_nan_audit_defect_as_synthetic_regression():
    result, plan, candidate = example()
    candidate["clauses"][1]["numeric_values"][0]["value"] = float("nan")
    output = realize_v1(FIXTURES.ONTOLOGY, result, plan, candidate)
    assert output["audit"]["status"] == "ACCEPTED"
    assert output["audit"]["numeric_mismatches"] == ()
    assert "0.25 m/s" in output["final_response"]


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_v2_nonfinite_number_repairs_only_affected_claim(invalid):
    result, plan, candidate = example()
    before = deepcopy(candidate)
    candidate["clauses"][1]["numeric_values"][0]["value"] = invalid
    output = realize_v2(FIXTURES.ONTOLOGY, result, plan, candidate)
    assert output["realizer_version"] == "v2-development-finite-numbers"
    assert output["audit"]["status"] == "REPAIRED"
    assert "claim-command-motion-discrepancy:commanded_speed" in output["audit"]["numeric_mismatches"]
    assert output["final_clauses"][0]["clause_id"] == "keep-outcome"
    assert all(any(retained["clause_id"] == clause["clause_id"] for retained in output["final_clauses"])
               for clause in before["clauses"][2:])
    assert any(clause["clause_id"] == "repair-claim-claim-command-motion-discrepancy"
               for clause in output["final_clauses"])
    assert "0.25 m/s" in output["final_response"]
    assert "nan" not in output["final_response"].lower()
    assert "inf" not in output["final_response"].lower()


def test_finite_candidate_outputs_are_identical_except_version():
    result, plan, candidate = example()
    old = realize_v1(FIXTURES.ONTOLOGY, result, plan, candidate)
    new = realize_v2(FIXTURES.ONTOLOGY, result, plan, candidate)
    new["realizer_version"] = old["realizer_version"]
    assert new == old


def test_v2_still_rejects_invalid_approved_plan_values():
    result, plan, candidate = example()
    plan["approved_numeric_values"][0]["value"] = float("nan")
    with pytest.raises(ValueError, match="finite numeric value"):
        realize_v2(FIXTURES.ONTOLOGY, result, plan, candidate)


def test_prospective_diff_preserves_old_realizer_and_closed_scope():
    result = audit()
    assert result["source_changes"] == 3
    assert result["old_realizer_changed"] is False
    assert result["new_version_used_in_pilot"] is False


def test_repair_cannot_claim_a_retrospective_rescore(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    manifest["old_outputs_rescored"] = True
    path = tmp_path / "modified.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(path)
