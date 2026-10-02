"""Completed physical-development diagnostics, not explanation effect estimates."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from roboboat_owned_player_bundle_v1 import binding
from build_roboboat_terminal_batch import save


def summarize(profile_path, declaration_path, terminal_path):
    profile_path, declaration_path, terminal_path = map(lambda p: Path(p).resolve(),
                                                       (profile_path, declaration_path, terminal_path))
    p = json.loads(profile_path.read_text()); d = json.loads(declaration_path.read_text())
    t = json.loads(terminal_path.read_text())
    if (t['status'] != 'TRACE_QUALIFIED_DEVELOPMENT_BATCH_FINISHED' or
        t['declaration_sha256'] != binding(declaration_path)['sha256'] or
        t['physical_attempts'] != len(d['rows'])):
        raise ValueError('complete exact declared batch required')
    rows = p['rows']; identifiers = [r['id'] for r in rows]
    if len(set(identifiers)) != len(d['rows']) or set(identifiers) != set(d['rows']):
        raise ValueError('all once-only declared rows required')
    if any(r['status'] not in ('VALID_TRACE_QUALIFIED_DEVELOPMENT', 'TECHNICAL_FAILURE') for r in rows):
        raise ValueError('unfinished development cannot be a completed-batch report')
    terminal_ids = [r['row']['id'] for r in t['results']]
    if len(terminal_ids) != len(set(terminal_ids)) or set(terminal_ids) != set(identifiers):
        raise ValueError('batch terminal denominator differs')
    for dependency in p['dependencies']:
        if binding(dependency['path']) != dependency:
            raise ValueError('bound physical development source changed')
    groups = defaultdict(list); components = defaultdict(Counter); witnesses = Counter(); families = defaultdict(Counter)
    navigation = Counter(); failures = []
    for row in rows:
        groups[row['cluster_id']].append(row)
        families[row['family']][row['status']] += 1
        if row['status'] == 'TECHNICAL_FAILURE':
            failures.append({k: row[k] for k in ('id', 'cluster_id', 'family', 'error')})
            continue
        navigation[row['action_status']] += 1
        for key, state in row['component_support'].items():
            components[key][state] += 1
        witnesses.update(row['witness_components'])
    if any(len(rs) != 2 for rs in groups.values()):
        raise ValueError('this completed-batch report expects exactly two scheduled tolerances per geometry')
    total = len(groups); complete = sum(all(r['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT' for r in rs) for rs in groups.values())
    valid = sum(r['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT' for r in rows)
    if complete != p['complete_geometry_pairs'] or valid != t['valid_recordings']:
        raise ValueError('published/profile counts differ')
    # Independent geometry indicators allow heterogeneous means. No homogeneous
    # binomial assumption across families or independence of tolerance variants.
    alpha = .05; half_width = math.sqrt(math.log(2/alpha)/(2*total))
    rate = complete/total; lower = max(0., rate-half_width); upper = min(1., rate+half_width)
    return {'schema': 'roboboat-completed-development-summary/v22',
        'sources': [binding(p) for p in (profile_path, declaration_path, terminal_path, Path(__file__))],
        'platform_version': p['platform_version'], 'physical_attempts': len(rows), 'valid_recordings': valid,
        'scheduled_geometry_draws': total, 'complete_geometry_pairs': complete,
        'incomplete_geometries': sorted(k for k, rs in groups.items() if any(r['status'] == 'TECHNICAL_FAILURE' for r in rs)),
        'technical_failures_retained': failures, 'family_recording_dispositions': {k: dict(v) for k, v in families.items()},
        'navigation_statuses_among_valid': dict(navigation), 'L2_task_states_among_valid': p['L2_sampled_task_recording_counts'],
        'L2_component_support_among_valid': {k: dict(v) for k, v in components.items()},
        'L2_failure_witness_component_counts': dict(witnesses),
        'geometry_completion_planning': {'point_rate': rate, 'two_sided_95pct_Hoeffding_mean_interval': [lower, upper],
            'assumptions': 'Independent generated geometry draws, binary complete-pair indicators; heterogeneous family means allowed. Interval concerns mean completion probability for this fixed allocation/version, not a new population or realized future count.',
            'illustrative_attempts_for_expected_complete_geometry_count': [{'desired_complete_count': n,
                'using_observed_rate': math.ceil(n/rate), 'using_Hoeffding_lower_mean': math.ceil(n/lower) if lower else None}
                for n in (100, 200, 400, 800)],
            'not_confirmation_N_selection': True, 'not_guaranteed_realized_valid_N': True,
            'not_transferred_to_unqualified_new_start_or_shutdown_platform': True},
        'scientific_limits': ['No B4-vs-B2 paired endpoint scores or observed effect/discordance/reliability estimates.',
            'All admitted navigation outcomes succeeded; two timeout episodes are retained as technical failures. Fault-inclusive clean completion is still being operationally tested.',
            'Valid L2 task states include false/unknown but no true. New start/distance scenarios must be assessed empirically without selecting based on method wins.',
            'Tolerance variants, evidence levels and engineering calls add no independent N.'],
        'confirmation_frozen': False, 'confirmation_n': 0, 'replication_n': 0, 'land_n_added': 0, 'scored_method_pairs': 0}


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('--profile', required=True)
    a.add_argument('--declaration', required=True); a.add_argument('--terminal', required=True)
    a.add_argument('--output', required=True); args = a.parse_args()
    if Path(args.output).exists(): raise FileExistsError('fresh immutable summary required')
    result = summarize(args.profile, args.declaration, args.terminal)
    save(Path(args.output), result)
    print(json.dumps({k: result[k] for k in ('physical_attempts', 'valid_recordings', 'scheduled_geometry_draws', 'complete_geometry_pairs', 'navigation_statuses_among_valid', 'L2_task_states_among_valid', 'L2_failure_witness_component_counts')}))
