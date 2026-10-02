#!/usr/bin/env python3
"""Release descriptive development scores only after complete source/citation review.

Never runs a significance test or counts questions as independent configurations.
Frozen declarations/returns and their original scoring-pending flags stay intact.
"""
import argparse
import json
from pathlib import Path

from run_roboboat_population_responses_v1 import binding, checked
from roboboat_material_workflow_v3 import score
from roboboat_material_qualification_validation_v3 import validate
from evidence_calibration_io import canonical_sha256
from build_roboboat_terminal_batch import save


def reviewed_score(packet_path, annotation_root, review_path):
    packet = json.loads(packet_path.read_text())
    review = json.loads(review_path.read_text())
    key = packet['forms'][0]['packet_id']
    # Abstraction-level taxonomy is a supporting metric, absent from material-v3
    # primary scoring. Preserve its disagreement without silently changing it or
    # blocking an otherwise complete primary review. No other unresolved field
    # receives this exception, including any claim, unit or limitation judgment.
    secondary_only = (review['status'] == 'PASS_PRIMARY_WITH_SECONDARY_ISSUES'
                      and review['unresolved_decision_keys'] == ['highest_asserted_abstraction_level']
                      and bool(review.get('supporting_metric_issues')))
    clean = review['status'] == 'PASS' and not review['unresolved_decision_keys']
    if (review['schema'] != 'roboboat-population-citation-review/v1'
            or review['packet_id'] != key or not (clean or secondary_only)
            or review['complete_source_review'] is not True
            or review['project_agent_review_not_human_validation'] is not True
            or review['issues']):
        raise ValueError('complete clean agent-assisted citation review required')
    if checked(review['packet']).resolve() != packet_path.resolve():
        raise ValueError('review packet identity mismatch')
    inputs = {checked(item).resolve() for item in review['inputs']}
    required = {annotation_root/name for name in (
        'annotation-A.json', 'annotation-B.json', 'agreement.json', 'final.json')}
    if not {p.resolve() for p in required} <= inputs:
        raise ValueError('review must bind both passes, disagreement report and final decisions')
    for slot in ('A', 'B'):
        validate(packet, json.loads((annotation_root/f'annotation-{slot}.json').read_text()),
                 packet['response_text'])
    final = json.loads((annotation_root/'final.json').read_text())
    if final['packet_set_sha256'] != canonical_sha256(packet) or final['packet_id'] != key:
        raise ValueError('final decision packet identity mismatch')
    values = {k:v for k,v in final['final_decisions'].items()
              if k.startswith(('claim:', 'unit:', 'limitation:'))}
    return score(packet, values)


def summarize(declaration_path, root):
    declaration = json.loads(declaration_path.read_text())
    if declaration['disposition'] != 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING':
        raise ValueError('development-only declaration required')
    for item in declaration['dependencies'] + declaration['packets']:
        checked(item)
    results, secondary_issues, bindings = {}, [], [binding(declaration_path), binding(Path(__file__))]
    for item in declaration['packets']:
        packet = checked(item); key=packet.stem
        terminal_path=root/'terminals'/f'{key}.json'
        review_path=root/'citation_reviews'/f'{key}.json'
        if not terminal_path.exists() or not review_path.exists():
            raise ValueError('full declared bank must finish and receive citation review before release')
        terminal=json.loads(terminal_path.read_text())
        if terminal['status'] != 'SUPPORT_COMPLETE_CITATION_REVIEW_PENDING':
            raise ValueError('unfinished or failed support packet retained; no selective score release')
        if terminal['source_identity'] != {'packet':item, 'declaration_sha256':binding(declaration_path)['sha256']}:
            raise ValueError('support terminal identity mismatch')
        folder=root/'annotations'/key
        results[key]=reviewed_score(packet,folder,review_path)
        review=json.loads(review_path.read_text())
        if review.get('supporting_metric_issues'):
            secondary_issues.append({'support_packet_id':key,
                                     'issues':review['supporting_metric_issues'],
                                     'unresolved_decision_keys':review['unresolved_decision_keys']})
        bindings += [binding(terminal_path), binding(review_path), binding(packet)]
        bindings += [binding(p) for p in sorted(folder.glob('*.json'))]
    join_path=root/'evaluator-join.json'
    joins=json.loads(join_path.read_text())['entries']
    bindings.append(binding(join_path))
    rows=[{'response_id':j['response_id'], 'method':j['method'],
           'support_packet_id':j['support_packet_id'], 'score':results[j['support_packet_id']]}
          for j in joins]
    expected={(j['response_id'], m) for j in joins for m in ('B2','B4')}
    actual={(j['response_id'], j['method']) for j in joins}
    if actual != expected or len(actual) != len(joins):
        raise ValueError('complete unique method pairing required')
    totals={}
    for method in ('B2','B4'):
        bounds=[r['score']['proposed_primary_success_bounds'] for r in rows if r['method']==method]
        totals[method]={'answer_count':len(bounds), 'definite_successes':sum(b==[1,1] for b in bounds),
                        'definite_failures':sum(b==[0,0] for b in bounds),
                        'unresolved_answers':sum(b==[0,1] for b in bounds)}
    pairs=[]
    for identifier in sorted({r['response_id'] for r in rows}):
        pair={r['method']:r['score']['proposed_primary_success_bounds'] for r in rows if r['response_id']==identifier}
        pairs.append({'response_id':identifier, **pair,
                      'difference_bounds':[pair['B4'][0]-pair['B2'][1], pair['B4'][1]-pair['B2'][0]]})
    return {'schema':'roboboat-population-descriptive-support/v1',
            'status':'DEVELOPMENT_ONLY_SOURCE_REVIEWED_DESCRIPTIVE_RELEASE',
            'method_scope':'Inherited renderer benchmark; not full-CRANE superiority evidence.',
            'dependencies':bindings, 'rows':rows, 'method_totals':totals, 'paired_questions':pairs,
            'secondary_metric_issues_retained':secondary_issues,
            'question_count_is_independent_n':False, 'independent_n_added':0,
            'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'p_value':None,
            'effect_variance_estimation':'Requires complete valid independent configuration clusters; answer counts are not a variance sample.',
            'human_validation':False, 'frozen_source_records_revised':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--declaration',required=True,type=Path)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.output.exists(): raise FileExistsError('immutable release already exists')
    save(a.output,summarize(a.declaration.resolve(),a.root.resolve()))


if __name__=='__main__':main()
