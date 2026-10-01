"""Architecture and adversarial tests using construction-defined packet variants."""
import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import roboboat_full_crane_v2 as adapter
from roboboat_temporal_certificate_v2 import upgrade_development_packet

ROOT = Path(__file__).resolve().parents[1]


def packet():
    old = json.loads((ROOT / 'artifacts/roboboat-terminal-settling-v1/batches/boat-terminal-settling-002/method_packets/L2.json').read_text())
    task = json.loads((ROOT / 'docs/roboboat_terminal_evidence/task_contract_v2.json').read_text())
    return upgrade_development_packet(old, 'construction-full-crane-v2', task)


def explain(p, **kw):
    return adapter.explain(p, configuration_id='configuration', episode_id='episode',
                           condition_id='condition', **kw)


def timeout_packet():
    p = packet()
    p['action'].update(status='timeout', identity=None, receipt_wall_seconds=None,
                       receipt_clock=None, event_time_support='historical-event-time-unavailable')
    p.pop('post_result', None)
    p['return_observation']['alignment'] = 'last-pre-result-observation'
    return p


def claims(output):
    return set(output['diagnostic_result']['approved_claim_ids'])


@pytest.mark.parametrize('clock', ['fixture-monotonic', 'other', '', None])
def test_unsupported_sample_clock_cannot_emit_ros_header_clock_claim(clock):
    p = packet(); p['task']['clock'] = clock
    with pytest.raises(ValueError, match='sample clock'):
        explain(p)


@pytest.mark.parametrize('alignment', ['unrelated-observation', '', None])
def test_unregistered_reference_alignment_cannot_emit_temporal_scope(alignment):
    p = packet(); p['return_observation']['alignment'] = alignment
    with pytest.raises(ValueError, match='reference alignment'):
        explain(p)


def test_missing_reference_alignment_fails_closed():
    p = packet(); p['return_observation'].pop('alignment')
    with pytest.raises(ValueError, match='reference alignment'):
        explain(p)


@pytest.mark.parametrize('contradiction', ['recorded_receipt', 'post_result', 'receipt_aligned_reference'])
def test_fixture_timeout_cannot_supply_unobserved_terminal_result_scope(contradiction):
    p = timeout_packet()
    if contradiction == 'recorded_receipt':
        p['action'].update(event_time_support='recorded-client-receipt',
                           receipt_clock='fixture-monotonic', receipt_wall_seconds=1.0)
    elif contradiction == 'post_result':
        p['post_result'] = packet()['post_result']
    else:
        p['return_observation']['alignment'] = 'latest-delivered-at-client-receipt'
    with pytest.raises(ValueError, match='timeout.*result'):
        explain(p)


@pytest.mark.parametrize('location', ['return_observation', 'post_result'])
@pytest.mark.parametrize('source', ['command-instead-of-measured-odometry', '', None])
def test_velocity_must_be_delivered_odometry_not_command_or_unknown(location, source):
    p = packet()
    row = p[location] if location == 'return_observation' else p[location][0]
    row['velocity']['source'] = source
    with pytest.raises(ValueError, match='velocity source'):
        explain(p)


@pytest.mark.parametrize('scope', ['command-trace', '', None])
def test_unregistered_measurement_scope_is_rejected(scope):
    p = packet(); p['task']['measurement_scope'] = scope
    with pytest.raises(ValueError, match='measurement scope'):
        explain(p)


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


def slots(out, claim):
    return {row['slot_id']: row['value'] for row in out['plan']['approved_numeric_values']
            if row['claim_id'] == 'claim-' + claim}


def test_fixture_timeout_without_result_evidence_is_not_a_terminal_action_or_failure():
    p = packet()
    p['action'] = {'status': 'timeout', 'name': '/navigate_to_pose', 'identity': None,
                   'receipt_wall_seconds': None, 'receipt_clock': None,
                   'event_time_support': 'historical-event-time-unavailable'}
    p.pop('return_observation'); p.pop('post_result')
    out = explain(p)
    assert 'claim-action-timeout' in claims(out)
    assert 'claim-fixture-timeout-scope' in claims(out)
    assert 'claim-dwell-unknown' in claims(out)
    assert not claims(out) & {'claim-action-aborted', 'claim-action-canceled',
                              'claim-action-succeeded', 'claim-dwell-failed',
                              'claim-receipt-clock', 'claim-dwell-anchor'}
    assert out['condition_entry']['method_packet']['evidence']['marine_visible_packet']['packet'] == p
    assert 'The navigation fixture reported timeout.' in out['realization']['final_response']
    assert 'terminal ROS action result' in out['realization']['final_response']
    assert out['schema'] == 'roboboat-full-crane/v2-development'


def test_exact_configured_and_public_slots_remain_distinct_and_source_bound():
    p = packet()
    p['configuration'].update(xy_goal_tolerance=0.21, yaw_goal_tolerance=0.31,
                             trans_stopped_velocity=0.012, rot_stopped_velocity=0.022)
    out = explain(p)
    for key in ('xy_goal_tolerance', 'yaw_goal_tolerance', 'trans_stopped_velocity', 'rot_stopped_velocity'):
        assert slots(out, 'configured-' + key) == {key: p['configuration'][key]}
        binding = next(x for x in out['numeric_source_bindings'] if x['claim_id'] == 'claim-configured-' + key)
        assert binding['source'] == '/configuration/' + key
        assert binding['packet_sha256'] == adapter.canonical_sha256(p)
    public = slots(out, 'public-docking-requirements')
    assert public['position_tolerance_m'] == 0.4
    assert public['dwell_s'] == 5.0
    assert public['position_tolerance_m'] != slots(out, 'configured-xy_goal_tolerance')['xy_goal_tolerance']
    assert 'claim-physical-cause' not in claims(out)


