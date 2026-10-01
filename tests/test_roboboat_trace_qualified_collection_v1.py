import copy
import json
from pathlib import Path
from unittest.mock import patch
import pytest
import run_roboboat_population_development_v9 as collector
from export_roboboat_trace_qualified_v1 import publish_terminal


def declaration(tmp_path):
    registry=tmp_path/'registry.json';registry.write_text(json.dumps({'status':'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION','rows':[{'id':'fresh-a'}]}))
    review=tmp_path/'review.json';review.write_text(json.dumps({'status':'READY_FOR_TRACE_QUALIFIED_DEVELOPMENT','confirmation_authorized':False}))
    (tmp_path/'prior').mkdir()
    paths=[Path(collector.__file__).resolve(),registry,review,collector.BUILD_IDENTITY.resolve()]
    paths += [collector.ROOT/'analysis'/name for name in ('export_roboboat_trace_qualified_v1.py','export_roboboat_population_v2.py','roboboat_trace_qualified_validity_v1.py','audit_roboboat_trace_semantics_v1.py','audit_roboboat_action_trace_v1.py','audit_roboboat_frame_timing_v1.py','roboboat_owned_player_bundle_v1.py','roboboat_hidden_render_v3.py')]
    d={'schema':'roboboat-trace-qualified-development-declaration/v1','confirmation_n':0,'registry':str(registry),
       'overhead_qualification_review':str(review),'dependencies':[{'path':str(p),'sha256':collector.digest(p)} for p in paths],
       'rows':['fresh-a'],'prior_capture_roots':[str(tmp_path/'prior')],'domain':195,'port':11485,'maximum_delta_time':.04}
    return d


def test_declaration_requires_qualified_review_unique_rows_and_fresh_identity(tmp_path):
    d=declaration(tmp_path);path=tmp_path/'d.json'
    assert collector.validate_declaration(d,path)[2]==[{'id':'fresh-a'}]
    for fault in ('unqualified','duplicate','old','changed_source','missing_registry_binding'):
        bad=copy.deepcopy(d)
        if fault=='unqualified':
            review=tmp_path/'unqualified.json';review.write_text(json.dumps({'status':'NOT_READY','confirmation_authorized':False}));bad['overhead_qualification_review']=str(review);bad['dependencies'].append({'path':str(review),'sha256':collector.digest(review)})
        if fault=='duplicate':bad['rows']=['fresh-a','fresh-a']
        if fault=='old':
            folder=tmp_path/'prior/old';folder.mkdir(parents=True);(folder/'capture-intent.json').write_text(json.dumps({'row':{'id':'fresh-a'}}))
        if fault=='changed_source':bad['dependencies'][0]['sha256']='wrong'
        if fault=='missing_registry_binding':bad['dependencies']=bad['dependencies'][:1]+bad['dependencies'][2:]
        with pytest.raises(ValueError):collector.validate_declaration(bad,path)


def test_old_failure_cannot_be_salvaged_even_under_a_later_declaration(tmp_path):
    row={'id':'old-a'};registry=tmp_path/'registry.json';registry.write_text('{}')
    d=tmp_path/'declaration.json';d.write_text(json.dumps({'rows':['old-a']}))
    capture=tmp_path/'capture';capture.mkdir()
    (capture/'capture-attempt.json').write_text(json.dumps({'row':row,'registry_sha256':collector.digest(registry),'status':'TECHNICAL_FAILURE','development_recording_admitted':False}))
    with pytest.raises(ValueError,match='cannot salvage'):publish_terminal(row,registry,capture,tmp_path/'config',d)


def test_full_schedule_continues_across_technical_failures_without_retries(tmp_path,monkeypatch):
    d=declaration(tmp_path);d['rows']=['fresh-a','fresh-b','fresh-c'];registry=Path(d['registry']);registry.write_text(json.dumps({'status':'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION','rows':[{'id':i} for i in d['rows']]}));d['dependencies'][1]['sha256']=collector.digest(registry)
    d['output_root']=str(tmp_path/'out');path=tmp_path/'declaration.json';path.write_text(json.dumps(d))
    monkeypatch.setattr('sys.argv',['collector','--declaration',str(path)])
    seen=[]
    def capture(row,*args):seen.append(row['id']);return {'status':'TECHNICAL_FAILURE','row':row}
    with patch.object(collector,'verify_player'),patch.object(collector,'capture',side_effect=capture),patch.object(collector.fcntl,'flock'):
        collector.main()
    assert seen==d['rows']
    t=json.loads((tmp_path/'out/terminal.json').read_text());assert t['physical_attempts']==3 and t['valid_recordings']==0 and t['confirmation_n']==0
    with pytest.raises(FileExistsError):collector.main()


def test_capture_and_export_roundtrip_of_serialized_stale_fault_with_mocked_launch(tmp_path):
    """Run real gate/projector/exporter code; copied inputs are only a temporary test."""
    import shutil
    from unittest.mock import Mock
    source=collector.ROOT/'artifacts/roboboat-population-development-42005/captures-v8-trace-pilot-001/boat-geom-42005-00001-v1'
    registry_path=collector.ROOT/'docs/roboboat_terminal_evidence/populations/development-42005/registry.json'
    registry=json.loads(registry_path.read_text());row=copy.deepcopy(registry['rows'][0]);row['id']='fresh-a'
    declaration_path=tmp_path/'declaration.json';declaration_path.write_text(json.dumps({'rows':[row['id']]}))
    output=tmp_path/'captures';output.mkdir()
    def launch(command,**kwargs):
        out=Path(kwargs['env']['CRANE_RESULT_ROOT'])
        for name in ('navigation-reset-summary.json','worker-0/result.json','fixture-summary.json','runtime-parameters.json','action-timing.jsonl','worker-0/player.log','render-audit.json','frame-timing.jsonl'):
            target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
        process=Mock();process.wait.return_value=0;return process
    bundle={'executable':{'path':'/mock/player'},'expected_class':'mock'}
    with patch.object(collector,'verify_player'),patch.object(collector,'prepare_bundle',return_value=bundle),patch.object(collector,'verify_bundle'),patch.object(collector,'default_affinity',return_value=[0]),patch.object(collector.subprocess,'Popen',side_effect=launch):
        result=collector.capture(row,registry,registry_path,output,195,11485,.04,declaration_path)
    assert result['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT'
    assert result['stale_actions_observed']==1 and result['worker_valid_original'] is False
    assert result['confirmation_n']==0 and result['prior_dispositions_changed'] is False
    original=json.loads((source/'capture-attempt.json').read_text());assert original['status']=='TECHNICAL_FAILURE'
    assert len(list((output/row['id']/'exports-v2/method_packets').glob('L*.json')))==3
    assert (output/row['id']/'capture-export-terminal-trace-v1.json').exists()
