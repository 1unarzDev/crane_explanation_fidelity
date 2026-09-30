from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_source_context_bundle import build  # noqa: E402


def test_all_valid_b2_calls_share_exact_source_and_tool_context() -> None:
    assets, audit = build()
    assert audit["valid_b2_conditions"] == 57
    assert len(audit["condition_bindings"]) == 57
    assert audit["source_context_common_to_all_conditions"] is True
    assert audit["source_assets_derived_from_b2_accessible_files"] is True
    assert {asset["asset_id"] for asset in assets} == {
        "source/behavior_tree.xml", "source/nav2.yaml", "source/diagnostic_config.json",
        "tools/inspect_evidence_calibration_packet.py",
    }
