"""Versioned streaming executor with serialized durable registry initialization.

Locks protect only registry construction, never a provider call. Partial prior
registry writes remain indeterminate and are rejected, never overwritten.
Scientific/provider admission remains an independent caller responsibility.
"""
import fcntl
from pathlib import Path

from .streaming_registry_shards_v1 import StreamingExecutor, verify, read_index, read_shard
from .registered_attempt_executor_v2 import RegisteredExecutor, MAX_ARTIFACT_BYTES
from .strict_json import load
from .journal import exclusive_json


class StreamingExecutorV2(StreamingExecutor):
    def __init__(self, root, bundle, expected_index_sha256, admit):
        self.root,self.bundle,self.admit=Path(root),Path(bundle),admit
        self.index=verify(self.bundle,expected_index_sha256);self.index_hash=expected_index_sha256
        self.lookup={job:item for item in self.index['shards'] for job in item['job_ids']}
        self.authorize(None)
        self.root.mkdir(parents=True,exist_ok=True)
        with (self.root/'.phase_registry_init.lock').open('a+b') as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            self.authorize(None)
            path=self.root/'phase_index.json'
            if path.exists():
                if load(path.read_bytes(),MAX_ARTIFACT_BYTES)!=self.index:
                    raise ValueError('execution root bound to another or partial phase; no overwrite')
            else:
                exclusive_json(path,self.index)

    def execute(self, job_id, backend):
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
        shard=item['path'].removesuffix('.json')
        with (self.root/(shard+'.registry_init.lock')).open('a+b') as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            # A second job/thread/process cannot observe an in-progress
            # registered_jobs.json write. A crashed partial remains rejected.
            engine=RegisteredExecutor(self.root/shard,value,admit_registry)
        # Existing independent per-job lock/no-reissue semantics protect calls.
        return engine.execute(job_id,backend)
