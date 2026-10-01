import copy
import json
from pathlib import Path
import pytest
from analysis.hexar_external.acquisition.public_context import extend,MANIFEST,ROOT


def test_public_source_does_not_displace_evidence_or_expose_hidden_episode_metadata():
    packet=dict(question='Why could you not finish?',evidence={'charging_state':[{'value':True}]},
                source_context={'indicator_semantics':'No governing source supplied','event_scope':'bounded logs'})
    original=copy.deepcopy(packet);updated=extend(packet)
    assert packet==original
    assert updated['evidence']==original['evidence'] and updated['question']==original['question']
    config=updated['source_context']['controller_configuration']
    assert config['locks_yaml']==(MANIFEST.parent/'twist_mux_locks.yaml').read_text()
    assert config['topics_yaml']==(MANIFEST.parent/'twist_mux_topics.yaml').read_text()
    assert 'not proof of a human' in updated['source_context']['indicator_semantics']
    assert 'equal/higher-priority' in updated['source_context']['controller_source_scope']
    assert 'No per-episode runtime' in updated['source_context']['controller_source_scope']
    assert not any(k in config for k in ('family','method','hidden_intervention','expected_winner'))


def test_modified_controller_config_is_rejected(tmp_path):
    manifest=json.loads(MANIFEST.read_text())
    for path in manifest['files']:
        destination=tmp_path/path;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes((ROOT/path).read_bytes()+b'changed')
    p=tmp_path/'manifest.json';p.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='source changed'):
        extend(dict(source_context={}),p,tmp_path)
