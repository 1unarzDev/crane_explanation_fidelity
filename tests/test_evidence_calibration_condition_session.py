import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_condition_session import ExecutionScope,create_registry,claim,serve
from evidence_calibration_mcp_stdio_v5 import encode
from test_evidence_calibration_mcp_stdio_v5 import config,rpc


def configuration(tmp_path,method='B2'):
    c=config(tmp_path,method)
    c.update(scope_registry=str(tmp_path/'registry'),execution_scope={
        'campaign_id':'synthetic-dev','episode_id':'synthetic-one','condition_id':'E0','method_id':method},
        plan_sha256='a'*64)
    create_registry(Path(c['scope_registry']),'synthetic-dev',c['plan_sha256'])
    return c


def test_scope_claim_binds_configuration_and_sources_before_session(tmp_path):
    from evidence_calibration_io import canonical_sha256
    c=configuration(tmp_path);owner=claim(c)
    row=json.loads((owner/'session-owner.intent.json').read_text())
    assert row['execution_scope']==c['execution_scope']
    assert row['configuration_sha256']==canonical_sha256(c)
    assert row['computation_cpu_limit']==c['computation_cpu_limit']
    assert len(row['source_sha256'])==5 and row['terminal_record_pending']
    assert not Path(c['records']).exists()


@pytest.mark.parametrize('change',['records','cpu','workspace_identity','model_metadata','plan'])
def test_new_configuration_cannot_reset_condition_ownership(tmp_path,change):
    c=configuration(tmp_path);claim(c)
    if change=='records':c['records']=str(tmp_path/'fresh-events')
    elif change=='cpu':c['computation_cpu_limit']['total_nanoseconds']=6_000_000_000
    elif change=='workspace_identity':c['identity']['workspace_sha256']='b'*64
    elif change=='model_metadata':c['identity']['model_configuration_sha256']='c'*64
    elif change=='plan':c['plan_sha256']='b'*64
    with pytest.raises(ValueError,match='already reserved|binding mismatch'):claim(c)
    assert not Path(c['records']).exists()


def test_all_methods_and_distinct_conditions_have_distinct_owners(tmp_path):
    c=configuration(tmp_path)
    owners=[]
    for method in ['B0','B1','B2','B3','B4']:
        c['identity']['method_id']=c['execution_scope']['method_id']=method
        for level in ['E0','E1']:
            c['execution_scope']['condition_id']=level
            owners.append(claim(c))
    assert len(set(owners))==10


def test_concurrent_processes_cannot_claim_sibling_servers(tmp_path):
    c=configuration(tmp_path);path=tmp_path/'config.json';path.write_text(json.dumps(c))
    script="import json,sys;from pathlib import Path;sys.path.insert(0,'analysis');from evidence_calibration_condition_session import claim;claim(json.load(open(sys.argv[1])))"
    processes=[subprocess.Popen([sys.executable,'-c',script,str(path)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
    rows=[(p.communicate(timeout=5),p.returncode) for p in processes]
    assert sorted(code for _,code in rows)==[0,1]
    assert sum(b'already reserved' in output[1] for output,_ in rows)==1
    assert not Path(c['records']).exists()


def test_actual_stdio_session_retains_owner_and_cannot_restart(tmp_path):
    from evidence_calibration_tool_broker_v7 import COMPUTE
    c=configuration(tmp_path);path=tmp_path/'config.json';path.write_text(json.dumps(c))
    wire=b''.join([rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'synthetic','version':'1'}},id=0),
        rpc('notifications/initialized',id=None),rpc('tools/call',{'name':COMPUTE,'arguments':{'code':'print(42)'}})])
    argv=[sys.executable,str(ROOT/'analysis/evidence_calibration_condition_session.py'),'--configuration',str(path)]
    result=subprocess.run(argv,input=wire,capture_output=True,timeout=10)
    assert result.returncode==0 and result.stderr==b''
    rows=[json.loads(line) for line in result.stdout.splitlines()]
    assert rows[-1]['result']['structuredContent']['result']['stdout']=='42\n'
    assert 'execution_scope' not in json.dumps(rows)
    owner=next(Path(c['scope_registry']).glob('*/session-owner.result.json'))
    assert json.loads(owner.read_text())['computation_cpu_ledger']['spent_nanoseconds']>0
    again=subprocess.run(argv,input=wire,capture_output=True,timeout=10)
    assert again.returncode!=0 and again.stdout==b'' and b'already reserved' in again.stderr


def test_server_construction_failure_stays_owned(tmp_path):
    c=configuration(tmp_path);c['max_messages']=0
    with pytest.raises(ValueError):serve(c,io.BytesIO(),io.BytesIO())
    row=json.loads(next(Path(c['scope_registry']).glob('*/session-owner.result.json')).read_text())
    assert row['status']=='FAILED_RETAIN_NO_RESTART' and row['computation_cpu_ledger'] is None
    c['max_messages']=20
    with pytest.raises(ValueError,match='already reserved'):serve(c,io.BytesIO(),io.BytesIO())


@pytest.mark.parametrize('stage',['intent','terminal'])
def test_retention_failure_leaves_ownership_and_no_replacement(tmp_path,monkeypatch,stage):
    import evidence_calibration_condition_session as module
    c=configuration(tmp_path);original=module.write_once
    def fail(path,row):
        if path.name==f'session-owner.{"intent" if stage=="intent" else "result"}.json':raise OSError('injected retention failure')
        return original(path,row)
    monkeypatch.setattr(module,'write_once',fail)
    with pytest.raises(OSError):serve(c,io.BytesIO(),io.BytesIO())
    assert not list(Path(c['scope_registry']).glob('*/session-owner.result.json'))
    with pytest.raises(ValueError,match='already reserved'):claim(c)


@pytest.mark.parametrize('defect',['method','scope','extra','registry_inside','records_overlap','registry_binding'])
def test_invalid_bindings_rejected_before_claim(tmp_path,defect):
    c=configuration(tmp_path)
    if defect=='method':c['identity']['method_id']='B4'
    elif defect=='scope':c['execution_scope']['episode_id']='../truth'
    elif defect=='extra':c['retry']=True
    elif defect=='registry_inside':c['scope_registry']=c['workspace']
    elif defect=='records_overlap':c['records']=str(Path(c['scope_registry'])/'events')
    elif defect=='registry_binding':c['plan_sha256']='b'*64
    with pytest.raises(ValueError):claim(c)
    assert not list((tmp_path/'registry').glob('*/session-owner.intent.json'))


def test_partial_registry_cannot_be_initialized_or_used(tmp_path):
    c=configuration(tmp_path);(Path(c['scope_registry'])/'registry.intent.json').unlink()
    with pytest.raises(FileExistsError):create_registry(Path(c['scope_registry']),'synthetic-dev','a'*64)
    with pytest.raises(FileNotFoundError):claim(c)
