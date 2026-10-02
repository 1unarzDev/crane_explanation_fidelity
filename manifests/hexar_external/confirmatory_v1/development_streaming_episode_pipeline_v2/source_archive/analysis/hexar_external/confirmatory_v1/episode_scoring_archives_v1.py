"""Bounded per-episode scoring archives; no dispatch or scientific admission.

Constructs the unchanged unique-request/opaque A/B(+C)/whole-episode workflow
without a multi-gigabyte cohort public plan. Final roots and chronology need
independent admission. Development replay cannot authorize confirmation.
"""
import copy
import hashlib
import hmac
import re
from pathlib import Path

from .journal import canonical,exclusive_json,fingerprint
from .registered_attempt_executor_v2 import MAX_ARTIFACT_BYTES
from .strict_json import load
from .unique_request_plan import build
from .blinded_scoring_workflow import reference_registry,prepare,finalize,METHODS,JOBS

FILES=('neutral_reference_registry.json','unique_method_plan.json','method_outputs.json',
       'public_scoring_plan.json','sealed_method_linkage.json')


def bounded(value,maximum_bytes=MAX_ARTIFACT_BYTES):
    raw=canonical(value)+b'\n'
    if type(maximum_bytes) is not int or not 1<=maximum_bytes<=MAX_ARTIFACT_BYTES or len(raw)>maximum_bytes:
        raise ValueError('complete episode artifact exceeds fixed bound; no truncation')
    return raw


def episode_plan(entries,bindings):
    if not entries or len({e['episode_id'] for e in entries})!=1 or set(bindings)!=set(METHODS):
        raise ValueError('one complete episode and both primary implementation bindings required')
    neutral=reference_registry(entries)
    plan=build([dict(episode_id=e['episode_id'],method=method,job_id=e['job_id'],packet=e['packet'],
                     implementation_binding=bindings[method]) for e in entries for method in METHODS])
    if plan['unique_requests']!=12 or plan['battery_cells']!=18:
        raise ValueError('fixed nine-cell/six-unique primary battery required')
    return neutral,plan


def scoring_artifacts(neutral,plan,outputs,master_blinding_key,shuffle_seed):
    ids={r['episode_id'] for r in plan['requests']}
    if len(ids)!=1 or not isinstance(master_blinding_key,bytes) or len(master_blinding_key)<32 or type(shuffle_seed) is not int:
        raise ValueError('single episode, independent master key and fixed shuffle seed required')
    episode=next(iter(ids));key=hmac.new(master_blinding_key,canonical(['episode-scoring-archive/v1',episode]),hashlib.sha256).digest()
    # Separate deterministic randomization namespace per independent episode.
    seed=int.from_bytes(hmac.new(master_blinding_key,canonical([episode,shuffle_seed]),hashlib.sha256).digest()[:8],'big')
    public,private=prepare(plan,outputs,neutral,key,seed)
    values=dict(zip(FILES,(neutral,plan,outputs,public,private)))
    for value in values.values():bounded(value)
    return values


def write_episode(destination,artifacts,study_binding,phase):
    if set(artifacts)!=set(FILES) or phase not in ('development_qualification','confirmation'):
        raise ValueError('complete explicit-phase episode scoring archive required')
    if type(study_binding) is not str or not re.fullmatch('[0-9a-f]{64}',study_binding):
        raise ValueError('exact independent study/development binding required')
    # Verification is computational only. No permissive callback can dispatch
    # or make a confirmation artifact scientifically authorized here.
    plan=artifacts['unique_method_plan.json'];ids={r['episode_id'] for r in plan['requests']}
    if len(ids)!=1 or plan.get('unique_requests')!=12 or plan.get('battery_cells')!=18:
        raise ValueError('one complete paired physical episode per scoring archive')
    rows={name:dict(sha256=hashlib.sha256(bounded(value)).hexdigest(),bytes=len(bounded(value)))
          for name,value in artifacts.items()}
    index=dict(schema='hexar-episode-scoring-archive/v1',episode_id=next(iter(ids)),
        study_binding_sha256=study_binding,phase=phase,files=rows,maximum_artifact_bytes=MAX_ARTIFACT_BYTES,
        unique_requests=12,battery_cells=18,dispatch_authorized=False)
    bounded(index);destination=Path(destination);destination.mkdir(exist_ok=False)
    for name,value in artifacts.items():exclusive_json(destination/name,value)
    exclusive_json(destination/'episode_index.json',index)
    return index


