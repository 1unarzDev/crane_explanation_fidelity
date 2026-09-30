"""Development service-backed computation candidate; existing callers stay unchanged."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import uuid

from evidence_calibration_local_tool_sandbox_v2 import ExecutionFailure, Limits, command as namespace_command
from observe_evidence_calibration_cgroup_limits import write_once
from stage_evidence_calibration_workspace import verify


@dataclass(frozen=True)
class TreeLimits:
    memory_bytes: int
    tasks: int
    cpu_rate_percent: int

    def __post_init__(self):
        for field, low, high in [('memory_bytes', 64 * 1024**2, 8 * 1024**3),
                                 ('tasks', 8, 256), ('cpu_rate_percent', 1, 400)]:
            value = getattr(self, field)
            if type(value) is not int or not low <= value <= high:
                raise ValueError('invalid explicit tree limit: ' + field)



@dataclass(frozen=True)
class ScratchLimits:
    temporary_bytes: int
    shared_memory_bytes: int

    def __post_init__(self):
        for field in ('temporary_bytes', 'shared_memory_bytes'):
            value = getattr(self, field)
            if type(value) is not int or not 64 * 1024 <= value <= 256 * 1024**2 or value % 4096:
                raise ValueError('invalid explicit page-aligned scratch limit: ' + field)


def bounded_namespace_command(workspace: Path, identity: dict, python_arguments: list[str],
                              limits: Limits, scratch_limits: ScratchLimits) -> list[str]:
    if not isinstance(scratch_limits, ScratchLimits):
        raise ValueError('explicit ScratchLimits required')
    argv = namespace_command(workspace, identity, python_arguments, limits)
    index = argv.index('--tmpfs')
    if argv[index + 1] != '/tmp':
        raise ValueError('registered namespace scratch layout differs')
    argv[index:index + 2] = ['--size', str(scratch_limits.temporary_bytes), '--tmpfs', '/tmp']
    separator = argv.index('--')
    argv[separator:separator] = ['--size', str(scratch_limits.shared_memory_bytes), '--tmpfs', '/dev/shm',
                               '--remount-ro', '/dev', '--remount-ro', '/', '--disable-userns']
    return argv

def command(workspace: Path, identity: dict, python_arguments: list[str], limits: Limits,
            tree_limits: TreeLimits, scratch_limits: ScratchLimits, unit: str) -> list[str]:
    if not isinstance(tree_limits, TreeLimits):
        raise ValueError('explicit TreeLimits required')
    if not unit.startswith('crane-compute-') or len(unit) != 46 or any(
            char not in '0123456789abcdef' for char in unit[14:]):
        raise ValueError('registered fresh service identity required')
    return ['/usr/bin/systemd-run', '--user', '--quiet', '--wait', '--pipe', '--expand-environment=no', '--unit=' + unit,
            '-p', f'MemoryMax={tree_limits.memory_bytes}', '-p', 'MemorySwapMax=0',
            '-p', f'TasksMax={tree_limits.tasks}', '-p', f'CPUQuota={tree_limits.cpu_rate_percent}%',
            '-p', 'OOMPolicy=kill', '-p', f'RuntimeMaxSec={limits.wall_seconds}s',
            '-p', 'TimeoutStopSec=1s', '-p', 'KillMode=control-group',
            *bounded_namespace_command(workspace, identity, python_arguments, limits, scratch_limits)]


def _environment() -> dict:
    return {key: os.environ[key] for key in ('PATH', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')
            if key in os.environ}


def _control(environment: dict, unit: str, *arguments: str) -> dict:
    result = subprocess.run(['/usr/bin/systemctl', '--user', *arguments, unit], env=environment,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=5)
    return {'return_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def run(workspace: Path, identity: dict, python_arguments: list[str], *, limits: Limits,
        tree_limits: TreeLimits, scratch_limits: ScratchLimits, event_directory: Path) -> subprocess.CompletedProcess:
    """Retain one-shot intent/terminal; partial output is audit only, never tool success."""
    workspace = workspace.resolve()
    if event_directory.resolve() == workspace or workspace in event_directory.resolve().parents:
        raise ValueError('event directory must be outside the method workspace')
    unit = 'crane-compute-' + uuid.uuid4().hex
    argv = command(workspace, identity, python_arguments, limits, tree_limits, scratch_limits, unit)
    event_directory.mkdir(parents=True, exist_ok=False)
    request = {'schema': 'crane-service-computation-intent/v5-development',
               'unit': unit, 'command': argv, 'workspace_identity': identity,
               'local_limits': asdict(limits), 'tree_limits': asdict(tree_limits), 'scratch_limits': asdict(scratch_limits),
               'executor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_once(event_directory / 'intent.json', request)
    environment = _environment()
    started = time.monotonic()
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    observed = 0
    proc = None
    selector = selectors.DefaultSelector()
    terminal = {'schema': 'crane-service-computation-terminal/v5-development',
                'unit': unit, 'status': 'TECHNICAL_FAILURE', 'result': None}
    reason = None
    error = None
    completed = None
    try:
        proc = subprocess.Popen(argv, env=environment, close_fds=True, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        for name in captured:
            stream = getattr(proc, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or proc.poll() is None:
            remaining = limits.wall_seconds - (time.monotonic() - started)
            if remaining <= 0:
                reason = 'WALL_TIME_LIMIT'
                break
            for key, _ in selector.select(min(remaining, 0.05)):
                stored = sum(map(len, captured.values()))
                chunk = os.read(key.fileobj.fileno(), min(65536, limits.combined_output_bytes - stored + 1))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                observed += len(chunk)
                captured[key.data].extend(chunk[:limits.combined_output_bytes - stored])
                if observed > limits.combined_output_bytes:
                    reason = 'OUTPUT_LIMIT'
                    break
            if reason:
                break
        if not reason:
            return_code = proc.wait()
            state = _control(environment, unit, 'show', '--property=LoadState,Result,ActiveState')
            terminal['unit_state'] = state
            props = dict(line.split('=', 1) for line in state['stdout'].splitlines() if '=' in line)
            if state['return_code'] != 0:
                reason = 'UNIT_STATE_UNVERIFIED'
            elif props.get('Result') == 'oom-kill':
                reason = 'PROCESS_TREE_OOM'
            elif props.get('Result') == 'timeout':
                reason = 'SERVICE_WALL_TIME_LIMIT'
            elif return_code != 0 and props.get('Result') not in {'exit-code', 'signal', 'core-dump'}:
                reason = 'UNIT_START_OR_DISPOSITION_UNVERIFIED'
            else:
                try:
                    stdout, stderr = (bytes(captured[name]).decode('utf-8') for name in ('stdout', 'stderr'))
                    completed = subprocess.CompletedProcess(argv, return_code, stdout, stderr)
                except UnicodeDecodeError:
                    reason = 'INVALID_UTF8_OUTPUT'
    except (OSError, ValueError, subprocess.TimeoutExpired) as caught:
        error = caught
        reason = 'EXECUTION_TRANSPORT_FAILURE'
    finally:
        selector.close()
        cleanup = []
        try:
            # Stop the service cgroup, including detached descendants, before killing its CLI.
            for verb in ('stop', 'reset-failed'):
                cleanup.append({'verb': verb, **_control(environment, unit, verb)})
            state = _control(environment, unit, 'show', '--property=LoadState', '--value')
            terminal['cleanup'] = {'actions': cleanup, 'final_state': state}
            if state['return_code'] != 0 or state['stdout'].strip() != 'not-found':
                reason = 'SERVICE_CLEANUP_UNVERIFIED'
        except (OSError, subprocess.TimeoutExpired) as caught:
            terminal['cleanup'] = {'actions': cleanup, 'error': str(caught)}
            reason = 'SERVICE_CLEANUP_UNVERIFIED'
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            proc.stdout.close()
            proc.stderr.close()
        try:
            verify(workspace, identity)
        except (ValueError, OSError) as caught:
            terminal['workspace_error'] = str(caught)
            reason = 'WORKSPACE_CHANGED'
        audit = {'local_limits': asdict(limits), 'tree_limits': asdict(tree_limits), 'scratch_limits': asdict(scratch_limits),
                 'reason': reason, 'partial_output_only': bool(reason) or completed is None,
                 'captured_bytes': sum(map(len, captured.values())), 'observed_bytes_lower_bound': observed,
                 'stdout_base64': base64.b64encode(captured['stdout']).decode('ascii'),
                 'stderr_base64': base64.b64encode(captured['stderr']).decode('ascii')}
        terminal['execution_audit'] = audit
        terminal['error'] = str(error) if error else None
        if not reason and completed is not None:
            terminal['status'] = 'RETURNED' if completed.returncode == 0 else 'TOOL_RUNTIME_FAILURE'
            terminal['result'] = {'return_code': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr}
        write_once(event_directory / 'terminal.json', terminal)
    if reason or completed is None:
        raise ExecutionFailure(reason or 'EXECUTION_INTERRUPTED', terminal)
    return completed
