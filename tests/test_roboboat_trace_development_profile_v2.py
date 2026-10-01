import json
from pathlib import Path
import pytest
from profile_roboboat_trace_development_v2 import profile, binding


def test_all_declared_failures_running_and_unattempted_remain_without_score_reads(tmp_path):
    registry=tmp_path/'registry.json';rows=[{'id':i,'cluster_id':'g','family':'test'} for i in ('a','b','c')];registry.write_text(json.dumps({'rows':rows,'clusters':[{'cluster_id':'g','rows':['a','b']}]}))
    captures=tmp_path/'captures';captures.mkdir();out=captures/'a';out.mkdir();(out/'capture-attempt.json').write_text(json.dumps({'row':rows[0],'registry_sha256':binding(registry)['sha256'],'status':'TECHNICAL_FAILURE','error':'retained'}));out=captures/'b';out.mkdir();(out/'capture-intent.json').write_text('{}')
    declaration=tmp_path/'d.json';declaration.write_text(json.dumps({'schema':'roboboat-trace-qualified-development-declaration/v1','confirmation_n':0,'registry':str(registry),'dependencies':[binding(registry)],'rows':['a','b','c'],'output_root':str(captures),'platform_version':'construction'}))
    result=profile(declaration);assert result['declared_attempts']==3 and result['recording_dispositions']=={'TECHNICAL_FAILURE':1,'RUNNING':1,'UNATTEMPTED':1}
    assert result['valid_recordings']==0 and result['complete_geometry_pairs']==0 and not result['inference']
    registry.write_text('{}')
    with pytest.raises(ValueError,match='registry changed'):profile(declaration)


def test_operational_replay_cannot_enter_fresh_collection_profile(tmp_path):
    registry=tmp_path/'registry.json';row={'id':'old-replay','cluster_id':'old-g','family':'test'};registry.write_text(json.dumps({'rows':[row],'clusters':[{'cluster_id':'old-g','rows':[row['id']]}]}))
    captures=tmp_path/'captures';folder=captures/row['id'];folder.mkdir(parents=True)
    declaration=tmp_path/'d.json';declaration.write_text(json.dumps({'schema':'roboboat-trace-qualified-development-declaration/v1','confirmation_n':0,'registry':str(registry),'dependencies':[binding(registry)],'rows':[row['id']],'output_root':str(captures),'platform_version':'repaired'}))
    export={'row':row,'registry_sha256':binding(registry)['sha256'],'status':'VALID_TRACE_QUALIFIED_DEVELOPMENT','operational_replay':True,'platform_version':'repaired'}
    (folder/'capture-export-terminal-trace-v4.json').write_text(json.dumps(export))
    with pytest.raises(ValueError,match='fresh revised-platform'):profile(declaration)
