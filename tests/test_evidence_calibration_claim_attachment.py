from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from evidence_calibration_io import canonical_sha256  # noqa: E402
from validate_evidence_calibration_claim_attachment import (  # noqa: E402
    DECLARATION, INPUT_SCHEMA, RETURN_SCHEMA, audit_candidate, validate,
)


def example(text="Measured response recovered in the later interval.", *, question="Did measured response recover?"):
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v2_development.json").read_text())
    payload = {"schema": INPUT_SCHEMA, "opaque_response_id": "synthetic-attachment-01",
               "question_text": question, "response_text": text,
               "claims": [{"item_id": "atom-1", "claim_text": text,
                           "response_span": {"start": 0, "end": len(text), "text": text}}]}
    proposal = {"item_id": "atom-1", "contextual_proposition": text,
                "stance": "ASSERTED_FACT", "polarity": "POSITIVE", "scope": "EPISODE_EVENT",
                "referent_status": "RESOLVED", "attachment_status": "PROPOSED_MATCH",
                "proposed_contract_id": "claim-measured-response-recovered",
                "context_quotes": [{"source": "ANSWER", "start": 0, "end": len(text), "text": text}],
                "scope_note": "Project-authored synthetic proposal; equivalence is not mechanically established."}
    returned = {"schema": RETURN_SCHEMA, "opaque_response_id": payload["opaque_response_id"],
                "input_sha256": canonical_sha256(payload), "ontology_sha256": canonical_sha256(ontology),
                "claim_attachments": [proposal], "attestation": "UNQUALIFIED_CONTEXTUAL_ATTACHMENT_PROPOSAL"}
    return payload, returned, ontology


def test_valid_proposal_never_authorizes_support_or_rank():
    result = validate(*example())
    assert result["proposal_counts"]["PROPOSED_MATCH"] == 1
    assert result["semantic_equivalence_verified"] is False
    assert result["semantic_attachment_qualified"] is False
    assert result["mechanistic_flag_authorized"] is False
    assert result["response_rank_authorized"] is False
    assert result["endpoint_scoring_authorized"] is False


@pytest.mark.parametrize("key", ["question_text", "response_text"])
def test_full_context_changes_invalidate_old_return(key):
    payload, returned, ontology = example()
    payload[key] += " Different context."
    with pytest.raises(ValueError, match="context/ontology binding"):
        validate(payload, returned, ontology)


def test_changed_ontology_invalidates_binding():
    payload, returned, ontology = example()
    ontology["catalog_version"] += "-changed"
    with pytest.raises(ValueError, match="context/ontology binding"):
        validate(payload, returned, ontology)


def test_endorsed_hedge_remains_a_proposed_assertion():
    payload, returned, ontology = example("Measured response probably recovered in the later interval.")
    returned["claim_attachments"][0]["stance"] = "HEDGED_CURRENT_EPISODE"
    assert validate(payload, returned, ontology)["proposal_counts"]["PROPOSED_MATCH"] == 1


def test_negative_causation_cannot_borrow_positive_recovery_contract():
    payload, returned, ontology = example("Measured response recovery did not cause task success.")
    proposal = returned["claim_attachments"][0]
    proposal["polarity"] = "NEGATIVE"
    with pytest.raises(ValueError, match="positive episode contracts"):
        validate(payload, returned, ontology)
    proposal.update(attachment_status="OUT_OF_CATALOG", proposed_contract_id=None)
    result = validate(payload, returned, ontology)
    assert result["proposal_counts"]["OUT_OF_CATALOG"] == 1
    proposal["attachment_status"] = "NOT_APPLICABLE"
    with pytest.raises(ValueError, match="asserted unmatched"):
        validate(payload, returned, ontology)


def test_limitation_and_unendorsed_quote_have_no_selected_contract():
    for text, stance, scope in [
        ("Recovery does not establish success.", "INFERENCE_LIMITATION", "EVIDENTIAL_LIMITATION"),
        ('Someone suggested "motor failure"; I do not endorse that claim.',
         "UNENDORSED_HYPOTHETICAL_OR_QUOTE", "GENERAL_OR_HYPOTHETICAL"),
    ]:
        payload, returned, ontology = example(text)
        proposal = returned["claim_attachments"][0]
        proposal.update(stance=stance, scope=scope, polarity="NOT_APPLICABLE")
        with pytest.raises(ValueError, match="positive episode contracts"):
            validate(payload, returned, ontology)
        proposal.update(attachment_status="NOT_APPLICABLE", proposed_contract_id=None)
        assert validate(payload, returned, ontology)["proposal_counts"]["NOT_APPLICABLE"] == 1


