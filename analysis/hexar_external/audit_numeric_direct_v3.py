#!/usr/bin/env python3
"""Packet-only literal/clock predicates; never overwrite qualified semantic gold."""
import json
import re
from pathlib import Path

from audit_release import sha, write
from verify_v3 import V3, study

# Parent-selected event boundaries, using only opaque answers and their packets.
# No method keys, annotation returns or performance informed these bindings.
TIMES = {
    '61fc429eb6533bbd-a006': ('l0006', 'l0010', 'zone_goal_to_reported_success'),
    '10b5442e001badb0-a002': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    '3e489abb146fc4b1-a003': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    'e15c51eae54b4b47-a001': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    'cfcc7c500b7626b0-a004': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    '7e01b70af8e28b6d-a002': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    'a87699c70df09cf7-a004': ('l0001', 'l0006', 'zone_success_to_next_zone_goal'),
    'a87699c70df09cf7-a005': ('l0001', 'l0006', 'zone_success_to_next_zone_goal'),
    '70f7ba15ecb5efa9-a001': ('window_start', 'window_end', 'requested_task_window'),
    '1330ac6b80d84a8b-a005': ('l0010', 'l0011', 'pose_success_to_next_zone_goal'),
    'bbf3cded2e17333d-a003': ('l0000', 'l0002', 'zone_goal_to_reported_success'),
    'bbf3cded2e17333d-a004': ('l0006', 'l0008', 'zone_goal_to_reported_success'),
}


def nanoseconds(value):
    second, fraction = value.split('.')
    return int(second) * 1_000_000_000 + int(fraction)


def main():
    study()
    ann = V3 / 'reserved/annotation'
    load = lambda path: json.loads(path.read_text())
    numeric = load(ann / 'numerical_predicate_audit.json')['rows']
    bank = {r['response_id']: r['robot_visible_evidence'] for r in load(ann / 'blind_bank.json')['items']}
    rows = []
    assert len(numeric) == 25
    assert set(TIMES) == {r['item_id'] for r in numeric if r['claimed_seconds']}
    for atom in numeric:
        packet = bank[atom['response_id']]
        logs = packet['evidence']['navigation_logs']
        indexed = {log['evidence_id']: log for log in logs}
        row = {'item_id': atom['item_id'], 'statement': atom['statement']}
        if atom['item_id'] in TIMES:
            start, end, kind = TIMES[atom['item_id']]
            if kind == 'requested_task_window':
                first, last = packet['task_window']
                identity = 'requested upstream task-window bounds; not independently verified physical completion time'
            else:
                left, right = indexed[start], indexed[end]
                first, last = left['callback_time'], right['callback_time']
                if kind == 'zone_goal_to_reported_success':
                    assert left['logger'] == right['logger'] == 'skill_navigate_to_zone'
                    assert 'received a new goal' in left['message']
                    assert right['message'] == 'Skill completed successfully'
                else:
                    assert left['logger'] == ('skill_navigate_to_pose' if kind.startswith('pose') else 'skill_navigate_to_zone')
                    assert left['message'] == 'Skill completed successfully'
                    assert right['logger'] == 'skill_navigate_to_zone' and 'received a new goal' in right['message']
                identity = 'logger/event types verified; destination concordance is ordinal task/log matching, not an explicit goal UUID/target binding'
            elapsed = (nanoseconds(last) - nanoseconds(first)) / 1e9
            assert elapsed >= 0 and len(atom['claimed_seconds']) == 1
            claimed = atom['claimed_seconds'][0]
            zone_tasks = [s for s in packet['evidence']['recorded_task'][0]['value']['skill_sequence'] if s['skill'] == 'navigate_to_zone']
            zone_goals = [l for l in logs if l['logger'] == 'skill_navigate_to_zone' and 'received a new goal' in l['message']]
            row.update(predicate=kind, evidence_ids=[start, end], recovered_receipt_seconds=elapsed,
                       legacy_float_seconds=float(last) - float(first), claimed_seconds=claimed,
                       absolute_error_seconds=abs(claimed - elapsed),
                       within_existing_one_second_candidate_tolerance=abs(claimed - elapsed) <= 1,
                       identity_scope=identity,
                       zone_task_destinations=[s['params'].get('location') for s in zone_tasks],
                       task_goal_count_concordance=len(zone_tasks) == len(zone_goals),
                       physical_motion_duration_or_delay_cause_verified=False)
        elif atom['numbers'] == ['6']:
            matches = [l for l in logs if l['logger'] == 'skill_navigate_to_zone'
                       and re.fullmatch(r'NavigateToZone action server returned code: 6', l['message'])]
            row.update(predicate='explicit_navigation_server_return_code', claimed_code=6,
                       matching_evidence_ids=[l['evidence_id'] for l in matches],
                       literal_predicate_verified=bool(matches), code_mechanism_cause_verified=False)
        else:
            assert atom['numbers'] == ['3.07', '-0.34']
            matches = [l for l in logs if l['logger'] == 'planner_server'
                       and 'failed to generate a valid path to (3.07, -0.34)' in l['message']]
            assert 'repeatedly' in atom['statement']
            row.update(predicate='repeated_explicit_planner_goal_coordinate_report',
                       matching_evidence_ids=[l['evidence_id'] for l in matches],
                       literal_predicate_verified=len(matches) >= 2,
                       measured_geometry_or_obstacle_verified=False)
            if 'aborted' in atom['statement']:
                aborts = [l for l in logs if l['logger'] == 'skill_navigate_to_zone'
                          and l['message'] == 'NavigateToZone action server returned code: 6']
                task_aborted = any(s['skill'] == 'navigate_to_zone' and s['status'] == 'failed'
                                   and 'aborted' in s['error_msg'] for s in packet['evidence']['recorded_task'][0]['value']['skill_sequence'])
                row['planner_reports_precede_abort_code'] = bool(matches and aborts and task_aborted) and all(
                    nanoseconds(l['callback_time']) <= nanoseconds(aborts[0]['callback_time']) for l in matches)
                row['abort_identity_scope'] = 'explicit current-task aborted error plus navigation-server return code; not a physical-cause assertion'
        rows.append(row)
    write(ann / 'direct_numeric_predicate_audit.json', {
        'schema': 'hexar-independent-literal-and-clock-predicates/v3', 'rows': rows,
        'bank_sha256': sha(ann / 'blind_bank.json'),
        'inventory_sha256': sha(ann / 'atomic_inventory.json'),
        'auditor_sha256': sha(Path(__file__)), 'method_keys_accessed': False,
        'qualified_support_labels_accessed': False, 'parent_binding_qualified': False,
        'semantic_gold_or_primary_scores_overridden': False, 'alpha_consumed': 0,
        'scope': 'Direct literal/event-type/clock checks supplement the frozen numerical candidate audit. One-second tolerance is inherited, not a new grading rule. No identity is inferred from arbitrary number membership; explicit UUID/destination binding and physical-motion timing remain unverified.',
    })
    print('DIRECT_PACKET_NUMERIC_PREDICATES', len(rows), 'SEMANTIC_GOLD_UNCHANGED')


if __name__ == '__main__':
    main()
