import copy
import pytest
from roboboat_public_configuration_judging_v1 import (build_packet,annotation_payload,
    adjudication_payload,BASIS,canonical_sha256,authenticated_basis)
from roboboat_temporal_certificate_v2 import certificate
from test_roboboat_full_population_support_v4 import prepare_partial


def construction(tmp_path):
    import json
    decl,out,d,availability,key=prepare_partial(tmp_path)
    return json.loads(next((out/'blind_packets').glob('*.json')).read_text())


def test_context_propagates_to_both_agents_and_disagreement_adjudicator_without_core_change(tmp_path):
    old=construction(tmp_path);new=build_packet(old,BASIS)
    assert new['response_text']==old['response_text']
    assert new['forms'][0]['packet_id']!=old['forms'][0]['packet_id']
    for before,after in zip(old['forms'],new['forms']):
        for name in ['robot_visible_evidence','atomic_statements','required_unit_coverage','limitation_preservation']:
            assert before[name]==after[name]
        assert certificate(before['robot_visible_evidence'])==certificate(after['robot_visible_evidence'])
    contexts=[annotation_payload(new,s)['form']['public_configuration_context'] for s in ['A','B']]
    handoff={'packet_id':new['forms'][0]['packet_id'],'packet_set_sha256':canonical_sha256(new)}
    assert adjudication_payload(new,handoff)['blinded_form']['public_configuration_context']==contexts[0]==contexts[1]
    assert contexts[0]['configuration_basis']['internal-consumption-of-odometry-proven'] is False


@pytest.mark.parametrize('attack',['basis','top_join','form_method','context'])
def test_altered_basis_and_identity_leaks_rejected(tmp_path,attack):
    old=construction(tmp_path);basis=copy.deepcopy(BASIS)
    if attack=='basis':basis['goal_checker_values']='controller-consumed'
    elif attack=='top_join':old['evaluator_join']={}
    elif attack=='form_method':old['forms'][0]['method']='hidden'
    else:
        new=build_packet(old,basis);new['forms'][0]['public_configuration_context']['configuration_basis']['goal_checker_values']='invented'
        with pytest.raises(ValueError):annotation_payload(new,'A')
        return
    with pytest.raises(ValueError):build_packet(old,basis)


def test_wrong_adjudication_binding_rejected(tmp_path):
    new=build_packet(construction(tmp_path),BASIS)
    with pytest.raises(ValueError):adjudication_payload(new,{'packet_id':'old','packet_set_sha256':'wrong'})


def test_nested_core_join_cannot_reach_any_judge(tmp_path):
    old=construction(tmp_path)
    for form in old['forms']: form['robot_visible_evidence']['evaluator_join']={}
    with pytest.raises(ValueError):build_packet(old,BASIS)


def test_original_declaration_basis_and_source_hashes_authenticated(tmp_path):
    import json
    from pathlib import Path
    import run_roboboat_full_population_responses_v2 as original
    from run_roboboat_population_responses_v1 import binding
    value={'schema':'roboboat-full-population-response-declaration/v2',
           'disposition':'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE',
           'configuration_basis':BASIS,'runner':binding(Path(original.__file__)),
           'prompt':binding(original.PROMPT),'method_sources':[]}
    path=tmp_path/'construction-original-declaration.json';path.write_text(json.dumps(value))
    basis,inputs=authenticated_basis(path)
    assert basis==BASIS and inputs[0]['path']==str(path.resolve())
    value['runner']['sha256']='0'*64;path.write_text(json.dumps(value))
    with pytest.raises(ValueError):authenticated_basis(path)


def test_engineering_lock_requires_original_binding_and_complete_runtime_closure(tmp_path):
    import json
    from pathlib import Path
    import roboboat_public_configuration_judging_v1 as builder
    from roboboat_runtime_source_closure_v1 import source_closure
    from run_roboboat_population_responses_v1 import binding
    original=tmp_path/'original.json';original.write_text('{}')
    lock={'schema':'roboboat-public-configuration-engineering-lock/v1',
          'calls_authorized':False,'qualification_status':'PENDING_BALANCED_CONSTRUCTION_QUALIFICATION',
          'original_response_declarations':[binding(original)],
          'dependencies':[binding(p) for p in source_closure([Path(builder.__file__)])]}
    path=tmp_path/'lock.json';path.write_text(json.dumps(lock))
    assert builder.verify_source_lock(path,original)['calls_authorized'] is False
    lock['dependencies']=[];path.write_text(json.dumps(lock))
    with pytest.raises(ValueError,match='closure'):builder.verify_source_lock(path,original)
