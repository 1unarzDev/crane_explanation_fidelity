import copy
import hashlib
import json
import pytest
from analysis.hexar_external.confirmatory_v1.provider_binding_admission import admission_errors


def fixture(tmp_path):
    def pin(name,value):
        path=tmp_path/name;path.write_text(value)
        return dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    docs={'comparator_freeze.json':{'baseline':{}},'annotation_freeze.json':{}};reports={}
    for role,config in (('baseline',docs['comparator_freeze.json']['baseline']),('judge',docs['annotation_freeze.json'])):
        system='a'*64;decoding=dict(reasoning_effort='high',temperature=dict(status='not_supported',provider_documented=True))
        config.update(model='SYNTHETIC_REQUEST_MODEL',model_version='SYNTHETIC_IMMUTABLE_VERSION',decoding=decoding)
        config['system_instructions_sha256' if role=='baseline' else 'complete_system_instructions_sha256']=system
        report=dict(schema='hexar-provider-binding-qualification/v1',status='QUALIFIED',role=role,
            confirmatory_outputs_generated=0,requested_model=config['model'],served_model_version=config['model_version'],
            immutable_served_version_attested=True,full_system_and_request_binding_verified=True,
            decoding_binding_verified=True,automatic_retries_disabled=True,effective_system_sha256=system,
            frozen_decoding=decoding,evidence={key:pin(role+'-'+key,key) for key in
                ('version_stability_basis','effective_request_and_system','decoding_behavior','single_attempt_transport')})
        config['provider_binding_qualification']=pin(role+'.json',json.dumps(report));reports[role]=report
    return docs,reports


def test_complete_synthetic_binding_and_no_provider_calls(tmp_path):
    docs,_=fixture(tmp_path)
    assert admission_errors(docs,tmp_path)==[]


@pytest.mark.parametrize('change',['alias_only','missing_decoding','different_version','user_prompt_only','automatic_retry','missing_evidence','exposed'])
def test_unbound_alias_defaults_or_system_cannot_activate_confirmation(tmp_path,change):
    docs,reports=fixture(tmp_path);report=reports['baseline'];config=docs['comparator_freeze.json']['baseline']
    if change=='alias_only':report['immutable_served_version_attested']=False
    elif change=='missing_decoding':config['decoding']=None
    elif change=='different_version':report['served_model_version']='another'
    elif change=='user_prompt_only':report['effective_system_sha256']='b'*64
    elif change=='automatic_retry':report['automatic_retries_disabled']=False
    elif change=='missing_evidence':report['evidence'].pop('version_stability_basis')
    else:report['confirmatory_outputs_generated']=1
    path=tmp_path/'baseline.json';path.write_text(json.dumps(report));config['provider_binding_qualification']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    assert admission_errors(docs,tmp_path)
