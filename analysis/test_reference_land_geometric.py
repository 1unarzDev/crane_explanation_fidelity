import json
from pathlib import Path

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
    assert findings["deadline_alignment_supported"] is True
    assert findings["terminal_timeout_tick_directly_observed"] is False
    assert measurements["direct_route_first_blocked"]["cost"] >= 253
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
    assert findings["deadline_alignment_supported"] is True
    assert findings["terminal_timeout_tick_directly_observed"] is False
