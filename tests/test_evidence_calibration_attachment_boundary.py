import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_attachment_boundary import (  # noqa: E402
    LADDERS, ONTOLOGY, OUTPUT, ROLES, build, inventory,
)


def inputs():
    return [json.loads((ROOT / path).read_text()) for path in (ONTOLOGY, LADDERS, ROLES)]


def levels(result, claim_id):
    claim = next(item for item in result["contracts"] if item["claim_id"] == claim_id)
    return {item["ladder_id"]: item["first_role_complete_level"] for item in claim["role_availability"]}


def ladder_id(catalog, fragment):
    matches = [item["ladder_id"] for item in catalog["ladders"] if fragment in item["ladder_id"]]
    assert len(matches) == 1
    return matches[0]


def test_snapshot_reproduces_without_endpoint_attachment():
    result = build()
    assert result == json.loads((ROOT / OUTPUT).read_text())
    assert result["unattached_atom_count"] == 1084
    assert result["required_roles_are_sufficient_for_support"] is False
    assert result["endpoint_scores_generated"] is False
    assert result["pilot_annotation_authorized"] is False
    assert result["rank_scope"] == "WITHIN_MECHANISM_FAMILY_ONLY_NO_RESPONSE_RANK_MAPPING"


def test_software_recovery_and_measured_recovery_have_different_prerequisites():
    ontology, catalog, roles = inputs()
    result = inventory(ontology, catalog, roles)
    primary = ladder_id(catalog, "command-motion-full")
    missing = ladder_id(catalog, "missing-odometry")
    assert levels(result, "claim-recovery-invoked")[primary] == 1
    assert levels(result, "claim-measured-response-recovered")[primary] == 3
    assert levels(result, "claim-command-motion-discrepancy")[primary] == 3
    assert levels(result, "claim-command-motion-discrepancy")[missing] is None


def test_unique_physical_causes_never_gain_a_registered_level():
    result = inventory(*inputs())
    for claim in ("claim-motor-failure", "claim-collision", "claim-wheel-slip",
                  "claim-external-obstruction", "claim-intervention-identity"):
        assert set(levels(result, claim).values()) == {None}
        entries = next(item for item in result["contracts"] if item["claim_id"] == claim)
        assert all(item["status"] == "REQUIRED_ROLES_ABSENT_AT_ALL_REGISTERED_LEVELS"
                   for item in entries["role_availability"])


def test_nominal_success_does_not_supply_nontrigger_computation():
    ontology, catalog, roles = inputs()
    result = inventory(ontology, catalog, roles)
    nominal = ladder_id(catalog, "nominal")
    assert levels(result, "claim-task-success")[nominal] == 0
    assert levels(result, "claim-false-premise-success")[nominal] == 2


@pytest.mark.parametrize("field,value", [
    ("selected_role", {}), ("attached_contract", "claim-motor-failure"),
    ("asserted_rank", 2), ("mechanistic_flag", False), ("endpoint_scoring_authorized", 1),
])
def test_raw_role_conversion_is_rejected(field, value):
    ontology, catalog, roles = inputs()
    roles["rows"][0][field] = value
    with pytest.raises(ValueError, match="raw roles cannot"):
        inventory(ontology, catalog, roles)


def test_duplicate_atom_cannot_hide_an_unattached_claim():
    ontology, catalog, roles = inputs()
    roles["rows"][1] = copy.deepcopy(roles["rows"][0])
    with pytest.raises(ValueError, match="atom identity"):
        inventory(ontology, catalog, roles)
