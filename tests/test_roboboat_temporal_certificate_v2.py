"""Successor contact-policy tests use construction-defined, not robot, events."""
import copy
import json
from pathlib import Path
import pytest
from roboboat_temporal_certificate_v2 import certificate, render, upgrade_development_packet, validate_packet, audit_ladder
from reference_roboboat_temporal_v2 import calculate

ROOT = Path(__file__).resolve().parents[1]


def packet():
    old = json.loads((ROOT/'artifacts/roboboat-terminal-settling-v1/batches/boat-terminal-settling-002/method_packets/L2.json').read_text())
    task = json.loads((ROOT/'docs/roboboat_terminal_evidence/task_contract_v2.json').read_text())
    return upgrade_development_packet(old, 'construction-contact-v2', task)


def contact(p, *, hit=None, complete=False, clock=None, coverage=None):
    lo = p['post_result'][0]['simSeconds']; hi = lo + p['task']['dwell_s']
    return {'clock': clock or p['task']['clock'], 'coverage': coverage or [lo,hi],
            'complete': complete, 'sensor_identity': 'construction_only',
            'completeness_basis': 'complete-prohibited-contact-event-stream' if complete else 'no-completeness-guarantee',
            'samples': [] if hit is None else [{'time_s':hit,'count':1}]}


def checked(p, expected, contact_expected):
    c = certificate(p); r = calculate(p)
    assert c['sampled_task_support'] == r['sampled_task_support'] == expected
    assert c['component_support']['contact'] == r['contact_support'] == contact_expected
    return c


def test_no_contact_evidence_is_unknown_and_positive_kinematics_are_explained():
    p=packet(); c=checked(p,'unknown','unknown'); answer=render(p,c)
    assert 'no prohibited hull contact' in answer
    assert 'All 251 observed samples' in answer
    assert 'met the position' in answer
    assert 'do not identify the physical cause' in answer


@pytest.mark.parametrize('complete',[False,True])
def test_aligned_violation_is_sufficient_without_complete_capture(complete):
    p=packet(); hit=p['post_result'][20]['simSeconds']; p['contacts']=contact(p,hit=hit,complete=complete)
    c=checked(p,'false','false')
    assert c['witnesses']['contact']=={'time_s':hit,'count':1}
    assert '1 prohibited contacts' in render(p,c)


@pytest.mark.parametrize('hit',[False,True])
def test_wrong_clock_supports_neither_absence_nor_violation(hit):
    p=packet(); time=p['post_result'][20]['simSeconds'] if hit else None
    p['contacts']=contact(p,hit=time,complete=True,clock='fixture-monotonic')
    c=checked(p,'unknown','unknown')
    assert c['contact_evidence']['reason']=='contact-clock-unaligned'
    assert 'contact' not in c['witnesses']


def test_full_absence_guarantee_is_answerable_sampled_success():
    p=packet();p['contacts']=contact(p,complete=True)
    c=checked(p,'true','true'); answer=render(p,c)
    assert 'All required conditions held' in answer
    assert 'aligned complete prohibited-contact event stream' in answer
    assert c['continuous_task_support']=='unknown'
    assert 'Physical docking completion is unestablished' not in answer


@pytest.mark.parametrize('mode',['incomplete','short','late-hit'])
def test_silence_or_partial_coverage_cannot_establish_absence(mode):
    p=packet();lo=p['post_result'][0]['simSeconds']; hi=lo+p['task']['dwell_s']
    p['contacts']=contact(p,complete=mode!='incomplete')
    if mode=='short':p['contacts']['coverage'][1]=hi-.01
    if mode=='late-hit':
        p['contacts']['complete']=False
        p['contacts']['completeness_basis']='no-completeness-guarantee'
        p['contacts']['coverage'][1]=hi+1
        p['contacts']['samples']=[{'time_s':hi+1,'count':1}]
    checked(p,'unknown','unknown')