def read_episode(folder,expected_index_sha256,study_binding,phase):
    folder=Path(folder);index=load((folder/'episode_index.json').read_bytes(),MAX_ARTIFACT_BYTES)
    if (fingerprint(index)!=expected_index_sha256 or index.get('schema')!='hexar-episode-scoring-archive/v1'
            or index.get('study_binding_sha256')!=study_binding or index.get('phase')!=phase
            or set(index.get('files',{}))!=set(FILES) or index.get('dispatch_authorized') is not False
            or index.get('maximum_artifact_bytes')!=MAX_ARTIFACT_BYTES):
        raise ValueError('episode archive index/binding changed')
    values={}
    for name,pin in index['files'].items():
        path=folder/name
        if type(pin.get('bytes')) is not int or not 0<pin['bytes']<=MAX_ARTIFACT_BYTES or path.stat().st_size!=pin['bytes']:
            raise ValueError('retained episode scoring artifact changed or exceeds fixed bound')
        raw=path.read_bytes()
        if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
            raise ValueError('retained episode scoring artifact changed')
        values[name]=load(raw,MAX_ARTIFACT_BYTES)
        if bounded(values[name])!=raw:raise ValueError('episode artifact not canonical')
    if {r['episode_id'] for r in values['unique_method_plan.json']['requests']}!={index['episode_id']}:
        raise ValueError('archive belongs to another episode')
    return index,values


def close_episode(artifacts,initial,C):
    value=finalize(artifacts['unique_method_plan.json'],artifacts['method_outputs.json'],
        artifacts['neutral_reference_registry.json'],artifacts['public_scoring_plan.json'],
        artifacts['sealed_method_linkage.json'],initial,C)
    if len(value['recording_endpoints'])!=1 or len(value['jobs'])!=18:
        raise ValueError('one whole-episode endpoint per paired archive required')
    bounded(value)
    return value


def cohort_index(records,study_binding,phase):
    """Small closed pointer manifest; never aggregate full public payloads."""
    if phase not in ('development_qualification','confirmation') or type(study_binding) is not str or not re.fullmatch('[0-9a-f]{64}',study_binding):
        raise ValueError('explicit phase and exact binding required')
    episodes=set();paths=set();index_hashes=set()
    for record in records:
        if set(record)!={'episode_id','relative_path','episode_index_sha256'}:
            raise ValueError('closed episode pointer required')
        if (record['episode_id'] in episodes or record['relative_path'] in paths
                or record['episode_index_sha256'] in index_hashes):
            raise ValueError('duplicate independent episode/archive')
        path=Path(record['relative_path'])
        if path.is_absolute() or '..' in path.parts or type(record['episode_index_sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',record['episode_index_sha256']):
            raise ValueError('safe relative archive path and hash required')
        episodes.add(record['episode_id']);paths.add(record['relative_path']);index_hashes.add(record['episode_index_sha256'])
    if not records:raise ValueError('nonempty complete episode index required')
    value=dict(schema='hexar-cohort-episode-scoring-index/v1',study_binding_sha256=study_binding,
        phase=phase,records=copy.deepcopy(records),independent_episodes=len(records),
        maximum_artifact_bytes=MAX_ARTIFACT_BYTES,dispatch_authorized=False,
        scope='Pointers only; independent episode count is never answer/judge count.')
    bounded(value);return value
