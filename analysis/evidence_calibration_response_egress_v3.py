"""Development ledger for complete local MCP responses; not model-visible receipt."""
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path

from observe_evidence_calibration_cgroup_limits import write_once


@dataclass(frozen=True)
class ResponseByteLimit:
    total_bytes: int

    def __post_init__(self):
        if type(self.total_bytes) is not int or not 1024 <= self.total_bytes <= 2**31:
            raise ValueError('explicit response byte total required (1 KiB–2 GiB)')


def retain_wire(path: Path, wire: bytes):
    # Exact original framing is retained before any transport write.
    with path.open('xb') as stream:
        count = stream.write(wire)
        if type(count) is not int or count != len(wire):
            raise OSError('incomplete operator wire retention')
        stream.flush()
        os.fsync(stream.fileno())


class ResponseBudgetExhausted(OSError):
    pass


class BudgetedOutput:
    """Reserve a whole encoded response, write exactly, flush, then retain settlement.

    Any uncertain send or storage outcome closes admission. No partial byte replay,
    output truncation, ledger adoption or peer/model delivery assertion is possible.
    """
    def __init__(self, sink, directory: Path, *, limit: ResponseByteLimit):
        if not isinstance(limit, ResponseByteLimit):
            raise ValueError('typed response byte total required')
        directory.mkdir(parents=True, exist_ok=False)
        self.sink, self.directory, self.limit = sink, directory, limit
        self.settled = self.written = self.ordinal = 0
        self.pending = None
        self.write_completed = False
        self.unknown = False
        self.exhausted = False
        write_once(directory/'egress.intent.json', {
            'schema':'crane-response-egress/v3-development','limit':asdict(limit),
            'scope':'ENCODED_LOCAL_MCP_RESPONSE_BYTES_INCLUDING_FRAMING',
            'peer_receipt_verified':False,'model_visible_rendering_verified':False})

    def snapshot(self):
        uncertain = self.unknown or self.pending is not None
        return {'limit':asdict(self.limit),'settled_flushed_bytes':self.settled,
            'observed_write_bytes':self.written,'remaining_bytes':None if uncertain else self.limit.total_bytes-self.settled,
            'pending_response':self.pending['ordinal'] if self.pending else None,
            'unknown_delivery':self.unknown,'budget_exhausted':self.exhausted,
            'scope':'ENCODED_LOCAL_MCP_RESPONSE_BYTES_INCLUDING_FRAMING',
            'peer_receipt_verified':False,'model_visible_rendering_verified':False}

    def write(self, wire: bytes):
        if self.unknown or self.pending is not None or self.exhausted:
            raise ValueError('egress admission closed; no response replay')
        if not isinstance(wire, bytes) or not wire or not wire.endswith(b'\n'):
            raise ValueError('one complete encoded newline-terminated response required')
        self.ordinal += 1
        row={'schema':'crane-response-egress-reservation/v3-development', 'ordinal':self.ordinal,
            'wire_sha256':hashlib.sha256(wire).hexdigest(),'wire_bytes':len(wire),
            'settled_before_bytes':self.settled,'remaining_before_bytes':self.limit.total_bytes-self.settled}
        self.write_completed = False
        self.pending = row  # Retention interruption cannot reopen admission.
        write_once(self.directory/f'response-{self.ordinal:08d}.intent.json',row)
        retain_wire(self.directory/f'response-{self.ordinal:08d}.wire.bin',wire)
        if len(wire)>self.limit.total_bytes-self.settled:
            self.exhausted = True
            write_once(self.directory/f'response-{self.ordinal:08d}.result.json',{
                'status':'DENIED_COMPLETE_RESPONSE_EXCEEDS_REMAINING_BUDGET','reservation':row,
                'written_bytes':0,'settled_after_bytes':self.settled})
            self.pending = None
            raise ResponseBudgetExhausted('RESPONSE_BYTE_BUDGET_EXHAUSTED_FULL_RESPONSE_WITHHELD')
        try:
            offset=0
            while offset<len(wire):
                count=self.sink.write(wire[offset:])
                if type(count) is not int or not 0<count<=len(wire)-offset:
                    raise OSError('unknown or invalid sink write count')
                offset+=count
                self.written+=count
        except BaseException:
            self.unknown=True
            raise
        self.write_completed = True
        # No settlement until flush and record retention both succeed.
        return len(wire)

    def flush(self):
        if self.unknown or self.exhausted:
            raise ValueError('egress admission closed; no flush replay')
        if self.pending is None or not self.write_completed:
            raise ValueError('matching completely written pending response required')
        try:
            self.sink.flush()
            row=self.pending
            write_once(self.directory/f"response-{row['ordinal']:08d}.result.json",{
                'status':'COMPLETE_RESPONSE_WRITTEN_FLUSHED_AND_RETAINED','reservation':row,
                'written_bytes':row['wire_bytes'],'settled_after_bytes':self.settled+row['wire_bytes']})
        except BaseException:
            self.unknown=True
            raise
        self.settled+=row['wire_bytes']
        self.pending=None
        self.write_completed=False
