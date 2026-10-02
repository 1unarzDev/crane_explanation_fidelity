import json
from pathlib import Path
import pytest
import prepare_roboboat_baseline_interface_v4 as prep
from test_roboboat_shared_public_scope_v1 import public_inputs

AUDIT=prep.ROOT/'artifacts/roboboat-command-shutdown-v17/compiled-source-audit-v5.json'
BUILD=prep.ROOT/'artifacts/roboboat-command-shutdown-v17/full-build-v1.json'


def prepare(tmp_path):
    p,c=public_inputs();packet=tmp_path/'packet.json';packet.write_text(json.dumps(p));config=tmp_path/'config.yaml';config.write_bytes(c)
    out=tmp_path/'interface';m=prep.prepare(packet,config,out,compiled_audit=AUDIT,build_manifest=BUILD)
    return m,out


def test_sources_match_actual_version_and_configuration_basis_is_common(tmp_path):
    m,out=prepare(tmp_path);workspace=Path(m['workspace'])
    assert m['compiled_common_sources']==38 and m['call_readiness'] is False and m['baseline_promotion'] is False
    assert json.loads((workspace/'configuration-basis.json').read_text())==prep.BASIS
    assert not {r['relative_path'] for r in m['sources']}&prep.TREATMENT
    relative='packages/crane_ml/Assets/Scripts/Utils/Performance/CraneActionGate.cs'
    actual=prep.EXPERIMENTAL_PROJECT/'Assets/Scripts/Utils/Performance/CraneActionGate.cs'
    assert (workspace/relative).read_bytes()==actual.read_bytes()
    assert actual.read_bytes()!=(prep.ROOT/relative).read_bytes()
    assert prep.verify(out/'interface-manifest.json')==m
    assert m['deployment_wiring_proven'] is False and m['nav2_deployed_source_authentication']=='NOT_AUTHENTICATED'
    with pytest.raises(FileExistsError):prep.prepare(tmp_path/'packet.json',tmp_path/'config.yaml',out,compiled_audit=AUDIT,build_manifest=BUILD)

@pytest.mark.parametrize('source',['analysis/roboboat_full_crane_v3.py','configs/roboboat_claim_contracts_v3_development.json','analysis/reference_roboboat_temporal_v2.py'])
def test_treatment_and_evaluator_cannot_enter_common_namespace(source):
    with pytest.raises(ValueError):prep.admitted(source)


def test_changed_compiled_document_cannot_be_replaced_by_a_match_status_label(tmp_path):
    a=json.loads(AUDIT.read_text())
    for r in a['records']:
        if r.get('status')=='MATCHED_METADATA' and any(d.get('relative')=='Assets/Scripts/Utils/Performance/CraneActionGate.cs' for d in r.get('source_documents',[])):
            for d in r['source_documents']:
                if d.get('relative')=='Assets/Scripts/Utils/Performance/CraneActionGate.cs':d['document']['checksum']='0'*64
    path=tmp_path/'audit.json';path.write_text(json.dumps(a))
    with pytest.raises(ValueError,match='document checksum'):prep.compiled_source_bindings(path,BUILD)


def test_answer_injection_and_basis_mutation_fail_verification(tmp_path):
    m,out=prepare(tmp_path);workspace=Path(m['workspace']);rogue=workspace/'B4.json';rogue.write_text('{}')
    with pytest.raises(ValueError,match='undeclared'):prep.verify(out/'interface-manifest.json')
    rogue.unlink();basis=workspace/'configuration-basis.json';basis.chmod(0o644);basis.write_text('{}')
    with pytest.raises(ValueError,match='immutable input changed'):prep.verify(out/'interface-manifest.json')


def test_old_platform_cannot_be_relabelled_as_repaired():
    old_audit=prep.ROOT/'artifacts/roboboat-action-timing-v9/compiled-document-source-audit-root-v1.json'
    old_build=prep.ROOT/'artifacts/roboboat-action-timing-v9/full-build-root-v1.json'
    with pytest.raises(ValueError,match='compiled audit|command-shutdown-v17 platform'):
        prep.compiled_source_bindings(old_audit,old_build)


def test_publisher_sources_include_real_epoch_repair(tmp_path):
    m,out=prepare(tmp_path);workspace=Path(m['workspace'])
    for name in ('Controllers/CraneROSNavigationState.cs','Utils/ROS/ROSClock.cs'):
        relative='packages/crane_ml/Assets/Scripts/'+name
        data=(workspace/relative).read_bytes()
        assert data==(prep.EXPERIMENTAL_PROJECT/'Assets/Scripts'/name).read_bytes()
        assert data!=(Path('/home/lunarz/worktrees/roboboat-action-timing-v9/crane_ml/Assets/Scripts')/name).read_bytes()
        assert b'publisherEpisodeId' in data
    basis=json.loads((workspace/'robot-source-basis.json').read_text())
    assert 'EpisodeId' in basis['experimental_version']
    assert basis['deployment_wiring_proven'] is False


def test_new_shutdown_and_start_sources_are_equal_common_inputs_without_promotion(tmp_path):
    m,out=prepare(tmp_path);workspace=Path(m['workspace'])
    for suffix in ('Controllers/RoboBoatInitialPose.cs', 'Performance/CraneCaptureCompletion.cs',
                   'Performance/CraneBenchmarkRunner.cs', 'Controllers/ROSOmniXCommand.cs'):
        relative='packages/crane_ml/Assets/Scripts/'+suffix
        assert (workspace/relative).read_bytes()==(prep.EXPERIMENTAL_PROJECT/'Assets/Scripts'/suffix).read_bytes()
    assert b'command_intake_shutdown' in (workspace/'packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs').read_bytes()
    assert m['packet_platform_authenticated'] is False
    assert m['operational_platform_qualified_by_preparation'] is False
    manifest=out/'interface-manifest.json';m['packet_platform_authenticated']=True
    manifest.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='prepared development'):prep.verify(manifest)


def test_prior_completion_platform_cannot_be_substituted_for_shutdown_build():
    with pytest.raises(ValueError,match='imported compiler root|command-shutdown-v17 platform'):
        prep.compiled_source_bindings(prep.ROOT/'artifacts/roboboat-capture-complete-v15/compiled-source-audit-v4.json',
            prep.ROOT/'artifacts/roboboat-capture-complete-v15/full-build-v1.json')
