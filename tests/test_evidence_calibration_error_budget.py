import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ec_error_budget", ROOT / "analysis/audit_evidence_calibration_error_budget.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
DECLARATION = json.loads(
    (ROOT / "manifests/study/evidence-calibration-error-budget-audit-v1.json").read_text()
)


def test_current_ledger_leaves_only_one_percent_for_discovery() -> None:
    result = MODULE.audit(ROOT, DECLARATION)
    assert result["status"] == "PASS_PROVISIONAL_UNBOUND"
    assert result["program_alpha"] == 0.05
    assert result["consumed_alpha"] == 0.02
    assert result["maximum_discovery_alpha"] == 0.01
    assert result["reserved_replication_alpha"] == 0.02
    assert result["confirmation_authorized"] is False


def test_replication_alpha_cannot_be_relabelled_as_discovery() -> None:
    changed = copy.deepcopy(DECLARATION)
    changed["prospective_boundary"]["discovery_allocation_id"] = "selected-method-replication"
    with pytest.raises(ValueError, match="candidate alpha"):
        MODULE.audit(ROOT, changed)


def test_audit_cannot_bind_or_consume_alpha() -> None:
    for field in ("bound_by_this_audit", "consumed_by_this_audit"):
        changed = copy.deepcopy(DECLARATION)
        changed[field] = 0.01
        with pytest.raises(ValueError, match="must not"):
            MODULE.audit(ROOT, changed)


def test_source_hash_change_fails_closed() -> None:
    changed = copy.deepcopy(DECLARATION)
    changed["source_ledger"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source hash mismatch"):
        MODULE.audit(ROOT, changed)
