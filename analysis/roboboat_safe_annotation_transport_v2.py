"""Fresh support transport: inspect decoded JSON before qualified persistence."""
import json
import subprocess
from pathlib import Path
import roboboat_safe_annotation_execution_v1 as original
import roboboat_isolated_transport_v3 as extraction_transport


def safe_isolated_run(command, **kwargs):
    secrets=original.transport.provider_secret_values()
    try:
        result=original.safe_isolated_run(command, **kwargs)
    except subprocess.TimeoutExpired as error:
        stdout="\n".join(json.dumps(event,ensure_ascii=False) for event in
            extraction_transport.safe_events(error.output,secrets))
        raise subprocess.TimeoutExpired(['credential-safe-isolated-provider'],error.timeout,
            output=stdout,stderr=error.stderr) from None
    # Qualified caller persists decoded event types; sanitize parsed event objects.
    result.stdout="\n".join(json.dumps(event,ensure_ascii=False) for event in
        extraction_transport.safe_events(result.stdout,secrets))
    if result.returncode != 0:return result
    output=Path(command[command.index('--output-last-message')+1])
    raw=output.read_text() if output.exists() else ''
    try:value=json.loads(raw)
    except ValueError:return result  # Qualified caller retains invalid JSON without parsed return.
    secrets=original.transport.provider_secret_values()
    # JSON serialization with ASCII escaping disabled exposes decoded key/value strings.
    decoded=json.dumps(value,ensure_ascii=False)
    if any(secret in decoded for secret in secrets):
        output.write_text(json.dumps(original.transport.redact(value,secrets),ensure_ascii=False))
        return subprocess.CompletedProcess(['credential-safe-isolated-provider'],125,'',
            'Provider credential appeared in decoded final output; annotation excluded.')
    return result
