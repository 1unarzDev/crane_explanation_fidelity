import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from audit_evidence_calibration_namespace_lifecycle import audit
from observe_evidence_calibration_namespace_status_v2 import validate


def wire(*rows):return b''.join(json.dumps(row).encode()+b'\n' for row in rows)


def test_initial_pid_is_not_payload_execution_or_model_failure():
    r=audit(wire({'child-pid':123,'mnt-namespace':456}),1)
    assert r['disposition']=='NAMESPACE_LIFECYCLE_INCOMPLETE'
    assert not r['payload_exit_verified'] and not r['model_failure_attributed']


def test_matching_nonzero_payload_exit_is_verified_without_semantic_attribution():
    r=audit(wire({'child-pid':123},{'exit-code':7}),7)
    assert r['payload_exit_verified'] and not r['model_failure_attributed']


def test_empty_status_remains_unverified():
    assert audit(b'',1)['disposition']=='NAMESPACE_LIFECYCLE_UNVERIFIED'


@pytest.mark.parametrize('raw,code',[
    (wire({'child-pid':True},{'exit-code':0}),0),
    (wire({'child-pid':123},{'exit-code':True}),1),
    (wire({'child-pid':123},{'exit-code':7.0}),7),
    (wire({'child-pid':123},{'exit-code':0}),7),
    (wire({'child-pid':123},{'exit-code':256}),255),
    (b'{"child-pid":1,"child-pid":2}\n',1),
    (b'{"child-pid":NaN}\n',1),
    (b'{"child-pid":1',1),
    (b'\xff',1),
    (b'x'*8193,1),
])
def test_corrupt_unmatched_or_unbounded_status_is_rejected(raw,code):
    with pytest.raises(ValueError):audit(raw,code)


def test_known_exec_and_setup_probe_shapes_remain_incomplete():
    row={'return_code':1,'stdout':'','status_records':[{'child-pid':123}]}
    validate('setup_failure',row);validate('exec_failure',row)
    with pytest.raises(ValueError):
        validate('setup_failure',{**row,'status_records':[{'child-pid':123},{'exit-code':1}]})


def test_payload_visible_descriptor_is_not_accepted():
    row={'return_code':0,'stdout':'{"status_descriptor_visible":true}',
         'status_records':[{'child-pid':123},{'exit-code':0}]}
    with pytest.raises(ValueError,match='accessible'):
        validate('descriptor_visibility',row)
