import fcntl
import json
import multiprocessing
import os
from pathlib import Path

import pytest
from roboboat_render_fps_lease_v1 import FPSLease, process_identity


def lease(tmp_path, state, **kw):
    def write(value):
        state['writes'].append(value); state['fps'] = value
    return FPSLease(lambda: state['fps'], write, gate=tmp_path / 'gate',
                    directory=tmp_path / 'leases', **kw)


def test_first_changes_and_last_restores_for_overlapping_workers(tmp_path):
    state = {'fps': 13, 'writes': []}
    a, b = lease(tmp_path, state), lease(tmp_path, state)
    assert a.acquire()['active_owners'] == 1
    assert b.acquire()['active_owners'] == 2
    assert state['writes'] == [60]
    assert a.release() == {'remaining_owners': 1, 'original_restored': False, 'fps': 60}
    assert state['fps'] == 60 and state['writes'] == [60]
    assert b.release() == {'remaining_owners': 0, 'original_restored': True, 'fps': 13}
    assert state['writes'] == [60, 13]
    assert not (tmp_path / 'leases/state.json').exists()


def test_reverse_finish_order_and_zero_original_fps(tmp_path):
    state = {'fps': 0, 'writes': []}
    a, b = lease(tmp_path, state), lease(tmp_path, state)
    a.acquire(); b.acquire(); b.release()
    assert state['fps'] == 60
    a.release(); assert state['fps'] == 0
    with pytest.raises(RuntimeError, match='active owned'):
        a.release()


def test_external_setting_change_is_retained_without_overwrite(tmp_path):
    state = {'fps': 0, 'writes': []}; a = lease(tmp_path, state)
    a.acquire(); state['fps'] = 37
    with pytest.raises(RuntimeError, match='readback'):
        a.release()
    assert state['writes'] == [60] and state['fps'] == 37
    assert (tmp_path / 'leases/state.json').exists()
    with pytest.raises(RuntimeError, match='readback'):
        lease(tmp_path, state).acquire()


def test_interrupted_first_transition_is_not_erased(tmp_path):
    state = {'fps': 0, 'writes': []}
    a = FPSLease(lambda: 0, lambda value: None, gate=tmp_path / 'gate', directory=tmp_path / 'leases')
    with pytest.raises(RuntimeError, match='readback'):
        a.acquire()
    record = json.loads((tmp_path / 'leases/state.json').read_text())
    assert record['phase'] == 'STARTING' and record['original_fps'] == 0
    with pytest.raises(RuntimeError, match='unfinished'):
        lease(tmp_path, state).acquire()
    assert state['writes'] == []


def test_pid_reuse_does_not_grant_lease_ownership(tmp_path):
    state = {'fps': 0, 'writes': []}; a = lease(tmp_path, state); a.acquire()
    a.identity = lambda pid: {'pid': pid, 'start': a.owner['start'] + 1}
    with pytest.raises(RuntimeError, match='abandoned'):
        a.release()
    assert state['writes'] == [60]


def test_incompatible_fps_request_leaves_active_workers_unchanged(tmp_path):
    state = {'fps': 9, 'writes': []}; a = lease(tmp_path, state); a.acquire()
    with pytest.raises(RuntimeError, match='incompatible'):
        lease(tmp_path, state, desired=30).acquire()
    assert state['writes'] == [60]
    a.release(); assert state['fps'] == 9


def child_acquire(tmp_path, events):
    state = {'fps': 7, 'writes': []}; a = lease(Path(tmp_path), state)
    events.put('before'); a.acquire(); events.put(('acquired', state['writes']))
    a.release(); events.put(('released', state['fps']))


def test_real_process_waits_for_legacy_exclusive_gate_before_mutation(tmp_path):
    context = multiprocessing.get_context('spawn'); events = context.Queue()
    with (tmp_path / 'gate').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        process = context.Process(target=child_acquire, args=(str(tmp_path), events)); process.start()
        assert events.get(timeout=5) == 'before'
        assert not (tmp_path / 'leases/state.json').exists()
        fcntl.flock(lock, fcntl.LOCK_UN)
    assert events.get(timeout=5) == ('acquired', [60])
    assert events.get(timeout=5) == ('released', 7)
    process.join(timeout=5); assert process.exitcode == 0


def test_own_identity_is_live_linux_process():
    identity = process_identity(os.getpid())
    assert identity['pid'] == os.getpid() and identity['start'] > 0
    assert process_identity(-1) is None


def overlap_worker(tmp, events, commands):
    tmp = Path(tmp)
    def read():
        return int((tmp / 'fps').read_text())
    def write(value):
        (tmp / 'fps').write_text(str(value))
        with (tmp / 'writes').open('a') as stream:
            stream.write(str(value) + '\n')
    owner = FPSLease(read, write, gate=tmp / 'gate', directory=tmp / 'leases')
    acquired = owner.acquire(); events.put(('acquired', acquired))
    assert commands.get(timeout=5) == 'release'
    events.put(('released', owner.release()))


def test_two_real_processes_overlap_without_premature_global_restore(tmp_path):
    (tmp_path / 'fps').write_text('11')
    context = multiprocessing.get_context('spawn')
    events = [context.Queue(), context.Queue()]; commands = [context.Queue(), context.Queue()]
    workers = [context.Process(target=overlap_worker, args=(str(tmp_path), events[i], commands[i])) for i in range(2)]
    try:
        workers[0].start(); first = events[0].get(timeout=5)
        assert first[0] == 'acquired' and first[1]['active_owners'] == 1
        workers[1].start(); second = events[1].get(timeout=5)
        assert second[0] == 'acquired' and second[1]['active_owners'] == 2
        assert first[1]['owner']['pid'] != second[1]['owner']['pid']
        commands[0].put('release'); released = events[0].get(timeout=5)
        assert released[1]['original_restored'] is False
        assert (tmp_path / 'fps').read_text() == '60'
        commands[1].put('release'); released = events[1].get(timeout=5)
        assert released[1]['original_restored'] is True
        assert (tmp_path / 'fps').read_text() == '11'
        assert (tmp_path / 'writes').read_text().splitlines() == ['60', '11']
        for process in workers:
            process.join(timeout=5); assert process.exitcode == 0
    finally:
        for process in workers:
            if process.pid is not None and process.is_alive():
                process.terminate(); process.join(timeout=5)


def test_other_compositor_scope_cannot_reuse_same_state_directory(tmp_path, monkeypatch):
    state = {'fps': 0, 'writes': []}
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE', 'first')
    a = lease(tmp_path, state); a.acquire()
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE', 'second')
    with pytest.raises(RuntimeError, match='invalid FPS'):
        lease(tmp_path, state).acquire()
    assert state['writes'] == [60]
    a.release()
