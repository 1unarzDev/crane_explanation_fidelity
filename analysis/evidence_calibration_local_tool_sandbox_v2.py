"""Bounded offline local execution candidate; original sandbox remains hash-bound."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from evidence_calibration_local_tool_sandbox import command as original_command
from stage_evidence_calibration_workspace import verify

PRLIMIT = Path('/usr/bin/prlimit')


@dataclass(frozen=True)
class Limits:
    wall_seconds: int
    cpu_seconds_per_process: int
    address_space_bytes_per_process: int
    combined_output_bytes: int

    def __post_init__(self):
        bounds = {'wall_seconds': (1, 60), 'cpu_seconds_per_process': (1, 60),
                  'address_space_bytes_per_process': (64 * 1024**2, 8 * 1024**3),
                  'combined_output_bytes': (1, 16 * 1024**2)}
        for field, (low, high) in bounds.items():
            value = getattr(self, field)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'invalid explicit local limit: {field}')


class ExecutionFailure(RuntimeError):
    """Contains bounded partial bytes as audit material, never successful tool output."""
    def __init__(self, reason: str, audit: dict):
        super().__init__(reason)
        self.audit = audit


def command(workspace: Path, identity: dict, python_arguments: list[str], limits: Limits) -> list[str]:
    if not isinstance(limits, Limits):
        raise ValueError('explicit Limits required')
    if not PRLIMIT.is_file() or PRLIMIT.is_symlink():
        raise ValueError('registered prlimit executable unavailable')
    argv = original_command(workspace, identity, python_arguments)
    separator = argv.index('--')
    cpu, memory = limits.cpu_seconds_per_process, limits.address_space_bytes_per_process
    return argv[:separator + 1] + [str(PRLIMIT), f'--cpu={cpu}:{cpu}',
        f'--as={memory}:{memory}', '--core=0:0', '--'] + argv[separator + 1:]


def run(workspace: Path, identity: dict, python_arguments: list[str], *, limits: Limits) -> subprocess.CompletedProcess:
    argv = command(workspace, identity, python_arguments, limits)
    started = time.monotonic()
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    observed = 0
    reason = None
    proc = None
    selector = selectors.DefaultSelector()
    try:
        proc = subprocess.Popen(argv, env={}, close_fds=True, stdin=subprocess.DEVNULL,
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
                # At most one extra detection byte; host capture is bounded across both pipes.
                stored = sum(len(value) for value in captured.values())
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
        if reason:
            raise ExecutionFailure(reason, {'limits': asdict(limits), 'reason': reason,
                'partial_output_only': True, 'captured_bytes': sum(map(len, captured.values())),
                'observed_bytes_lower_bound': observed,
                'stdout_base64': base64.b64encode(captured['stdout']).decode('ascii'),
                'stderr_base64': base64.b64encode(captured['stderr']).decode('ascii')})
        return_code = proc.wait()
        try:
            stdout, stderr = (bytes(captured[name]).decode('utf-8') for name in ('stdout', 'stderr'))
        except UnicodeDecodeError as error:
            raise ExecutionFailure('INVALID_UTF8_OUTPUT', {'limits': asdict(limits),
                'reason': 'INVALID_UTF8_OUTPUT', 'partial_output_only': True,
                'captured_bytes': sum(map(len, captured.values())), 'observed_bytes_lower_bound': observed,
                'stdout_base64': base64.b64encode(captured['stdout']).decode('ascii'),
                'stderr_base64': base64.b64encode(captured['stderr']).decode('ascii')}) from error
        return subprocess.CompletedProcess(argv, return_code, stdout, stderr)
    finally:
        selector.close()
        if proc is not None:
            # Kill the launcher group even after launcher exit; bwrap's namespace init dies
            # with its parent, terminating descendants in that private PID namespace.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            proc.stdout.close()
            proc.stderr.close()
        verify(workspace, identity)
