"""Pure alias expansion, preserving one unique attempt and scoring disposition.

No provider calls, retries, scoring decisions, admission or significance tests.
"""
import copy
import hashlib


def requests(plan):
    if plan.get('schema')!='hexar-within-episode-unique-request-plan/v1':raise ValueError('known unique-request plan required')
    rows=plan['requests'];byid={r['unique_request_id']:r for r in rows}
    if len(byid)!=len(rows) or len(rows)!=plan['unique_requests']:raise ValueError('unique request identity/count mismatch')
    seen=set()
    if len(plan['aliases'])!=plan['battery_cells']:raise ValueError('all battery aliases required')
    for row in plan['aliases']:
        key=(row['episode_id'],row['method'],row['job_id'])
        if key in seen or row['unique_request_id'] not in byid:raise ValueError('duplicate or unknown alias')
        seen.add(key);source=byid[row['unique_request_id']]
        if (row['episode_id'],row['method'])!=(source['episode_id'],source['method']):raise ValueError('cross-episode or cross-method alias forbidden')
    if {r['unique_request_id'] for r in plan['aliases']}!=set(byid):raise ValueError('unique request without battery alias')
    return byid


def expand_outputs(plan,outcomes):
    expected=requests(plan);byid={}
    for row in outcomes:
        uid=row['unique_request_id']
        if uid in byid or uid not in expected:raise ValueError('duplicate/unknown unique method outcome')
        source=expected[uid]
        if (row['episode_id'],row['method'],row['request_sha256'],row['packet_sha256'])!=(source['episode_id'],source['method'],source['request_sha256'],source['packet_sha256']):
            raise ValueError('unique method outcome provenance mismatch')
        if row['status'] not in ('VALID','TECHNICAL_FAILURE','INDETERMINATE_AFTER_CRASH'):raise ValueError('closed unique method attempt required')
        if row['status']=='VALID':
            if type(row['answer']) is not str or not row['answer'].strip() or hashlib.sha256(row['answer'].encode()).hexdigest()!=row['answer_sha256']:
                raise ValueError('exact retained raw answer and hash required')
        byid[uid]=row
    if set(byid)!=set(expected):raise ValueError('every unique request needs an explicit closed disposition')
    first={uid:min(r['job_id'] for r in plan['aliases'] if r['unique_request_id']==uid) for uid in expected}
    cells=[]
    for alias in plan['aliases']:
        source=byid[alias['unique_request_id']];is_alias=alias['job_id']!=first[alias['unique_request_id']]
        cells.append(dict(episode_id=alias['episode_id'],method=alias['method'],job_id=alias['job_id'],
                          source_unique_request_id=alias['unique_request_id'],is_generation_alias=is_alias,
                          status=source['status'],answer=source.get('answer'),answer_sha256=source.get('answer_sha256'),
                          packet_sha256=source['packet_sha256'],cell_generation_calls=0 if is_alias else source.get('model_calls',0),
                          shared_raw_output=True,error=source.get('error')))
    return cells


def expand_labels(plan,labels):
    expected=requests(plan)
    if set(labels)!=set(expected):raise ValueError('one closed scoring disposition per unique method request required')
    for value in labels.values():
        if value.get('status') not in ('PASS','FAIL','UNRESOLVED'):raise ValueError('closed scoring disposition required; no pending C')
    return [dict(episode_id=a['episode_id'],method=a['method'],job_id=a['job_id'],
                 source_unique_request_id=a['unique_request_id'],scoring_reused_for_identical_request=True,
                 disposition=copy.deepcopy(labels[a['unique_request_id']])) for a in plan['aliases']]
