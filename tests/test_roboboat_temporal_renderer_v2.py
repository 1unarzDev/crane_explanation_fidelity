import pytest
from roboboat_temporal_renderer_v2 import distinct_decimals,render_v2


@pytest.mark.parametrize('value,bound',[(.050010012123028094,.05),(.40000000001,.4),(.35+.000001,.35)])
def test_printed_measurement_preserves_threshold_crossing(value,bound):
    observed,threshold=distinct_decimals(value,bound)
    assert float(observed)>float(threshold)


def test_actual_near_bound_speed_pattern_gets_distinct_final_numbers():
    from pathlib import Path
    import json
    root=Path(__file__).resolve().parents[1]
    batch=root/'artifacts/roboboat-terminal-v3/batches/boat-terminal-pilot-005'
    if not batch.exists():pytest.skip('retained development recording unavailable')
    packet=json.loads((batch/'method_packets/L2.json').read_text())
    output=json.loads((batch/'contract_outputs/L2.json').read_text())
    assert '0.0500 m/s, exceeding the 0.0500' in output['answer']
    corrected=render_v2(packet,output['certificate'])
    assert '0.05001 m/s, exceeding the 0.05000 m/s bound' in corrected
    assert 'do not identify the physical cause' in corrected
