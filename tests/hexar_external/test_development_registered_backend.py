import json
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.development_registered_backend import DevelopmentBackend, transcript_policy

ROOT = Path(__file__).resolve().parents[2]


def test_actual_retained_cli_transcripts_pass_but_tools_or_missing_turn_do_not():
    run = ROOT/'manifests/hexar_external/confirmatory_v1/development_v4_complete_instrument_screen_v1'
    raw = next(run.glob('*/stdout.jsonl')).read_bytes()
    assert transcript_policy(raw, 0)
    assert not transcript_policy(raw, 124)
    assert not transcript_policy(b'', 0)
    events = [json.loads(line) for line in raw.splitlines()]
    assert not transcript_policy(b'\n'.join(json.dumps(e).encode() for e in events[:-1]), 0)
    tool = dict(type='item.completed', item=dict(type='command_execution', command='forbidden'))
    events.insert(-1, tool)
    assert not transcript_policy(b'\n'.join(json.dumps(e).encode() for e in events), 0)


def test_development_backend_cannot_accept_confirmation_or_changed_request(tmp_path):
    with pytest.raises(ValueError, match='confirmation forbidden'):
        DevelopmentBackend({'phase':'confirmation'}, tmp_path/'not-invoked', 'f'*64)
    registry = {'phase':'development_qualification', 'jobs':[{'request':{'development_only':True}}]}
    backend = DevelopmentBackend(registry, tmp_path/'not-invoked', 'f'*64)
    with pytest.raises(ValueError, match='exact registered'):
        backend({'development_only':False})
