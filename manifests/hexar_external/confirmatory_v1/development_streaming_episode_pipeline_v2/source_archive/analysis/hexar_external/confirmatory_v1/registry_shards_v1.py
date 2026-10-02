"""Bounded immutable phase registries; no study or provider authorization.

Admission must independently verify the prospective study, stage chronology,
provider, exact index and execution root before every operation. This module
never creates a job after sealing and never redispatches a closed/crashed job.
"""
import copy
import hashlib
from pathlib import Path
import re

from .journal import canonical, exclusive_json, fingerprint
from .registered_attempt_executor_v2 import MAX_ARTIFACT_BYTES, RegisteredExecutor, registry
from .strict_json import load

STAGES = ('methods', 'initial_judges', 'adjudication_judges')
DEFAULT_SHARD_BYTES = 8 * 1024 * 1024
DEFAULT_SHARD_JOBS = 128


def encoded(value):
    return canonical(value) + b'\n'


def check_limits(maximum_shard_bytes, maximum_jobs):
    if (type(maximum_shard_bytes) is not int or not 1 <= maximum_shard_bytes <= MAX_ARTIFACT_BYTES
            or type(maximum_jobs) is not int or maximum_jobs < 1):
        raise ValueError('positive bounded shard bytes and job count required')


def build(binding_sha256, phase, stage, jobs, maximum_shard_bytes=DEFAULT_SHARD_BYTES,
          maximum_jobs=DEFAULT_SHARD_JOBS):
    """Partition a declared phase schedule deterministically, never truncate it."""
    if stage not in STAGES:
        raise ValueError('explicit registered workflow stage required')
    check_limits(maximum_shard_bytes, maximum_jobs)
    complete = registry(binding_sha256, phase, jobs)
    batches, current = [], []
    for row in complete['jobs']:
        job = dict(job_id=row['job_id'], request=row['request'])
        tentative = registry(binding_sha256, phase, current + [job])
        if len(encoded(tentative)) > maximum_shard_bytes or len(tentative['jobs']) > maximum_jobs:
            if not current:
                raise ValueError('one complete request exceeds frozen shard bound; no truncation')
            batches.append(registry(binding_sha256, phase, current))
            current = [job]
            if len(encoded(registry(binding_sha256, phase, current))) > maximum_shard_bytes:
                raise ValueError('one complete request exceeds frozen shard bound; no truncation')
        else:
            current.append(job)
    if current:
        batches.append(registry(binding_sha256, phase, current))
    shards, rows = {}, []
    for number, batch in enumerate(batches):
        name = f'shard-{number:06d}.json'
        data = encoded(batch)
        shards[name] = batch
        rows.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                         registry_sha256=fingerprint(batch), job_ids=[j['job_id'] for j in batch['jobs']]))
    index = dict(schema='hexar-registered-phase-shards/v1', binding_sha256=binding_sha256,
        phase=phase, stage=stage, maximum_shard_bytes=maximum_shard_bytes,
        maximum_jobs=maximum_jobs, maximum_index_bytes=MAX_ARTIFACT_BYTES,
        complete_registry_sha256=fingerprint(complete), total_jobs=len(complete['jobs']), shards=rows)
    if len(encoded(index)) > MAX_ARTIFACT_BYTES:
        raise ValueError('phase index exceeds frozen persisted-artifact bound; prospectively redesign before dispatch')
    return index, shards


def write(destination, index, shards):
    """Exclusive creation only; preserve even partially written namespaces."""
    # Validate the whole bundle before creating its directory.
    verify_bundle(index, shards)
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    for name, value in shards.items():
        exclusive_json(destination/name, value)
    exclusive_json(destination/'index.json', index)


