"""Declared safe transport override for unchanged qualified annotation logic.

No shared globals, prompts, models, deadlines, or retry policies are changed.
"""
import subprocess
import types
from pathlib import Path
import roboboat_isolated_transport_v2 as transport
import run_roboboat_atomization_extension_v5 as atomizer
from run_evidence_calibration_agent_annotation import run as qualified_annotate


def safe_isolated_run(command, **kwargs):
    secrets = transport.provider_secret_values()
    try:
        result = transport.isolated_run(command, **kwargs)
    except subprocess.TimeoutExpired as error:
        def clean(value):
            if isinstance(value, bytes): value = value.decode('utf-8', errors='replace')
            return transport.redact(value or '', secrets)
        raise subprocess.TimeoutExpired(['credential-safe-isolated-provider'], error.timeout,
            output=clean(error.output), stderr=clean(error.stderr)) from None
    except Exception:
        raise RuntimeError('Isolated annotation provider failed; command omitted.') from None
    # The qualified caller reads this file independently of process stdout.
    output = Path(command[command.index('--output-last-message') + 1])
    raw = output.read_text() if output.exists() else ''
    if any(secret in raw for secret in secrets):
        output.write_text(transport.redact(raw, secrets))
        return subprocess.CompletedProcess(['credential-safe-isolated-provider'], 125, '',
            'Provider credential appeared in final output; annotation excluded.')
    return subprocess.CompletedProcess(['credential-safe-isolated-provider'], result.returncode,
        transport.redact(result.stdout, secrets), transport.redact(result.stderr, secrets))


def safe_execute(case, slot, freeze, out):
    # Execute exact v5 bytecode with a private globals copy: only transport changes.
    implementation = types.FunctionType(atomizer.execute.__code__,
        {**atomizer.execute.__globals__, 'call': transport.call},
        atomizer.execute.__name__, atomizer.execute.__defaults__, atomizer.execute.__closure__)
    return implementation(case, slot, freeze, out)


def safe_annotate(packet, output, *, caller):
    caller.runner = safe_isolated_run
    return qualified_annotate(packet, output, caller=caller)


def execution_sources():
    return [Path(__file__), Path(transport.__file__),
        Path(__file__).resolve().parents[1]/'tests/test_roboboat_safe_annotation_execution_v1.py']


EXECUTION_CONTRACT = {
    'schema': 'roboboat-safe-annotation-execution/v1',
    'override': 'private v5 execute globals call; fresh support caller runner',
    'scientific_settings': 'unchanged qualified prompts/schemas/models/tools/deadlines',
    'failure_policy': 'credential-safe retained failure; no reissue or quality retry',
}
