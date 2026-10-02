import hashlib,json
import pytest
import probe_roboboat_isolated_baseline_capability_v1 as probe

def receipt():
    body={'schema':'roboboat-synthetic-tool-result/v1','permission_errors':[],'input_sha256':hashlib.sha256(probe.INPUT).hexdigest(),'yaml_import':True,'subprocess_child':'42','scratch_roundtrip':'disposable-synthetic-marker'}
    return {'status':'valid','parsed_final':{'executed':True,'probe_output':body,'permission_errors':[]},'events':[{'item':{'type':'command_execution','command':'python3 synthetic_challenge.py','exit_code':0,'aggregated_output':probe.MARKER+json.dumps(body)}}]}

def test_actual_trace_required_and_self_report_not_enough():
    r=receipt();assert probe.validate_receipt(r)['synthetic_expected_results_verified']
    r['events']=[];assert not probe.validate_receipt(r)['synthetic_expected_results_verified']

@pytest.mark.parametrize('attack',['echo','failed-exit','wrong-hash','scratch-denied','multiple-commands','self-report-mismatch'])
def test_truthful_capability_failure_for_missing_or_inconsistent_trace(attack):
    r=receipt();item=r['events'][0]['item']
    if attack=='echo':item['command']='echo '+item['aggregated_output']
    elif attack=='failed-exit':item['exit_code']=1
    elif attack=='multiple-commands':r['events'].append({'item':dict(item)})
    elif attack=='self-report-mismatch':r['parsed_final']['probe_output']=None
    else:
        body=json.loads(item['aggregated_output'][len(probe.MARKER):])
        if attack=='wrong-hash':body['input_sha256']='incorrect'
        else:body['scratch_roundtrip']=None;body['permission_errors']=[{'operation':'scratch_roundtrip','error_type':'PermissionError'}]
        item['aggregated_output']=probe.MARKER+json.dumps(body)
    assert probe.validate_receipt(r)['status']=='CAPABILITY_UNVERIFIED_OR_FAILED'

def test_declaration_binding_and_one_shot_intent_precede_transport(tmp_path,monkeypatch):
    root=tmp_path/'probe';probe.prepare(root);calls=[]
    def call(*args,**kwargs):
        assert (root/'call-intent.json').exists();calls.append(1);assert kwargs=={'allow_tools':True,'timeout':600};return receipt()
    monkeypatch.setattr(probe.transport,'call',call)
    assert probe.execute(root)['status']=='TRACE_VERIFIED_SYNTHETIC_CAPABILITY_PASS'
    with pytest.raises(FileExistsError):probe.execute(root)
    assert len(calls)==1

def test_changed_input_refused_before_intent(tmp_path,monkeypatch):
    root=tmp_path/'probe';probe.prepare(root);(root/'synthetic_packet/synthetic_input.txt').write_text('changed')
    with pytest.raises(ValueError):probe.execute(root)
    assert not (root/'call-intent.json').exists()
