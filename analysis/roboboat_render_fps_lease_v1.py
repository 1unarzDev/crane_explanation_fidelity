"""Reference-counted compositor FPS ownership, compatible with legacy collectors.

New render workers retain a shared legacy render lock and a unique process/start
lease. Only the first lease changes FPS; only the last restores the original.
No compositor command is invoked by importing this module.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid


def process_identity(pid):
    try:
        raw = Path(f'/proc/{pid}/stat').read_text()
        fields = raw[raw.rfind(')') + 2:].split()
        if fields[0] == 'Z':
            return None
        return {'pid': pid, 'start': int(fields[19])}
    except (OSError, ValueError, IndexError):
        return None


class FPSLease:
    def __init__(self, read_fps, write_fps, *, gate='/tmp/crane-roboboat-population-render.lock',
                 directory=None, desired=60, identity=process_identity):
        if type(desired) is not int or desired < 0:
            raise ValueError('nonnegative integer FPS required')
        self.read_fps, self.write_fps = read_fps, write_fps
        self.gate_path = Path(gate)
        self.scope = hashlib.sha256(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', 'test-no-compositor').encode()).hexdigest()
        self.directory = Path(directory or f'/tmp/crane-roboboat-render-fps-{os.getuid()}-{self.scope[:16]}')
        self.desired, self.identity = desired, identity
        self.owner = identity(os.getpid())
        if self.owner is None:
            raise RuntimeError('own process identity unavailable')
        self.owner = {**self.owner, 'nonce': uuid.uuid4().hex}
        self.gate = None
        self.active = False

    def _load(self):
        path = self.directory / 'state.json'
        if not path.exists():
            return None
        state = json.loads(path.read_text())
        if (state.get('schema') != 'roboboat-render-fps-leases/v1' or
                state.get('compositor_scope_sha256') != self.scope or
                state.get('phase') != 'ACTIVE' or type(state.get('original_fps')) is not int or
                type(state.get('desired_fps')) is not int or not isinstance(state.get('owners'), list)):
            raise RuntimeError('unfinished or invalid FPS lease state; retained for recovery')
        if state['desired_fps'] != self.desired or not state['owners']:
            raise RuntimeError('incompatible or empty active FPS lease state')
        seen = set()
        for owner in state['owners']:
            if set(owner) != {'pid', 'start', 'nonce'} or owner['nonce'] in seen:
                raise RuntimeError('invalid lease owner records')
            seen.add(owner['nonce'])
            actual = self.identity(owner['pid'])
            if actual is None or actual != {'pid': owner['pid'], 'start': owner['start']}:
                raise RuntimeError('abandoned FPS lease retained; no automatic PID reuse or restore')
        return state

    def _save(self, state):
        fd, name = tempfile.mkstemp(prefix='state-', dir=self.directory)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(state, stream, indent=2); stream.write('\n')
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name, self.directory / 'state.json')
        finally:
            Path(name).unlink(missing_ok=True)

    def _verify_fps(self, expected):
        actual = self.read_fps()
        if type(actual) is not int or actual != expected:
            raise RuntimeError('compositor FPS readback differs from owned setting')

    def acquire(self):
        if self.active or self.gate is not None:
            raise RuntimeError('one acquisition per active lease')
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink() or self.directory.stat().st_uid != os.getuid():
            raise RuntimeError('FPS state directory ownership mismatch')
        self.gate = self.gate_path.open('a')
        try:
            # Legacy collectors hold LOCK_EX for their whole run. This blocks
            # before touching FPS, yet permits multiple new workers together.
            fcntl.flock(self.gate, fcntl.LOCK_SH)
            with (self.directory / 'transition.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                state = self._load()
                if state is None:
                    original = self.read_fps()
                    if type(original) is not int:
                        raise RuntimeError('integer compositor FPS readback required')
                    state = {'schema': 'roboboat-render-fps-leases/v1', 'phase': 'STARTING',
                             'compositor_scope_sha256': self.scope,
                             'original_fps': original, 'desired_fps': self.desired, 'owners': [self.owner]}
                    # Preserve original before changing global state, including
                    # failed transitions. An interrupted transition is not erased.
                    self._save(state)
                    self.write_fps(self.desired)
                    self._verify_fps(self.desired)
                    state['phase'] = 'ACTIVE'
                else:
                    self._verify_fps(self.desired)
                    state['owners'].append(self.owner)
                self._save(state)
                self.active = True
                return {'owner': self.owner, 'original_fps': state['original_fps'],
                        'desired_fps': self.desired, 'active_owners': len(state['owners']),
                        'compatibility_gate': str(self.gate_path)}
        except BaseException:
            self.gate.close(); self.gate = None
            raise

    def release(self):
        if not self.active or self.gate is None:
            raise RuntimeError('active owned lease required for release')
        try:
            with (self.directory / 'transition.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                state = self._load()
                if state is None or self.owner not in state['owners']:
                    raise RuntimeError('exact owned lease missing; refuse restore')
                self._verify_fps(self.desired)
                remaining = [owner for owner in state['owners'] if owner != self.owner]
                if remaining:
                    state['owners'] = remaining
                    self._save(state)
                    return {'remaining_owners': len(remaining), 'original_restored': False, 'fps': self.desired}
                state['phase'] = 'RESTORING'
                self._save(state)
                self.write_fps(state['original_fps'])
                self._verify_fps(state['original_fps'])
                (self.directory / 'state.json').unlink()
                return {'remaining_owners': 0, 'original_restored': True, 'fps': state['original_fps']}
        finally:
            # A failed release retains its on-disk evidence and refuses future
            # acquisitions. It never silently discards an unresolved owner.
            self.active = False
            self.gate.close(); self.gate = None
