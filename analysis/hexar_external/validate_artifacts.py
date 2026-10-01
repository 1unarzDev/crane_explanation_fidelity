#!/usr/bin/env python3
"""Read-only boundary/artifact validation. Failed measurement is a valid retained outcome."""
import hashlib
import json
from pathlib import Path
import sys
from audit_release import ROOT,sha
from contract_adapter import check_core_pin
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256

def validate():
    check_core_pin()
    audit=ROOT/'data/hexar_external/audit'
    historical=json.loads((audit/'historical_results.json').read_text())
    for field in ('duplicates','majority_mismatches','missing_pairs','accuracy_composition_mismatches','experiment_correspondence_mismatches'):
        assert historical[field]==[],field
    assert historical['methods']['explanation']['all']['accuracy']['positive']==167
    inventory=json.loads((audit/'navigation_inventory.json').read_text())['recordings']
    assert len(inventory)==18
    assert {x['situation'] for x in inventory}=={'obstacle','manual_joystick','charging','localization','dynamic_env','success'}
    assert all(x['sql_message_count']==x['metadata_message_count'] and not x['metadata_count_mismatches'] for x in inventory)
    split=json.loads((audit/'split.json').read_text())
    assert len(split['development'])==6 and len(split['reserved'])==12
    assert set(split['development']).isdisjoint(split['reserved'])
    development=ROOT/'data/hexar_external/development'
    packets=json.loads((development/'packets.json').read_text())['packets']
    byid={x['job_id']:x for x in packets}
    references=json.loads((development/'independent_references.json').read_text())['references']
    assert len(references)==len(packets)==9
    for ref in references:
        assert ref['method_packet_sha256']==byid[ref['job_id']]['packet_sha256']
    decl=json.loads((development/'execution_declaration.json').read_text())
    assert decl['adapter_sha256']==sha(ROOT/'analysis/hexar_external/contract_adapter.py')
    assert decl['packets_sha256']==sha(development/'packets.json')
    assert decl['calibration_prompt_sha256']==sha(ROOT/'docs/hexar_external/prompt_calibration_v1.txt')
    responses=[json.loads(p.read_text()) for p in (development/'responses').glob('*.json')]
    assert len(responses)==27 and all(r['status']=='VALID' for r in responses)
    assert len({(r['method'],r['question_id'],r['condition']) for r in responses})==27
    for r in responses:
        base=r['job_id'].rsplit('-HX-',1)[0]
        assert r['packet_sha256']==byid[base]['packet_sha256']
        if r['method']=='HX-CONTRACT':
            assert not r['model_calls'] and r['contract_artifact']['realization']['audit']['missing_required_claim_ids']==[]
            assert len(r['answer'].split())<=60
    ann=ROOT/'data/hexar_external/annotation'
    bank=json.loads((ann/'blind_bank.json').read_text())
    inv=json.loads((ann/'atomic_inventory.json').read_text())
    bankrows={r['response_id']:r for r in bank['items']}
    assert {r['response_id'] for r in inv['items']}==set(bankrows)
    assert inv['source_bank_sha256']==sha(ann/'blind_bank.json')
    for row in inv['items']:
        text=bankrows[row['response_id']]['response_text']
        assert row['response_text_sha256']==hashlib.sha256(text.encode()).hexdigest()
        for atom in row['atoms']:assert atom['response_span'] in text
    qual=ROOT/'data/hexar_external/qualification'
    suite=json.loads((qual/'suite.json').read_text());freeze=json.loads((qual/'freeze.json').read_text())
    result=json.loads((qual/'qualification-result.json').read_text())
    assert canonical_sha256(suite)==freeze['qualification_suite_sha256']==result['suite_sha256']
    assert canonical_sha256(freeze)==result['freeze_sha256']
    assert result['status']=='FAILED_RETAIN_NO_RETRY' and not any(p['passed'] for p in result['passes'])
    report=json.loads((ROOT/'data/hexar_external/reports/development_summary.json').read_text())
    assert report['primary_paired_effect'] is None and report['p_value'] is None and report['alpha_consumed']==0
    assert not decl['primary_endpoint_scoring_authorized']
    print(json.dumps({'artifact_integrity':'PASS','responses':27,'recordings':1,'qualified_endpoint':'BLOCKED','alpha_consumed':0}))
if __name__=='__main__':validate()
