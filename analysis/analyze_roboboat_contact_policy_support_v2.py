#!/usr/bin/env python3
"""Reproduce complete-bank contact-v2 development labels; no primary inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
from adjudicate_evidence_calibration_annotations import compare,finalize,_values,_item_id
from evidence_calibration_io import canonical_sha256
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from run_roboboat_contact_policy_support_v2 import OUT,DECLARATION
from roboboat_material_endpoint_v1 import UNITS,PARTIAL_UNIT,LIMITS,SUPPORTED,LABELS

PLAN=DOC/'contact_policy_support_analysis_plan_v2.json'


def score(decisions,partial_answerable):
    claims={k:v for k,v in decisions.items() if k.startswith('claim:')}
    units={k:v for k,v in decisions.items() if k.startswith('unit:')}
    limits={k:v for k,v in decisions.items() if k.startswith('limitation:')}
    expected={'unit:'+_item_id('u-',u) for u in UNITS}
    partial_key='unit:'+_item_id('u-',PARTIAL_UNIT)
    if partial_answerable:expected.add(partial_key)
    if (not claims or set(units)!=expected or set(limits)!={'limitation:'+_item_id('l-',l) for l in LIMITS}):
        raise ValueError('declared complete score inventory required')
    if any(v not in LABELS for v in claims.values()) or any(type(v) is not bool for v in [*units.values(),*limits.values()]):
        raise ValueError('final labels required; unavailable decisions are not omitted')
    common_keys={'unit:'+_item_id('u-',u) for u in UNITS}
    all_supported=all(v==SUPPORTED for v in claims.values())
    common_success=all_supported and all(units[k] for k in common_keys) and all(limits.values())
    partial=units[partial_key] if partial_answerable else None
    return {'strict_common_success':common_success,'strict_extended_success':common_success and partial is not False,
            'all_reviewed_claims_supported':all_supported,'claim_label_counts':dict(Counter(claims.values())),
            'claims_n':len(claims),'common_units_communicated':sum(units[k] for k in common_keys),'common_units_n':4,
            'partial_compliance_communicated':partial,'whole_answer_limits_preserved':limits,
            'material_primary_score_authorized':False}


def summarize(rows):
    if len(rows)!=12 or len({(r['response_id'],r['method']) for r in rows})!=12:raise ValueError('complete fixed twelve-answer bank required')
    physical={r['response_id'].rsplit('-',1)[0] for r in rows}
    if len(physical)!=2:raise ValueError('two fixed inspected physical variants required')
    expected={(p+'-'+level,m) for p in physical for level in ('L0','L1','L2') for m in ('B2','B4')}
    if {(r['response_id'],r['method']) for r in rows}!=expected:raise ValueError('evidence/method population differs')
    methods={}
    for method in ('B2','B4'):
        selected=[r for r in rows if r['method']==method]
        methods[method]={view:{'answers':6,'strict_common_successes':sum(r[view]['strict_common_success'] for r in selected),
            'strict_extended_successes':sum(r[view]['strict_extended_success'] for r in selected),
            'common_units_communicated':sum(r[view]['common_units_communicated'] for r in selected),'common_units_n':24,
            'partial_answerable_questions':sum(r['partial_information_answerable'] for r in selected),
            'partial_compliance_communicated':sum(r[view]['partial_compliance_communicated'] is True for r in selected)} for view in ('pass_A','pass_B','final')}
    return {'methods':methods,'rows':rows,'physical_variants_reissued':2,'new_independent_configuration_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'p_value':None,'confidence_interval':None,'paired_cluster_effect_estimated':False,'analysis_scope':'Complete inspected contract-repair response replay over two existing approach clusters, no pooling with original/fresh confirmation population.','endpoint_scope':'Strict common/positive-information development sensitivities; material relevance primary remains unqualified.','agent_assessed':True,'human_validation':False,'judge_uncertainty':'Two same-family passes and adjudication may share errors; agreement is not human validity or accuracy.'}


def analyze():
    plan=json.loads(PLAN.read_text())
    if plan['disposition']!='INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY':raise ValueError('development analysis gate closed')
    for b in plan['dependencies']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('analysis lock changed')
    declaration=json.loads(DECLARATION.read_text())
    for b in declaration['dependencies']+declaration['packets']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('support freeze changed')
    joins=json.loads((OUT/'evaluator-join.json').read_text())['entries'];rows=[]
    missing=[j['support_packet_id'] for j in joins if not (OUT/'annotations'/j['support_packet_id']/'development-summary.json').exists()]
    if missing:raise ValueError('complete-bank release gate closed; retain missing judgments: '+str(len(missing)))
    packets={Path(b['path']).stem:b for b in declaration['packets']}
    for join in joins:
        key=join['support_packet_id'];b=packets[key];packet=json.loads((ROOT/b['path']).read_text());target=OUT/'annotations'/key
        terminal=json.loads((target/'development-summary.json').read_text())
        if terminal['packet_sha256']!=b['sha256'] or not terminal['finalized']:raise ValueError('terminal source mismatch')
        a=json.loads((target/'annotation-A.json').read_text());c=json.loads((target/'annotation-B.json').read_text());report=compare(packet,a,c)
        if report!=json.loads((target/'agreement.json').read_text()):raise ValueError('agreement does not reproduce')
        adj=json.loads((target/'adjudication.json').read_text()) if report['disagreement_count'] else {'schema':'crane-blinded-atomic-annotation-adjudication/v1','agreement_report_sha256':canonical_sha256(report),'adjudicator_id':'coordinator-no-disagreements','decisions':[],'attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'}
        final=finalize(report,adj)
        if final!=json.loads((target/'final.json').read_text()):raise ValueError('final labels do not reproduce')
        answerable=join['partial_information_answerable']
        rows.append({**join,'pass_A':score(_values(a),answerable),'pass_B':score(_values(c),answerable),'final':score(final['final_decisions'],answerable),'disagreements':report['disagreements'],'final_sha256':digest(target/'final.json')})
    result=summarize(rows);result.update(schema='roboboat-contact-policy-support-results/v2',analysis_plan_sha256=digest(PLAN),support_declaration_sha256=digest(DECLARATION),missing_annotations=[],old_banks_replaced=False)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('immutable analysis release already exists')
    r=analyze();save(a.output,r);print(json.dumps(r['methods'],indent=2))
