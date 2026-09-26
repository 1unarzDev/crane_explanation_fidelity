import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_checked_composition_annotation_reference import (  # noqa: E402
    build_reference,
    load_inventory,
)
from build_command_motion_composition_packet_v2 import build as build_command_packet  # noqa: E402
from build_geometric_composition_packet_v4 import build as build_geometric_packet  # noqa: E402
from compose_diagnostic_hypotheses_v2 import compose  # noqa: E402
from render_diagnostic_composition_v2 import render  # noqa: E402


INVENTORY_PATH = (
    ROOT
    / "research/explanation_fidelity/references/development/coverage-complete-v4-references-v1.json"
)
REGISTRY_PATH = ROOT / "configs/diagnostic_composition_registry_v1.json"
CASE_INPUTS = {
    "ccv4-geometry-001": (
        "data/robot_visible/dev/mccv4-dev-001/geometric-route-diagnostic-v2.json",
        "geometry",
    ),
    "ccv4-geometry-masked-001m": (
        "data/robot_visible/dev/mccv4-dev-001-mask-no-costmap-cells/geometric-route-diagnostic-v2.json",
        "geometry",
    ),
    "ccv4-geometry-002": (
        "data/robot_visible/dev/mccv4-dev-002/geometric-route-diagnostic-v2.json",
        "geometry",
    ),
    "ccv4-geometry-003": (
        "data/robot_visible/dev/mccv4-dev-003/geometric-route-diagnostic-v2.json",
        "geometry",
    ),
    "ccv4-persistent-004": (
        "data/robot_visible/dev/mccv4-dev-004/command-motion-diagnostic-v3-low-speed.json",
        "command",
    ),
    "ccv4-missing-odometry-004m": (
        "data/robot_visible/dev/mccv4-dev-004-mask-no-odometry/command-motion-diagnostic-v3.json",
        "command",
    ),
    "ccv4-compensation-005": (
        "data/robot_visible/dev/mccv4-dev-005/command-motion-diagnostic-v3-low-speed.json",
        "command",
    ),
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory() -> dict:
    return load_inventory(INVENTORY_PATH)


def _reference_cases() -> dict[str, dict]:
    return {item["case_id"]: item for item in _inventory()["cases"]}


def _screen_case(case_id: str) -> dict:
    path, _ = CASE_INPUTS[case_id]
    return {
        "case_id": case_id,
        "diagnostic_path": path,
        "diagnostic_sha256": _digest(ROOT / path),
    }


def _render(case_id: str) -> str:
    path, family = CASE_INPUTS[case_id]
    raw = (ROOT / path).read_bytes()
    document = json.loads(raw)
    builder = build_geometric_packet if family == "geometry" else build_command_packet
    packet = builder(document, source_sha256=hashlib.sha256(raw).hexdigest())
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    certificate = compose(packet, registry)
    assert certificate["status"] == "composed"
    return render(certificate)


def test_inventory_has_seven_unique_cases_and_five_independent_clusters():
    inventory = _inventory()
    assert inventory["status"] == "FROZEN_BEFORE_ANY_RESPONSE_OR_JUDGMENT"
    cases = inventory["cases"]
    assert len(cases) == 7
    assert {item["case_id"] for item in cases} == set(CASE_INPUTS)
    assert len({item["case_id"] for item in cases}) == len(cases)

    # The two masks are paired views of existing scenarios, not new independent clusters.
    assert sum(not item["case_id"].endswith(("001m", "004m")) for item in cases) == 5


def test_every_reference_source_hash_and_diagnostic_binding_validates():
    for case_id, reference_case in _reference_cases().items():
        built = build_reference(_screen_case(case_id), reference_case)
        assert built["completeness_audit"]["accepted"] is True
        assert built["completeness_audit"]["source_hashes_verified"] is True
        for source in reference_case["reference_sources"]:
            assert _digest(ROOT / source["path"]) == source["sha256"]


def test_required_units_are_atomic_and_endpoint_eligibility_fails_closed():
    for case in _inventory()["cases"]:
        units = case["required_units"]
        unit_ids = [item["unit_id"] for item in units]
        predicates = [item["atomic_predicate"] for item in units]
        assert units
        assert len(unit_ids) == len(set(unit_ids))
        assert len(predicates) == len(set(predicates))
        assert all(item["text"].strip() for item in units)
        if case["primary_endpoint_eligible"]:
            assert case["diagnosable"] is True
            assert case["mechanism_unit_id"] in unit_ids
        else:
            assert case["diagnosable"] is False
            assert case["mechanism_unit_id"] is None


def test_independent_references_support_declared_decisive_quantities():
    rendered = {case_id: _render(case_id) for case_id in CASE_INPUTS}

    assert "near x=12.425 m" in rendered["ccv4-geometry-001"]
    assert "-1.383 m to 1.272 m" in rendered["ccv4-geometry-001"]
    assert "1.325 m maximum lateral deviation" in rendered["ccv4-geometry-001"]
    assert "near x=11.525 m" in rendered["ccv4-geometry-002"]
    assert "-1.130 m to 1.054 m" in rendered["ccv4-geometry-002"]
    assert "1.105 m maximum lateral deviation" in rendered["ccv4-geometry-002"]
    assert "-1.303 m to 1.523 m" in rendered["ccv4-geometry-003"]
    assert "1.558 m maximum lateral deviation" in rendered["ccv4-geometry-003"]

    masked_geometry = rendered["ccv4-geometry-masked-001m"]
    assert "costmap cell payload is unavailable" in masked_geometry
    assert "cannot be classified" in masked_geometry
    assert "near x=12.425 m" not in masked_geometry

    persistent = rendered["ccv4-persistent-004"]
    assert "median command 0.26 m/s" in persistent
    assert "median measured speed 0 m/s during 11--21 s" in persistent
    assert "0.25974 m/s during 0--5 s" in persistent
    assert "aborted after 3 FollowPath attempts" in persistent
    assert "does not uniquely identify" in persistent

    masked_motion = rendered["ccv4-missing-odometry-004m"]
    assert "414 delivered command samples and 0 independent odometry samples" in masked_motion
    assert "cannot be assessed" in masked_motion
    assert "median measured speed 0 m/s" not in masked_motion

    compensation = rendered["ccv4-compensation-005"]
    assert "median measured speed 0 m/s during 10--20 s" in compensation
    assert "recovered to 0.25974 m/s during 22--23 s" in compensation
    assert "recorded navigation action succeeded" in compensation
    assert "does not establish that a Wait invocation caused" in compensation


def test_rendered_geometry_preserves_scope_and_consumption_limits():
    for case_id in ("ccv4-geometry-001", "ccv4-geometry-002", "ccv4-geometry-003"):
        answer = _render(case_id)
        assert "does not prove global physical no-path" in answer
        assert "unique obstacle identity" in answer
        assert "exact Nav2 consumption" in answer
        assert "snapshot caused the delivered plan change" in answer
