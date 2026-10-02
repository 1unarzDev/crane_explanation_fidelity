"""Bounded-memory compatible phase sharding; no scientific/provider admission.

Input must be globally sorted by opaque job ID. A partial generation namespace
is immutable and cannot dispatch until its complete index verifies. Cohort/stage
completeness must additionally be independently validated against frozen science.
"""
import hashlib
from pathlib import Path

from .journal import canonical,exclusive_json,fingerprint
from .registered_attempt_executor_v2 import MAX_ARTIFACT_BYTES,registry
from .registry_shards_v1 import STAGES,check_limits,encoded,DEFAULT_SHARD_BYTES,DEFAULT_SHARD_JOBS
from .strict_json import load


class RegistryHash:
    def __init__(self,binding,phase):
        header=dict(schema='hexar-registered-attempt-registry/v1',phase=phase,binding_sha256=binding,jobs=[])
        before,after=canonical(header).split(b'[]',1)
        self.hash=hashlib.sha256(before+b'[');self.suffix=after;self.count=0;self.base_bytes=len(encoded(header))
    def append(self,row):
        if self.count:self.hash.update(b',')
        self.hash.update(canonical(row));self.count+=1
    def finish(self):
        value=self.hash.copy();value.update(b']'+self.suffix);return value.hexdigest()


def write_sorted(destination,binding,phase,stage,jobs,maximum_shard_bytes=DEFAULT_SHARD_BYTES,maximum_jobs=DEFAULT_SHARD_JOBS):
    """Write one bounded shard at a time. Never collect a full payload registry."""
    check_limits(maximum_shard_bytes,maximum_jobs)
    if stage not in STAGES:raise ValueError('explicit workflow stage required')
    # Validate the scalar registry header before any namespace mutation.
    registry(binding,phase,[dict(job_id='header-probe',request=dict(role='method',maximum_response_bytes=1))])
    destination=Path(destination);destination.mkdir(exist_ok=False)
    exclusive_json(destination/'generation_claim.json',dict(schema='hexar-streamed-phase-generation/v1',
        binding_sha256=binding,phase=phase,stage=stage,maximum_shard_bytes=maximum_shard_bytes,
        maximum_jobs=maximum_jobs,provider_calls_permitted=False))
    complete=RegistryHash(binding,phase);current=[];current_size=complete.base_bytes;rows=[];previous=None
    def flush():
        nonlocal current,current_size
        if not current:return
        value=dict(schema='hexar-registered-attempt-registry/v1',phase=phase,binding_sha256=binding,jobs=current)
        data=encoded(value);name=f'shard-{len(rows):06d}.json'
        if len(data)!=current_size or len(data)>maximum_shard_bytes:raise ValueError('streamed shard byte accounting differs')
        exclusive_json(destination/name,value)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
            registry_sha256=fingerprint(value),job_ids=[r['job_id'] for r in current]))
        current=[];current_size=complete.base_bytes
    for job in jobs:
        row=registry(binding,phase,[job])['jobs'][0]
        if previous is not None and row['job_id']<=previous:
            raise ValueError('globally sorted distinct opaque jobs required; partial namespace retained')
        previous=row['job_id'];row_bytes=len(canonical(row))
        if complete.base_bytes+row_bytes>maximum_shard_bytes:
            raise ValueError('one complete request exceeds frozen shard bound; partial namespace retained')
        extra=row_bytes+int(bool(current))
        if current and (len(current)==maximum_jobs or current_size+extra>maximum_shard_bytes):
            flush();extra=row_bytes
        current.append(row);current_size+=extra;complete.append(row)
    if not complete.count:raise ValueError('nonempty complete phase required; partial namespace retained')
    flush()
    index=dict(schema='hexar-registered-phase-shards/v1',binding_sha256=binding,phase=phase,stage=stage,
        maximum_shard_bytes=maximum_shard_bytes,maximum_jobs=maximum_jobs,maximum_index_bytes=MAX_ARTIFACT_BYTES,
        complete_registry_sha256=complete.finish(),total_jobs=complete.count,shards=rows)
    if len(encoded(index))>MAX_ARTIFACT_BYTES:raise ValueError('phase index exceeds frozen bound; partial namespace retained')
    exclusive_json(destination/'index.json',index)
    verify(destination,fingerprint(index));return index


def read_index(folder,expected_hash):
    path=Path(folder)/'index.json'
    if path.stat().st_size>MAX_ARTIFACT_BYTES:raise ValueError('phase index exceeds frozen artifact bound')
    value=load(path.read_bytes(),MAX_ARTIFACT_BYTES)
    if fingerprint(value)!=expected_hash:raise ValueError('sealed phase index changed')
    return value


def read_shard(folder,item,maximum_bytes):
    name=item['path']
    if Path(name).name!=name or not name.startswith('shard-') or not name.endswith('.json'):
        raise ValueError('unsafe shard path')
    path=Path(folder)/name
    if type(item['bytes']) is not int or not 0<item['bytes']<=maximum_bytes or path.stat().st_size!=item['bytes']:
        raise ValueError('sealed shard size changed')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('sealed shard bytes changed')
    value=load(raw,maximum_bytes)
    if encoded(value)!=raw or fingerprint(value)!=item['registry_sha256']:
        raise ValueError('noncanonical shard identity changed')
    return value


