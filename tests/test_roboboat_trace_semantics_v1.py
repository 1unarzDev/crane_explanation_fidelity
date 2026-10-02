import copy
import struct
import pytest
from audit_roboboat_trace_semantics_v1 import audit, ROS_SOURCE

def rows():
    base={'source':ROS_SOURCE,'episode':4,'sequence':1,'applicationTick':13,'callbackCompletionTick':13}
    return [{'kind':'metadata'},dict(base,kind='ros_callback',ordinal=1,monotonic=10),dict(base,kind='receive',ordinal=2,monotonic=11),dict(base,kind='post_apply_callback',ordinal=3,monotonic=12,payloadEncoding='float32-le[]',payload=list(struct.pack('<fff',.25,-.5,0))),{'kind':'footer'}]

def test_decodes_desired_velocity_without_claiming_raw_or_physical_linkage():
    result=audit(rows());assert result['checks_pass']
    assert result['desired_velocity_component_ranges'][1]['minimum']==-.5
    assert not result['raw_input_payload_linkage_proven'] and not result['scientific_admission_authorized']

@pytest.mark.parametrize('change,issue',[('clock','SESSION_CLOCK_REVERSED'),('size','ROS_THREE_FLOAT_PAYLOAD_REQUIRED'),('nan','NONFINITE_DESIRED_VELOCITY'),('step','ROS_CALLBACK_CROSSED_FIXED_STEP')])
def test_clock_and_payload_faults_retained(change,issue):
    x=rows()
    if change=='clock':x[2]['monotonic']=9
    if change=='size':x[3]['payload'].pop()
    if change=='nan':x[3]['payload']=list(struct.pack('<fff',float('nan'),0,0))
    if change=='step':x[3]['callbackCompletionTick']=14
    assert issue in audit(x)['issues']
