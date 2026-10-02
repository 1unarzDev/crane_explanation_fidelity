#!/usr/bin/env python3
"""Read-only metadata projection; never reads answers, caches, labels, or join keys."""
import argparse, collections, csv, datetime, hashlib, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, default=Path('.'))
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--scheduled-through', type=int, default=1600,
                    help='Operational launch cutoff, not the scientific candidate cap')
args = parser.parse_args()
root = args.root.resolve()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
study = 'evidence-calibration-b4-b2-confirmation-2026-10-01'
freeze_path = root / 'manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json'
freeze_bytes = freeze_path.read_bytes()
freeze = json.loads(freeze_bytes)
allocation = json.loads((root / freeze['candidate_allocation_path']).read_text())
exceptions = json.loads((root / 'manifests/study/evidence-calibration-handoff-freshness-exceptions-v1.json').read_text())
excluded = {x['run_id'] for x in exceptions['exceptions']}
configs = [x for x in allocation['configurations'] if x['stage'] == 'confirmation']
assert len({x['run_id'] for x in configs}) == len(configs)
assert len({x['cluster_id'] for x in configs}) == len(configs)
physical_root = root / 'data/evaluator_only/analysis/handoff-fresh-candidate-collection-v1'
status_root = root / 'model_outputs' / study / 'status'
rows = []
condition_statuses = collections.Counter()
technical_failure_ids = []
for config in configs:
    run_id = config['run_id']
    p = physical_root / (run_id + '.json')
    s = status_root / (run_id + '.json')
    intent = status_root / (run_id + '.intent.json')
    row = {'run_id': run_id, 'independent_cluster_id': config['cluster_id'],
           'prefreeze_excluded': run_id in excluded,
           'operationally_scheduled': int(run_id.rsplit('-', 1)[1]) <= args.scheduled_through,
           'physical_record_present': p.exists(), 'physical_return_code': '',
           'physical_technical_valid': '', 'physical_preprocessing_complete': '',
           'method_status_present': s.exists(), 'method_intent_present': intent.exists(),
           'complete_pair': False, 'method_disposition': '',
           'failed_b2_conditions': 0, 'failed_b4_conditions': 0}
    if p.exists():
        raw = json.loads(p.read_text())
        # Project only capture/admission metadata. No dynamic observations are accessed.
        for src, dst in [('return_code', 'physical_return_code'),
                         ('technical_valid', 'physical_technical_valid'),
                         ('preprocessing_complete', 'physical_preprocessing_complete')]:
            row[dst] = raw.get(src, '')
        assert raw.get('run_id') == run_id
    if s.exists():
        raw = json.loads(s.read_text())
        assert raw.get('run_id') == run_id
        row['complete_pair'] = bool(raw.get('complete_pair', False))
        row['method_disposition'] = raw.get('disposition', '')
        assert raw.get('quality_driven_retries', 0) == 0
        for call in raw.get('b2_calls', []):
            status = call.get('status', 'UNSPECIFIED')
            condition_statuses[status] += 1
            if status == 'TECHNICAL_FAILURE':
                row['failed_b2_conditions'] += 1
        row['failed_b4_conditions'] = len(raw.get('b4_technical_failures', []))
        if row['failed_b2_conditions'] or row['failed_b4_conditions']:
            technical_failure_ids.append(run_id)
    if row['prefreeze_excluded']:
        row['flow_class'] = 'PREFREEZE_EXCLUDED'
    elif row['complete_pair']:
        row['flow_class'] = 'METHOD_COMPLETE'
    elif row['method_disposition']:
        row['flow_class'] = row['method_disposition']
    elif row['method_status_present']:
        row['flow_class'] = 'METHOD_INCOMPLETE_TECHNICAL_FAILURE'
    elif row['method_intent_present']:
        row['flow_class'] = 'METHOD_IN_FLIGHT'
    elif row['physical_return_code'] not in ('', 0):
        row['flow_class'] = 'CAPTURE_FAILURE'
    elif row['physical_technical_valid'] is False:
        row['flow_class'] = 'PHYSICAL_TECHNICAL_INVALID_AWAITING_ADMISSION'
    elif row['physical_technical_valid'] is True:
        row['flow_class'] = 'PHYSICAL_VALID_AWAITING_METHOD_ADMISSION'
    elif row['physical_record_present']:
        row['flow_class'] = 'PHYSICAL_RECORD_INCOMPLETE'
    else:
        row['flow_class'] = 'NO_TERMINAL_PHYSICAL_RECORD'
    rows.append(row)
