"""Verify expanded battery rows against their sealed unique-request schedule."""
from .journal import fingerprint
from .unique_result_expansion import requests

COMPONENTS=('unsupported_material','overlicensed_specificity','missing_required_unit')


def verify(bundle, expected, freeze_sha256):
    plan=bundle.get('unique_request_plan')
    if not isinstance(plan,dict) or fingerprint(plan)!=bundle.get('unique_request_plan_sha256'):
        raise ValueError('hash-bound unique request plan required')
    if (plan.get('status')!='SEALED_FOR_CONFIRMATORY_GENERATION'
            or plan.get('binding_freeze_sha256')!=freeze_sha256
            or plan.get('implementation_binding_qualified') is not True):
        raise ValueError('unique plan is not sealed under this qualified freeze')
    byid=requests(plan)
    aliases={}
    for row in plan['aliases']:
        question,condition=row['job_id'].split('-',1)
        key=(row['episode_id'],row['method'],question,condition)
        if key in aliases:raise ValueError('duplicate scheduled alias')
        aliases[key]=row['unique_request_id']
    if set(aliases)!=expected:
        raise ValueError('unique schedule does not cover the exact frozen battery')
    clusters={(k[0],k[1]) for k in expected}
    for episode,method in clusters:
        if sum(r['episode_id']==episode and r['method']==method for r in byid.values())!=6:
            raise ValueError('six unique requests per episode/method required')
    dispositions={};seen=set()
    for job in bundle['jobs']:
        key=(job['recording_id'],job['method'],job['question_id'],job['condition'])
        if key in seen or key not in aliases:raise ValueError('extra/duplicate expanded battery row')
        seen.add(key);uid=aliases[key]
        if job.get('source_unique_request_id')!=uid:
            raise ValueError('battery row names another unique request')
        required=('response_sha256','scoring_artifact_sha256',*COMPONENTS)
        if any(field not in job for field in required):raise ValueError('explicit output/scoring disposition required')
        signature=tuple(job[field] for field in required)
        if uid in dispositions and dispositions[uid]!=signature:
            raise ValueError('identical aliases have different raw output, scoring or endpoint labels')
        dispositions[uid]=signature
    if seen!=expected or set(dispositions)!=set(byid):
        raise ValueError('every scheduled unique outcome and alias must be retained')
