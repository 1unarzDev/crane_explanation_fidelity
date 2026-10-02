"""Fresh development annotation resource arm; unchanged qualified semantics."""
import types
from pathlib import Path
import roboboat_safe_annotation_execution_v1 as safe
import roboboat_safe_annotation_transport_v2 as transport
import roboboat_isolated_transport_v3 as extraction_transport

TIMEOUT_S = 600
EXECUTION_CONTRACT = {**safe.EXECUTION_CONTRACT,
    'schema':'roboboat-safe-annotation-execution/v2-600s',
    'scientific_settings':'unchanged qualified prompts/schemas/models/tools; prospective 600-second deadline',
    'prior_arm':'300-second attempts retained; this arm must be declared before its own calls'}


def safe_execute(case, slot, freeze, out):
    def call(*args, **kwargs):
        kwargs['timeout'] = TIMEOUT_S
        return extraction_transport.call(*args, **kwargs)
    implementation = types.FunctionType(safe.atomizer.execute.__code__,
        {**safe.atomizer.execute.__globals__, 'call':call},
        safe.atomizer.execute.__name__, safe.atomizer.execute.__defaults__, safe.atomizer.execute.__closure__)
    return implementation(case, slot, freeze, out)


def safe_annotate(packet, output, *, caller):
    if caller.timeout_s != TIMEOUT_S:
        raise ValueError('600-second declaration required')
    caller.runner = transport.safe_isolated_run
    return safe.qualified_annotate(packet, output, caller=caller)


def execution_sources():
    return [*safe.execution_sources(), Path(__file__), Path(transport.__file__), Path(extraction_transport.__file__),
        Path(safe.qualified_annotate.__code__.co_filename),
        Path(safe.atomizer.__file__),
        Path(__file__).resolve().parents[1]/'tests/test_roboboat_annotation_deadline_v2.py',
        Path(__file__).resolve().parents[1]/'tests/test_roboboat_isolated_transport_v3.py']