def test_configuration_fact_cannot_attach_as_episode_occurrence():
    payload, returned, ontology = example("The source contains a response-recovery threshold.")
    proposal = returned["claim_attachments"][0]
    proposal["scope"] = "SOURCE_OR_CONFIG_FACT"
    with pytest.raises(ValueError, match="positive episode contracts"):
        validate(payload, returned, ontology)
    proposal.update(attachment_status="OUT_OF_CATALOG", proposed_contract_id=None)
    assert validate(payload, returned, ontology)["proposal_counts"]["OUT_OF_CATALOG"] == 1


def test_unresolved_recovery_and_deictic_referents_remain_unattached():
    for text in ("Recovery handled it.", "These specific physical causes are not established.", "Yes."):
        payload, returned, ontology = example(text)
        proposal = returned["claim_attachments"][0]
        proposal["referent_status"] = "UNRESOLVED"
        with pytest.raises(ValueError, match="unresolved context"):
            validate(payload, returned, ontology)
        proposal.update(attachment_status="UNRESOLVED", proposed_contract_id=None)
        assert validate(payload, returned, ontology)["proposal_counts"]["UNRESOLVED"] == 1


def test_same_text_at_wrong_offset_cannot_quote_another_atom():
    payload, returned, ontology = example("Yes. Yes.")
    payload["claims"][0]["response_span"] = {"start": 0, "end": 4, "text": "Yes."}
    payload["claims"][0]["claim_text"] = "Yes."
    returned["input_sha256"] = canonical_sha256(payload)
    returned["claim_attachments"][0]["context_quotes"] = [
        {"source": "ANSWER", "start": 5, "end": 9, "text": "Yes."}]
    with pytest.raises(ValueError, match="own retained atom span"):
        validate(payload, returned, ontology)


@pytest.mark.parametrize("field", ["highest_asserted_rank", "mechanistic", "label", "raw_roles"])
def test_support_and_endpoint_fields_are_rejected(field):
    payload, returned, ontology = example()
    returned["claim_attachments"][0][field] = 1
    with pytest.raises(ValueError, match="missing or unknown fields"):
        validate(payload, returned, ontology)


def test_missing_and_reordered_atoms_are_rejected():
    payload, returned, ontology = example()
    second = deepcopy(payload["claims"][0])
    second["item_id"] = "atom-2"
    payload["claims"].append(second)
    returned["input_sha256"] = canonical_sha256(payload)
    with pytest.raises(ValueError, match="exactly and in order"):
        validate(payload, returned, ontology)
    second_proposal = deepcopy(returned["claim_attachments"][0])
    second_proposal["item_id"] = "atom-2"
    returned["claim_attachments"].insert(0, second_proposal)
    with pytest.raises(ValueError, match="exactly and in order"):
        validate(payload, returned, ontology)


@pytest.mark.parametrize("offset", [True, -1, 0.0])
def test_offsets_are_exact_nonboolean_integers(offset):
    payload, returned, ontology = example("Réponse: yes.")
    payload["claims"][0]["response_span"]["start"] = offset
    with pytest.raises(ValueError, match="Unicode character offsets"):
        validate(payload, returned, ontology)


def test_candidate_declaration_is_bound_but_unqualified():
    result = audit_candidate()
    assert result["authorized_model_calls"] == 0
    assert result["semantic_attachment_qualified"] is False
    assert result["endpoint_mapping_bound"] is False


def test_candidate_cannot_activate_pilot_or_drop_failed_gate(tmp_path):
    declaration = json.loads(DECLARATION.read_text())
    path = tmp_path / "modified.json"
    altered = deepcopy(declaration)
    altered["pilot_annotation_authorized"] = True
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="cannot authorize"):
        audit_candidate(path)
    altered = deepcopy(declaration)
    del altered["bindings"]["failed_measurement_gate"]
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="bindings are incomplete"):
        audit_candidate(path)


def test_invalid_proposed_contract_id_is_not_a_match():
    payload, returned, ontology = example()
    returned["claim_attachments"][0]["proposed_contract_id"] = "claim-software-recovery-means-motion-recovered"
    with pytest.raises(ValueError, match="positive episode contracts"):
        validate(payload, returned, ontology)
