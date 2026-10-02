"""Existing-V16 exploratory stage execution; fixed eight workers.

No scientific admission or confirmation provider is implemented here. Whole
cohort membership and final chronology must be qualified independently.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..confirmatory_v1.journal import exclusive_json, fingerprint
from ..confirmatory_v1.registered_attempt_executor_v2 import load_artifact
from ..confirmatory_v1.streaming_registry_shards_v1 import write_sorted
from ..confirmatory_v1.streaming_registry_executor_v2 import StreamingExecutorV2 as StreamingExecutor
from ..acquisition.raw_archive_v1 import digest


def dispatch(root, binding, stage, jobs, prerequisites, source_guard, backend_factory, workers=8):
    """One immutable per-episode stage, at most 24 requests; no restart/reissue."""
    if stage not in ('methods', 'initial_judges', 'adjudication_judges') or workers != 8:
        raise ValueError('fixed stage and development worker limit required')
    if not prerequisites:
        raise ValueError('pre-dispatch immutable prerequisites required')
    if len(jobs) > 24:
        raise ValueError('bounded single-episode stage required')
    ordered = sorted(jobs, key=lambda j:j['job_id'])
    if len({j['job_id'] for j in ordered}) != len(ordered):
        raise ValueError('duplicate stage request')
    pins = {str(Path(path).resolve()):sha for path,sha in prerequisites.items()}
    def check():
        source_guard()
        if any(digest(Path(path)) != sha for path,sha in pins.items()):
            raise ValueError('pre-dispatch prerequisite changed; no call authorized')
    check()
    root = Path(root); root.mkdir(exist_ok=False)
    declaration = dict(schema='hexar-development-episode-stage/v1', phase='development_qualification',
        stage=stage, binding_sha256=binding, prerequisites=pins, workers=workers,
        exact_job_ids=[j['job_id'] for j in ordered], exact_jobs_sha256=fingerprint(ordered),
        confirmation_authorized=False, provider_qualified=False)
    exclusive_json(root/'stage_declaration.json', declaration)
    index = write_sorted(root/'payloads', binding, 'development_qualification', stage,
        iter(ordered), maximum_shard_bytes=2*1024*1024, maximum_jobs=4) if ordered else None
    receipt = dict(schema='hexar-development-stage-pre-dispatch/v1',
        stage_declaration_sha256=digest(root/'stage_declaration.json'),
        index_sha256=fingerprint(index) if index is not None else None,
        prerequisite_sha256=fingerprint(pins), provider_calls_started=False)
    exclusive_json(root/'pre_dispatch_receipt.json', receipt)
    receipt_hash = digest(root/'pre_dispatch_receipt.json')
    def admit(payload):
        check()
        if (digest(root/'pre_dispatch_receipt.json') != receipt_hash
                or digest(root/'stage_declaration.json') != receipt['stage_declaration_sha256']
                or payload['index_sha256'] != receipt['index_sha256']
                or payload['index']['total_jobs'] != len(ordered)
                or sorted(j for s in payload['index']['shards'] for j in s['job_ids']) != declaration['exact_job_ids']):
            raise ValueError('sealed development stage membership/chronology changed')
        return dict(authorized=True, index_sha256=payload['index_sha256'], execution_root=payload['execution_root'])
    if index is not None:
        engine = StreamingExecutor(root/'attempts', root/'payloads', fingerprint(index), admit)
        def call(job):
            item = engine.lookup[job['job_id']]
            # Factory receives only the exact bounded requested shard.
            from ..confirmatory_v1.streaming_registry_shards_v1 import read_shard
            reg = read_shard(root/'payloads', item, index['maximum_shard_bytes'])
            return job['job_id'], engine.execute(job['job_id'], backend_factory(reg))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = dict(pool.map(call, ordered))
        if any(r['dispatch_performed'] is not True for r in results.values()):
            raise ValueError('new exclusive stage unexpectedly reused an attempt')
        outcomes = {key:r['outcome'] for key,r in results.items()}
    else:
        outcomes = {}
    check()
    exclusive_json(root/'closed_outcomes.json', outcomes)
    completed = dict(schema='hexar-development-stage-completion/v1', phase='development_qualification',
        stage=stage, stage_declaration_sha256=receipt['stage_declaration_sha256'],
        pre_dispatch_receipt_sha256=receipt_hash, closed_outcomes_sha256=digest(root/'closed_outcomes.json'),
        complete_job_ids=declaration['exact_job_ids'], attempts=len(ordered),
        valid=sum(r['status']=='VALID' for r in outcomes.values()),
        confirmation_authorized=False, confirmatory_N=0, alpha_consumed=0)
    exclusive_json(root/'completion_receipt.json', completed)
    return outcomes, completed
