import json
from pathlib import Path
import pytest
from roboboat_owned_player_bundle_v1 import binding
from profile_roboboat_clock_repair_operational_v11 import profile


def fixture(tmp_path):
    ids=['failure','running','missing','failure2'];registry=tmp_path/'registry.json';registry.write_text(json.dumps({'rows':[{'id':i} for i in ids]}))
    output=tmp_path/'captures';output.mkdir();declaration=tmp_path/'declaration.json';d={'schema':'roboboat-clock-repair-operational-declaration/v1','independent_n_added':0,'confirmation_n':0,'replication_n':0,'registry':str(registry),'output_root':str(output),'origin_rows':{i:'same-old-geometry' for i in ids},'rows':ids,'dependencies':[binding(registry)]};declaration.write_text(json.dumps(d))
    for identifier in ('failure','failure2'):
        folder=output/identifier;folder.mkdir();capture={'row':{'id':identifier},'registry_sha256':binding(registry)['sha256'],'prospective_declaration':binding(declaration),'operational_replay':True,'independent_n_added':0,'status':'TECHNICAL_FAILURE','checks':{'command_trace_integrity':False},'error':'retained trace error'}
        (folder/'capture-attempt.json').write_text(json.dumps(capture))
    folder=output/'running';folder.mkdir();(folder/'capture-intent.json').write_text('{}')
    return declaration,output


def test_failure_running_unattempted_denominator_never_becomes_independent_n(tmp_path):
    declaration,output=fixture(tmp_path);result=profile(declaration)
    assert result['dispositions']=={'TECHNICAL_FAILURE':2,'RUNNING':1,'UNATTEMPTED':1}
    assert len(result['rows'])==4 and result['independent_n_added']==0
    assert result['rows'][0]['failed_checks']==['command_trace_integrity']


def test_replay_cannot_be_promoted_to_new_geometry(tmp_path):
    declaration,output=fixture(tmp_path);p=output/'failure/capture-attempt.json';d=json.loads(p.read_text());d['independent_n_added']=1;p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='independent evidence'):profile(declaration)


def test_declared_registry_identity_checked_even_without_success(tmp_path):
    declaration,output=fixture(tmp_path);p=tmp_path/'registry.json';p.write_text('{}')
    with pytest.raises(ValueError,match='registry changed'):profile(declaration)