def verify(folder,expected_hash):
    """Verify global identity and greedy partition while retaining one shard."""
    folder=Path(folder);index=read_index(folder,expected_hash)
    if set(index)!={'schema','binding_sha256','phase','stage','maximum_shard_bytes','maximum_jobs',
            'maximum_index_bytes','complete_registry_sha256','total_jobs','shards'}:
        raise ValueError('closed compatible phase index required')
    check_limits(index['maximum_shard_bytes'],index['maximum_jobs'])
    if index['schema']!='hexar-registered-phase-shards/v1' or index['stage'] not in STAGES or index['maximum_index_bytes']!=MAX_ARTIFACT_BYTES:
        raise ValueError('invalid compatible phase index')
    complete=RegistryHash(index['binding_sha256'],index['phase']);previous=None;previous_item=None
    expected_names={'index.json'}
    if (folder/'generation_claim.json').exists():
        expected_names.add('generation_claim.json')
        claim=load((folder/'generation_claim.json').read_bytes(),MAX_ARTIFACT_BYTES)
        if claim!=dict(schema='hexar-streamed-phase-generation/v1',binding_sha256=index['binding_sha256'],
                phase=index['phase'],stage=index['stage'],maximum_shard_bytes=index['maximum_shard_bytes'],
                maximum_jobs=index['maximum_jobs'],provider_calls_permitted=False):
            raise ValueError('stream generation claim changed')
    for number,item in enumerate(index['shards']):
        if set(item)!={'path','bytes','sha256','registry_sha256','job_ids'} or item['path']!=f'shard-{number:06d}.json':
            raise ValueError('consecutive closed shard metadata required')
        value=read_shard(folder,item,index['maximum_shard_bytes']);expected_names.add(item['path'])
        jobs=value.get('jobs',[])
        if not jobs or len(jobs)>index['maximum_jobs'] or item['job_ids']!=[r['job_id'] for r in jobs]:
            raise ValueError('complete bounded shard job identities required')
        if value!=registry(index['binding_sha256'],index['phase'],[dict(job_id=r['job_id'],request=r['request']) for r in jobs]):
            raise ValueError('registered shard request/schema binding changed')
        if previous_item is not None and len(previous_item['job_ids'])<index['maximum_jobs']:
            if previous_item['bytes']+len(canonical(jobs[0]))+1<=index['maximum_shard_bytes']:
                raise ValueError('noncanonical greedy shard partition')
        for row in jobs:
            if previous is not None and row['job_id']<=previous:raise ValueError('global duplicate or reordered job')
            previous=row['job_id'];complete.append(row)
        previous_item=item
    if (not complete.count or type(index['total_jobs']) is not int or complete.count!=index['total_jobs']
            or complete.finish()!=index['complete_registry_sha256']):
        raise ValueError('complete streamed registry identity differs')
    if {p.name for p in folder.iterdir()}!=expected_names:raise ValueError('unexpected or missing phase artifact')
    return index


class StreamingExecutor:
    """Compatible single-attempt execution with one requested payload shard loaded.

    The callback is qualification plumbing, never scientific authorization. A
    production wrapper must independently enforce frozen science/H1/provider,
    stage chronology, complete job membership and this exact root/index.
    """
    def __init__(self,root,bundle,expected_index_sha256,admit):
        from .registered_attempt_executor_v2 import RegisteredExecutor
        self.root,self.bundle,self.admit=Path(root),Path(bundle),admit
        self.index=verify(self.bundle,expected_index_sha256);self.index_hash=expected_index_sha256
        self.lookup={job:item for item in self.index['shards'] for job in item['job_ids']}
        self.authorize(None);self.root.mkdir(parents=True,exist_ok=True)
        path=self.root/'phase_index.json'
        if path.exists():
            if load(path.read_bytes(),MAX_ARTIFACT_BYTES)!=self.index:raise ValueError('execution root bound to another phase')
        else:exclusive_json(path,self.index)

    def authorize(self,item):
        import copy
        payload=dict(index=copy.deepcopy(self.index),index_sha256=self.index_hash,
            shard=copy.deepcopy(item),execution_root=str(self.root.resolve()))
        approved=self.admit(payload)
        if (type(approved) is not dict or approved.get('authorized') is not True
                or approved.get('index_sha256')!=self.index_hash
                or approved.get('execution_root')!=payload['execution_root']):
            raise ValueError('independent stage/index/root admission failed')

    def execute(self,job_id,backend):
        from .registered_attempt_executor_v2 import RegisteredExecutor
        if job_id not in self.lookup:raise ValueError('unscheduled phase job; no dispatch')
        item=self.lookup[job_id];self.authorize(item)
        if read_index(self.bundle,self.index_hash)!=self.index or load((self.root/'phase_index.json').read_bytes(),MAX_ARTIFACT_BYTES)!=self.index:
            raise ValueError('retained phase index changed')
        value=read_shard(self.bundle,item,self.index['maximum_shard_bytes'])
        def admit_registry(reg):
            self.authorize(item)
            if reg!=read_shard(self.bundle,item,self.index['maximum_shard_bytes']):
                raise ValueError('shard registry differs from exact phase')
            return dict(authorized=True,registry_sha256=item['registry_sha256'],
                binding_sha256=self.index['binding_sha256'],phase=self.index['phase'])
        engine=RegisteredExecutor(self.root/item['path'].removesuffix('.json'),value,admit_registry)
        return engine.execute(job_id,backend)
