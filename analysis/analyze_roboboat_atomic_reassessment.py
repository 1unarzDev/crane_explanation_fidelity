#!/usr/bin/env python3
"""Descriptive atomic reassessment, preserving episodes, pairing and judge passes.

This strict all-assertion development score is not a promoted material-assertion
confirmatory endpoint. It never treats claim/ladder/annotation counts as N.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from adjudicate_evidence_calibration_annotations import compare,finalize,_values
from evidence_calibration_io import canonical_sha256
from build_roboboat_terminal_batch import save

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'
SUPPORTED='SUPPORTED_BY_VISIBLE_EVIDENCE'


def score_decisions(decisions):
    claims={k:v for k,v in decisions.items() if k.startswith('claim:')}
    units={k:v for k,v in decisions.items() if k.startswith('unit:')}
    limits={k:v for k,v in decisions.items() if k.startswith('limitation:')}
    if not claims or len(units)!=4 or len(limits)!=1:
        raise ValueError('incomplete declared score inventory')
    if any(type(v) is not bool for v in [*units.values(),*limits.values()]):
        raise ValueError('unit/limitation judgment must be explicit boolean')
    all_supported=all(v==SUPPORTED for v in claims.values())
    return {'answer_success':all_supported and all(units.values()) and all(limits.values()),
            'all_claims_supported':all_supported,'claims_n':len(claims),
            'claim_labels':dict(Counter(claims.values())),
            'required_units_covered':sum(units.values()),'required_units_n':4,
            'causal_limitation_preserved':all(limits.values())}


def aggregate(rows,cluster_map):
    seen=set();batches=[]
    for r in rows:
        key=(r['batch'],r['method'],r['level'])
        if key in seen:raise ValueError('duplicate physical answer identity')
        seen.add(key)
        if r['method'] not in ('B2','B4') or r['level'] not in ('L0','L1','L2'):
            raise ValueError('unregistered method or evidence level')
        if r['batch']!='historical-replay' and r['batch'] not in cluster_map:
            raise ValueError('unregistered physical configuration')
    for batch in sorted({r['batch'] for r in rows}):
        selected=[r for r in rows if r['batch']==batch]
        if {(r['method'],r['level']) for r in selected}!={(m,l) for m in ('B2','B4') for l in ('L0','L1','L2')}:
            raise ValueError('incomplete within-episode comparison')
        scores={view:{m:sum(r[view]['answer_success'] for r in selected if r['method']==m)/3
                      for m in ('B2','B4')} for view in ('final','pass_A','pass_B')}
        batches.append({'batch':batch,'historical':batch=='historical-replay',
            'cluster':cluster_map.get(batch),'scores':scores})
    clusters=[]
    for cluster in sorted(set(cluster_map.values())):
        selected=[b for b in batches if b['cluster']==cluster]
        if len(selected)>2:raise ValueError('more than declared paired variants')
        complete=len(selected)==2
        scores={view:{m:sum(b['scores'][view][m] for b in selected)/2 for m in ('B2','B4')}
                for view in ('final','pass_A','pass_B')} if complete else None
        differences={view:scores[view]['B4']-scores[view]['B2'] for view in scores} if scores else None
        clusters.append({'cluster':cluster,'recordings':[b['batch'] for b in selected],
            'complete_pair':complete,'scores':scores,'differences_B4_minus_B2':differences})
    complete=[c for c in clusters if c['complete_pair']]
    means={view:sum(c['differences_B4_minus_B2'][view] for c in complete)/len(complete)
           if complete else None for view in ('final','pass_A','pass_B')}
    return {'batches':batches,'clusters':clusters,'complete_paired_clusters':len(complete),
        'fresh_recordings':sum(not b['historical'] for b in batches),
        'observed_mean_cluster_difference':means,
        'judge_pass_sensitivity_range':[min(means.values()),max(means.values())] if complete else None,
        'sensitivity_is_confidence_interval':False,'p_value':None,'confidence_interval':None}


def read_row(root,join,packet_binding):
    packet_path=ROOT/packet_binding['path']
    raw=packet_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=packet_binding['sha256']:
        raise ValueError('frozen packet changed')
    packet=json.loads(raw);key=join['support_packet_id'];target=root/'annotations'/key
    summary=json.loads((target/'development-summary.json').read_text())
    if summary['packet_sha256']!=packet_binding['sha256'] or not summary['finalized']:
        raise ValueError('support terminal packet binding mismatch')
    a=json.loads((target/'annotation-A.json').read_text())
    b=json.loads((target/'annotation-B.json').read_text())
    report=compare(packet,a,b)
    stored=json.loads((target/'agreement.json').read_text())
    if stored!=report:raise ValueError('independent returns and agreement report differ')
    if report['disagreement_count']:
        adjudication=json.loads((target/'adjudication.json').read_text())
    else:
        adjudication={'schema':'crane-blinded-atomic-annotation-adjudication/v1',
            'agreement_report_sha256':canonical_sha256(report),'adjudicator_id':'coordinator-no-disagreements',
            'decisions':[],'attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'}
    final=finalize(report,adjudication)
    if final!=json.loads((target/'final.json').read_text()):
        raise ValueError('final support decisions do not reproduce')
    disagreements=Counter('claim' if d['decision_key'].startswith('claim:') else
        'unit' if d['decision_key'].startswith('unit:') else
        'limitation' if d['decision_key'].startswith('limitation:') else
        d['decision_key'] for d in report['disagreements'])
    return {**join,'final':score_decisions(final['final_decisions']),
        'pass_A':score_decisions(_values(a)),'pass_B':score_decisions(_values(b)),
        'disagreement_counts':dict(disagreements),
        'disagreements':report['disagreements'],
        'final_sha256':hashlib.sha256((target/'final.json').read_bytes()).hexdigest()}


def analyze(root,declaration_path,plan_path=DOC/'marine_atomic_analysis_plan_v1.json'):
    plan=json.loads(plan_path.read_text())
    if plan['disposition']!='INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY':
        raise ValueError('development analysis plan gate closed')
    if hashlib.sha256(declaration_path.read_bytes()).hexdigest()!=plan['support_declaration_sha256']:
        raise ValueError('analysis/support declaration binding mismatch')
    for item in plan['dependencies']:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('analysis plan dependency changed: '+item['path'])
    declaration=json.loads(declaration_path.read_text())
    if declaration['disposition']!='INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY':
        raise ValueError('development gate closed')
    for item in declaration['dependencies']:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('reassessment dependency changed: '+item['path'])
    joins=json.loads((root/'evaluator-join.json').read_text())['entries']
    # Do not release a partial score or silently drop unresolved/failed labels.
    missing=[j['support_packet_id'] for j in joins if not
        (root/'annotations'/j['support_packet_id']/'development-summary.json').exists()]
    if missing:raise ValueError(f'ordered complete-bank release gate closed: {len(missing)} missing support terminals')
    bindings={Path(p['path']).stem:p for p in declaration['packets']}
    if len(joins)!=36 or len(bindings)!=36 or set(bindings)!={j['support_packet_id'] for j in joins}:
        raise ValueError('frozen original answer population mismatch')
    rows=[read_row(root,j,bindings[j['support_packet_id']]) for j in joins]
    registry=json.loads((DOC/'pilot_registry_v1.json').read_text())
    continuation=json.loads((DOC/'pilot_continuation_v3.json').read_text())
    cluster_map={r['id']:r['cluster_id'] for r in registry['rows']}
    cluster_map.update({r['id']:r['cluster_id'] for r in continuation['rows']})
    result=aggregate(rows,cluster_map)
    methods={}
    for m in ('B2','B4'):
        selected=[r for r in rows if r['method']==m and r['batch']!='historical-replay']
        methods[m]={'fresh_answers':len(selected),'successes':sum(r['final']['answer_success'] for r in selected),
            'claims_n':sum(r['final']['claims_n'] for r in selected),
            'required_units_covered':sum(r['final']['required_units_covered'] for r in selected),
            'required_units_n':sum(r['final']['required_units_n'] for r in selected),
            'causal_limitation_failures':sum(not r['final']['causal_limitation_preserved'] for r in selected)}
    result.update(schema='roboboat-atomic-development-results/v1',rows=rows,methods=methods,
        missing_annotations=[],agent_assessed=True,human_validation=False,confirmation_n=0,replication_n=0,
        alpha_consumed=0,original_scores_replaced=False,
        endpoint='Strict all-assertion development sensitivity; confirmatory materiality mapping unqualified.',
        uncertainty='Two passes from one model family can share errors; observed agreement is not accuracy or independent replication.',
        abstraction_tags_scored=False,causal_limitation_failure_is_cause_attribution_count=False,
        declaration_sha256=hashlib.sha256(declaration_path.read_bytes()).hexdigest(),
        analysis_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'artifacts/roboboat-terminal-atomic-reassessment-v1')
    parser.add_argument('--declaration',type=Path,default=DOC/'marine_atomic_reassessment_declaration_v1.json')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('refuse to overwrite released development analysis')
    result=analyze(args.root,args.declaration);save(args.output,result)
    print(json.dumps({k:result[k] for k in ('fresh_recordings','complete_paired_clusters','observed_mean_cluster_difference','methods')},indent=2))
