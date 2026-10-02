import hashlib
import pytest
import roboboat_player_cpu_affinity_v1 as wrapper


def test_affinity_applied_before_exact_unchanged_player_exec(tmp_path,monkeypatch):
    player=tmp_path/'physical';player.write_bytes(b'immutable')
    monkeypatch.setattr(wrapper,'PLAYER',player)
    monkeypatch.setattr(wrapper,'PLAYER_SHA256',hashlib.sha256(player.read_bytes()).hexdigest())
    state={'affinity':set(range(20))}
    monkeypatch.setattr(wrapper.os,'sched_getaffinity',lambda pid:state['affinity'])
    monkeypatch.setattr(wrapper.os,'sched_setaffinity',lambda pid,cpus:state.update(affinity=cpus))
    monkeypatch.setattr(wrapper.os,'execv',lambda path,args:state.update(path=path,args=args))
    wrapper.launch(['-screen-width','640','--crane-duration','340'])
    assert state['affinity']==set(range(16))
    assert state['path']==str(player)
    assert state['args']==[str(player),'-screen-width','640','--crane-duration','340']


def test_changed_physical_player_never_launched(tmp_path,monkeypatch):
    player=tmp_path/'physical';player.write_bytes(b'changed')
    monkeypatch.setattr(wrapper,'PLAYER',player)
    monkeypatch.setattr(wrapper.os,'sched_getaffinity',lambda pid:set(range(20)))
    monkeypatch.setattr(wrapper.os,'execv',lambda *args:pytest.fail('changed player launched'))
    with pytest.raises(RuntimeError,match='player changed'):wrapper.launch([])
