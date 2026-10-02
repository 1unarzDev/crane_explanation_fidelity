"""Construction fidelity only: source context, blinding and provenance, no scoring."""
import copy
import json
from pathlib import Path
import pytest
import roboboat_public_source_judging_v2 as judge
from test_roboboat_public_configuration_judging_v1 import construction

MANIFEST=Path('/home/lunarz/worktrees/roboboat-terminal-evidence/artifacts/roboboat-clock-baseline-interface-v3-001/L0/interface-manifest.json')


def packet(tmp_path):
    p=construction(tmp_path)
    m=json.loads(MANIFEST.read_text());evidence=json.loads((Path(m['workspace'])/'evidence.json').read_text())
    # The old fixture supplies annotation structure only. Substitution creates
    # a transport construction; its inventory is never judged or scientifically scored.
    for f in p['forms']:f['robot_visible_evidence']=copy.deepcopy(evidence)
    return p


def test_source_context_identical_for_two_judges_and_adjudicator_without_core_change(tmp_path):
    old=packet(tmp_path);new=judge.build_packet(old,MANIFEST)
    assert new['response_text']==old['response_text']
    for before,after in zip(old['forms'],new['forms']):
        for key in ('robot_visible_evidence','atomic_statements','required_unit_coverage','limitation_preservation'):
            assert before[key]==after[key]
    a=judge.annotation_payload(new,'A')['form']['public_source_context'];b=judge.annotation_payload(new,'B')['form']['public_source_context']
    handoff={'packet_id':new['forms'][0]['packet_id'],'packet_set_sha256':judge.canonical_sha256(new)}
    assert judge.adjudication_payload(new,handoff)['blinded_form']['public_source_context']==a==b
    assert len(a['files'])==45
    assert not {x['relative_path'] for x in a['files']}&judge.common.TREATMENT
    assert 'does not establish' in a['scope']
    assert new['forms'][0]['public_configuration_context']['configuration_basis']['internal-consumption-of-odometry-proven'] is False
    source_basis=json.loads(next(f for f in a['files'] if f['relative_path']=='robot-source-basis.json')['text'])
    assert source_basis['deployment_wiring_proven'] is False


def test_wrong_evidence_condition_cannot_borrow_source_context(tmp_path):
    p=packet(tmp_path)
    for f in p['forms']:f['robot_visible_evidence']['action']['status']='aborted'
    with pytest.raises(ValueError,match='another evidence condition'):judge.build_packet(p,MANIFEST)


@pytest.mark.parametrize('fault',['bytes','missing_file','identity','unequal_context'])
def test_altered_sources_missingness_and_join_leaks_cannot_reach_judges(tmp_path,fault):
    p=judge.build_packet(packet(tmp_path),MANIFEST)
    if fault=='bytes':p['forms'][0]['public_source_context']['files'][0]['text']+='modified'
    if fault=='missing_file':
        for f in p['forms']:
            c=f['public_source_context'];c['files'].pop();c['source_set_sha256']=judge.canonical_sha256(c['files'])
    if fault=='identity':p['forms'][0]['public_source_context']['method_identity']='B4'
    if fault=='unequal_context':p['forms'][0]['public_source_context']['scope']='different'
    with pytest.raises(ValueError):judge.annotation_payload(p,'A')


def test_immutable_receipt_authenticates_actual_common_manifest_not_only_in_packet_hashes(tmp_path):
    p=packet(tmp_path);original=tmp_path/'original.json';original.write_text(json.dumps(p));target=tmp_path/'new.json';receipt=tmp_path/'receipt.json'
    r=judge.prepare(original,MANIFEST,target,receipt)
    assert r['calls_authorized']is False and r['scores_released']is False and r['independent_n_added']==0
    assert judge.verify_receipt(receipt)==r
    with pytest.raises(FileExistsError):judge.prepare(original,MANIFEST,target,receipt)
    changed=json.loads(target.read_text())
    for f in changed['forms']:
        c=f['public_source_context'];c['files'][0]['text']+='change';c['files'][0]['sha256']=__import__('hashlib').sha256(c['files'][0]['text'].encode()).hexdigest();c['source_set_sha256']=judge.canonical_sha256(c['files'])
    target.write_text(json.dumps(changed))
    with pytest.raises(ValueError):judge.verify_receipt(receipt)
    # Even recomputing an in-packet hash and its outer file binding does not
    # authenticate altered source bytes against the actual common workspace.
    r['new_packet']=judge.binding(target);receipt.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='authenticated common workspace'):judge.verify_receipt(receipt)


def test_adjudication_cannot_use_another_packet_handoff(tmp_path):
    p=judge.build_packet(packet(tmp_path),MANIFEST)
    with pytest.raises(ValueError,match='packet mismatch'):judge.adjudication_payload(p,{'packet_id':'wrong','packet_set_sha256':'wrong'})


def test_runtime_source_closure_cannot_be_omitted_from_authentication(tmp_path):
    original=tmp_path/'original.json';original.write_text(json.dumps(packet(tmp_path)));target=tmp_path/'new.json';receipt=tmp_path/'receipt.json'
    r=judge.prepare(original,MANIFEST,target,receipt);r['source_closure']=[];receipt.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='complete source-context runtime closure'):judge.verify_receipt(receipt)
