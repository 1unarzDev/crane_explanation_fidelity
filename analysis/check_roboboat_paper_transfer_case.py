"""Check every raw reconstruction and actual interval-boundary counterexamples."""
import copy
import json
import math
from pathlib import Path
from build_roboboat_paper_transfer_case import DEFAULT, binding, check, reconstruct, save


def main():
    records = [json.loads(line) for line in (DEFAULT / 'raw-field-capsule.jsonl').read_text().splitlines()]
    eligible = [r for r in records if r['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT']
    published = json.loads((DEFAULT / 'episode-reconstruction.json').read_text())
    summary = json.loads((DEFAULT / 'descriptive-summary.json').read_text())
    checks = {}; maximum_numeric_difference = 0.; sources = []
    checks['all_48_identities_unique'] = len({r['id'] for r in records}) == len(records) == 48
    checks['all_46_reconstruct_identically'] = [reconstruct(r) for r in eligible] == published
    for record, result in zip(eligible, published):
        check(record['raw_fixture']); check(record['task_source']); check(record['export_terminal'])
        raw = json.loads(Path(record['raw_fixture']['path']).read_text())
        assert record['post_result'] == [r for r in raw['trajectory'] if r['phase'] == 'post_result']
        assert record['terminal_event'] == raw['terminalEventV2']
        assert record['task'] == json.loads(Path(record['task_source']['path']).read_text())
        packets = [json.loads(check(p).read_text()) for p in record['packets']]
        assert packets[0]['action'] == packets[1]['action'] == packets[2]['action']
        assert 'post_result' not in packets[0] and 'return_observation' not in packets[0]
        assert 'post_result' not in packets[1] and packets[1]['return_observation'] == packets[2]['return_observation']
        assert packets[0]['task'] == packets[1]['task'] == packets[2]['task'] == record['task']
        assert len(packets[2]['post_result']) == len(record['post_result'])
        for source, packet_row in zip(record['post_result'], packets[2]['post_result']):
            assert all(source[k] == packet_row[k] for k in ('x', 'y', 'yaw', 'simSeconds'))
            u, v, angle = source['bodySurge'], source['bodySway'], source['yaw']
            assert abs(packet_row['velocity']['vx'] - (u * math.cos(angle) - v * math.sin(angle))) < 1e-12
            assert abs(packet_row['velocity']['vy'] - (u * math.sin(angle) + v * math.cos(angle))) < 1e-12
            assert packet_row['velocity']['yaw_rate'] == source['bodyYawRate']
        output = json.loads(check(record['production_output']).read_text())['certificate']
        assert result['component_support'] == output['component_support']
        assert result['interval_sim_seconds'] == output['interval_s']
        assert result['full_sampled_window'] == output['coverage']['complete_sampled_window']
        assert result['in_dwell_sample_count'] == output['coverage']['sample_count']
        for m, prod in zip([m for m in result['measurements'] if m['sim_seconds'] <= result['interval_sim_seconds'][1]], output['measurements']):
            differences = [abs(m['signed_margins'][k] - prod['signed_margins'][k]) for k in m['signed_margins']]
            maximum_numeric_difference = max(maximum_numeric_difference, *differences)
            assert max(differences) < 1e-12
        assert set(result['witnesses']) == set(output['witnesses'])
        for k, witness in result['witnesses'].items():
            assert witness['sim_seconds'] == output['witnesses'][k]['time_s']
            assert result['interval_sim_seconds'][0] <= witness['sim_seconds'] <= result['interval_sim_seconds'][1]
            assert witness['signed_margins'][k] < 0
        sources.extend([record['raw_fixture'], record['task_source'], *record['packets'], record['production_output']])
    checks['all_actual_raw_fields_and_tasks_exact'] = True
    checks['all_actual_removal_only_ladders_exact'] = True
    checks['all_actual_packet_pose_velocity_conversions_exact'] = True
    checks['all_production_states_intervals_coverage_and_witnesses_agree_after_raw_recheck'] = True
    checks['independent_rectangle_extents_match_all_production_corner_margins'] = maximum_numeric_difference < 1e-12
    checks['categories_partition_all_admitted_records'] = sum(summary['mutually_exclusive_categories'].values()) == 46
    checks['coverage_partition'] = summary['full_sampled_windows'] == 45
    checks['violation_marginals_retained_with_overlap'] = summary['component_violation_marginals'] == {
        'position': 19, 'heading': 0, 'speed': 13, 'yaw_rate': 1, 'hull': 0}
    checks['no_full_satisfaction_claim_from_missing_contact'] = summary['full_completion'] == {'refuted': 23, 'unresolved': 23}
    # Actual sampled-compliant record, extended with an out-of-dwell violation.
    base = next(r for r, s in zip(eligible, published) if s['sampled_observed_component_compliance'])
    extended = copy.deepcopy(base)
    late = copy.deepcopy(extended['post_result'][-1])
    late['simSeconds'] += 1; late['wallSeconds'] += 1; late['x'] += 100
    extended['post_result'].append(late)
    original = reconstruct(base); later = reconstruct(extended)
    checks['out_of_dwell_violation_cannot_refute_fixed_dwell'] = later['category'] == original['category'] and not later['witnesses']
    # Truncate an actual violation episode after its first negative witness.
    base = next(r for r, s in zip(eligible, published) if s['first_violation'])
    original = reconstruct(base); short = copy.deepcopy(base)
    short['post_result'] = [r for r in short['post_result'] if r['simSeconds'] <= original['first_violation']['sim_seconds']]
    partial = reconstruct(short)
    checks['point_violation_refutes_despite_incomplete_window_and_missing_contact'] = (
        not partial['full_sampled_window'] and partial['full_completion'] == 'refuted')
    checks['incomplete_no_violation_is_unresolved'] = any(
        r['category'] == 'incomplete-window-no-observed-violation' and r['full_completion'] == 'unresolved'
        for r in published)
    if not all(checks.values()):
        raise AssertionError(checks)
    report = {'schema': 'roboboat-paper-raw-reconstruction-qa/v1', 'checker': binding(__file__),
              'analysis': binding(Path(__file__).with_name('build_roboboat_paper_transfer_case.py')),
              'checks': checks, 'passing_checks': len(checks), 'records_checked': 46,
              'maximum_signed_margin_difference': maximum_numeric_difference,
              'source_bindings': sources,
              'scope': 'Full original local raw-source audit plus independent numerical/temporal reconstruction, exact removal-only packet verification, and actual-record boundary perturbations. No language-judge accuracy or hardware validation.'}
    save(DEFAULT / 'raw-reconstruction-qa.json', report)
    print(json.dumps({k: report[k] for k in ('passing_checks', 'records_checked', 'maximum_signed_margin_difference')}))


if __name__ == '__main__':
    main()
