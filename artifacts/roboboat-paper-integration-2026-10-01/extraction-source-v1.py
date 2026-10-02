"""Reproduce a descriptive marine transfer case; no certificate/evaluator imports.

Extract authentic post-result measurements once, then reproduce from the compact
raw-field capsule. No production answers or scores determine the numerical result.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'artifacts/roboboat-paper-integration-2026-10-01'
COMPONENTS = ('position', 'heading', 'speed', 'yaw_rate', 'hull')


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def check(item):
    path = Path(item['path'])
    if binding(path) != item:
        raise ValueError(f'Changed bound source: {path}')
    return path


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def extract(lock_path, output):
    lock = json.loads(lock_path.read_text())
    profile = json.loads(check(lock['profile']).read_text())
    declaration = json.loads(check(lock['declaration']).read_text())
    check(lock['closed_terminal']); check(lock['historical_summary'])
    if lock['eligible_ids'] != [r['id'] for r in profile['rows']
                               if r['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT']:
        raise ValueError('Fixed eligibility differs')
    records = []
    for row in lock['rows']:
        folder = Path(declaration['output_root']) / row['id']
        original = folder / 'capture-attempt.json'
        terminal = json.loads(original.read_text())
        if terminal['status'] != row['status']:
            raise ValueError('Original disposition differs')
        record = {**row, 'original_terminal': binding(original)}
        if row['id'] in lock['eligible_ids']:
            exported_path = folder / 'capture-export-terminal-trace-v4.json'
            exported = json.loads(exported_path.read_text())
            if check(exported['original_capture_terminal']) != original:
                raise ValueError('Export/capture binding differs')
            for item in exported['raw_sources']:
                check(item)
            task_item = terminal['row']['task_contract']
            task_path = Path(task_item['path'])
            if not task_path.is_absolute():
                task_path = ROOT / task_path
            if binding(task_path)['sha256'] != task_item['sha256']:
                raise ValueError('Task contract differs')
            fixture_path = folder / 'fixture-summary.json'
            fixture = json.loads(fixture_path.read_text())
            packets = [folder / exported['export_directory'] / 'method_packets' / f'L{i}.json'
                       for i in range(3)]
            certificate_path = folder / exported['export_directory'] / 'candidate_outputs/L2.json'
            record.update(task=json.loads(task_path.read_text()),
                          action_status=fixture['status'], action_name=fixture['actionName'],
                          terminal_event=fixture.get('terminalEventV2'),
                          post_result=[r for r in fixture['trajectory'] if r['phase'] == 'post_result'],
                          raw_fixture=binding(fixture_path), task_source=binding(task_path),
                          export_terminal=binding(exported_path), packets=[binding(p) for p in packets],
                          production_output=binding(certificate_path),
                          contact_evidence_available=False)
            # The docking evaluator is deliberately not projected as contact or
            # task truth; these are public delivered-odometry fields only.
        records.append(record)
    capsule = output / 'raw-field-capsule.jsonl'
    capsule.write_text(''.join(json.dumps(r, separators=(',', ':'), allow_nan=False) + '\n'
                               for r in records))
    save(output / 'capsule-provenance.json', {
        'cohort_lock': binding(lock_path), 'capsule': binding(capsule),
        'projection': 'Exact raw post_result trajectory rows and terminalEventV2; original status, task and source hashes. No evaluator labels or certificate numbers.',
        'archive_limit': 'Compact raw-field projection is included; full original fixture/log/native deployment remains local and is hash-referenced, not included in this capsule.',
        'extractor': binding(__file__)})


def measured(row, task):
    if row['frameId'] != task['frame'] or row['childFrameId'] != 'base_link':
        raise ValueError('Unsupported measurement frame')
    values = [row[k] for k in ('x', 'y', 'yaw', 'simSeconds', 'bodySurge', 'bodySway', 'bodyYawRate')]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite raw value')
    x, y, yaw = row['x'], row['y'], row['yaw']
    goal = task['goal']; berth = task['berth_center']
    radial = math.dist((x, y), (goal['x'], goal['y']))
    heading = abs((yaw - goal['yaw'] + math.pi) % (2 * math.pi) - math.pi)
    speed = math.hypot(row['bodySurge'], row['bodySway'])
    relative = yaw - berth['yaw']
    dx, dy = x - berth['x'], y - berth['y']
    longitudinal = dx * math.cos(berth['yaw']) + dy * math.sin(berth['yaw'])
    lateral = -dx * math.sin(berth['yaw']) + dy * math.cos(berth['yaw'])
    # Rectangle support-function extents, independently of production corner loop.
    half_length, half_beam = task['hull_length_m'] / 2, task['hull_beam_m'] / 2
    long_extent = half_length * abs(math.cos(relative)) + half_beam * abs(math.sin(relative))
    lat_extent = half_length * abs(math.sin(relative)) + half_beam * abs(math.cos(relative))
    hull = min(task['berth_depth_m'] / 2 - abs(longitudinal) - long_extent,
               task['berth_width_m'] / 2 - abs(lateral) - lat_extent)
    margins = {'position': task['position_tolerance_m'] - radial,
               'heading': task['heading_tolerance_rad'] - heading,
               'speed': task['speed_tolerance_mps'] - speed,
               'yaw_rate': task['yaw_rate_tolerance_radps'] - abs(row['bodyYawRate']),
               'hull': hull}
    return {'sim_seconds': row['simSeconds'], 'x_m': x, 'y_m': y, 'yaw_rad': yaw,
            'position_error_m': radial, 'wrapped_heading_error_rad': heading,
            'measured_speed_mps': speed, 'measured_yaw_rate_radps': row['bodyYawRate'],
            'signed_margins': margins}


def reconstruct(record):
    task = record['task']; rows = record['post_result']; event = record['terminal_event']
    assert task['interval_policy'] == 'first-post-result-observation-fixed-dwell'
    assert task['clock'] == 'ros-header-stamp'
    assert all(task[k] == 0 for k in ('position_uncertainty_m', 'heading_uncertainty_rad',
                                     'speed_uncertainty_mps', 'yaw_rate_uncertainty_radps'))
    times = [r['simSeconds'] for r in rows]
    if not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Missing/nonmonotone post-result samples')
    receipt = bool(event and event['goal_id'] and event['status'] == record['action_status']
                   and event['action_name'] == record['action_name'])
    if not receipt:
        raise ValueError('Closed eligible cohort must have authenticated result identity')
    if any(r['wallSeconds'] < event['receipt_wall_seconds'] for r in rows):
        raise ValueError('Post-result row precedes client receipt in fixture clock')
    start = times[0]; end = start + task['dwell_s']
    all_measurements = [measured(r, task) for r in rows]
    window = [m for m in all_measurements if start <= m['sim_seconds'] <= end]
    boundary_gaps = [b - a for a, b in zip(times, times[1:]) if a <= end]
    full = times[-1] >= end and bool(boundary_gaps) and max(boundary_gaps) <= task['max_sample_gap_s']
    witnesses = {}
    for component in COMPONENTS:
        hit = next((m for m in window if m['signed_margins'][component] < 0), None)
        if hit:
            witnesses[component] = hit
    observed_compliance = not witnesses and full
    category = ('observed-within-dwell-violation' if witnesses else
                'complete-sampled-observed-component-compliance-contact-unknown' if full else
                'incomplete-window-no-observed-violation')
    states = {k: 'false' if k in witnesses else 'true' if full else 'unknown' for k in COMPONENTS}
    states['contact'] = 'unknown'
    first = min(witnesses.values(), key=lambda m: m['sim_seconds']) if witnesses else None
    return {'id': record['id'], 'cluster_id': record['cluster_id'], 'family': record['family'],
            'action_status': record['action_status'], 'result_receipt_present': receipt,
            'goal_id': event['goal_id'], 'receipt_wall_seconds': event['receipt_wall_seconds'],
            'receipt_clock': event['receipt_clock'],
            'result_simulator_time_unavailable': True,
            'result_adjacent': measured(event['measurement'], task),
            'interval_anchor': 'first-post-result-delivered-observation',
            'interval_sim_seconds': [start, end], 'delivered_sim_range': [times[0], times[-1]],
            'post_result_sample_count': len(rows), 'in_dwell_sample_count': len(window),
            'max_gap_including_end_bracket_s': max(boundary_gaps) if boundary_gaps else None,
            'full_sampled_window': full, 'component_support': states,
            'witnesses': witnesses, 'first_violation': first,
            'sampled_observed_component_compliance': observed_compliance,
            'full_completion': 'refuted' if witnesses else 'unresolved', 'category': category,
            'missing_conditions': ['contact'] if full else [*COMPONENTS, 'contact'],
            'measurements': all_measurements}


def figure(record, result, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig = plt.figure(figsize=(11.5, 4.0), layout='constrained')
    grid = fig.add_gridspec(1, 2, width_ratios=(1.1, 1.2))
    ax = fig.add_subplot(grid[0]); ladder = fig.add_subplot(grid[1]); ladder.axis('off')
    start, end = result['interval_sim_seconds']; task = record['task']
    ms = result['measurements']
    ax.axvspan(0, end - start, color='#dceaf4', label='Declared five-second dwell')
    ax.plot([m['sim_seconds'] - start for m in ms], [m['position_error_m'] for m in ms],
            color='#175c82', linewidth=1.8, label='Delivered position error')
    ax.axhline(task['position_tolerance_m'], color='#a63732', linestyle='--', linewidth=1.2,
               label=f"Task bound ({task['position_tolerance_m']:.2f} m)")
    witness = result['witnesses']['position']; wx = witness['sim_seconds'] - start
    ax.scatter([wx], [witness['position_error_m']], color='#a63732', s=35, zorder=4)
    ax.annotate(f"First violating sample\n{witness['position_error_m']:.4f} m at +{wx:.2f} s",
                (wx, witness['position_error_m']), xytext=(.35, .89), textcoords='axes fraction',
                arrowprops={'arrowstyle': '->', 'color': '#a63732'}, fontsize=9)
    ax.axvline(0, color='#616970', linestyle=':', linewidth=1)
    ax.set(xlabel='Simulator seconds after first post-result observation', ylabel='Position error (m)',
           title='A  Observed motion and the fixed task interval')
    ax.legend(loc='lower right', fontsize=8, frameon=False); ax.spines[['top', 'right']].set_visible(False)
    ret = result['result_adjacent']
    boxes = [
        ('L0  Software status', 'Navigation reported success.',
         'Withhold: sustained physical completion.'),
        ('L1  Result-adjacent measurement',
         f"Position error {ret['position_error_m']:.4f} m; speed {ret['measured_speed_mps']:.4f} m/s.",
         'Withhold: satisfaction across the five-second dwell.'),
        ('L2  Delivered interval trajectory',
         f"Within-dwell position violation: {witness['position_error_m']:.4f} m > 0.40 m.",
         'Refute that interval requirement; withhold physical cause.')]
    ladder.set_title('B  Same recording, removal-only evidence', loc='left')
    for i, (title, claim, withheld) in enumerate(boxes):
        y = .74 - i * .30
        ladder.add_patch(FancyBboxPatch((.01, y), .98, .24, boxstyle='round,pad=0.01',
                                        facecolor=['#eef2f5', '#e4eef5', '#dbeaf0'][i],
                                        edgecolor='#bac7d0', transform=ladder.transAxes))
        ladder.text(.04, y + .18, title, weight='bold', transform=ladder.transAxes, fontsize=10)
        ladder.text(.04, y + .10, claim, transform=ladder.transAxes, fontsize=9)
        ladder.text(.04, y + .035, withheld, transform=ladder.transAxes, fontsize=9, color='#49545c')
    for extension in ('svg', 'pdf', 'png'):
        fig.savefig(output / f'temporal-evidence-transfer.{extension}', dpi=180)
    plt.close(fig)


def reproduce(output):
    provenance = json.loads((output / 'capsule-provenance.json').read_text())
    check(provenance['capsule'])
    records = [json.loads(line) for line in (output / 'raw-field-capsule.jsonl').read_text().splitlines()]
    eligible = [r for r in records if r['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT']
    results = [reconstruct(r) for r in eligible]
    # Illustration selection is declared by category and fixed schedule order,
    # never as a representative-frequency assertion or a method-score selector.
    selected = next((r, s) for r, s in zip(eligible, results)
                    if 'position' in s['witnesses'] and s['full_sampled_window'])
    summary = {'schema': 'roboboat-paper-raw-reconstruction/v1',
               'cohort_lock': provenance['cohort_lock'], 'capsule': provenance['capsule'],
               'analysis': binding(__file__), 'attempts': len(records), 'admitted': len(results),
               'technical_failures': len(records) - len(results),
               'geometry_draws': len({r['cluster_id'] for r in records}),
               'complete_admitted_geometry_pairs': sum(v == 2 for v in Counter(r['cluster_id'] for r in eligible).values()),
               'observed_result_receipts': sum(r['result_receipt_present'] for r in results),
               'action_statuses': dict(Counter(r['action_status'] for r in results)),
               'full_sampled_windows': sum(r['full_sampled_window'] for r in results),
               'mutually_exclusive_categories': dict(Counter(r['category'] for r in results)),
               'component_violation_marginals': {k: sum(k in r['witnesses'] for r in results) for k in COMPONENTS},
               'contact_unknown': len(results),
               'full_completion': dict(Counter(r['full_completion'] for r in results)),
               'illustration_id': selected[0]['id'],
               'illustration_selection': 'First eligible scheduled record with a position violation and complete sampled window; illustrative, not representative.',
               'semantic_validation': 'Independent raw numerical/temporal and task-contract conformance only; no new independent language judgments.',
               'confirmation_n': 0, 'replication_n': 0, 'scored_method_pairs': 0}
    save(output / 'episode-reconstruction.json', results)
    save(output / 'descriptive-summary.json', summary)
    lines = ['| Closed cohort flow or evidence category | Recordings |', '|---|---:|',
             f"| Scheduled attempts | {summary['attempts']} |",
             f"| Technically admitted / retained technical failures | {summary['admitted']} / {summary['technical_failures']} |",
             f"| Recorded action success and result receipt | {summary['observed_result_receipts']} |",
             f"| Complete sampled dwell coverage | {summary['full_sampled_windows']} |"]
    for category, count in summary['mutually_exclusive_categories'].items():
        lines.append(f'| {category} | {count} |')
    lines += [f"| Full completion: refuted / unresolved | {summary['full_completion'].get('refuted', 0)} / {summary['full_completion'].get('unresolved', 0)} |",
              '', 'The three evidence-category rows partition admitted recordings. Other rows are flow counts or marginals, not additional observations.',
              f"Scheduled diversity: {summary['geometry_draws']} geometry draws, two tolerance variants each; {summary['complete_admitted_geometry_pairs']} have both variants admitted. Evidence levels/replays add no diversity or independent N.",
              'Contact is unknown in every admitted record. Complete coverage means sampled time coverage under the declared maximum gap, not continuous-time proof. No population prevalence or explanation-effect estimate.']
    (output / 'descriptive-table.md').write_text('\n'.join(lines) + '\n')
    figure(*selected, output)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--extract', action='store_true')
    args = parser.parse_args()
    if args.extract:
        if (args.output / 'raw-field-capsule.jsonl').exists():
            raise FileExistsError('Preserve original extraction; reproduction needs no --extract')
        extract(args.output / 'cohort-lock.json', args.output)
    print(json.dumps(reproduce(args.output), indent=2))
