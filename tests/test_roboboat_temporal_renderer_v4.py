import copy
import json
from pathlib import Path
import pytest
from roboboat_temporal_renderer_v4 import render_v4
from roboboat_temporal_renderer_v3 import render_v3

ROOT=Path(__file__).resolve().parents[1]


def retained(level=2):
    root=ROOT/'artifacts/roboboat-terminal-settling-v1/batches/boat-terminal-settling-001'
    if not root.exists():pytest.skip('retained development capture unavailable')
    packet=json.loads((root/'method_packets'/f'L{level}.json').read_text())
    cert=json.loads((root/'candidate_v3_outputs'/f'L{level}.json').read_text())['certificate']
    return packet,cert


def test_sampled_success_is_communicated_without_contact_absence_or_continuous_claim():
    p,c=retained();text=render_v4(p,c)
    assert 'All 251 observed samples in the declared 248.420270–253.420270 s dwell' in text
    assert 'met the position, heading, translational-speed, yaw-rate and hull-containment requirements' in text
    assert 'maximum sample gap 0.0200 s' in text
    assert 'contact restrictions' in text and 'completion is unestablished' in text
    assert 'Continuous-time compliance remains unestablished' in text
    assert 'do not identify the physical cause' in text


def test_l0_l1_missing_interval_and_incomplete_component_cannot_be_promoted():
    for level in (0,1):
        p,c=retained(level);assert render_v4(p,c)==render_v3(p,c)
    p,c=retained();c=copy.deepcopy(c);c['component_support']['speed']='unknown'
    assert render_v4(p,c)==render_v3(p,c)
    p,c=retained();c['coverage']['complete_sampled_window']=False
    assert render_v4(p,c)==render_v3(p,c)


def test_fully_observed_task_success_keeps_positive_language():
    p,c=retained();c['component_support']['contact']='true';c['unavailable']=[]
    c['sampled_task_support']='true'
    text=render_v4(p,c)
    assert 'All required conditions held at the observed samples' in text
    assert 'Physical docking completion is unestablished' not in text
    assert 'continuous-time compliance remains unestablished' in text
