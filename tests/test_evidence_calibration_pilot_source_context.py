from __future__ import annotations

import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_source_context import build  # noqa: E402


def test_context_matches_retained_b2_source_and_tool_hashes() -> None:
    assets = build("cm-land-conf-041-E0")
    assert {asset["asset_id"] for asset in assets} == {
        "source/behavior_tree.xml", "source/nav2.yaml", "source/diagnostic_config.json",
        "tools/inspect_evidence_calibration_packet.py",
    }
    assert all(hashlib.sha256(asset["text"].encode()).hexdigest() == asset["sha256"] for asset in assets)
