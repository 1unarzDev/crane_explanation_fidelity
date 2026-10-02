import json
from pathlib import Path
import pytest
from roboboat_temporal_renderer_v3 import render_v3

ROOT=Path(__file__).resolve().parents[1]


def packet_output(level):
    batch=ROOT/'artifacts/roboboat-terminal-v3/batches/boat-terminal-pilot-005'
    if not batch.exists():pytest.skip('retained development recording unavailable')
    return (json.loads((batch/f'method_packets/L{level}.json').read_text()),
            json.loads((batch/f'contract_outputs/L{level}.json').read_text())['certificate'])


def test_unknown_interval_is_not_described_as_missing_requirement_definitions():
    p,c=packet_output(1);text=render_v3(p,c)
    assert 'remain unestablished over the declared dwell' in text
    assert 'Missing requirements' not in text and 'yaw_rate' not in text
    assert 'position error 0.1953 m' in text


def test_margin_and_error_growth_keep_distinct_origins_and_near_bound_precision():
    p,c=packet_output(2);text=render_v3(p,c)
    assert 'radial error increased by 0.1472 m' in text
    assert 'remaining position margin at the result-adjacent observation was 0.2047 m' in text
    assert 'grew by 0.1472 m from' not in text
    assert '0.05001 m/s, exceeding the 0.05000 m/s bound' in text
    assert 'do not identify the physical cause' in text


def test_inward_motion_is_not_called_growth():
    p,c=packet_output(2);c['radial_error_growth_m']=-.01
    assert 'radial error decreased by 0.0100 m' in render_v3(p,c)
