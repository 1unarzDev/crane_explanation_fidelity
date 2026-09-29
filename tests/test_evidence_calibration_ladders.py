import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
SPEC = importlib.util.spec_from_file_location(
    "ladder_validator", ROOT / "analysis/validate_evidence_calibration_ladders.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CATALOG = json.loads(
    (ROOT / "configs/evidence_calibration_ladders_v1_development.json").read_text()
)


def test_development_ladders_match_public_contract_roles() -> None:
    result = MODULE.validate(ROOT, CATALOG)
    assert result["status"] == "PASS_DEVELOPMENT_NOT_FROZEN"
    assert result["ladder_count"] == 4
    assert result["independent_unit"] == "episode_configuration"
    assert result["confirmation_authorized"] is False


def test_primary_ladder_never_exposes_specific_cause_or_intervention_evidence() -> None:
    ladder = next(item for item in CATALOG["ladders"] if item["ladder_id"] == "command-motion-full-v1-development")
    roles = set(ladder["terminal_evidence_roles"])
    assert not roles.intersection({
        "validated_motor_evidence", "validated_collision_evidence", "validated_slip_evidence",
        "validated_obstruction_evidence", "robot_visible_intervention_evidence",
    })
    terminal_claims = set(ladder["levels"][-1]["potentially_assessable_claim_ids"])
    assert not terminal_claims.intersection({
        "claim-motor-failure", "claim-collision", "claim-wheel-slip",
        "claim-external-obstruction", "claim-intervention-identity",
    })


def test_missing_odometry_ladder_cannot_assess_discrepancy_or_recovery() -> None:
    ladder = next(item for item in CATALOG["ladders"] if "missing-odometry" in item["ladder_id"])
    assert "delivered_odometry_stream" not in ladder["terminal_evidence_roles"]
    assert "command_motion_computation" not in ladder["terminal_evidence_roles"]
    terminal_claims = set(ladder["levels"][-1]["potentially_assessable_claim_ids"])
    assert "claim-command-motion-discrepancy" not in terminal_claims
    assert "claim-measured-response-recovered" not in terminal_claims


def test_non_nested_ladder_fails_closed() -> None:
    changed = copy.deepcopy(CATALOG)
    changed["ladders"][0]["levels"][2]["available_evidence_roles"].remove("source_anchors")
    with pytest.raises(ValueError, match="removes evidence"):
        MODULE.validate(ROOT, changed)


def test_claim_exposed_before_required_roles_fails_closed() -> None:
    changed = copy.deepcopy(CATALOG)
    changed["ladders"][0]["levels"][2]["potentially_assessable_claim_ids"].append(
        "claim-command-motion-discrepancy"
    )
    with pytest.raises(ValueError, match="assessable claims differ"):
        MODULE.validate(ROOT, changed)
