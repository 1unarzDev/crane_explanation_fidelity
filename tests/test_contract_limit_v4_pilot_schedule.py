from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "packages/crane_ml/Tools/ReferenceEnvironments"))

from build_contract_limit_v4_pilot_schedule import build  # noqa: E402
from generate_contract_limit_development_catalog import build_catalog  # noqa: E402


def test_v4_pilot_balances_two_missing_stream_contracts_and_controls() -> None:
    catalog = build_catalog()
    raw = json.dumps(catalog, indent=2).encode()
    schedule = build(catalog, hashlib.sha256(raw).hexdigest())
    runs = schedule["runs"]
    assert len(runs) == 16
    assert schedule["primary_count"] == 12
    assert schedule["control_count"] == 4
    assert sum(item["evidence_mask"] == "remove-delivered-odometry-v1" for item in runs) == 6
    assert sum(item["evidence_mask"] == "remove-delivered-command-v1" for item in runs) == 6
    assert sum(item["study_role"] == "fully-evidenced-control" for item in runs) == 2
    assert sum(item["study_role"] == "nominal-control" for item in runs) == 2
    assert len({item["layout_id"] for item in runs}) == 16
    assert [item["order"] for item in runs] == list(range(1, 17))


def test_v4_pilot_generation_is_deterministic() -> None:
    catalog = build_catalog()
    assert build(catalog, "a" * 64) == build(catalog, "a" * 64)
