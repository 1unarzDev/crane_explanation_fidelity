import copy
import json
from pathlib import Path

import pytest

from compose_land_diagnostics import _render, _verify, compose
from reference_land_diagnostic_composition import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "data/robot_visible/dev/diagnostic-land-composition-dev-009"
COMMAND = RUN_ROOT / "command-motion-diagnostic-v3.json"
GEOMETRY = RUN_ROOT / "geometric-route-diagnostic-v2.json"
CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "land-diagnostic-composition-plan-v1.json"
)


def test_retained_bounded_diagnostics_compose_and_independently_audit():
    payload = compose(COMMAND, GEOMETRY, CONTRACT)
    reference = audit(
        json.loads(COMMAND.read_text(encoding="utf-8")),
        json.loads(GEOMETRY.read_text(encoding="utf-8")),
        payload,
    )

    assert payload["answer_plan"]["primary_mechanism"] == "command_to_motion_discrepancy"
    assert payload["answer_plan"]["competing_mechanisms"][0]["disposition"] == "insufficient"
    assert "no terminal result was observed" in payload["final_answer"].lower()
    assert "eventual action outcome is unresolved" in payload["final_answer"].lower()
    assert payload["final_text_verification"]["accepted"]
    assert reference["accepted"]
    assert all(reference["numeric_parity"].values())
    assert all(reference["semantic_checks"].values())


def test_composition_rejects_tampered_input_hash(tmp_path: Path):
    changed = json.loads(COMMAND.read_text(encoding="utf-8"))
    changed["diagnostic_result"]["disposition"] = "not_triggered"
    changed_path = tmp_path / "command.json"
    changed_path.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(ValueError, match="hash does not match"):
        compose(changed_path, GEOMETRY, CONTRACT)


def test_composition_rejects_mismatched_episode_even_with_rebound_hash(tmp_path: Path):
    changed = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    changed["episode_id"] = "different-episode"
    changed_path = tmp_path / "geometry.json"
    changed_path.write_text(json.dumps(changed), encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    import hashlib

    contract["source"]["geometric_export_sha256"] = hashlib.sha256(
        changed_path.read_bytes()
    ).hexdigest()
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="episode IDs do not match"):
        compose(COMMAND, changed_path, contract_path)


def test_composition_rejects_terminal_or_supported_geometry_even_with_rebound_hash(tmp_path: Path):
    changed = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    changed["diagnostic_result"]["disposition"] = "supported"
    changed["method_input"]["observation_cutoff"]["terminal_result_observed"] = True
    changed_path = tmp_path / "geometry.json"
    changed_path.write_text(json.dumps(changed), encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    import hashlib

    contract["source"]["geometric_export_sha256"] = hashlib.sha256(
        changed_path.read_bytes()
    ).hexdigest()
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="requires insufficient geometric evidence"):
        compose(COMMAND, changed_path, contract_path)


def test_final_text_verifier_rejects_generic_geometry_mention():
    payload = compose(COMMAND, GEOMETRY, CONTRACT)
    plan = copy.deepcopy(payload["answer_plan"])
    plan["limits"] = plan["limits"].replace(
        "Geometric evidence is insufficient",
        "Geometry is discussed",
    )

    result = _verify(plan, _render(plan))

    assert not result["accepted"]
    assert "Geometric evidence is insufficient" in result["missing_required_spans"]
