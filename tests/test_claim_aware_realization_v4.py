from copy import deepcopy
from test_claim_aware_realization_v3 import inputs
from realize_evidence_calibrated_explanation_v3 import realize as old_realize
from realize_evidence_calibrated_explanation_v4 import realize, LIMITATION


def test_causal_limitation_preserves_recovery_and_outcome_without_excluding_causation():
    ontology, entry, contract = inputs("cm-land-conf-047-E3")
    original = deepcopy(ontology)
    output = realize(ontology, entry, contract)
    assert ontology == original
    assert "does not establish or cause" not in output["answer"]
    assert LIMITATION in output["answer"]
    assert "later 30–31 s interval" in output["answer"]
    assert "recorded navigation action aborted" in output["answer"]
    assert "does not establish or cause" in old_realize(ontology, entry, contract)["answer"]
