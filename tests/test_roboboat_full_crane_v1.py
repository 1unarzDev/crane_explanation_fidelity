"""Architecture and adversarial tests using construction-defined packet variants."""
import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import roboboat_full_crane_v1 as adapter
from roboboat_temporal_certificate_v2 import upgrade_development_packet

ROOT = Path(__file__).resolve().parents[1]


def packet():
    old = json.loads((ROOT / 'artifacts/roboboat-terminal-settling-v1/batches/boat-terminal-settling-002/method_packets/L2.json').read_text())
    task = json.loads((ROOT / 'docs/roboboat_terminal_evidence/task_contract_v2.json').read_text())
    return upgrade_development_packet(old, 'construction-full-crane-v1', task)


def explain(p, **kw):
    return adapter.explain(p, configuration_id='configuration', episode_id='episode',
                           condition_id='condition', **kw)


def claims(output):
    return set(output['diagnostic_result']['approved_claim_ids'])


def test_calls_actual_shared_architecture_and_preserves_inputs():
    p = packet(); original = copy.deepcopy(p)
    with patch.object(adapter, 'diagnose', wraps=adapter.diagnose) as planner, \
         patch.object(adapter, 'realize', wraps=adapter.realize) as realizer:
        out = explain(p)
    planner.assert_called_once(); realizer.assert_called_once()
    assert p == original
    assert out['development_only']
    assert out['realization_mode'] == 'deterministic-zero-model-closed-template'
    assert out['realization']['audit']['status'] == 'ACCEPTED'
    assert set(out['plan']['required_claim_ids']) == claims(out)
    assert len(out['numeric_source_bindings']) == len(out['plan']['approved_numeric_values'])
    assert out['realization']['audit']['missing_required_claim_ids'] == ()
    assert 'claim-physical-cause' not in claims(out)
    assert 'claim-continuous-compliance' not in claims(out)


@pytest.mark.parametrize('level',[0,1,2])
def test_ladder_missing_evidence_is_not_invented(level):
    p = packet()
    if level < 2: p.pop('post_result')
    if level == 0: p.pop('return_observation')
    out = explain(p)
    assert 'claim-dwell-unknown' in claims(out)
    assert ('claim-return-position' in claims(out)) == (level > 0)
    assert ('claim-position-compliance' in claims(out)) == (level == 2)
    assert 'claim-contact-unknown' in claims(out)
    text = out['realization']['final_response']
    assert 'do not identify the physical cause' in text
    assert 'do not establish continuous-time compliance' in text


@pytest.mark.parametrize('component',['position','heading','speed','yaw_rate','hull'])
def test_witness_failure_preserves_sample_time_margin_and_bound(component):
    p = packet(); row = p['post_result'][20]
    if component == 'position': row['x'] += 2
    elif component == 'heading': row['yaw'] += 1
    elif component == 'speed': row['velocity']['vx'] = 4
    elif component == 'yaw_rate': row['velocity']['yaw_rate'] = 3
    else: row['x'] += 8
    out = explain(p)
    assert 'claim-dwell-failed' in claims(out)
    assert 'claim-' + component + '-violation' in claims(out)
    nums = {x['slot_id']: x['value'] for x in out['plan']['approved_numeric_values']
            if x['claim_id'] == 'claim-' + component + '-violation'}
    assert nums['witness_time'] == row['simSeconds']
    assert nums['signed_margin'] < 0
    assert 'claim-' + component + '-compliance' not in claims(out)


def contact(p, hit=False, complete=False, clock=None):
    lo=p['post_result'][0]['simSeconds']; hi=lo+p['task']['dwell_s']
    return {'clock': clock or p['task']['clock'], 'coverage':[lo,hi], 'complete':complete,
            'sensor_identity':'construction_only',
            'completeness_basis':'complete-prohibited-contact-event-stream' if complete else 'no-completeness-guarantee',
            'samples':[{'time_s':lo,'count':1}] if hit else []}


@pytest.mark.parametrize('mode',['hit','complete','silence','unaligned'])
def test_contact_uses_event_policy_and_clock(mode):
    p=packet();p['contacts']=contact(p, hit=mode in ('hit','unaligned'),
                                    complete=mode=='complete',clock='other' if mode=='unaligned' else None)
    out=explain(p)
    wanted={'hit':'violation','complete':'compliance','silence':'unknown','unaligned':'unknown'}[mode]
    assert 'claim-contact-'+wanted in claims(out)
    if mode=='complete': assert 'claim-dwell-sampled-success' in claims(out)
    if mode=='hit': assert 'claim-dwell-failed' in claims(out)


def test_unknown_cause_injection_repaired_and_missing_information_restored():
    p=packet(); initial=explain(p); candidate=copy.deepcopy(initial['candidate'])
    candidate['clauses']=[{'clause_id':'attack','kind':'CLAIM','contract_id':'claim-physical-cause','numeric_values':[]}]
    out=explain(p,candidate=candidate);audit=out['realization']['audit']
    assert audit['status']=='REPAIRED'
    assert 'claim-physical-cause' in audit['unapproved_claim_ids']
    assert set(audit['represented_required_claim_ids']) == claims(out)
    assert audit['missing_limitation_ids']==()
    assert not any(c['contract_id']=='claim-physical-cause' for c in out['realization']['final_clauses'])


@pytest.mark.parametrize('mode',['value','unit','slot','missing'])
def test_wrong_numeric_slots_are_removed_then_reconstructed(mode):
    p=packet();initial=explain(p);candidate=copy.deepcopy(initial['candidate'])
    clause=next(c for c in candidate['clauses'] if c['contract_id']=='claim-return-position')
    if mode=='value': clause['numeric_values'][0]['value'] += 999
    elif mode=='unit': clause['numeric_values'][0]['unit']='feet'
    elif mode=='slot': clause['numeric_values'][0]['slot_id']='fabricated_slot'
    else: clause['numeric_values']=[]
    out=explain(p,candidate=candidate);audit=out['realization']['audit']
    assert audit['status']=='REPAIRED'
    assert audit['numeric_mismatches']
    repaired=next(c for c in out['realization']['final_clauses'] if c['contract_id']=='claim-return-position')
    original=next(c for c in initial['realization']['final_clauses'] if c['contract_id']=='claim-return-position')
    assert repaired['text']==original['text']


@pytest.mark.parametrize('field',['gold','evaluator_truth','source_path','diagnostic_result'])
def test_evaluator_and_path_fields_rejected(field):
    p=packet();p[field]='hidden'
    with pytest.raises(ValueError):explain(p)


def test_packet_binding_and_unknown_status_fail_closed():
    p=packet();initial=explain(p); candidate=copy.deepcopy(initial['candidate'])
    p['return_observation']['x'] += 1
    with pytest.raises(ValueError,match='bound'):explain(p,candidate=candidate)
    p=packet();p['action']['status']='custom-result'
    with pytest.raises(ValueError,match='unregistered action'):explain(p)


@pytest.mark.parametrize('value',[float('nan'),float('inf'),float('-inf')])
def test_nonfinite_candidate_values_fail_closed(value):
    p=packet(); initial=explain(p); candidate=copy.deepcopy(initial['candidate'])
    clause=next(c for c in candidate['clauses'] if c['contract_id']=='claim-return-position')
    clause['numeric_values'][0]['value']=value
    with pytest.raises(ValueError,match='finite'):explain(p,candidate=candidate)
