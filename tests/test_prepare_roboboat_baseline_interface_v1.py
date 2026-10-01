import json
from pathlib import Path
import pytest
import prepare_roboboat_baseline_interface_v1 as prep
from test_roboboat_shared_public_scope_v1 import public_inputs


def inputs(tmp_path):
    p,c=public_inputs();packet=tmp_path/'packet.json';config=tmp_path/'config.yaml'
    packet.write_text(json.dumps(p,indent=4)+'\n');config.write_bytes(c)
    return packet,config


def test_immutable_common_input_source_manifest_all_five_helpers_importable(tmp_path):
    packet,config=inputs(tmp_path);output=tmp_path/'architecture'
    manifest=prep.prepare(packet,config,output)
    workspace=Path(manifest['workspace'])
    names={s['relative_path'] for s in manifest['sources']}
    assert set(prep.HELPERS)<=names
    assert not names&prep.TREATMENT
    assert (workspace/'evidence.json').read_bytes()==packet.read_bytes()
    assert (workspace/'effective-configuration.yaml').read_bytes()==config.read_bytes()
    assert (workspace/'public-scope.json').read_bytes()==prep.SCOPE.read_bytes()
    assert prep.verify(output/'interface-manifest.json')==manifest
    probe=prep.probe_local_workspace(workspace,tmp_path/'scratch')
    assert probe['status']=='OFFLINE_HELPER_IMPORTS_AND_SCRATCH_PASS'
    assert probe['actual_transport_sandbox_verified'] is False
    assert manifest['call_readiness'] is False
    assert manifest['nav2_deployed_source_authentication']['status']=='NOT_AUTHENTICATED'
    with pytest.raises(FileExistsError):prep.prepare(packet,config,output)


@pytest.mark.parametrize('source',sorted(prep.TREATMENT))
def test_exact_full_treatment_modules_excluded(source):
    with pytest.raises(ValueError,match='excluded treatment'):prep.admitted(source)


@pytest.mark.parametrize('source',['analysis/reference_roboboat_temporal_v2.py',
    'packages/crane_ml/Assets/Scripts/Physics/RoboBoatDockingEvaluator.cs',
    'artifacts/old/responses/B4.json','analysis/judge_labels.py'])
def test_evaluator_references_and_answer_banks_excluded(source):
    with pytest.raises(ValueError):prep.admitted(source)


def test_undeclared_output_or_changed_snapshot_cannot_be_admitted(tmp_path):
    packet,config=inputs(tmp_path);output=tmp_path/'architecture';m=prep.prepare(packet,config,output)
    workspace=Path(m['workspace']);rogue=workspace/'B4.json';rogue.write_text('{}')
    with pytest.raises(ValueError,match='undeclared'):prep.verify(output/'interface-manifest.json')
    rogue.unlink();changed=workspace/prep.HELPERS[0];changed.chmod(0o644);changed.write_text('altered')
    with pytest.raises(ValueError,match='immutable input changed'):prep.verify(output/'interface-manifest.json')


def test_scratch_probe_does_not_claim_writes_to_source_workspace(tmp_path):
    packet,config=inputs(tmp_path);m=prep.prepare(packet,config,tmp_path/'architecture')
    with pytest.raises(ValueError,match='scratch must be separate'):
        prep.probe_local_workspace(m['workspace'],Path(m['workspace'])/'scratch')


def test_build_source_list_comparison_is_not_deployment_or_nav2_authentication(tmp_path):
    assets=[{'path':r.removeprefix('packages/crane_ml/'),'sha256':prep.digest(prep.ROOT/r)} for r in prep.ROBOT_FILES]
    manifest=tmp_path/'build.json';manifest.write_text(json.dumps({'schema':'crane-build-manifest-v1',
        'buildGuid':'construction-build','unityVersion':'construction','assets':assets}))
    audit=prep.build_source_audit(manifest)
    assert len(audit['matched_common_sources'])==len(prep.ROBOT_FILES)
    assert audit['status']=='SOURCE_LIST_COMPARISON_ONLY_NOT_DEPLOYMENT_AUTHENTICATION'
    assets[0]['sha256']='0'*64;manifest.write_text(json.dumps({'schema':'crane-build-manifest-v1',
        'buildGuid':'construction-build','unityVersion':'construction','assets':assets}))
    assert prep.build_source_audit(manifest)['mismatched_common_sources']==[prep.ROBOT_FILES[0]]


def test_unreviewed_generic_runner_cannot_enter_shared_source_bundle():
    with pytest.raises(ValueError,match='outside reviewed'):
        prep.admitted('analysis/run_roboboat_full_population_responses_v2.py')
