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
import summarize_roboboat_population_support_v1 as base
import run_roboboat_full_population_responses_v2 as responses


def reviewed_score(packet_path, annotation_root, review_path):
    result=base.reviewed_score(packet_path,annotation_root,review_path)
    final=json.loads((annotation_root/'final.json').read_text())
    primary={k:v for k,v in final['final_decisions'].items() if k.startswith(('claim:','unit:','limitation:'))}
    if not primary or any(v is None for v in primary.values()):
        raise ValueError('unresolved primary support decisions prohibit release')
    return result


def describe_clusters(registry, entries, rows):
    """Equal six-question means only for two complete registered variants."""
    grouped={}
    for row in registry['rows']:
        grouped.setdefault(row['cluster_id'],[]).append(row)
    available={(r['response_id'],r['method']):r for r in rows}
    snapshot={e['id']:e for e in entries}
    if len(available)!=len(rows) or len(snapshot)!=len(entries):
        raise ValueError('duplicate question/method identity cannot increase geometry N')
    if any(r['answer_status']=='SOURCE_REVIEWED' and r['primary_bounds'] not in ([0,0],[1,1]) for r in rows):
        raise ValueError('complete source-reviewed primary decision required')
    complete,partial=[],[]
    for key, configurations in sorted(grouped.items()):
        expected=[row['id']+f'-L{level}' for row in configurations for level in range(3)]
        valid_identity=(len(configurations)==2 and {row.get('variant') for row in configurations}=={1,2})
        missing=[(identifier,method) for identifier in expected for method in ('B2','B4')
                 if identifier not in snapshot or (identifier,method) not in available
                 or available[(identifier,method)]['answer_status']!='SOURCE_REVIEWED']
        if not valid_identity or missing:
            partial.append({'cluster_id':key,'registered_row_ids':[row['id'] for row in configurations],
                            'snapshot_question_count':sum(identifier in snapshot for identifier in expected),
                            'missing_or_unreviewed_slots':missing,'independent_n_added':0,
                            'reason':'INCOMPLETE_TWO_VARIANT_THREE_LEVEL_PAIRING' if valid_identity
                                     else 'REGISTRY_DOES_NOT_DECLARE_TWO_DISTINCT_VARIANTS'})
            continue
        values={m:[available[(identifier,m)]['primary_bounds'][0] for identifier in expected] for m in ('B2','B4')}
        means={m:sum(v)/6 for m,v in values.items()}
        complete.append({'cluster_id':key,'row_ids':[row['id'] for row in configurations],
                         'question_count':6,'independent_geometry_n':1,
                         'B2_mean':means['B2'],'B4_mean':means['B4'],
                         'difference':means['B4']-means['B2'],
                         'B4_only_success_questions':sum(a==0 and b==1 for a,b in zip(values['B2'],values['B4'])),
                         'B2_only_success_questions':sum(a==1 and b==0 for a,b in zip(values['B2'],values['B4']))})
    aggregates={'complete_independent_geometry_count':len(complete)}
    if complete:
        aggregates.update({name:sum(c[name] for c in complete)/len(complete)
                           for name in ('B2_mean','B4_mean','difference')})
        aggregates['cluster_difference_sign_counts']={sign:sum((c['difference']>0 if sign=='positive' else
            c['difference']<0 if sign=='negative' else c['difference']==0) for c in complete)
            for sign in ('positive','negative','tie')}
    return complete,partial,aggregates


