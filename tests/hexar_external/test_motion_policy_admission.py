import copy
import hashlib
import json

import pytest
from analysis.hexar_external.confirmatory_v1.motion_policy_admission import admission_errors,MANIFESTS,BINDINGS,CHECKS
from analysis.hexar_external.confirmatory_v1.motion_usefulness import PUBLIC_REQUIREMENT


def fixture(tmp_path):
    def pin(name,value):
        path=tmp_path/name;path.write_text(value)
        return dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    bindings={key:pin(key,key) for key in BINDINGS}
    report=dict(schema='hexar-motion-policy-qualification/v1',status='QUALIFIED',bindings=bindings,
        checks=dict.fromkeys(CHECKS,True),evidence={key:pin(key,key) for key in CHECKS},confirmatory_outputs_generated=0)
    qualification=pin('qualification.json',json.dumps(report))
    policy=dict(bindings,status='READY_FOR_FREEZE',whole_endpoint_qualified=True,
        maximum_resolution_or_range_width_m='0.1',physical_no_motion_threshold=None,
        public_requirement_sha256=hashlib.sha256(PUBLIC_REQUIREMENT.encode()).hexdigest(),qualification=qualification)
    return {name:dict(motion_usefulness_policy=copy.deepcopy(policy)) for name in MANIFESTS},report


def test_complete_synthetic_preconfirmation_evidence_passes(tmp_path):
    docs,_=fixture(tmp_path)
    assert admission_errors(docs,tmp_path)==[]


@pytest.mark.parametrize('mutation',['absent','unequal','different_threshold','physical_threshold','stale_code','unqualified','missing_check','missing_evidence','exposed','nonobject'])
def test_incomplete_or_changed_policy_fails_before_generation(tmp_path,mutation):
    docs,report=fixture(tmp_path)
    if mutation=='absent':del docs[MANIFESTS[0]]['motion_usefulness_policy']
    elif mutation=='unequal':docs[MANIFESTS[0]]['motion_usefulness_policy']['public_requirement_sha256']='other'
    elif mutation=='different_threshold':
        for doc in docs.values():doc['motion_usefulness_policy']['maximum_resolution_or_range_width_m']='1'
    elif mutation=='physical_threshold':
        for doc in docs.values():doc['motion_usefulness_policy']['physical_no_motion_threshold']=.1
    elif mutation=='stale_code':(tmp_path/BINDINGS[0]).write_text('changed')
    else:
        if mutation=='unqualified':report['status']='AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION'
        elif mutation=='missing_check':report['checks'].pop(CHECKS[0])
        elif mutation=='missing_evidence':report['evidence'].pop(CHECKS[0])
        elif mutation=='nonobject':report=[]
        else:report['confirmatory_outputs_generated']=1
        path=tmp_path/'qualification.json';path.write_text(json.dumps(report))
        for doc in docs.values():doc['motion_usefulness_policy']['qualification']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    assert admission_errors(docs,tmp_path)