def verify_bundle(index, shards):
    try:
        check_limits(index['maximum_shard_bytes'], index['maximum_jobs'])
        if (index['schema'] != 'hexar-registered-phase-shards/v1' or index['stage'] not in STAGES
                or index['maximum_index_bytes'] != MAX_ARTIFACT_BYTES
                or len(encoded(index)) > MAX_ARTIFACT_BYTES):
            raise ValueError('invalid bounded phase index')
        jobs = []
        names = []
        for number, item in enumerate(index['shards']):
            name = f'shard-{number:06d}.json'
            if item['path'] != name or not item['job_ids']:
                raise ValueError('complete consecutive bounded shard names required')
            value = shards[name]
            data = encoded(value)
            if (value['binding_sha256'] != index['binding_sha256'] or value['phase'] != index['phase']
                    or len(data) != item['bytes'] or len(data) > index['maximum_shard_bytes']
                    or hashlib.sha256(data).hexdigest() != item['sha256']
                    or fingerprint(value) != item['registry_sha256']
                    or [j['job_id'] for j in value['jobs']] != item['job_ids']
                    or len(value['jobs']) > index['maximum_jobs']):
                raise ValueError('shard bytes, requests or schedule differ from index')
            names.append(name)
            jobs.extend(dict(job_id=j['job_id'], request=j['request']) for j in value['jobs'])
        complete = registry(index['binding_sha256'], index['phase'], jobs)
        if (set(shards) != set(names) or len(jobs) != index['total_jobs']
                or [j['job_id'] for j in complete['jobs']] != [j['job_id'] for j in jobs]
                or fingerprint(complete) != index['complete_registry_sha256']):
            raise ValueError('global phase schedule duplicated, omitted, reordered or changed')
        # Rebuild enforces exact closed index/registry schemas and deterministic partition.
        expected = build(index['binding_sha256'], index['phase'], index['stage'], jobs,
                         index['maximum_shard_bytes'], index['maximum_jobs'])
        if expected != (index, shards):
            raise ValueError('noncanonical sealed phase bundle')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('incomplete sealed phase bundle') from exc
    return True


class ShardedExecutor:
    """One persistent stage root across bounded registered executors."""
    def __init__(self, root, bundle, expected_index_sha256, admit):
        self.root, self.bundle = Path(root), Path(bundle)
        self.admit = admit
        self.index = load((self.bundle/'index.json').read_bytes(), MAX_ARTIFACT_BYTES)
        if fingerprint(self.index) != expected_index_sha256:
            raise ValueError('phase index differs from independently sealed identity')
        self.index_hash = expected_index_sha256
        shards = {}
        for item in self.index.get('shards', []):
            name = item.get('path', '')
            if not re.fullmatch(r'shard-[0-9]{6}\.json', name):
                raise ValueError('unsafe shard path')
            shards[name] = self.read_shard(item)
        verify_bundle(self.index, shards)
        self.lookup = {job: item for item in self.index['shards'] for job in item['job_ids']}
        self.authorize(None)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root/'phase_index.json'
        if path.exists():
            if load(path.read_bytes(), MAX_ARTIFACT_BYTES) != self.index:
                raise ValueError('execution root already bound to another phase index')
        else:
            exclusive_json(path, self.index)

    def read_shard(self, item):
        data = (self.bundle/item['path']).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('sealed shard archive changed')
        value = load(data, self.index['maximum_shard_bytes'])
        if fingerprint(value) != item['registry_sha256']:
            raise ValueError('sealed shard identity changed')
        return value

    def authorize(self, item):
        payload = dict(index=copy.deepcopy(self.index), index_sha256=self.index_hash,
                       shard=copy.deepcopy(item), execution_root=str(self.root.resolve()))
        approved = self.admit(payload)
        if (type(approved) is not dict or approved.get('authorized') is not True
                or approved.get('index_sha256') != self.index_hash
                or approved.get('execution_root') != payload['execution_root']):
            raise ValueError('independent stage/index/root admission failed')

    def execute(self, job_id, backend):
        if job_id not in self.lookup:
            raise ValueError('unscheduled phase job; no dispatch permitted')
        item = self.lookup[job_id]
        self.authorize(item)
        for path in (self.bundle/'index.json', self.root/'phase_index.json'):
            if load(path.read_bytes(), MAX_ARTIFACT_BYTES) != self.index:
                raise ValueError('sealed phase index changed')
        value = self.read_shard(item)
        def admit_registry(reg):
            self.authorize(item)
            if reg != self.read_shard(item):
                raise ValueError('shard registry differs from sealed phase')
            return dict(authorized=True, registry_sha256=item['registry_sha256'],
                        binding_sha256=self.index['binding_sha256'], phase=self.index['phase'])
        engine = RegisteredExecutor(self.root/item['path'].removesuffix('.json'), value, admit_registry)
        return engine.execute(job_id, backend)
