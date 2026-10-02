#!/usr/bin/env python3
"""Fresh prospectively reviewed external qualification; preserve every v1 result."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
import tempfile
from audit_release import ROOT,sha,write
from qualify_v2 import effective_prompt as v2_prompt
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller,PROMPT,RETURN_SCHEMA
from run_evidence_calibration_agent_qualification import _packet,score_case,aggregate,gates_pass
from adjudicate_evidence_calibration_annotations import validate_return
V2=ROOT/'data/hexar_external/v3'
AMEND=ROOT/'docs/hexar_external/v3/sentinel_clarification.txt'

def effective_prompt():return v2_prompt()+'\n\n'+AMEND.read_text()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build-only',action='store_true');a=ap.parse_args()
    out=V2/'qualification';value=json.loads((out/'suite.candidate.json').read_text())
    for c in value['cases']:
        text=c['form']['response_text']
        assert all(a['response_span'] in text for a in c['form']['atomic_statements'])
        assert all(f['response_span'] in text for f in c['expected']['required_unit_coverage'] if f['communicated'])
    old=json.loads((ROOT/'data/hexar_external/qualification/qualification-result.json').read_text())
    assert old['status']=='FAILED_RETAIN_NO_RETRY'
    freeze={'schema':'hexar-external-qualification-freeze/v3','qualification_suite_sha256':canonical_sha256(value),
       'candidate':{'model':'gpt-6-astra','reasoning_effort':'high','transport':'codex-cli-chatgpt-login-ephemeral/v1','tools':'none'},
       'main_qualification_binding_sha256':sha(ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json'),
       'prompt_sha256':sha(PROMPT),'amendment_sha256':sha(AMEND),'schema_sha256':sha(RETURN_SCHEMA),
       'review_sha256':sha(ROOT/'docs/hexar_external/v3/INTERFACE_REVIEW.md'),
       'second_construction_review_sha256':sha(ROOT/'docs/hexar_external/v3/ROOT_FIXTURE_REVIEW.md'),
       'base_external_v2_amendment_sha256':sha(ROOT/'docs/hexar_external/v2/annotation_amendment.txt'),
       'second_construction_review':'Root must independently check every fresh fixture before inference; freeze is not permitted until the review record exists.',
       'passes':['A','B'],'workers':2,'quality_retries':0,
       'heldout_gates':{'minimum_atomic_accuracy':1.0,'maximum_unsupported_false_acceptance_rate':0.0,
         'maximum_supported_false_rejection_rate':0.0,'minimum_physically_true_but_unsupported_recall':1.0,
         'minimum_field_accuracy':1.0,'minimum_prompt_injection_case_accuracy':1.0},
       'old_candidate_disposition':'V1 failed and V2 field-invalid pilot jobs retained unchanged. V2 synthetic qualification passed but did not cover original nominal/subjective sentinel compliance. No prior qualification/job is retried or rescored.',
       'primary_materiality':'All asserted navigation diagnostic/outcome/state/software-mechanism propositions are material; unsupported non-entailment clauses and stronger negative causes are material too. Pure lexical style and exact wording are not endpoints.',
       'alpha_consumed':0,'human_validity_established':False}
    path=out/'freeze.json'
    if path.exists() and json.loads(path.read_text())!=freeze:raise ValueError('Prospective freeze changed')
    write(path,freeze)
    if a.build_only:print('V3_INTERFACE_QUALIFICATION_FROZEN_BEFORE_INFERENCE');return
    resultpath=out/'qualification-result.json'
    if resultpath.exists():print(json.loads(resultpath.read_text())['status']);return
    temp=V2/'tmp';temp.mkdir(parents=True,exist_ok=True);os.environ['TMPDIR']=str(temp);tempfile.tempdir=str(temp)
    schema=json.loads(RETURN_SCHEMA.read_text());prompt=effective_prompt()
    def run(item):
        slot,case=item;caller=StructuredCodexCliAgentCaller(out/f'pass-{slot}'/'calls',model='gpt-6-astra',effort='high',timeout_s=240)
        pkt=_packet(case,slot,canonical_sha256(value));form=pkt['forms'][0]
        payload={'task':'BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION','annotation_origin':'automated_agent_qualification',
          'agent_identity':f'agent-{slot}-astra-external-v3','packet_set_sha256':canonical_sha256(pkt),'response_text':case['form']['response_text'],
          'form':form,'required_attestation':'INDEPENDENT_BLINDED_COMPLETE'}
        try:
            r=caller.call(logical_role=f'hexar-v3-qualification-{slot}-{case["case_id"]}',payload=payload,schema=schema,prompt=prompt)
            ret=r['parsed_final'];validate_return(pkt,ret);score=score_case(case,ret)
            write(out/f'pass-{slot}'/f'{case["case_id"]}-score.json',score)
            print(slot,case['case_id'],'scored',flush=True);return slot,score,None
        except Exception as e:return slot,None,str(e)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[(s,c) for s in ('A','B') for c in value['cases']]))
    passes=[];failures=[e for s,r,e in results if e]
    for slot in ('A','B'):
        rows=[r for s,r,e in results if s==slot and r]
        if len(rows)!=len(value['cases']):passes.append({'slot':slot,'passed':False,'status':'TECHNICAL_INCOMPLETE'});continue
        metrics=aggregate(rows,'heldout');passed,checks=gates_pass(metrics,freeze['heldout_gates'])
        passes.append({'slot':slot,'heldout_metrics':metrics,'gate_checks':checks,'passed':passed,'case_scores':rows})
    result={'schema':'hexar-external-qualification-result/v3','suite_sha256':canonical_sha256(value),'freeze_sha256':canonical_sha256(freeze),
      'passes':passes,'technical_failures':failures,'status':'QUALIFIED' if not failures and all(p['passed'] for p in passes) else 'FAILED_RETAIN_NO_RETRY',
      'quality_driven_retries':0,'human_validity_established':False,'alpha_consumed':0}
    write(resultpath,result);print(result['status'],flush=True)
if __name__=='__main__':main()
