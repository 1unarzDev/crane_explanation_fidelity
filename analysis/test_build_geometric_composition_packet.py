import copy
import hashlib
import json
from pathlib import Path

import pytest

from build_geometric_composition_packet import build
from compose_diagnostic_hypotheses import compose
from render_diagnostic_composition import render


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "configs/diagnostic_composition_registry_v1.json").read_text())


def compile_fixture(relative: str):
    raw = (ROOT / relative).read_bytes()
    document = json.loads(raw)
    packet = build(document, source_sha256=hashlib.sha256(raw).hexdigest())
    certificate = compose(packet, REGISTRY)
    return document, packet, certificate, render(certificate)


def test_old_positive_geometry_export_fails_closed_without_structured_action_status():
    relative = "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/geometric-diagnostic.json"
    raw = (ROOT / relative).read_bytes()
    with pytest.raises(ValueError, match="action-status measurement"):
        build(json.loads(raw), source_sha256=hashlib.sha256(raw).hexdigest())


def test_route_change_with_insufficient_geometry_withholds_physical_trigger():
    _, _, certificate, text = compile_fixture(
        "data/robot_visible/dev/diagnostic-land-binding-dev-007/geometric-route-diagnostic-v2.json"
    )
    assert certificate["answer_plan"]["primary_mechanism_id"] == "recorded_route_change"
    assert "does not prove controller consumption" in text
    assert "74 plans" in text


def test_nominal_geometry_rejects_false_failure_premise():
    _, _, certificate, text = compile_fixture(
        "data/robot_visible/dev/diagnostic-pilot-v1/diagnostic-land-nominal-20260922-001/geometric-diagnostic.json"
    )
    assert certificate["answer_plan"]["primary_mechanism_id"] == "nominal_route_geometry"
    assert "0.379 m minimum clearance" in text
    assert "reject the question's failure premise" in text


def test_newer_nonterminal_geometry_export_preserves_insufficiency():
    _, _, certificate, text = compile_fixture(
        "data/robot_visible/dev/diagnostic-land-composition-dev-009/geometric-route-diagnostic-v2.json"
    )
    assert certificate["answer_plan"]["primary_mechanism_id"] == "geometry_evidence_insufficient"
    assert "cannot be assessed" in text
    assert "No terminal action result is retained" in text


def test_geometric_adapter_rejects_evaluator_only_input():
    relative = "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/geometric-diagnostic.json"
    raw = (ROOT / relative).read_bytes()
    document = copy.deepcopy(json.loads(raw))
    document["visibility"] = "evaluator_only"
    with pytest.raises(ValueError, match="robot-visible"):
        build(document, source_sha256=hashlib.sha256(raw).hexdigest())
