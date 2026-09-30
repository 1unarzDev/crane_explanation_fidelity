"""Development service-backed computation candidate; existing callers stay unchanged."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import hashlib
import os
import stat
from pathlib import Path
import selectors
import signal
import subprocess
import time
import uuid

from evidence_calibration_local_tool_sandbox_v2 import ExecutionFailure, Limits, command as namespace_command
from observe_evidence_calibration_cgroup_limits import write_once
from stage_evidence_calibration_workspace import verify
from audit_evidence_calibration_namespace_lifecycle import audit as audit_lifecycle
from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS, parse_properties

WRAPPER = Path(__file__).with_name("evidence_calibration_namespace_wrapper.py")


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



@dataclass(frozen=True)
class CpuBudget:
    cumulative_nanoseconds: int
    poll_milliseconds: int
    query_timeout_milliseconds: int

    def __post_init__(self):
        for field, low, high in [('cumulative_nanoseconds', 10_000_000, 240_000_000_000),
                                 ('poll_milliseconds', 5, 250),
                                 ('query_timeout_milliseconds', 50, 1000)]:
            value = getattr(self, field)
            if type(value) is not int or not low <= value <= high:
                raise ValueError('invalid explicit sampled CPU budget: ' + field)


class CpuAccountingError(ValueError):
    pass


class CpuMonitor:
    """Persist counter samples before cleanup; never interpret missing usage as zero."""
    def __init__(self, environment: dict, unit: str, budget: CpuBudget, directory: Path):
        self.environment, self.unit, self.budget, self.directory = environment, unit, budget, directory
        self.samples = []
        self.last_cpu = None
        self.final_cpu = None

    def sample(self) -> dict | None:
        started = time.monotonic_ns()
        raw = subprocess.run(['/usr/bin/systemctl', '--user', 'show', self.unit, '--property=' + FIELDS],
            env=self.environment, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=self.budget.query_timeout_milliseconds / 1000)
        record = {'schema': 'crane-service-cpu-sample/v1-development', 'unit': self.unit,
                  'started_monotonic_ns': started, 'completed_monotonic_ns': time.monotonic_ns(),
                  'return_code': raw.returncode, 'stdout': raw.stdout, 'stderr': raw.stderr}
        # Raw query evidence persists even when parsing fails or the unit has not started.
        write_once(self.directory / f'cpu-sample-{len(self.samples):08d}.json', record)
        self.samples.append(record)
        if raw.returncode:
            raise CpuAccountingError('CPU accounting query failed')
        properties = {}
        for line in raw.stdout.splitlines():
            if '=' not in line or line.split('=', 1)[0] in properties:
                raise CpuAccountingError('malformed CPU accounting properties')
            key, value = line.split('=', 1)
            properties[key] = value
        pending_loaded_startup = (properties.get('LoadState') == 'loaded'
            and properties.get('ActiveState') == 'inactive' and properties.get('SubState') == 'dead'
            and properties.get('ExecMainCode') == '0' and properties.get('Result') == 'success'
            and properties.get('CPUUsageNSec') == '[not set]')
        if self.last_cpu is None and (properties.get('LoadState') == 'not-found' or pending_loaded_startup):
            return None  # startup only, never a zero counter or successful completion
        try:
            row = parse_properties(raw.stdout)
        except ValueError as error:
            raise CpuAccountingError(str(error)) from error
        if row['LoadState'] != 'loaded':
            raise CpuAccountingError('loaded unit disappeared before final CPU retention')
        value = row['CPUUsageNSec']
        if self.last_cpu is not None and value < self.last_cpu:
            raise CpuAccountingError('CPU usage counter regressed')
        self.last_cpu = value
        return row

    def reached(self) -> bool:
        return self.last_cpu is not None and self.last_cpu >= self.budget.cumulative_nanoseconds

    def save_final(self, row: dict) -> None:
        if not (row['SubState'] == 'exited' or row['ActiveState'] == 'failed'):
            raise CpuAccountingError('CPU counter sampled before tree exit')
        self.final_cpu = row['CPUUsageNSec']

    def audit(self) -> dict:
        times = [sample['started_monotonic_ns'] for sample in self.samples]
        return {'budget': asdict(self.budget), 'sample_count': len(self.samples),
                'last_observed_cpu_nanoseconds': self.last_cpu,
                'final_cpu_nanoseconds': self.final_cpu,
                'observed_overshoot_nanoseconds': None if self.final_cpu is None else
                    max(0, self.final_cpu - self.budget.cumulative_nanoseconds),
                'maximum_sample_spacing_nanoseconds': max((b-a for a,b in zip(times,times[1:])), default=None),
                'hard_cpu_cap_verified': False, 'whole_turn_cpu_accounting_verified': False}


def bounded_namespace_command(workspace: Path, identity: dict, python_arguments: list[str],
                              limits: Limits, scratch_limits: ScratchLimits) -> list[str]:
    if not isinstance(scratch_limits, ScratchLimits):
        raise ValueError('explicit ScratchLimits required')
    argv = namespace_command(workspace, identity, python_arguments, limits)
    index = argv.index('--tmpfs')
    if argv[index + 1] != '/tmp':
        raise ValueError('registered namespace scratch layout differs')
    argv.insert(1, '--unshare-user')
    index += 1
    argv[index:index + 2] = ['--size', str(scratch_limits.temporary_bytes), '--tmpfs', '/tmp']
    separator = argv.index('--')
    argv[separator:separator] = ['--size', str(scratch_limits.shared_memory_bytes), '--tmpfs', '/dev/shm',
                               '--remount-ro', '/dev', '--remount-ro', '/', '--disable-userns']
    return argv

def command(workspace: Path, identity: dict, python_arguments: list[str], limits: Limits,
            tree_limits: TreeLimits, scratch_limits: ScratchLimits, unit: str, wrapper_request: Path, wrapper_request_sha256: str) -> list[str]:
    if not isinstance(tree_limits, TreeLimits):
        raise ValueError('explicit TreeLimits required')
    if not unit.startswith('crane-compute-') or len(unit) != 46 or any(
            char not in '0123456789abcdef' for char in unit[14:]):
        raise ValueError('registered fresh service identity required')
    return ['/usr/bin/systemd-run', '--user', '--quiet', '--wait', '--pipe', '--expand-environment=no', '--unit=' + unit,
            '-p', f'MemoryMax={tree_limits.memory_bytes}', '-p', 'MemorySwapMax=0',
            '-p', f'TasksMax={tree_limits.tasks}', '-p', f'CPUQuota={tree_limits.cpu_rate_percent}%',
            '-p', 'OOMPolicy=kill', '-p', 'RemainAfterExit=yes', '-p', f'RuntimeMaxSec={limits.wall_seconds}s',
            '-p', 'TimeoutStopSec=1s', '-p', 'KillMode=control-group',
            '/usr/bin/python3', '-I', '-S', '-B', str(WRAPPER.resolve()),
            str(wrapper_request.resolve()), wrapper_request_sha256]


def _environment() -> dict:
    return {key: os.environ[key] for key in ('PATH', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')
            if key in os.environ}


def _control(environment: dict, unit: str, *arguments: str) -> dict:
    result = subprocess.run(['/usr/bin/systemctl', '--user', *arguments, unit], env=environment,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=5)
    return {'return_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def run(workspace: Path, identity: dict, python_arguments: list[str], *, limits: Limits,
        tree_limits: TreeLimits, scratch_limits: ScratchLimits, cpu_budget: CpuBudget, event_directory: Path) -> subprocess.CompletedProcess:
    """Retain one-shot intent/terminal; partial output is audit only, never tool success."""
    if not isinstance(cpu_budget, CpuBudget):
        raise ValueError('explicit CpuBudget required')
    workspace = workspace.resolve()
    if event_directory.resolve() == workspace or workspace in event_directory.resolve().parents:
        raise ValueError('event directory must be outside the method workspace')
    unit = 'crane-compute-' + uuid.uuid4().hex
    namespace_argv = bounded_namespace_command(workspace, identity, python_arguments, limits, scratch_limits)
    if not isinstance(tree_limits, TreeLimits):
        raise ValueError('explicit TreeLimits required')
    event_directory = event_directory.resolve()
    event_directory.mkdir(parents=True, exist_ok=False)
    wrapper_request = event_directory / 'namespace-request.json'
    status_path = event_directory / 'namespace-status.bin'
    write_once(wrapper_request, {'command': namespace_argv, 'status_path': str(status_path)})
    wrapper_request_sha256 = hashlib.sha256(wrapper_request.read_bytes()).hexdigest()
    argv = command(workspace, identity, python_arguments, limits, tree_limits, scratch_limits, unit,
                   wrapper_request, wrapper_request_sha256)
    request = {'schema': 'crane-service-computation-intent/v9-development',
               'unit': unit, 'command': argv, 'workspace_identity': identity,
               'local_limits': asdict(limits), 'tree_limits': asdict(tree_limits), 'scratch_limits': asdict(scratch_limits),
               'executor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'namespace_wrapper_sha256': hashlib.sha256(WRAPPER.read_bytes()).hexdigest(),
               'wrapper_request_sha256': wrapper_request_sha256, 'cpu_budget': asdict(cpu_budget)}
    write_once(event_directory / 'intent.json', request)
    environment = _environment()
    started = time.monotonic()
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    observed = 0
    proc = None
    selector = selectors.DefaultSelector()
    terminal = {'schema': 'crane-service-computation-terminal/v9-development',
                'unit': unit, 'status': 'TECHNICAL_FAILURE', 'result': None}
    reason = None
    error = None
    completed = None
    monitor = CpuMonitor(environment, unit, cpu_budget, event_directory)
    final_props = None
    release = None
    next_sample = started
    try:
        proc = subprocess.Popen(argv, env=environment, close_fds=True, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        for name in captured:
            stream = getattr(proc, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or proc.poll() is None:
            if release is None and time.monotonic() >= next_sample:
                props = monitor.sample()
                next_sample = time.monotonic() + cpu_budget.poll_milliseconds / 1000
                if monitor.reached():
                    reason = 'CUMULATIVE_CPU_LIMIT'
                    break
                if props is not None and (props['SubState'] == 'exited' or props['ActiveState'] == 'failed'):
                    monitor.save_final(props)
                    final_props = props
                    if props['SubState'] == 'exited':
                        # Release the retained success unit only after its final counter is saved.
                        release = _control(environment, unit, 'stop')
                        terminal['success_unit_release'] = release
                        if release['return_code'] != 0:
                            reason = 'CPU_UNIT_RELEASE_UNVERIFIED'
                            break
                    else:
                        release = {'failed_unit_retained': True}
            remaining = limits.wall_seconds - (time.monotonic() - started)
            if remaining <= 0:
                reason = 'WALL_TIME_LIMIT'
                break
            for key, _ in selector.select(min(remaining, cpu_budget.poll_milliseconds / 1000)):
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
            if monitor.final_cpu is None:
                props = monitor.sample()
                if props is None:
                    raise CpuAccountingError('no loaded final CPU counter')
                monitor.save_final(props)
                final_props = props
                if monitor.reached():
                    reason = 'CUMULATIVE_CPU_LIMIT'
            return_code = proc.wait()
            props = final_props
            terminal['unit_state_before_release'] = props
            if reason:
                pass
            elif props is None or monitor.final_cpu is None:
                reason = 'CPU_ACCOUNTING_UNVERIFIED'
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
    except CpuAccountingError as caught:
        error = caught
        reason = 'CPU_ACCOUNTING_UNVERIFIED'
    except (OSError, ValueError, subprocess.TimeoutExpired) as caught:
        error = caught
        reason = 'EXECUTION_TRANSPORT_FAILURE'
    finally:
        selector.close()
        cleanup = []
        # Failed/resource-interrupted computations retain final CPU before reset/unload.
        if proc is not None and monitor.final_cpu is None:
            try:
                killed = _control(environment, unit, 'kill', '--signal=SIGKILL', '--kill-whom=all')
                terminal['cpu_stop_action'] = killed
                deadline = time.monotonic() + 1
                while time.monotonic() < deadline:
                    props = monitor.sample()
                    if props is not None and (props['SubState'] == 'exited' or props['ActiveState'] == 'failed'):
                        monitor.save_final(props)
                        final_props = props
                        break
                    time.sleep(cpu_budget.poll_milliseconds / 1000)
                if monitor.final_cpu is None:
                    raise CpuAccountingError('final CPU accounting missing after termination')
            except (OSError, ValueError, subprocess.TimeoutExpired) as caught:
                terminal['cpu_accounting_error'] = str(caught)
                if not reason:
                    reason = 'CPU_ACCOUNTING_UNVERIFIED'
        terminal['cpu_accounting'] = monitor.audit()
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
        try:
            fd = os.open(status_path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise ValueError('namespace status is not a regular file')
                raw_status = os.read(fd, 8193)
            finally:
                os.close(fd)
            terminal['namespace_status_sha256'] = hashlib.sha256(raw_status).hexdigest()
            lifecycle = audit_lifecycle(raw_status, completed.returncode if completed is not None else 1)
            terminal['namespace_lifecycle'] = lifecycle
            if not reason and not lifecycle['payload_exit_verified']:
                reason = lifecycle['disposition']
        except (OSError, ValueError) as caught:
            terminal['namespace_status_error'] = str(caught)
            if not reason:
                reason = 'NAMESPACE_STATUS_UNVERIFIED'
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
