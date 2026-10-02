import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('capture_health', ROOT / 'analysis/audit_roboboat_capture_health_v1.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)


def fixture(tmp_path):
    rows = [{'simulatedSeconds': float(i), 'observationQueueAgeTicks': 2,
             'staleObservations': 0, 'failedObservations': 0} for i in range(3)]
    result = {key: 0 for key in health.ZERO_COUNTERS}
    result.update(valid=True, validationSamplesCaptured=3, maximumObservationQueueAgeTicks=2,
                  actionTiming={'maximumSourceToApplicationTicks': 5, 'maximumReceiveToApplicationTicks': 1})
    return result, rows


def write(tmp_path, result, rows):
    (tmp_path / 'result.json').write_text(json.dumps(result))
    (tmp_path / 'result.validation.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
    return health.audit(tmp_path)


def test_clean_worker(tmp_path):
    result, rows = fixture(tmp_path)
    assert write(tmp_path, result, rows)['healthy']


def test_catches_stale_burst_even_if_terminal_counter_falsely_clean(tmp_path):
    result, rows = fixture(tmp_path)
    rows[1]['staleObservations'] = rows[2]['staleObservations'] = 3
    rows[1]['observationQueueAgeTicks'] = 17
    report = write(tmp_path, result, rows)
    assert not report['healthy']
    assert 'trace_staleObservations_not_zero' in report['failures']
    assert report['first_counter_events']['staleObservations']['previous_sample_seconds'] == 0
    assert report['maximum_observation_queue_age_ticks'] == 17


def test_catches_action_invalid_and_truncated_trace(tmp_path):
    result, rows = fixture(tmp_path)
    result['staleActions'] = result['rejectedActions'] = 1
    report = write(tmp_path, result, rows[:2])
    assert 'staleActions_not_zero' in report['failures']
    assert 'validation_stream_count_mismatch' in report['failures']


def test_nonmonotonic_counter_and_timestamp(tmp_path):
    result, rows = fixture(tmp_path)
    rows[1]['staleObservations'] = 1
    rows[2]['simulatedSeconds'] = -1
    report = write(tmp_path, result, rows)
    assert 'invalid_trace_timestamp' in report['failures']