def test_receipt_and_sample_anchor_use_distinct_clocks_without_substitution():
    p = packet(); p['action']['receipt_wall_seconds'] = 10000.25
    out = explain(p)
    assert slots(out, 'receipt-clock')['receipt_wall_seconds'] == 10000.25
    assert slots(out, 'dwell-anchor')['interval_start'] == p['post_result'][0]['simSeconds']
    assert slots(out, 'dwell-anchor')['interval_end'] == p['post_result'][0]['simSeconds'] + 5.0
    assert 'fixture-monotonic wall clock' in out['realization']['final_response']


def test_changed_plugin_supports_settings_only_not_algorithm_or_cause():
    p = packet(); p['configuration']['plugin'] = 'other::UnknownChecker'
    out = explain(p)
    assert 'claim-configured-xy_goal_tolerance' in claims(out)
    assert 'claim-physical-cause' not in claims(out)
    text = out['realization']['final_response']
    assert 'does not establish internal consumption or why the boat stopped' in text
    assert 'UnknownChecker' not in text


def test_missing_configuration_slot_is_withheld_instead_of_defaulted():
    p = packet(); del p['configuration']['xy_goal_tolerance']
    assert 'claim-configured-xy_goal_tolerance' not in claims(explain(p))


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -0.1, True, '0.2'])
def test_untrustworthy_configured_numbers_are_rejected(value):
    p = packet(); p['configuration']['xy_goal_tolerance'] = value
    with pytest.raises(ValueError, match='configured tolerance'):
        explain(p)


@pytest.mark.parametrize('value', [float('nan'), None, -1, True])
def test_claimed_recorded_receipt_requires_valid_clock_and_time(value):
    p = packet(); p['action']['receipt_wall_seconds'] = value
    with pytest.raises(ValueError, match='receipt time'):
        explain(p)


def test_new_required_numeric_claim_is_repaired_by_shared_realizer():
    p = packet(); initial = explain(p); candidate = copy.deepcopy(initial['candidate'])
    clause = next(c for c in candidate['clauses'] if c['contract_id'] == 'claim-configured-xy_goal_tolerance')
    clause['numeric_values'][0]['value'] = 999.0
    candidate['clauses'] = [c for c in candidate['clauses'] if c['contract_id'] != 'claim-public-docking-requirements']
    out = explain(p, candidate=candidate)
    assert out['realization']['audit']['status'] == 'REPAIRED'
    final = {c['contract_id']: c for c in out['realization']['final_clauses']}
    original = next(c for c in initial['realization']['final_clauses'] if c['contract_id'] == 'claim-configured-xy_goal_tolerance')
    assert final['claim-configured-xy_goal_tolerance']['text'] == original['text']
    assert 'claim-public-docking-requirements' in final


def test_timeout_cancellation_injection_is_removed_and_original_status_restored():
    p = timeout_packet()
    initial = explain(p); candidate = copy.deepcopy(initial['candidate'])
    candidate['clauses'].append({'clause_id': 'fake-cancellation', 'kind': 'CLAIM',
                                'contract_id': 'claim-action-canceled', 'numeric_values': []})
    out = explain(p, candidate=candidate)
    assert out['realization']['audit']['status'] == 'REPAIRED'
    assert not any(c['contract_id'] == 'claim-action-canceled' for c in out['realization']['final_clauses'])


@pytest.mark.parametrize('status', ['succeeded', 'aborted', 'canceled'])
def test_v1_kinematic_and_status_diagnosis_retained_exactly(status):
    import roboboat_full_crane_v1 as previous
    p = packet(); p['action']['status'] = status
    old = previous.explain(p, configuration_id='configuration', episode_id='episode', condition_id='condition')
    out = explain(p)
    new_ids = {'claim-action-timeout', 'claim-fixture-timeout-scope',
               'claim-public-docking-requirements', 'claim-receipt-clock'}
    new_ids.update('claim-configured-' + k for k in ('xy_goal_tolerance', 'yaw_goal_tolerance',
                                                   'trans_stopped_velocity', 'rot_stopped_velocity'))
    assert claims(out) - new_ids == claims(old)
    assert [v for v in out['plan']['approved_numeric_values'] if v['claim_id'] not in new_ids] == old['plan']['approved_numeric_values']
    assert [b for b in out['numeric_source_bindings'] if b['claim_id'] not in new_ids] == old['numeric_source_bindings']


def test_inherited_measurement_uses_public_geometry_not_configured_threshold():
    import math
    p = packet(); p['configuration']['xy_goal_tolerance'] = 100.0
    out = explain(p); observed = p['return_observation']; goal = p['task']['goal']
    expected = math.hypot(observed['x'] - goal['x'], observed['y'] - goal['y'])
    numeric = slots(out, 'return-position')
    assert numeric['position_error'] == pytest.approx(expected, abs=1e-14)
    assert numeric['position_margin'] == pytest.approx(p['task']['position_tolerance_m'] - expected, abs=1e-14)
    assert numeric['position_bound'] == p['task']['position_tolerance_m']


def test_full_v2_source_references_and_method_hash_bind_original_packet():
    p = timeout_packet(); out = explain(p)
    method = out['condition_entry']['method_packet']
    expected_ref = 'marine-packet-' + adapter.canonical_sha256(p)
    assert out['facts']['method_packet_sha256'] == adapter.canonical_sha256(method)
    assert out['condition_entry']['condition']['method_packet_sha256'] == adapter.canonical_sha256(method)
    assert all(v['support_reference'] == expected_ref for v in out['plan']['approved_numeric_values'])
    assert all(b['packet_sha256'] == adapter.canonical_sha256(p) for b in out['numeric_source_bindings'])
