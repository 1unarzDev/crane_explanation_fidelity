"""One-shot development ledger for service CPU across computation calls.

Host monitor/read/provider CPU is outside this counter; this is not whole-turn accounting.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import stat

from evidence_calibration_local_tool_sandbox_v10 import CpuBudget
from evidence_calibration_mcp_stdio_v3 import strict_json
from observe_evidence_calibration_tree_cpu_accounting_v3 import parse_properties
from observe_evidence_calibration_cgroup_limits import write_once


@dataclass(frozen=True)
class ComputationCpuLimit:
    total_nanoseconds: int

    def __post_init__(self):
        if type(self.total_nanoseconds) is not int or not 10_000_000 <= self.total_nanoseconds <= 3_600_000_000_000:
            raise ValueError('explicit computation CPU total required')


def bounded_json(path: Path, maximum: int = 64*1024**2) -> tuple[dict, str]:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('operator record is not a regular file')
        chunks=[]; size=0
        while size <= maximum:
            chunk=os.read(fd,min(65536,maximum+1-size))
            if not chunk:break
            chunks.append(chunk);size+=len(chunk)
        if size>maximum:raise ValueError('operator record exceeds audit bound')
    finally:os.close(fd)
    raw=b''.join(chunks)
    parsed=strict_json(raw)
    if not isinstance(parsed,dict):raise ValueError('operator record must be an object')
    return parsed,hashlib.sha256(raw).hexdigest()


class ComputationCpuLedger:
    def __init__(self, directory: Path, workspace_sha256: str, *, limit: ComputationCpuLimit, per_call: CpuBudget):
        if not isinstance(limit,ComputationCpuLimit) or not isinstance(per_call,CpuBudget):
            raise ValueError('typed computation CPU total and per-call budget required')
        if not isinstance(workspace_sha256,str) or not re.fullmatch('[0-9a-f]{64}',workspace_sha256):
            raise ValueError('bound workspace SHA-256 required')
        directory.mkdir(parents=True,exist_ok=False)
        self.directory=directory.resolve();self.workspace_sha256=workspace_sha256
        self.limit,self.per_call=limit,per_call
        self.spent=0;self.pending=None;self.unknown=False;self.ordinal=0
        self.completed_events=set();self.settlement_attempts=set()
        write_once(self.directory/'ledger.intent.json',{
            'schema':'crane-computation-cpu-ledger-intent/v2-development',
            'workspace_sha256':workspace_sha256,'limit':asdict(limit),'per_call':asdict(per_call),
            'ledger_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'COMPUTATION_SERVICE_TREES_ONLY','hard_cpu_cap_verified':False,
            'whole_turn_cpu_accounting_verified':False,'existing_ledgers_may_be_adopted':False})

    def snapshot(self) -> dict:
        return {'spent_nanoseconds':None if self.unknown or self.pending is not None else self.spent,
                'settled_known_cpu_nanoseconds':self.spent,
                'remaining_nanoseconds':None if self.unknown or self.pending is not None else max(0,self.limit.total_nanoseconds-self.spent),
                'unknown_accounting':self.unknown,'pending_event':self.pending['event_id'] if self.pending else None,
                'limit':asdict(self.limit),'scope':'COMPUTATION_SERVICE_TREES_ONLY'}

    def ensure_known(self) -> None:
        if self.unknown:raise ValueError('CPU_LEDGER_ACCOUNTING_UNKNOWN')
        if self.pending is not None:raise ValueError('CPU_LEDGER_UNSETTLED_RESERVATION')

    def reserve(self,event_id: str,execution_directory: Path,request_sha256: str) -> dict:
        self.ensure_known()
        if (not isinstance(event_id,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',event_id)
                or event_id in self.completed_events):
            raise ValueError('invalid or retained CPU reservation identity; no replay')
        if not isinstance(request_sha256,str) or not re.fullmatch('[0-9a-f]{64}',request_sha256):
            raise ValueError('bound tool request SHA-256 required')
        remaining=self.limit.total_nanoseconds-self.spent
        threshold=min(remaining,self.per_call.cumulative_nanoseconds)
        if threshold<10_000_000:
            raise ValueError('COMPUTATION_CPU_BUDGET_EXHAUSTED_OR_BELOW_EXECUTOR_MINIMUM')
        self.ordinal+=1
        reservation={'schema':'crane-computation-cpu-reservation/v2-development','ordinal':self.ordinal,
            'event_id':event_id,'execution_directory':str(execution_directory.resolve()),
            'tool_request_sha256':request_sha256,'workspace_sha256':self.workspace_sha256,
            'spent_before_nanoseconds':self.spent,'remaining_before_nanoseconds':remaining,
            'effective_cpu_budget':asdict(replace(self.per_call,cumulative_nanoseconds=threshold))}
        # Set pending before retention; an interrupted/failed write cannot reopen admission.
        self.pending=reservation
        write_once(self.directory/f'reservation-{self.ordinal:08d}.intent.json',reservation)
        return deepcopy(reservation)

    def _verified_consumption(self,reservation: dict) -> tuple[int,dict]:
        directory=Path(reservation['execution_directory'])
        intent,intent_hash=bounded_json(directory/'intent.json')
        terminal,terminal_hash=bounded_json(directory/'terminal.json')
        budget=reservation['effective_cpu_budget'];accounting=terminal['cpu_accounting']
        cpu=accounting['final_cpu_nanoseconds']
        if (intent['schema']!='crane-service-computation-intent/v10-development'
                or terminal['schema']!='crane-service-computation-terminal/v10-development'
                or intent['unit']!=terminal['unit']
                or intent['workspace_identity']['workspace_sha256']!=self.workspace_sha256
                or intent['cpu_budget']!=budget or accounting['budget']!=budget
                or type(cpu) is not int or not 0<cpu<2**64-1
                or accounting['last_observed_cpu_nanoseconds']!=cpu
                or accounting['observed_overshoot_nanoseconds']!=max(0,cpu-budget['cumulative_nanoseconds'])
                or accounting['hard_cpu_cap_verified'] is not False
                or accounting['whole_turn_cpu_accounting_verified'] is not False
                or terminal['cleanup']['final_state']['return_code']!=0
                or terminal['cleanup']['final_state']['stdout'].strip()!='not-found'):
            raise ValueError('unverified service identity, budget, final consumption or cleanup')
        samples=sorted(directory.glob('cpu-sample-*.json'))
        count=accounting['sample_count']
        if type(count) is not int or count<1 or count!=len(samples):
            raise ValueError('CPU sample count mismatch')
        hashes=[];last_cpu=None;final=None
        for ordinal,path in enumerate(samples):
            if path.name!=f'cpu-sample-{ordinal:08d}.json':raise ValueError('CPU sample sequence gap')
            sample,sha=bounded_json(path,65536);hashes.append(sha)
            if sample['unit']!=intent['unit'] or sample['return_code']!=0:
                raise ValueError('CPU sample query or identity failed')
            props={}
            for line in sample['stdout'].splitlines():
                if '=' not in line or line.split('=',1)[0] in props:raise ValueError('invalid CPU properties')
                key,value=line.split('=',1);props[key]=value
            pending_startup=(props.get('LoadState')=='not-found' or
                (props.get('LoadState')=='loaded' and props.get('ActiveState')=='inactive'
                 and props.get('SubState')=='dead' and props.get('ExecMainCode')=='0'
                 and props.get('Result')=='success' and props.get('CPUUsageNSec')=='[not set]'))
            if last_cpu is None and pending_startup:continue
            final=parse_properties(sample['stdout'])
            if final['LoadState']!='loaded' or (last_cpu is not None and final['CPUUsageNSec']<last_cpu):
                raise ValueError('CPU unit disappeared or counter regressed')
            last_cpu=final['CPUUsageNSec']
        if (final is None or last_cpu!=cpu
                or not (final['SubState']=='exited' or final['ActiveState']=='failed')
                or not (final['TasksCurrent']=='0' or (final['TasksCurrent']=='[not set]' and final['ControlGroup']==''))):
            raise ValueError('CPU final counter lacks matching quiescent service')
        return cpu,{'execution_intent_sha256':intent_hash,'execution_terminal_sha256':terminal_hash,
                    'cpu_sample_sha256':hashes,'service_status':terminal['status']}

    def settle(self,event_id: str) -> dict:
        if self.pending is None or self.pending['event_id']!=event_id or event_id in self.settlement_attempts:
            raise ValueError('matching pending CPU reservation required; no replay')
        self.settlement_attempts.add(event_id)
        reservation=self.pending;before=self.spent
        hashes={};cpu=None;error=None
        try:
            cpu,hashes=self._verified_consumption(reservation)
        except (OSError,ValueError,KeyError,TypeError) as caught:
            error=str(caught)
        record={'schema':'crane-computation-cpu-settlement/v2-development','event_id':event_id,
                'ordinal':reservation['ordinal'],'reservation':reservation,
                'status':'CHARGED_ACTUAL_SERVICE_CPU' if cpu is not None else 'UNKNOWN_ACCOUNTING_ADMISSION_CLOSED',
                'actual_cpu_nanoseconds':cpu,'spent_before_nanoseconds':before,
                'spent_after_nanoseconds':before+cpu if cpu is not None else None,
                'unclamped_overshoot_nanoseconds':None if cpu is None else max(0,cpu-reservation['effective_cpu_budget']['cumulative_nanoseconds']),
                'evidence_hashes':hashes,'error':error}
        # Failure to persist settlement leaves the reservation pending and admission closed.
        write_once(self.directory/f"reservation-{reservation['ordinal']:08d}.result.json",record)
        if cpu is None:self.unknown=True
        else:self.spent+=cpu
        self.completed_events.add(event_id);self.pending=None
        return record
