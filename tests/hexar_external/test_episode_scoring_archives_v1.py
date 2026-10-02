import copy
import json
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.episode_scoring_archives_v1 import (
    bounded,cohort_index,scoring_artifacts,write_episode,read_episode,episode_plan,
)
from analysis.hexar_external.confirmatory_v1.journal import fingerprint

BASE=Path(__file__).resolve().parents[2]/'manifests/hexar_external/confirmatory_v1/development_episode_scoring_replay_v1'


def fixture():
    pointer=json.loads((BASE/'cohort_index.json').read_text())['records'][0]
    root_index=json.loads((BASE/'cohort_index.json').read_text())
    _,values=read_episode(BASE/pointer['relative_path'],pointer['episode_index_sha256'],root_index['study_binding_sha256'],'development_qualification')
    return values


def test_bounded_episode_roundtrip_rejects_reference_tampering(tmp_path):
    values=fixture();index=write_episode(tmp_path/'episode',values,'a'*64,'development_qualification')
    assert read_episode(tmp_path/'episode',fingerprint(index),'a'*64,'development_qualification')[1]==values
    p=tmp_path/'episode/neutral_reference_registry.json';p.write_text('{}')
    with pytest.raises(ValueError,match='artifact changed'):read_episode(tmp_path/'episode',fingerprint(index),'a'*64,'development_qualification')


def test_development_archive_never_matches_confirmation_identity(tmp_path):
    values=fixture();index=write_episode(tmp_path/'episode',values,'a'*64,'development_qualification')
    with pytest.raises(ValueError,match='index/binding changed'):
        read_episode(tmp_path/'episode',fingerprint(index),'a'*64,'confirmation')
    assert index['dispatch_authorized'] is False


def test_episode_archive_creation_is_exclusive(tmp_path):
    values=fixture();write_episode(tmp_path/'episode',values,'a'*64,'development_qualification')
    with pytest.raises(FileExistsError):write_episode(tmp_path/'episode',values,'a'*64,'development_qualification')


def test_no_truncation_when_complete_artifact_exceeds_bound():
    with pytest.raises(ValueError,match='exceeds fixed bound'):bounded(dict(complete='x'*100),10)


@pytest.mark.parametrize('field',['episode_id','relative_path','episode_index_sha256'])
def test_duplicate_episode_pointer_fields_reject_cluster_inflation(field):
    a=dict(episode_id='e1',relative_path='p1',episode_index_sha256='a'*64)
    b=dict(episode_id='e2',relative_path='p2',episode_index_sha256='b'*64);b[field]=a[field]
    with pytest.raises(ValueError,match='duplicate independent episode'):cohort_index([a,b],'f'*64,'development_qualification')


@pytest.mark.parametrize('path',['../outside','/outside'])
def test_cohort_pointers_cannot_escape_root(path):
    with pytest.raises(ValueError,match='safe relative'):
        cohort_index([dict(episode_id='e',relative_path=path,episode_index_sha256='a'*64)],'f'*64,'development_qualification')


def test_fresh_episode_builder_protects_whole_battery_and_equal_packets():
    entries=fixture()['neutral_reference_registry.json']['entries']
    plain=[{k:r[k] for k in ('episode_id','job_id','packet','reference')} for r in entries]
    neutral,plan=episode_plan(plain,{'HX-CONTRACT':dict(mode='fixture-contract'),'HX-PROMPT':dict(mode='fixture-strong-prompt')})
    assert plan['unique_requests']==12 and plan['battery_cells']==18 and len(neutral['entries'])==9
    with pytest.raises(ValueError,match='all nine'):episode_plan(plain[:-1],{'HX-CONTRACT':dict(mode='c'),'HX-PROMPT':dict(mode='p')})


def test_public_per_episode_jobs_omit_method_episode_and_prior_labels():
    values=fixture();public=values['public_scoring_plan.json']
    for job in public['initial_jobs']+public['reserved_C_jobs']:
        assert set(job['payload'])=={'question','visible_evidence','required_units','answer'}
        raw=json.dumps(job)
        assert 'HX-PROMPT' not in raw and 'HX-CONTRACT' not in raw and 'hexar-tiago-dev-' not in raw


def test_archives_remain_independent_under_shared_blinding_master():
    values=fixture();args=(values['neutral_reference_registry.json'],values['unique_method_plan.json'],values['method_outputs.json'])
    a=scoring_artifacts(*args,b'a'*32,1);b=scoring_artifacts(*args,b'b'*32,1)
    assert a['public_scoring_plan.json']['initial_jobs'][0]['opaque_job']!=b['public_scoring_plan.json']['initial_jobs'][0]['opaque_job']
    assert a['method_outputs.json']==b['method_outputs.json']
