import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "layout_freshness", ROOT / "analysis/audit_command_motion_layout_freshness.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
DECLARATION = json.loads(
    (ROOT / "manifests/study/command-motion-layout-freshness-audit-v1.json").read_text()
)


def test_current_reserve_inventory_is_reconciled() -> None:
    result = MODULE.audit(ROOT, DECLARATION)
    assert result["status"] == "PASS_RECONCILED"
    confirmation = result["splits"]["command-motion-confirmation-reserve"]
    replication = result["splits"]["command-motion-replication-reserve"]
    assert confirmation["physically_materialized_layouts"] == 120
    assert confirmation["never_physically_materialized_layouts"] == 0
    assert replication["physically_materialized_layouts"] == 20
    assert replication["never_physically_materialized_layouts"] == 100


def test_cr_pilot_layouts_are_not_counted_as_untouched_replication() -> None:
    result = MODULE.audit(ROOT, DECLARATION)
    records = {item["layout_id"]: item for item in result["records"]}
    item = records["diagnostic-command-motion-replication-reserve-nominal-clear-route-056"]
    assert item["physically_materialized"] is True
    assert "cr-pilot-001" in item["physical_run_ids"]
    assert item["semantic_outputs_present"] is True


def test_old_replication_schedule_allocation_is_distinct_from_materialization() -> None:
    result = MODULE.audit(ROOT, DECLARATION)
    records = {item["layout_id"]: item for item in result["records"]}
    item = records["diagnostic-command-motion-replication-reserve-connected-detour-003"]
    assert item["scheduled_run_ids"] == ["cm-land-repl-001"]
    assert item["physically_materialized"] is False


def test_pinned_schedule_change_fails_closed() -> None:
    changed = copy.deepcopy(DECLARATION)
    changed["allocation_sources"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source hash mismatch"):
        MODULE.audit(ROOT, changed)
