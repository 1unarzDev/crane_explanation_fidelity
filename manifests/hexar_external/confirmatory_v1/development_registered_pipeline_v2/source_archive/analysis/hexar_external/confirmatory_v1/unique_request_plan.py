"""Pure prospective per-episode deduplication; never dispatches or admits outputs.

Identical within-episode requests reuse one semantic attempt. Distinct episodes,
methods, queries, evidence or fully specified request configuration never merge.
"""
import math
from .journal import fingerprint
from .blind_bank import PACKET_KEYS,reject_metadata


def finite_json(value):
    if type(value) is dict:
        if any(type(k) is not str for k in value):raise ValueError('string JSON keys required')
        for child in value.values():finite_json(child)
    elif type(value) is list:
        for child in value:finite_json(child)
    elif type(value) is float:
        if not math.isfinite(value):raise ValueError('finite request numbers required')
    elif type(value) not in (str,int,bool,type(None)):
        raise ValueError('canonical JSON request values required')


def build(entries):
    if not entries:raise ValueError('nonempty complete battery plan required')
    unique={};aliases=[];seen=set()
    for entry in entries:
        if set(entry)!={'episode_id','method','job_id','packet','implementation_binding'}:
            raise ValueError('closed request-plan entry required')
        for field in ('episode_id','method','job_id'):
            if type(entry[field]) is not str or not entry[field].strip():raise ValueError('nonempty administrative identity required')
        identity=(entry['episode_id'],entry['method'],entry['job_id'])
        if identity in seen:raise ValueError('duplicate battery identity')
        seen.add(identity)
        if set(entry['packet'])!=set(PACKET_KEYS):raise ValueError('complete equal-evidence packet required')
        reject_metadata(entry['packet']);finite_json(entry['packet'])
        binding=entry['implementation_binding']
        if type(binding) is not dict or not binding:raise ValueError('nonempty whole implementation binding required')
        finite_json(binding)
        request=dict(packet=entry['packet'],implementation_binding=binding)
        digest=fingerprint(request)
        key=(entry['episode_id'],entry['method'],digest)
        handle=fingerprint(dict(episode=key[0],method=key[1],request_sha256=key[2]))
        unique.setdefault(key,dict(unique_request_id=handle,episode_id=key[0],method=key[1],request_sha256=digest,
                                   packet_sha256=fingerprint(entry['packet']),implementation_binding_sha256=fingerprint(binding)))
        aliases.append(dict(episode_id=identity[0],method=identity[1],job_id=identity[2],unique_request_id=handle))
    return dict(schema='hexar-within-episode-unique-request-plan/v1',status='PURE_PLAN_NOT_ADMITTED',
                dispatch_authorized=False,semantic_calls=0,
                battery_cells=len(entries),unique_requests=len(unique),aliases=sorted(aliases,key=lambda a:(a['episode_id'],a['method'],a['job_id'])),
                requests=sorted(unique.values(),key=lambda r:r['unique_request_id']),
                scope='No cross-episode/method reuse. A result or technical failure is reused for all byte-identical request aliases; no alias-triggered retry.',
                implementation_binding_qualified=False)
