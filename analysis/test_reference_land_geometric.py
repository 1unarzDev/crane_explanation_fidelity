import json
from pathlib import Path

import pytest

from reference_land_geometric import calculate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/fixture-summary.json"
MASKED = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002-mask-no-costmap-cells/fixture-summary.json"
BT_XML = ROOT / "packages/crane_ml/Tools/Performance/nav2_warehouse_replanning_deadline.xml"


def test_independent_land_reference_reproduces_bounded_route_findings():
    result = calculate(
        json.loads(FIXTURE.read_text(encoding="utf-8")),
        BT_XML.read_bytes(),
        episode_id="land-blockage-global-002",
    )

    findings = result["reference_findings"]
    measurements = result["measurements"]
    assert findings["direct_route_restriction_supported"] is True
    assert findings["retained_grid_has_connection"] is True
    assert findings["global_physical_no_path_supported"] is False
    assert findings["deadline_aligned_abort_supported"] is True
    assert findings["terminal_timeout_tick_directly_observed"] is False
    assert measurements["direct_route_first_blocked"]["cost"] >= 253
    assert measurements["direct_route_fully_covered"] is True
    assert abs(measurements["direct_route_first_blocked"]["center_x_m"] - 8.45) < 0.051
    assert abs(measurements["maximum_lateral_deviation_m"] - 2.70458) < 0.001


def test_missing_cells_preserves_timing_but_withholds_geometry():
    result = calculate(
        json.loads(MASKED.read_text(encoding="utf-8")),
        BT_XML.read_bytes(),
        episode_id="land-blockage-global-002-mask-no-costmap-cells",
    )

    findings = result["reference_findings"]
    assert findings["direct_route_restriction_supported"] is None
    assert findings["retained_grid_has_connection"] is None
    assert findings["deadline_aligned_abort_supported"] is True
    assert findings["terminal_timeout_tick_directly_observed"] is False


def test_success_near_deadline_is_not_called_a_deadline_aligned_abort():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["status"] = "succeeded"

    result = calculate(fixture, BT_XML.read_bytes(), episode_id="nominal")

    assert result["reference_findings"]["deadline_aligned_abort_supported"] is False
    assert "abort time" not in " ".join(result["allowed_conclusions"])


def test_out_of_bounds_route_cells_are_missing_coverage_not_obstacles():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snapshot = fixture["latestCostmapSnapshot"]
    snapshot["origin"]["x"] = 10.0

    result = calculate(fixture, BT_XML.read_bytes(), episode_id="rolling-grid")

    assert result["reference_findings"]["direct_route_restriction_supported"] is False
    assert result["measurements"]["direct_route_fully_covered"] is False
    assert "does not cover" in " ".join(result["required_withholding"])


def test_explicit_harness_deadline_supports_tree_without_timeout_node():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    result = calculate(
        fixture,
        b'<root BTCPP_format="4"/>',
        episode_id="external-deadline",
        explicit_deadline_seconds=100.0,
    )

    assert result["measurements"]["configured_deadline_seconds"] == 100.0


def test_tree_without_timeout_or_explicit_deadline_fails_closed():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="provide explicit_deadline_seconds"):
        calculate(fixture, b'<root BTCPP_format="4"/>', episode_id="missing-deadline")
