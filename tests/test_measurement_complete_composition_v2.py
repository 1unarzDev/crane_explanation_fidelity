from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_command_motion_composition_packet_v2 import build as build_command  # noqa: E402
from build_geometric_composition_packet_v3 import build as build_geometry  # noqa: E402
from build_geometric_composition_packet_v4 import build as build_geometry_v4  # noqa: E402
from compose_diagnostic_hypotheses_v2 import compose  # noqa: E402
from render_diagnostic_composition_v2 import render  # noqa: E402


REGISTRY = json.loads(
    (ROOT / "configs/diagnostic_composition_registry_v1.json").read_text(encoding="utf-8")
)


def load(relative: str) -> tuple[dict, str]:
    raw = (ROOT / relative).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def compiled_command(relative: str) -> str:
    document, digest = load(relative)
    return render(compose(build_command(document, source_sha256=digest), REGISTRY))


def test_v2_never_renders_internal_certificate_or_registry_metadata() -> None:
    text = compiled_command("data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json")
    assert "certificate" not in text.lower()
    assert "declared registry" not in text.lower()
    assert "Missing discriminators" not in text


def test_v2_retains_recovery_causation_limit() -> None:
    text = compiled_command("data/robot_visible/dev/cmv3-dev-002/command-motion-diagnostic-v3.json")
    assert "does not establish that a Wait invocation caused" in text
    assert "Measured response later recovered" in text
    assert "1 FollowPath failure" in text
    assert "1 source-qualified Wait invocation" in text
    assert "1 FollowPath failures" not in text


def test_v2_retains_nominal_healthy_comparator() -> None:
    text = compiled_command("data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json")
    assert "During 0--5 s" in text
    assert "median command 0.26 m/s" in text
    assert "median measured speed 0.25974 m/s" in text
    assert "failure premise" in text


def test_v2_retains_masked_sample_counts_and_qualification() -> None:
    text = compiled_command(
        "data/robot_visible/dev/cmv3-dev-001-mask-no-odometry/command-motion-diagnostic-v3.json"
    )
    assert "398 delivered command samples and 0 independent odometry samples" in text
    assert "does not establish a command-to-motion discrepancy" in text
    assert "Missing discriminators" not in text


def test_v2_retains_robot_visible_grid_coverage_progress_and_nonterminal_limit() -> None:
    document, digest = load(
        "data/robot_visible/dev/diagnostic-land-composition-dev-009/geometric-route-diagnostic-v2.json"
    )
    text = render(compose(build_geometry(document, source_sha256=digest), REGISTRY))
    assert "grid does not cover the complete requested route" in text
    assert "Maximum recorded forward progress was 2.710 m" in text
    assert "action remained active when the observation window ended" in text
    assert "does not establish a terminal navigation failure or a unique physical cause" in text


def test_v2_nominal_geometry_uses_exact_measurement_not_rounded_down_bound() -> None:
    document, digest = load(
        "data/robot_visible/dev/diagnostic-pilot-v1/diagnostic-land-nominal-20260922-001/geometric-diagnostic.json"
    )
    text = render(compose(build_geometry(document, source_sha256=digest), REGISTRY))
    assert "maximum recorded lateral deviation was 0.084414 m" in text
    assert "at most 0.084 m" not in text


def test_v2_geometry_fails_closed_without_method_visible_coverage_fact() -> None:
    document, digest = load(
        "data/robot_visible/dev/diagnostic-land-composition-dev-009/geometric-route-diagnostic-v2.json"
    )
    document.pop("reference_computation")
    try:
        build_geometry(document, source_sha256=digest)
    except ValueError as error:
        assert "route coverage is incomplete" in str(error)
    else:
        raise AssertionError("v2 adapter accepted an unavailable coverage fact")


def test_v2_promotes_only_bounded_independently_computed_geometric_restriction() -> None:
    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json"
    )
    certificate = compose(build_geometry(document, source_sha256=digest), REGISTRY)
    text = render(certificate)

    assert certificate["answer_plan"]["primary_mechanism_id"] == "geometric_route_restriction"
    assert "non-traversable near x=11.575 m" in text
    assert "retaining a below-threshold connection" in text
    assert "does not prove global physical no-path" in text
    assert "unique obstacle identity" in text


def test_v2_does_not_promote_route_change_without_blocked_route_cell() -> None:
    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-002/geometric-route-diagnostic-v2.json"
    )
    certificate = compose(build_geometry(document, source_sha256=digest), REGISTRY)

    assert certificate["answer_plan"]["primary_mechanism_id"] == "recorded_route_change"


def test_v2_does_not_convert_configured_deadline_into_triggered_deadline() -> None:
    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-006/geometric-route-diagnostic-v2.json"
    )
    certificate = compose(build_geometry(document, source_sha256=digest), REGISTRY)
    text = render(certificate)

    assert certificate["answer_plan"]["primary_mechanism_id"] == "geometry_evidence_insufficient"
    assert "aligned with" not in text
    assert "retained grid does not cover the complete requested route" in text
    assert "The action aborted" in text
    assert "action remained active" not in text


def test_v4_restores_supported_geometry_details_missing_from_v2_screen() -> None:
    expectations = {
        "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json": [
            "1.309 m maximum lateral deviation",
        ],
        "data/robot_visible/dev/mccv2-dev-001-mask-no-costmap-cells/geometric-route-diagnostic-v2.json": [
            "1.309 m maximum lateral deviation",
            "costmap cell payload is unavailable",
        ],
        "data/robot_visible/dev/mccv2-dev-002/geometric-route-diagnostic-v2.json": [
            "1.319 m maximum lateral deviation",
            "no observed blocked direct-route cell",
        ],
        "data/robot_visible/dev/mccv2-dev-006/geometric-route-diagnostic-v2.json": [
            "0.000 m maximum lateral deviation",
            "All 3 delivered plans spanned 0.000 to 0.000 m",
            "no observed blocked direct-route cell",
            "does not establish obstacle identity, global no-path",
        ],
    }
    for path, fragments in expectations.items():
        document, digest = load(path)
        text = render(compose(build_geometry_v4(document, source_sha256=digest), REGISTRY))
        for fragment in fragments:
            assert fragment in text


def test_v4_retains_v3_bounded_mechanism_and_deadline_repairs() -> None:
    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json"
    )
    certificate = compose(build_geometry_v4(document, source_sha256=digest), REGISTRY)
    assert certificate["answer_plan"]["primary_mechanism_id"] == "geometric_route_restriction"

    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-006/geometric-route-diagnostic-v2.json"
    )
    text = render(compose(build_geometry_v4(document, source_sha256=digest), REGISTRY))
    assert "aligned with" not in text
    assert "The action aborted" in text


def test_v4_rejects_unknown_masked_geometry_declarations() -> None:
    document, digest = load(
        "data/robot_visible/dev/mccv2-dev-001-mask-no-costmap-cells/geometric-route-diagnostic-v2.json"
    )
    document["reference_computation"]["missing"] = ["misspelledCostmapPayload"]
    with pytest.raises(ValueError, match="unexpected missing-evidence declaration"):
        build_geometry_v4(document, source_sha256=digest)
