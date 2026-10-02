"""Stable CLI token-usage accounting from retained closed attempt archives."""
import json
from pathlib import Path

from ..confirmatory_v1.journal import fingerprint
from ..confirmatory_v1.registered_attempt_executor_v2 import load_artifact
from ..confirmatory_v1.streaming_registry_shards_v1 import read_shard
from ..acquisition.raw_archive_v1 import digest


def collect(base):
    base=Path(base);d=load_artifact(base/'declaration.json');rows=[]
    for episode in d['records']:
        for stage in ('methods','initial_judges','adjudication_judges'):
            folder=base/episode['relative_path']/stage
            if not (folder/'completion_receipt.json').exists():continue
            receipt=load_artifact(folder/'pre_dispatch_receipt.json')
            if receipt['index_sha256'] is None:continue
            index=load_artifact(folder/'payloads/index.json')
            if fingerprint(index)!=receipt['index_sha256']:raise ValueError('usage source index changed')
            for item in index['shards']:
                reg=read_shard(folder/'payloads',item,index['maximum_shard_bytes'])
                root=folder/'attempts'/item['path'].removesuffix('.json')
                for request in reg['jobs']:
                    role=request['request']['role']
                    if role=='contract':continue
                    identity=dict(opaque_job=request['job_id']);handle=fingerprint(dict(freeze_sha256=fingerprint(d),job=identity))
                    outcome=load_artifact(root/'journal'/(handle+'.outcome.json'))['outcome']
                    path=root/fingerprint(identity)/'stdout.bin'
                    if digest(path)!=outcome['raw_sha256']['stdout.bin']:raise ValueError('usage transport source changed')
                    usage=None
                    for line in path.read_bytes().splitlines():
                        try:event=json.loads(line)
                        except ValueError:continue
                        if isinstance(event,dict) and event.get('type')=='turn.completed':usage=event.get('usage')
                    rows.append(dict(episode_id=episode['episode_id'],role=role,stage=stage,status=outcome['status'],
                        usage=usage,stdout_sha256=digest(path)))
    keys=('input_tokens','cached_input_tokens','output_tokens')
    return dict(provider_attempts_in_closed_stages=len(rows),usage_available_attempts=sum(isinstance(r['usage'],dict) for r in rows),
        totals={k:sum(r['usage'].get(k,0) for r in rows if isinstance(r['usage'],dict)) for k in keys},
        rows=rows,cost='Unavailable; token usage is reported without assuming a price or immutable served backend.',
        latency='Not stably timestamped in the retained per-attempt JSON; transient filesystem timing is not presented as reproducible provider latency.')
