"""Equal-evidence development extension with genuine public controller config.

No answers, labels or hidden episode/family metadata are read. Original packets
stay byte-preserved. Configuration alone is not evidence of observed execution.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
MANIFEST=ROOT/'manifests/hexar_external/acquisition/public_control_source_v1/manifest.json'


def extend(packet,manifest_path=MANIFEST,root=ROOT):
    manifest=json.loads(Path(manifest_path).read_text())
    if manifest.get('schema')!='hexar-public-controller-source/v1' or manifest.get('phase')!='development_only':
        raise ValueError('audited development public source required')
    sources={}
    for path,info in manifest['files'].items():
        raw=(Path(root)/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=info['sha256']:
            raise ValueError('controller source changed')
        sources[Path(path).name]=raw.decode()
    if set(sources)!={'twist_mux_locks.yaml','twist_mux_topics.yaml'}:
        raise ValueError('complete locks and input-topic configuration required')
    result=copy.deepcopy(packet)
    context=result['source_context']
    context['indicator_semantics']=(
        'The released component maps /joy_priority to manual selection and /power/is_charging to charging selection. '
        'In this adapted simulation these Bool states are supervisor interlock indicators, not proof of a human joystick action or physical battery charging. '
        'The genuine public controller configuration is supplied below. '
        'Only measurements explicitly visible in the packet can establish applied output or physical motion; missing measurements remain unknown.')
    context['controller_configuration']=dict(
        repository=manifest['upstream_repository'],commit=manifest['upstream_commit'],
        locks_yaml=sources['twist_mux_locks.yaml'],topics_yaml=sources['twist_mux_topics.yaml'])
    context['controller_source_scope']=(
        'These files license source-qualified descriptions of configured priority rules. '
        'A lower-priority navigation input is inhibited when a corresponding lock is active; equal/higher-priority inputs may remain eligible. '
        'Static configuration alone does not prove deployed node wiring, observed lock activation, applied controller output, physical motion, or a unique physical cause of task failure. '
        'No per-episode runtime configuration/wiring attestation is supplied in this development extension. '
        'Do not infer completed task causation from an unobserved source condition.')
    return result
