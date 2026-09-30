from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_computation_cpu_ledger_v2 import ComputationCpuLedger,ComputationCpuLimit
from evidence_calibration_local_tool_sandbox_v10 import CpuBudget


def test_returned_reservation_cannot_mutate_pending_bound_budget(tmp_path):
    budget=CpuBudget(100_000_000,20,250)
    ledger=ComputationCpuLedger(tmp_path/'ledger','a'*64,limit=ComputationCpuLimit(150_000_000),per_call=budget)
    returned=ledger.reserve('one',tmp_path/'execution','b'*64)
    returned['effective_cpu_budget']['cumulative_nanoseconds']=999_000_000
    returned['effective_cpu_budget']['poll_milliseconds']=250
    assert ledger.pending['effective_cpu_budget']==asdict(budget)
    retained=json.loads((tmp_path/'ledger/reservation-00000001.intent.json').read_text())
    assert retained['effective_cpu_budget']==ledger.pending['effective_cpu_budget']


def test_exact_isolation_repair_preserves_prior_version():
    first=(ROOT/'analysis/evidence_calibration_computation_cpu_ledger.py').read_text()
    second=(ROOT/'analysis/evidence_calibration_computation_cpu_ledger_v2.py').read_text()
    expected=first.replace('from dataclasses import asdict, dataclass, replace','from dataclasses import asdict, dataclass, replace\nfrom copy import deepcopy')
    expected=expected.replace('ledger-intent/v1-development','ledger-intent/v2-development').replace('reservation/v1-development','reservation/v2-development').replace('settlement/v1-development','settlement/v2-development')
    expected=expected.replace('        return dict(reservation)\n','        return deepcopy(reservation)\n')
    assert second==expected
    broker=(ROOT/'analysis/evidence_calibration_tool_broker_v6.py').read_text()
    repaired=(ROOT/'analysis/evidence_calibration_tool_broker_v7.py').read_text()
    assert repaired==broker.replace('from evidence_calibration_computation_cpu_ledger import','from evidence_calibration_computation_cpu_ledger_v2 import').replace('request/v6-development','request/v7-development')
