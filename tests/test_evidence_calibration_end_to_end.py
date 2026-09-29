import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_atomic_claim_annotation_packets import build as build_annotation  # noqa: E402
from build_evidence_calibration_method_packets import build as build_methods  # noqa: E402
from build_evidence_calibration_reference import build_reference  # noqa: E402
from evidence_calibration_io import canonical_json_bytes, canonical_sha256  # noqa: E402
from maximal_supported_diagnosis import diagnose  # noqa: E402
from realize_evidence_calibrated_explanation import realize  # noqa: E402

REF_SPEC = importlib.util.spec_from_file_location("ref_fixtures", ROOT / "tests/test_evidence_calibration_reference.py")
REF = importlib.util.module_from_spec(REF_SPEC)
assert REF_SPEC.loader is not None
REF_SPEC.loader.exec_module(REF)
DIAG_SPEC = importlib.util.spec_from_file_location("diag_fixtures", ROOT / "tests/test_maximal_supported_diagnosis.py")
DIAG = importlib.util.module_from_spec(DIAG_SPEC)
assert DIAG_SPEC.loader is not None
DIAG_SPEC.loader.exec_module(DIAG)
ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())


def test_development_fixture_flows_without_truth_leak_and_is_byte_reproducible():
    bundle = REF.bundle()
    e3 = next(item for item in bundle["conditions"] if item["condition"]["condition_id"] == "e3")
    reference = build_reference(ONTOLOGY, bundle, REF.reference_input(bundle))
    assessment = next(item for item in reference["conditions"] if item["condition_id"] == "e3")
    assert "claim-external-obstruction" in assessment["physically_true_but_unsupported_claim_ids"]
    assert "obstruction" not in json.dumps(e3["method_packet"], sort_keys=True).lower()

    result = diagnose(ONTOLOGY, e3, DIAG.fact_packet(e3))
    assert "claim-external-obstruction" not in result["approved_claim_ids"]
    execution_contract = {
        "contract_id": "e2e-parity-v1",
        "ordinary_runtime_presentation": "The retained action, recovery, command, and odometry records are available.",
        "presentation_evidence_ids": e3["condition"]["available_evidence_ids"],
        "source_assets": [{"asset_id": "source", "version": "v1", "sha256": "1" * 64}],
        "primitive_tools": [{"asset_id": "stats", "version": "v1", "sha256": "2" * 64}],
        "question_instruction": "State only the strongest diagnosis supported by visible evidence.",
        "contract_assets": [{"asset_id": "contracts", "version": "v1", "sha256": "3" * 64}],
    }
    methods_first = build_methods(copy.deepcopy(e3), copy.deepcopy(execution_contract))
    methods_second = build_methods(copy.deepcopy(e3), copy.deepcopy(execution_contract))
    assert canonical_json_bytes(methods_first) == canonical_json_bytes(methods_second)
    assert "evaluator" not in json.dumps(methods_first, sort_keys=True).lower()

    evaluation = next(item for item in result["claim_evaluations"]
                      if item["claim_id"] == "claim-command-motion-discrepancy")
    support = evaluation["support_references"][0]
    plan = {
        "schema": "crane-claim-realization-plan/v1", "plan_id": "e3-plan",
        "diagnostic_result_sha256": canonical_sha256(result),
        "required_claim_ids": ["claim-task-abort", "claim-command-motion-discrepancy"],
        "optional_claim_ids": [], "required_non_entailment_ids": result["required_non_entailment_ids"],
        "approved_numeric_values": [
            {"claim_id": "claim-command-motion-discrepancy", "slot_id": slot, "value": value,
             "unit": unit, "support_reference": support}
            for slot, value, unit in (("commanded_speed", 0.25, "m/s"),
                                      ("measured_speed", 0.01, "m/s"),
                                      ("interval_start", 2.0, "s"), ("interval_end", 5.0, "s"))
        ],
    }
    candidate = {"schema": "crane-claim-realization-candidate/v1", "response_id": "e3-B4",
                 "plan_sha256": canonical_sha256(plan), "clauses": []}
    realized = realize(ONTOLOGY, result, plan, candidate)
    assert realized["audit"]["status"] == "REPAIRED"
    assert "external obstruction" not in realized["final_response"].lower()

    response = {
        "response_id": "e3-B4", "method_id": "B4", "condition_id": "e3",
        "method_configuration_sha256": "4" * 64, "final_response": realized["final_response"],
        "atomic_claims": [
            {"claim_id": item["contract_id"], "text": item["text"], "response_span": item["text"],
             "asserted_abstraction_level": "registered",
             "support_references": next(
                 (audit["support_references"] for audit in realized["audit"]["clause_audits"]
                  if audit["clause_id"] == item["clause_id"]), [])}
            for item in realized["final_clauses"] if item["kind"] == "CLAIM"
        ],
    }
    rubric = {
        "rubric_id": "e3-rubric", "question_text": "Why did navigation fail?",
        "required_unit_prompts": ["outcome", "command-motion diagnosis"],
        "abstraction_level_options": ["outcome", "observation", "discrepancy", "specific cause"],
        "limitation_prompts": ["do not infer unique physical cause"],
        "false_premise_applicable": False,
        "sanitized_physical_facts": [{"fact": "Evaluator-side motion confirms the physical episode state."}],
    }
    packets, key = build_annotation(e3, response, rubric, "end-to-end-development-salt")
    assert '"method_id"' not in json.dumps(packets, sort_keys=True)
    assert key["method_id"] == "B4"
    assert canonical_sha256(packets) == key["packet_set_sha256"]
