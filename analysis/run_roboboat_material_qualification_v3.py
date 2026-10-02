#!/usr/bin/env python3
"""Operational v3 correction: same registered material-v2 requests, one cached return reused."""
import hashlib
import json
import shutil
from pathlib import Path
from run_evidence_calibration_agent_qualification import _packet,_payload,aggregate,gates_pass
from run_evidence_calibration_agent_annotation import PROMPT,StructuredCodexCliAgentCaller
from roboboat_material_qualification_validation_v3 import validate as validate_return
from evidence_calibration_io import canonical_sha256
from roboboat_isolated_transport import isolated_run
from roboboat_qualification_boolean_fields_v2 import score_case

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'
OUT=ROOT/'artifacts/roboboat-material-qualification-v3'


def main():
    freeze_path=DOC/'material_qualification_operational_freeze_v3.json';freeze=json.loads(freeze_path.read_text())
    for b in freeze['dependencies']:
        if hashlib.sha256((ROOT/b['path']).read_bytes()).hexdigest()!=b['sha256']:raise ValueError('qualification binding changed: '+b['path'])
    current=json.loads((ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json').read_text())['qualified_binding']
    if (current['model'],current['reasoning_effort'])!=(freeze['candidate']['model'],freeze['candidate']['reasoning_effort']):raise ValueError('current judge differs')
    suite=json.loads((DOC/'material_qualification_suite_v2.json').read_text());suite_hash=canonical_sha256(suite)
    if suite_hash!=freeze['qualification_suite_sha256']:raise ValueError('suite differs from prospective freeze')
    OUT.mkdir(parents=True,exist_ok=False)
    (OUT/'intent.json').write_text(json.dumps({'freeze_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),'quality_retries':0},indent=2)+'\n')
    for b in freeze['retained_call_reuse']:
        old=ROOT/b['path'];target=OUT/'pass-A/calls'/old.name;target.parent.mkdir(parents=True,exist_ok=True)
        if hashlib.sha256(old.read_bytes()).hexdigest()!=b['sha256']:raise ValueError('retained call changed')
        record=json.loads(old.read_text())
        if record['status']!='VALID' or record['attempt_count']!=1:raise ValueError('only exact valid cache may be reused')
        shutil.copyfile(old,target)
    passes=[]
    try:
        prompt=PROMPT.read_text();schema=json.loads((ROOT/freeze['candidate']['structured_output']).read_text())
        for slot in ('A','B'):
            caller=StructuredCodexCliAgentCaller(OUT/f'pass-{slot}/calls',model=current['model'],effort=current['reasoning_effort'],timeout_s=300,runner=isolated_run)
            rows=[]
            for case in suite['cases']:
                packet=_packet(case,slot,suite_hash);form=json.loads(json.dumps(packet['forms'][0]));form['_response_text']=case['form']['response_text']
                payload=_payload(packet,form,slot);payload['agent_identity']=f'agent-{slot}-marine-material-v2'
                retained=caller.call(logical_role=f'material-v2-{slot}-{case["case_id"]}',payload=payload,schema=schema,prompt=prompt)
                returned=retained['parsed_final'];validate_return(packet,returned,case['form']['response_text'])
                rows.append(score_case(case,returned));print('completed',slot,case['case_id'],flush=True)
            metrics=aggregate(rows,'heldout');passed,checks=gates_pass(metrics,freeze['heldout_gates'])
            passes.append({'slot':slot,'heldout_metrics':metrics,'gate_checks':checks,'passed':passed,'case_scores':rows})
    except Exception as exc:
        (OUT/'retained-failure.json').write_text(json.dumps({'status':'RETAINED_FAILURE_NO_RETRY','type':type(exc).__name__,'detail':str(exc),'completed_passes':passes},indent=2)+'\n')
        raise
    result={'schema':'roboboat-material-qualification-result/v3-operational-correction','suite_sha256':suite_hash,'freeze_sha256':canonical_sha256(freeze),'passes':passes,'status':'AUTOMATED_GATES_PASS_CITATION_REVIEW_PENDING' if all(p['passed'] for p in passes) else 'FAILED_RETAIN_NO_RETRY','semantic_citation_review_complete':False,'whole_endpoint_qualified':False,'global_binding_changed':False,'quality_retries':0,'new_configuration_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'human_validation':False,'retained_prior_calls_reused':1,'requests_reissued':0,'prior_validation_failure_preserved':True}
    (OUT/'qualification-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)


if __name__=='__main__':main()
