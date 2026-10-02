#!/usr/bin/env python3
"""Separate descriptive settling comparison; no new independent-cluster inference."""
import argparse
import hashlib
import json
from pathlib import Path
from adjudicate_evidence_calibration_annotations import compare,finalize,_values,_item_id
from evidence_calibration_io import canonical_sha256
from analyze_roboboat_atomic_reassessment import score_decisions
from run_roboboat_settling_support import ROOT,DOC,OUT,DECLARATION,PARTIAL_UNIT
from build_roboboat_terminal_batch import save,digest

PARTIAL_KEY='unit:'+_item_id('u-',PARTIAL_UNIT)


def scores(decisions,level):
    values=dict(decisions)
    if level=='L2':
        if PARTIAL_KEY not in values or type(values[PARTIAL_KEY]) is not bool:
            raise ValueError('partial-compliance coverage must be judged explicitly')
        partial=values.pop(PARTIAL_KEY)
    else:
        if PARTIAL_KEY in values:raise ValueError('partial interval unit belongs only at L2')
        partial=None
    inherited=score_decisions(values)
    return {'inherited':inherited,'partial_compliance_communicated':partial,
            'extended_answer_success':inherited['answer_success'] and partial is not False}


def summarize(rows):
    if len(rows)!=12 or len({(r['batch'],r['method'],r['level']) for r in rows})!=12:
        raise ValueError('complete fixed settling population required')
    expected={(b,m,l) for b in ('boat-terminal-settling-001','boat-terminal-settling-002')
        for m in ('B2','B4') for l in ('L0','L1','L2')}
    if {(r['batch'],r['method'],r['level']) for r in rows}!=expected:
        raise ValueError('fixed settling identities differ')
    methods={}
    for method in ('B2','B4'):
        selected=[r for r in rows if r['method']==method]
        methods[method]={view:{'answers':6,
            'inherited_successes':sum(r[view]['inherited']['answer_success'] for r in selected),
            'extended_successes':sum(r[view]['extended_answer_success'] for r in selected),
            'answerable_partial_compliance_questions':2,
            'partial_compliance_coverage':sum(r[view]['partial_compliance_communicated'] is True for r in selected),
            'required_inherited_units_covered':sum(r[view]['inherited']['required_units_covered'] for r in selected),
            'required_inherited_units_n':24} for view in ('final','pass_A','pass_B')}
    return {'rows':rows,'methods':methods,'new_independent_cluster_n':0,'physical_recordings':2,
        'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'p_value':None,'confidence_interval':None,
        'analysis':'Two inspected variants within existing approach clusters; no pooling with original fixed-six-question paired endpoint.',
        'coverage_unit_status':'Declared after response inspection and before support calls; development sensitivity, not a prospectively confirmatory endpoint.',
        'agent_assessed':True,'human_validation':False,
        'judge_uncertainty':'Same-family support passes may share errors; agreement is not accuracy or replication.'}


def analyze():
    plan=json.loads((DOC/'settling_support_analysis_plan_v1.json').read_text())
    if plan['disposition']!='INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY':
        raise ValueError('development analysis gate closed')
    for item in plan['dependencies']:
        if digest(ROOT/item['path'])!=item['sha256']:raise ValueError('analysis plan binding changed')
    declaration=json.loads(DECLARATION.read_text())
    for item in declaration['dependencies']+declaration['packets']:
        if digest(ROOT/item['path'])!=item['sha256']:raise ValueError('frozen support binding changed')
    joins=json.loads((OUT/'evaluator-join.json').read_text())['entries']
    missing=[j['support_packet_id'] for j in joins if not
        (OUT/'annotations'/j['support_packet_id']/'development-summary.json').exists()]
    if missing:raise ValueError(f'complete-bank release gate closed: {len(missing)} missing judgments')
    packets={Path(p['path']).stem:p for p in declaration['packets']};rows=[]
    for join in joins:
        key=join['support_packet_id'];binding=packets[key];packet=json.loads((ROOT/binding['path']).read_text())
        target=OUT/'annotations'/key;terminal=json.loads((target/'development-summary.json').read_text())
        if terminal['packet_sha256']!=binding['sha256'] or not terminal['finalized']:raise ValueError('terminal mismatch')
        a=json.loads((target/'annotation-A.json').read_text());b=json.loads((target/'annotation-B.json').read_text())
        report=compare(packet,a,b)
        if report!=json.loads((target/'agreement.json').read_text()):raise ValueError('agreement does not reproduce')
        adj=json.loads((target/'adjudication.json').read_text()) if report['disagreement_count'] else {
            'schema':'crane-blinded-atomic-annotation-adjudication/v1','agreement_report_sha256':canonical_sha256(report),
            'adjudicator_id':'coordinator-no-disagreements','decisions':[],'attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'}
        final=finalize(report,adj)
        if final!=json.loads((target/'final.json').read_text()):raise ValueError('adjudication does not reproduce')
        rows.append({**join,'final':scores(final['final_decisions'],join['level']),
            'pass_A':scores(_values(a),join['level']),'pass_B':scores(_values(b),join['level']),
            'disagreements':report['disagreements'],'final_sha256':digest(target/'final.json')})
    result=summarize(rows);result.update(schema='roboboat-settling-support-development-results/v1',
        support_declaration_sha256=digest(DECLARATION),original_banks_replaced=False,
        missing_annotations=[])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('released settling analysis is immutable')
    result=analyze();save(args.output,result);print(json.dumps(result['methods'],indent=2))
