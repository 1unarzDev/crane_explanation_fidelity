#!/usr/bin/env python3
"""Account for the stopped development queue without dropping its failed judgment.

The original complete-bank score remains unavailable. Bounds below are conditional
missing-judgment sensitivity, never confidence intervals or physical outcome labels.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from analyze_roboboat_atomic_reassessment import ROOT,DOC,read_row,aggregate
from evidence_calibration_io import canonical_sha256
from build_roboboat_terminal_batch import save


def bound_aggregate(rows,mapping):
    bounds={}
    for side in ('lower','upper'):
        completed=copy.deepcopy(rows)
        for row in completed:
            if row['annotation_status']=='RETAINED_TIMEOUT_SUPPORT_UNAVAILABLE':
                value=(row['method']=='B2') if side=='lower' else (row['method']=='B4')
                row.update({view:{'answer_success':value} for view in ('final','pass_A','pass_B')})
        bounds[side]=aggregate(completed,mapping)
    lo=bounds['lower']['observed_mean_cluster_difference'];hi=bounds['upper']['observed_mean_cluster_difference']
    return {'complete_paired_clusters':bounds['lower']['complete_paired_clusters'],
        'fresh_recordings':bounds['lower']['fresh_recordings'],
        'mean_cluster_difference_bounds':{view:[lo[view],hi[view]] for view in lo},
        'final_mean_identified_given_available_judgments':lo['final']==hi['final'],
        'identified_final_mean':lo['final'] if lo['final']==hi['final'] else None,
        'bound_scenarios':bounds,'bounds_are_confidence_intervals':False,'p_value':None,'confidence_interval':None}


def analyze(root,disposition_path):
    disposition=json.loads(disposition_path.read_text())
    if disposition['status']!='STOPPED_QUEUE_RETAINED_TIMEOUT_NO_RETRY':
        raise ValueError('failure disposition gate closed')
    for binding in disposition['dependencies']:
        if hashlib.sha256((ROOT/binding['path']).read_bytes()).hexdigest()!=binding['sha256']:
            raise ValueError('failure disposition binding changed')
    declaration_path=DOC/'marine_atomic_reassessment_declaration_v1.json'
    declaration=json.loads(declaration_path.read_text())
    for binding in declaration['dependencies']+declaration['packets']:
        if hashlib.sha256((ROOT/binding['path']).read_bytes()).hexdigest()!=binding['sha256']:
            raise ValueError('original reassessment binding changed')
    joins=json.loads((root/'evaluator-join.json').read_text())['entries']
    packets={Path(p['path']).stem:p for p in declaration['packets']}
    failures={f['packet_id']:f for f in disposition['failed_judgments']}
    if len(joins)!=36 or set(packets)!={j['support_packet_id'] for j in joins}:
        raise ValueError('complete original population required')
    rows=[]
    for join in joins:
        key=join['support_packet_id']
        if (root/'annotations'/key/'development-summary.json').exists():
            if key in failures:raise ValueError('failure disposition contradicts terminal')
            row=read_row(root,join,packets[key]);row['annotation_status']='FINALIZED_AGENT_ASSESSED'
        else:
            if key not in failures:raise ValueError('unaccounted missing judgment')
            failure=failures[key];call_path=ROOT/failure['call']['path']
            if hashlib.sha256(call_path.read_bytes()).hexdigest()!=failure['call']['sha256']:
                raise ValueError('retained failure bytes changed')
            record=json.loads(call_path.read_text());packet=json.loads((ROOT/packets[key]['path']).read_text())
            request=record['request_identity']
            if (record['status']!='TRANSPORT_OR_TOOL_POLICY_FAILURE' or not record['timed_out']
                or request['logical_role']!='atomic-agent-A'
                or request['payload']['packet_set_sha256']!=canonical_sha256(packet)
                or request['model']!=declaration['judge']['model']):
                raise ValueError('retained timeout does not bind declared packet/judge')
            row={**join,'annotation_status':'RETAINED_TIMEOUT_SUPPORT_UNAVAILABLE',
                'final':None,'pass_A':None,'pass_B':None,'score_bounds':[0,1],
                'physical_failure_inferred':False,'call_sha256':failure['call']['sha256']}
        rows.append(row)
    initial=json.loads((DOC/'pilot_registry_v1.json').read_text())
    continuation=json.loads((DOC/'pilot_continuation_v3.json').read_text())
    mapping={r['id']:r['cluster_id'] for r in initial['rows']}
    mapping.update({r['id']:r['cluster_id'] for r in continuation['rows']})
    result=bound_aggregate(rows,mapping)
    methods={}
    for method in ('B2','B4'):
        selected=[r for r in rows if r['method']==method and r['batch']!='historical-replay']
        known=[r for r in selected if r['final'] is not None];missing=len(selected)-len(known)
        successes=sum(r['final']['answer_success'] for r in known)
        methods[method]={'fresh_answers_fixed':len(selected),'finalized_answers':len(known),
            'unavailable_judgments':missing,'success_count_bounds':[successes,successes+missing],
            'mean_success_bounds':[successes/len(selected),(successes+missing)/len(selected)],
            'required_units_covered_assessed_only':sum(r['final']['required_units_covered'] for r in known),
            'required_units_n_assessed_only':sum(r['final']['required_units_n'] for r in known),
            'causal_limitation_failures_assessed_only':sum(not r['final']['causal_limitation_preserved'] for r in known)}
    finalized=[r for r in rows if r['final'] is not None]
    result.update(schema='roboboat-atomic-missing-judgment-development-sensitivity/v1',
        rows=rows,methods=methods,accounted_original_answers=len(rows),finalized_answers=len(finalized),
        unavailable_judgments=len(failures),missing_annotations=list(failures),
        original_complete_bank_score_released=False,original_scores_replaced=False,
        interpretation='Conditional missing-judgment sensitivity on a stopped inspected development queue; no inferential activation or superiority claim.',
        endpoint='Strict all-assertion sensitivity, not a promoted material-assertion primary endpoint.',
        uncertainty='Same-family support passes may share errors. Bounds account only for retained missing judgments, not semantic population error.',
        support_disagreements=sum(r['disagreement_counts'].get('claim',0) for r in finalized),
        unit_disagreements=sum(r['disagreement_counts'].get('unit',0) for r in finalized),
        limitation_disagreements=sum(r['disagreement_counts'].get('limitation',0) for r in finalized),
        unqualified_abstraction_disagreements=sum(r['disagreement_counts'].get('highest_asserted_abstraction_level',0) for r in finalized),
        alpha_consumed=0,confirmation_n=0,replication_n=0,agent_assessed=True,human_validation=False,
        disposition_sha256=hashlib.sha256(disposition_path.read_bytes()).hexdigest())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'artifacts/roboboat-terminal-atomic-reassessment-v1')
    parser.add_argument('--disposition',type=Path,default=DOC/'marine_atomic_timeout_disposition_v1.json')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('released failure sensitivity is immutable')
    result=analyze(args.root,args.disposition);save(args.output,result)
    print(json.dumps({k:result[k] for k in ('finalized_answers','unavailable_judgments','complete_paired_clusters','mean_cluster_difference_bounds','methods','support_disagreements','unit_disagreements','limitation_disagreements')},indent=2))