eligible = [r for r in rows if not r['prefreeze_excluded']]
count = lambda predicate: sum(bool(predicate(r)) for r in eligible)
complete = count(lambda r: r['complete_pair'])
method_incomplete = count(lambda r: r['flow_class'] == 'METHOD_INCOMPLETE_TECHNICAL_FAILURE')
summary = {
    'schema': 'preparation-metadata-cohort-snapshot/v1',
    'snapshot_started_utc': started,
    'snapshot_finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'non_atomic_live_snapshot': True,
    'study_id': study,
    'freeze_sha256': hashlib.sha256(freeze_bytes).hexdigest(),
    'independent_unit': freeze['independent_unit'],
    'counts': {
        'confirmation_allocated_including_prefreeze_exclusion': len(configs),
        'prefreeze_excluded': len(excluded), 'confirmation_candidate_cap': len(eligible),
        'operationally_scheduled_eligible': count(lambda r: r['operationally_scheduled']),
        'not_yet_operationally_scheduled': count(lambda r: not r['operationally_scheduled']),
        'terminal_physical_attempt_records': count(lambda r: r['physical_record_present']),
        'physical_valid': count(lambda r: r['physical_technical_valid'] is True),
        'physical_invalid': count(lambda r: r['physical_technical_valid'] is False),
        'capture_failures': count(lambda r: r['physical_return_code'] not in ('', 0)),
        'scheduled_without_terminal_physical_record': count(lambda r: r['operationally_scheduled'] and not r['physical_record_present']),
        'method_attempted_intent_or_status_without_no_call_disposition': count(lambda r: (r['method_intent_present'] or r['method_status_present']) and not r['method_disposition']),
        'method_complete': complete,
        'method_incomplete_technical_failure': method_incomplete,
        'method_in_flight': count(lambda r: r['flow_class'] == 'METHOD_IN_FLIGHT'),
        'remaining_complete_pairs_to_first_look': max(0, freeze['first_look_n']-complete),
        'remaining_complete_pairs_to_terminal_1200_if_continued': max(0, freeze['valid_paired_episode_n']-complete),
    },
    'mutually_exclusive_flow': dict(sorted(collections.Counter(r['flow_class'] for r in eligible).items())),
    'b2_condition_status_counts_not_independent_n': dict(condition_statuses),
    'method_failure_run_ids': technical_failure_ids,
    'capture_failure_run_ids': [r['run_id'] for r in eligible if r['physical_return_code'] not in ('',0)],
    'accounting_note': 'Physical counts include a backlog beyond the current ordered semantic prefix. Scheduled without terminal record may include a live capture and is not a final missingness exclusion.',
    'missingness_policy': freeze['technical_failure_rule'],
    'missingness_sensitivity_formula': 'For terminal complete n, primary-eligible method-missing m in the frozen acquisition prefix, and observed signed discordance d=b-c: (d-m)/(n+m) <= RD_all_eligible <= (d+m)/(n+m). No outcomes inspected here; pending episodes are not counted as terminal missing pairs.',
}
args.output.mkdir(parents=True, exist_ok=True)
(args.output / 'cohort-snapshot.json').write_text(json.dumps(summary, indent=2)+'\n')
with (args.output / 'cohort-flow.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print(json.dumps(summary['counts'], indent=2))