def test_late_contact_does_not_falsify_fixed_dwell():
    p=packet();hi=p['post_result'][0]['simSeconds']+p['task']['dwell_s']
    p['contacts']=contact(p,complete=True,coverage=[hi-p['task']['dwell_s'],hi+1],hit=hi+1)
    checked(p,'true','true')


@pytest.mark.parametrize('offset',[0,5])
def test_contact_at_either_declared_endpoint_is_a_violation(offset):
    p=packet();p['contacts']=contact(p,hit=p['post_result'][0]['simSeconds']+offset)
    checked(p,'false','false')


def test_pose_violation_remains_false_even_when_contact_clock_is_wrong():
    p=packet();p['post_result'][20]['x']+=2
    p['contacts']=contact(p,complete=True,clock='other')
    checked(p,'false','unknown')


@pytest.mark.parametrize('mode',['count','nan','clock','coverage','complete','basis','extra','sample-extra','sensor','duplicate','outside'])
def test_contact_schema_fails_closed(mode):
    p=packet();lo=p['post_result'][0]['simSeconds'];p['contacts']=contact(p,complete=True,hit=lo)
    c=p['contacts']
    if mode=='count':c['samples'][0]['count']=True
    elif mode=='nan':c['samples'][0]['time_s']=float('nan')
    elif mode=='clock':c['clock']=''
    elif mode=='coverage':c['coverage'].reverse()
    elif mode=='complete':c['complete']=1
    elif mode=='basis':c['completeness_basis']='no-completeness-guarantee'
    elif mode=='extra':c['gold']='true'
    elif mode=='sample-extra':c['samples'][0]['source_path']='/secret'
    elif mode=='sensor':c['sensor_identity']='/secret'
    elif mode=='duplicate':c['samples']*=2
    else:c['samples'][0]['time_s']=lo-1
    with pytest.raises(ValueError):validate_packet(p)


def test_ladder_is_removal_only_and_policy_identical_at_every_level():
    p=packet(); levels=[copy.deepcopy(p) for _ in range(3)]
    levels[0].pop('return_observation');levels[0].pop('post_result');levels[1].pop('post_result')
    assert audit_ladder(levels)['status']=='PASS'
    assert [certificate(x)['sampled_task_support'] for x in levels]==['unknown']*3
    assert all('no prohibited hull contact' in render(x,certificate(x)) for x in levels)
    levels[0]['contacts']=contact(p)
    with pytest.raises(ValueError):audit_ladder(levels)


def test_old_packet_and_contract_cannot_be_silently_reidentified():
    p=packet(); old=copy.deepcopy(p);old['schema']='roboboat-evidence-packet/v1'
    with pytest.raises(ValueError):validate_packet(old)
    with pytest.raises(ValueError):upgrade_development_packet(p,p['packet_id'],p['task'])


def test_unanchored_dwell_prevents_using_contacts_at_L0():
    p=packet();p['contacts']=contact(p,complete=True,hit=p['post_result'][0]['simSeconds'])
    p.pop('post_result');p.pop('return_observation')
    c=checked(p,'unknown','unknown')
    assert c['contact_evidence']['reason']=='declared-dwell-unanchored'


def test_upgrade_cannot_loosen_noncontact_requirement():
    old=json.loads((ROOT/'artifacts/roboboat-terminal-settling-v1/batches/boat-terminal-settling-002/method_packets/L2.json').read_text())
    task=json.loads((ROOT/'docs/roboboat_terminal_evidence/task_contract_v2.json').read_text())
    task['position_tolerance_m']=1
    with pytest.raises(ValueError,match='preserve all non-contact'):
        upgrade_development_packet(old,'new-contact-v2',task)


def test_policy_with_answer_metadata_is_rejected():
    p=packet();p['task']['contact_policy']['gold']='true'
    with pytest.raises(ValueError,match='unsupported contact policy'):
        validate_packet(p)
