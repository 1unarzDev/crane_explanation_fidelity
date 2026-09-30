import io
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_response_egress import BudgetedOutput,ResponseByteLimit,ResponseBudgetExhausted


class ShortSink(io.BytesIO):
    def write(self,wire):return super().write(wire[:3])


def test_short_writes_are_completed_without_repeating_response_bytes(tmp_path):
    sink=ShortSink();out=BudgetedOutput(sink,tmp_path/'egress',limit=ResponseByteLimit(1024))
    wire='αβ response\n'.encode()
    assert out.write(wire)==len(wire)
    assert out.snapshot()['remaining_bytes'] is None
    out.flush()
    assert sink.getvalue()==wire and out.snapshot()['settled_flushed_bytes']==len(wire)
    assert out.snapshot()['observed_write_bytes']==len(wire)


def test_complete_response_denied_without_partial_send_or_budget_rounding(tmp_path):
    sink=io.BytesIO();out=BudgetedOutput(sink,tmp_path/'egress',limit=ResponseByteLimit(1024))
    first=b'x'*1022+b'\n';out.write(first);out.flush()
    with pytest.raises(ResponseBudgetExhausted):out.write(b'{}\n')
    assert sink.getvalue()==first and out.snapshot()['remaining_bytes']==1
    assert out.snapshot()['budget_exhausted'] and out.snapshot()['pending_response'] is None
    with pytest.raises(ValueError,match='closed'):out.write(b'\n')


@pytest.mark.parametrize('count',[0,-1,None,True,9999])
def test_unverifiable_sink_count_closes_admission(tmp_path,count):
    class Sink:
        def write(self,wire):return count
        def flush(self):raise AssertionError('must not flush')
    out=BudgetedOutput(Sink(),tmp_path/'egress',limit=ResponseByteLimit(1024))
    with pytest.raises(OSError):out.write(b'{}\n')
    assert out.snapshot()['unknown_delivery'] and out.snapshot()['remaining_bytes'] is None
    with pytest.raises(ValueError,match='closed'):out.write(b'{}\n')
    with pytest.raises(ValueError,match='closed'):out.flush()


@pytest.mark.parametrize('defect',['partial_exception','flush_exception','intent_storage','settlement_storage'])
def test_send_or_storage_uncertainty_cannot_be_replayed_or_adopted(tmp_path,monkeypatch,defect):
    import evidence_calibration_response_egress as module
    class Sink(io.BytesIO):
        calls=0
        def write(self,wire):
            self.calls+=1
            if defect=='partial_exception':
                if self.calls==1:return super().write(wire[:2])
                raise OSError('injected partial send failure')
            return super().write(wire)
        def flush(self):
            if defect=='flush_exception':raise OSError('injected flush failure')
            return super().flush()
    sink=Sink();out=BudgetedOutput(sink,tmp_path/'egress',limit=ResponseByteLimit(1024))
    original=module.write_once
    def fail(path,row):
        if (defect=='intent_storage' and path.name.endswith('01.intent.json')) or (defect=='settlement_storage' and path.name.endswith('.result.json')):raise OSError('injected storage failure')
        return original(path,row)
    monkeypatch.setattr(module,'write_once',fail)
    with pytest.raises(OSError):
        out.write(b'{"x":1}\n');out.flush()
    assert out.snapshot()['remaining_bytes'] is None
    assert out.snapshot()['settled_flushed_bytes']==0
    with pytest.raises(ValueError,match='closed'):out.write(b'{"x":1}\n')
    with pytest.raises(FileExistsError):BudgetedOutput(io.BytesIO(),tmp_path/'egress',limit=ResponseByteLimit(1024))
    assert not list((tmp_path/'egress').glob('*.result.json'))


@pytest.mark.parametrize('value',[True,0,1023,None,2**31+1])
def test_limit_is_explicit_and_typed(value):
    with pytest.raises(ValueError):ResponseByteLimit(value)
