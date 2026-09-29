import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from evidence_calibration import (  # noqa: E402
    ClaimEvaluation,
    DiagnosticResult,
    DiagnosticState,
    EvidenceCondition,
    RequirementEvaluation,
    RequirementStatus,
    RESULT_SCHEMA,
    CONDITION_SCHEMA,
    validate_diagnostic_result,
    validate_evidence_condition,
)
from evidence_calibration_io import (  # noqa: E402
    canonical_json_bytes,
    ontology_from_dict,
)


CATALOG = json.loads(
    (ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text(encoding="utf-8")
)
SHA = "0" * 64


def test_public_ontology_is_strict_canonical_and_contains_required_non_entailments():
    ontology = ontology_from_dict(CATALOG)
    encoded = canonical_json_bytes(ontology)
    assert encoded == canonical_json_bytes(ontology_from_dict(json.loads(encoded)))
    text = encoded.decode("utf-8")
    assert "evaluator_only" not in text
    assert '"supported"' not in text
    discrepancy = next(item for item in ontology.claim_contracts if item.claim_id == "claim-command-motion-discrepancy")
    assert {
        "req-command-stream-valid",
        "req-odometry-stream-valid",
        "req-command-odometry-synchronized",
        "req-command-above-threshold",
        "req-interval-duration-sufficient",
        "req-measured-response-low",
    } == set(discrepancy.required_evidence_ids)
    relation = next(item for item in ontology.non_entailments if item.non_entailment_id == "ne-discrepancy-does-not-identify-physical-cause")
    assert set(relation.unsupported_consequent_claim_ids) == {
        "claim-motor-failure", "claim-collision", "claim-wheel-slip", "claim-external-obstruction"
    }


@pytest.mark.parametrize("mutation", ["duplicate", "dangling", "cycle", "leakage"])
def test_ontology_rejects_invalid_graph_contracts_and_leakage(mutation):
    value = copy.deepcopy(CATALOG)
    if mutation == "duplicate":
        value["claim_contracts"].append(copy.deepcopy(value["claim_contracts"][0]))
    elif mutation == "dangling":
        value["claim_contracts"][0]["required_evidence_ids"] = ["not-registered"]
    elif mutation == "cycle":
        value["diagnostic_nodes"][5]["parent_node_ids"] = ["node-motor-failure"]
    else:
        value["evidence_requirements"][0]["evidence_roles"] = ["evaluator_intervention"]
    with pytest.raises(ValueError):
        ontology_from_dict(value)


def condition(**changes):
    value = dict(
        schema=CONDITION_SCHEMA,
        episode_id="episode-1",
        configuration_id="config-1",
        condition_id="condition-e0",
        ladder_id="ladder-1",
        level_index=0,
        parent_condition_id=None,
        source_packet_sha256=SHA,
        method_packet_sha256=SHA,
        source_configuration_sha256=SHA,
        runtime_manifest_sha256=SHA,
        condition_builder_id="builder",
        condition_builder_version="v1",
        condition_builder_sha256=SHA,
        mask_id=None,
        mask_version=None,
        mask_sha256=None,
        available_evidence_ids=("action",),
        available_evidence_roles=("navigate_to_pose_result",),
        removed_json_pointers=(),
    )
    value.update(changes)
    return EvidenceCondition(**value)


def test_evidence_condition_enforces_mask_identity_and_truth_isolation():
    validate_evidence_condition(condition())
    validate_evidence_condition(condition(
        condition_id="condition-e0", mask_id="outcome-only", mask_version="v1", mask_sha256=SHA,
        removed_json_pointers=("/streams/odometry", "/streams/commands"),
    ))
    with pytest.raises(ValueError, match="evaluator truth"):
        validate_evidence_condition(condition(evaluator_only_absent=False))
    with pytest.raises(ValueError, match="mask identity"):
        validate_evidence_condition(condition(removed_json_pointers=("/streams/odometry",)))


def result_for(claim_id, requirement_ids, statuses, state=DiagnosticState.KNOWN, **changes):
    evaluations = tuple(
        RequirementEvaluation(identifier, status, (), "test")
        for identifier, status in zip(requirement_ids, statuses, strict=True)
    )
    supported = all(status is RequirementStatus.SATISFIED for status in statuses)
    claim = ClaimEvaluation(claim_id, supported, evaluations)
    value = dict(
        schema=RESULT_SCHEMA,
        episode_id="episode-1",
        configuration_id="config-1",
        condition_id="condition-e3",
        contract_catalog_id=CATALOG["catalog_id"],
        contract_catalog_sha256=SHA,
        diagnostic_algorithm_id="maximal-supported-v1",
        diagnostic_algorithm_version="v1",
        state=state,
        maximal_node_ids=(),
        approved_claim_ids=(claim_id,) if supported else (),
        claim_evaluations=(claim,),
        missing_requirement_ids=tuple(identifier for identifier, status in zip(requirement_ids, statuses, strict=True) if status is not RequirementStatus.SATISFIED),
        contradicted_claim_ids=(),
        ambiguity_node_ids=(),
        required_non_entailment_ids=(),
    )
    value.update(changes)
    return DiagnosticResult(**value)


def test_missing_odometry_cannot_approve_discrepancy():
    ontology = ontology_from_dict(CATALOG)
    contract = next(item for item in ontology.claim_contracts if item.claim_id == "claim-command-motion-discrepancy")
    statuses = tuple(
        RequirementStatus.ABSENT if item == "req-odometry-stream-valid" else RequirementStatus.SATISFIED
        for item in contract.required_evidence_ids
    )
    result = result_for(contract.claim_id, contract.required_evidence_ids, statuses, state=DiagnosticState.SUPPORTED_PARTIAL)
    validate_diagnostic_result(result, ontology)
    assert result.approved_claim_ids == ()
    tampered = copy.copy(result)
    object.__setattr__(tampered, "approved_claim_ids", (contract.claim_id,))
    with pytest.raises(ValueError, match="supported evaluations"):
        validate_diagnostic_result(tampered, ontology)


def test_false_premise_cannot_approve_failure_mechanism_and_ambiguity_needs_antichain():
    ontology = ontology_from_dict(CATALOG)
    contract = next(item for item in ontology.claim_contracts if item.claim_id == "claim-command-motion-discrepancy")
    statuses = (RequirementStatus.SATISFIED,) * len(contract.required_evidence_ids)
    false_premise = result_for(contract.claim_id, contract.required_evidence_ids, statuses, state=DiagnosticState.FALSE_PREMISE)
    with pytest.raises(ValueError, match="FALSE_PREMISE"):
        validate_diagnostic_result(false_premise, ontology)
    ambiguous = result_for(
        contract.claim_id, contract.required_evidence_ids, statuses, state=DiagnosticState.AMBIGUOUS,
        ambiguity_node_ids=("node-motor-failure", "node-collision"),
    )
    validate_diagnostic_result(ambiguous, ontology)
    bad = copy.copy(ambiguous)
    object.__setattr__(bad, "ambiguity_node_ids", ("node-command-motion-discrepancy", "node-motor-failure"))
    with pytest.raises(ValueError, match="incomparable"):
        validate_diagnostic_result(bad, ontology)


def test_loader_rejects_unknown_fields():
    value = copy.deepcopy(CATALOG)
    value["claim_contracts"][0]["episode_supported"] = True
    with pytest.raises(ValueError, match="unknown fields"):
        ontology_from_dict(value)


def test_ontology_schema_is_closed_draft_2020_12_with_exact_state_vocabulary():
    schema = json.loads((ROOT / "research/explanation_fidelity/schemas/evidence-calibration-ontology-v1.schema.json").read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "https://crane.local/schemas/evidence-calibration-ontology-v1.schema.json"
    assert schema["additionalProperties"] is False
    assert all(definition.get("additionalProperties") is False for definition in schema["$defs"].values() if definition.get("type") == "object")
    assert {state.value for state in DiagnosticState} == {
        "KNOWN", "SUPPORTED_PARTIAL", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE",
        "FALSE_PREMISE", "NOT_TRIGGERED",
    }