def summarize(declaration_path, root):
    declaration = json.loads(declaration_path.read_text())
    if declaration['output_root']!=str(root.resolve()): raise ValueError('support output identity mismatch')
    if declaration['schema']!='roboboat-full-population-reviewed-support/v3' or declaration['method_scope']!=responses.B4:
        raise ValueError('full-method support declaration required')
    if declaration['disposition'] != 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING':
        raise ValueError('development-only declaration required')
    for item in declaration['dependencies'] + declaration['packets']:
        checked(item)
    results, secondary_issues, bindings = {}, [], [binding(declaration_path), binding(Path(__file__)), binding(Path(base.__file__))]
    supporting_decisions={}
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
        final=json.loads((folder/'final.json').read_text())
        supporting_decisions[key]={'all_final_decisions':final['final_decisions'],
                                   'raw_agreement':json.loads((folder/'agreement.json').read_text())}
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
    # Snapshot denominators come from the declaration, never successful joins.
    joined={(j['response_id'],j['method']):j for j in joins}
    if len(joined)!=len(joins): raise ValueError('duplicate response-method join')
    expected={(entry['id'],m) for entry in declaration['snapshot_entries'] for m in ('B2','B4')}
    if not set(joined)<=expected: raise ValueError('orphan response-method join')
    ledger=json.loads(checked(declaration['response_accounting']).read_text())
    accounting={item['response_id']:item for item in ledger['entries']}
    required_available={(item['response_id'],m) for item in ledger['entries'] for m in ('B2','B4')
                        if item['methods'][m]=='INCLUDED_VALID_ANSWER'}
    if set(joined)!=required_available: raise ValueError('all source-bound answers required for release')
    rows=[]
    for entry in declaration['snapshot_entries']:
        for method in ('B2','B4'):
            join=joined.get((entry['id'],method))
            row={'response_id':entry['id'],'row_id':entry['row_id'],'cluster_id':entry['cluster_id'],
                 'level':entry['level'],'method':method}
            if join:
                key=join['support_packet_id']; result=results[key]
                row.update(answer_status='SOURCE_REVIEWED',support_packet_id=key,score=result,
                           primary_bounds=result['proposed_primary_success_bounds'],
                           whole_answer_and_supporting_labels=supporting_decisions[key],
                           answer_provenance=join['answer_provenance'])
            else:
                row.update(answer_status='MISSING_OR_FAILED_RESPONSE_RETAINED',score=None,
                           primary_bounds=[0,1],accounting=accounting[entry['id']])
            rows.append(row)
    totals={}
    for method in ('B2','B4'):
        subset=[r for r in rows if r['method']==method]
        totals[method]={'snapshot_answer_slots':len(subset),
            'reviewed_answers':sum(r['answer_status']=='SOURCE_REVIEWED' for r in subset),
            'missing_or_failed_answers':sum(r['answer_status']!='SOURCE_REVIEWED' for r in subset),
            'definite_successes':sum(r['primary_bounds']==[1,1] for r in subset),
            'definite_failures':sum(r['primary_bounds']==[0,0] for r in subset),
            'success_total_adverse':sum(r['primary_bounds'][0] for r in subset),
            'success_total_favorable':sum(r['primary_bounds'][1] for r in subset)}
    pairs=[]
    for entry in declaration['snapshot_entries']:
        pair={r['method']:r['primary_bounds'] for r in rows if r['response_id']==entry['id']}
        pairs.append({'response_id':entry['id'],**pair,
                      'difference_bounds':[pair['B4'][0]-pair['B2'][1],pair['B4'][1]-pair['B2'][0]]})
    registry=json.loads(checked(declaration['registry']).read_text())
    complete,partial,cluster_summary=describe_clusters(registry,declaration['snapshot_entries'],rows)
    return {'schema':'roboboat-full-population-descriptive-support/v3',
            'status':'DEVELOPMENT_ONLY_SOURCE_REVIEWED_DESCRIPTIVE_RELEASE',
            'method_scope':'Full CRANE v2 deterministic zero-model versus Astra/high tool-enabled method-reuse sensitivity; development only, no superiority inference.',
            'dependencies':bindings, 'rows':rows, 'method_totals':totals, 'paired_questions':pairs,
            'secondary_metric_issues_retained':secondary_issues,
            'complete_geometry_clusters':complete,'partial_geometry_clusters':partial,
            'complete_geometry_descriptive_summary':cluster_summary,
            'missing_response_bounds_are_sensitivity_not_scores':True,
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
