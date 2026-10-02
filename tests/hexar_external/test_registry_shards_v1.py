import copy
import hashlib

import pytest

from analysis.hexar_external.confirmatory_v1.journal import canonical, fingerprint
from analysis.hexar_external.confirmatory_v1.registry_shards_v1 import (
    ShardedExecutor, build, verify_bundle, write,
)


def jobs(n=9, padding=400):
    return [dict(job_id=f'opaque-{i:04d}', request=dict(role='method', maximum_response_bytes=1024,
                 payload={'visible': 'x'*padding})) for i in range(n)]


def approved(payload):
    return dict(authorized=payload['index']['phase']=='development_qualification',
                index_sha256=payload['index_sha256'], execution_root=payload['execution_root'])


def response(request):
    return dict(raw_response=b'{"answer":"fixture"}', stdout=b'fixture', stderr=b'',
                returncode=0, transport_policy_passed=True)


def bundle(tmp_path, n=9):
    index, shards = build('f'*64, 'development_qualification', 'methods', jobs(n), 2300, 3)
    write(tmp_path/'bundle', index, shards)
    return index, shards


def test_partition_is_bounded_deterministic_and_complete():
    index, shards = build('f'*64, 'development_qualification', 'methods', jobs(), 2300, 3)
    assert verify_bundle(index, shards)
    assert (index, shards)==build('f'*64, 'development_qualification', 'methods', list(reversed(jobs())), 2300, 3)
    assert index['total_jobs']==9 and len(index['shards'])>=3
    assert all(s['bytes']<=2300 and len(s['job_ids'])<=3 for s in index['shards'])
    assert [j for s in index['shards'] for j in s['job_ids']]==[j['job_id'] for j in jobs()]


def test_byte_and_job_limits_are_independent():
    i,_=build('f'*64, 'development_qualification', 'methods', jobs(7, 10), 10000, 2)
    assert [len(s['job_ids']) for s in i['shards']]==[2,2,2,1]
    i,_=build('f'*64, 'development_qualification', 'methods', jobs(4,1000), 1800, 100)
    assert len(i['shards'])==4
    with pytest.raises(ValueError,match='one complete request'):
        build('f'*64,'development_qualification','methods',jobs(1,3000),1800,100)


def test_duplicate_or_empty_schedule_refused():
    with pytest.raises(ValueError,match='unique'):
        build('f'*64,'development_qualification','methods',jobs(2)+jobs(1))
    with pytest.raises(ValueError,match='nonempty'):
        build('f'*64,'development_qualification','methods',[])


@pytest.mark.parametrize('change', ['extra','omitted','reordered','duplicate','request'])
def test_bundle_verification_rejects_changed_global_schedule(change):
    i,s=build('f'*64,'development_qualification','methods',jobs(9),2300,3)
    i,s=copy.deepcopy(i),copy.deepcopy(s)
    if change=='extra':s['shard-999999.json']=s[next(iter(s))]
    elif change=='omitted':i['shards'].pop()
    elif change=='reordered':i['shards'].reverse()
    elif change=='duplicate':i['shards'][1]['job_ids'][0]=i['shards'][0]['job_ids'][0]
    else:s[next(iter(s))]['jobs'][0]['request']['payload']['visible']='changed'
    with pytest.raises(ValueError):verify_bundle(i,s)


def test_all_shards_use_one_persistent_phase_index_and_no_reissue(tmp_path):
    i,_=bundle(tmp_path)
    engine=ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),approved)
    calls=[]
    for job in jobs():
        result=engine.execute(job['job_id'],lambda req:calls.append(req) or response(req))
        assert result['dispatch_performed'] and result['outcome']['status']=='VALID'
    recovered=ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),approved)
    for job in jobs():
        assert not recovered.execute(job['job_id'],lambda _:pytest.fail('no reissue'))['dispatch_performed']
    assert len(calls)==9
    with pytest.raises(ValueError,match='unscheduled'):
        recovered.execute('new-job',lambda _:pytest.fail('no dispatch'))


def test_crashed_shard_job_never_reissued(tmp_path):
    i,_=bundle(tmp_path)
    engine=ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),approved)
    def crash(_):raise KeyboardInterrupt('synthetic host interruption')
    with pytest.raises(KeyboardInterrupt):engine.execute('opaque-0000',crash)
    closed=engine.execute('opaque-0000',lambda _:pytest.fail('no crash reissue'))
    assert closed['outcome']['status']=='INDETERMINATE_AFTER_CRASH' and not closed['dispatch_performed']
    assert engine.execute('opaque-0008',response)['dispatch_performed']


def test_denied_admission_creates_no_execution_namespace(tmp_path):
    i,_=bundle(tmp_path)
    with pytest.raises(ValueError,match='admission'):
        ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),lambda _:dict(authorized=False))
    assert not (tmp_path/'run').exists()


def test_changed_phase_index_or_shard_prevents_dispatch(tmp_path):
    i,_=bundle(tmp_path)
    engine=ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),approved)
    name=i['shards'][0]['path']
    (tmp_path/'bundle'/name).write_bytes(b'{}')
    with pytest.raises(ValueError,match='archive changed'):
        engine.execute('opaque-0000',lambda _:pytest.fail('no dispatch'))


def test_changed_execution_root_binding_refused(tmp_path):
    i,_=bundle(tmp_path)
    ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),approved)
    new=copy.deepcopy(i);new['stage']='initial_judges'
    shards={item['path']: __import__('json').loads((tmp_path/'bundle'/item['path']).read_text()) for item in i['shards']}
    write(tmp_path/'second',new,shards)
    with pytest.raises(ValueError,match='already bound'):
        ShardedExecutor(tmp_path/'run',tmp_path/'second',fingerprint(new),approved)


def test_exclusive_bundle_preserves_failed_namespace(tmp_path):
    i,s=bundle(tmp_path)
    with pytest.raises(FileExistsError):write(tmp_path/'bundle',i,s)


def test_admission_rechecked_before_dispatch_and_size_bound_not_response_cap(tmp_path):
    i,_=bundle(tmp_path)
    allowed=[True]
    def admission(payload):
        return dict(approved(payload),authorized=allowed[0])
    engine=ShardedExecutor(tmp_path/'run',tmp_path/'bundle',fingerprint(i),admission)
    allowed[0]=False
    with pytest.raises(ValueError,match='admission'):
        engine.execute('opaque-0000',lambda _:pytest.fail('no dispatch'))
    allowed[0]=True
    r=engine.execute('opaque-0000',lambda req:dict(response(req),raw_response=b'{"answer":"'+b'x'*1500+b'"}'))
    assert r['outcome']['status']=='TECHNICAL_FAILURE'


def test_registry_above_single_response_bound_splits_without_changing_requests(tmp_path):
    scheduled=jobs(96,20000)
    i,s=build('f'*64,'development_qualification','methods',scheduled,128*1024,32)
    assert sum(item['bytes'] for item in i['shards'])>1048576
    assert len(i['shards'])>10 and verify_bundle(i,s)
    assert all(j['request']['maximum_response_bytes']==1024 for shard in s.values() for j in shard['jobs'])
    write(tmp_path/'large',i,s)
    engine=ShardedExecutor(tmp_path/'run',tmp_path/'large',fingerprint(i),approved)
    assert engine.execute('opaque-0095',response)['outcome']['status']=='VALID'
