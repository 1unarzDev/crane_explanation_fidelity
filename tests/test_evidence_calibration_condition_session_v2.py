from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import evidence_calibration_condition_session_v2 as module
from evidence_calibration_io import canonical_sha256
from test_evidence_calibration_mcp_stdio_v5 import config,rpc


def configurations(tmp_path,methods=('B2',),**overrides):
    rows=[]
    for method in methods:
        parent=tmp_path/method;parent.mkdir()
        c=config(parent,method,**overrides)
        c.update(scope_registry=str(tmp_path/'registry'),execution_plan=str(tmp_path/'plan.json'),
            execution_scope={'campaign_id':'synthetic-dev','episode_id':'synthetic-one','condition_id':'E0','method_id':method},plan_sha256='0'*64)
        rows.append(c)
    plan=module.build_plan(rows)
    module.write_once(tmp_path/'plan.json',plan)
    sha=hashlib.sha256((tmp_path/'plan.json').read_bytes()).hexdigest()
    for row in rows:row['plan_sha256']=sha
    module.create_registry(tmp_path/'registry',tmp_path/'plan.json',sha)
    return rows


@pytest.mark.parametrize('method',['B0','B1','B2','B3','B4'])
def test_planned_scopes_are_admitted_with_exact_configuration_hash(tmp_path,method):
    c=configurations(tmp_path,methods=(method,))[0];owner=module.claim(c)
    r=json.loads((owner/'session-owner.intent.json').read_text())
    assert r['planned_configuration_sha256']==module.configuration_hash(c)
    assert r['configuration_sha256']==canonical_sha256(c)
    assert r['plan_sha256']==hashlib.sha256(Path(c['execution_plan']).read_bytes()).hexdigest()
    assert r['source_sha256']==module.source_hashes()
    with pytest.raises(ValueError,match='already reserved'):module.claim(c)


@pytest.mark.parametrize('change',['scope','records','cpu','identity','registry','plan_path','method','campaign'])
def test_configuration_changes_are_denied_before_ownership_or_server(tmp_path,change):
    c=configurations(tmp_path)[0]
    if change=='scope':c['execution_scope']['condition_id']='E1'
    elif change=='records':c['records']=str(tmp_path/'new-events')
    elif change=='cpu':c['computation_cpu_limit']['total_nanoseconds']=6_000_000_000
    elif change=='identity':c['identity']['workspace_sha256']='b'*64
    elif change=='registry':c['scope_registry']=str(tmp_path/'second-registry')
    elif change=='plan_path':
        p=tmp_path/'copied-plan.json';p.write_bytes(Path(c['execution_plan']).read_bytes());c['execution_plan']=str(p)
    elif change=='method':c['identity']['method_id']=c['execution_scope']['method_id']='B4'
    elif change=='campaign':c['execution_scope']['campaign_id']='new-campaign'
    with pytest.raises(ValueError):module.claim(c)
    assert not list((tmp_path/'registry').glob('*/session-owner.intent.json'))
    assert not Path(c['records']).exists()


@pytest.mark.parametrize('change',['bytes','source','authorization','duplicate','configuration','campaign','schema','empty'])
def test_altered_plan_cannot_be_used_or_create_an_alternative_registry(tmp_path,change):
    c=configurations(tmp_path)[0];p=Path(c['execution_plan']);plan=json.loads(p.read_text())
    if change=='bytes':p.write_bytes(p.read_bytes()+b' ')
    else:
        if change=='source':plan['source_sha256'][module.__file__.split('/')[-1]]='b'*64
        elif change=='authorization':plan['model_execution_authorized']=True
        elif change=='duplicate':plan['entries'].append(deepcopy(plan['entries'][0]))
        elif change=='configuration':plan['entries'][0]['configuration_sha256']='b'*64
        elif change=='campaign':plan['entries'][0]['execution_scope']['campaign_id']='other'
        elif change=='schema':plan['schema']='confirmatory'
        elif change=='empty':plan['entries']=[]
        p.write_text(json.dumps(plan))
        # Even a recomputed supplied digest cannot change the already-bound registry.
        c['plan_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(ValueError):module.claim(c)
    assert not list((tmp_path/'registry').glob('*/session-owner.intent.json'))
    with pytest.raises(ValueError):module.create_registry(tmp_path/'alternative',p,c['plan_sha256'])
    assert not (tmp_path/'alternative').exists()


def test_duplicate_scope_with_different_budget_is_rejected_by_builder(tmp_path):
    c=configurations(tmp_path)[0];sibling=deepcopy(c);sibling['max_calls']=100
    with pytest.raises(ValueError,match='duplicate'):module.build_plan([c,sibling])


def test_source_drift_rejected_before_session_ownership(tmp_path,monkeypatch):
    c=configurations(tmp_path)[0];original=module.source_hashes
    monkeypatch.setattr(module,'source_hashes',lambda:{**original(),'evidence_calibration_condition_session_v2.py':'b'*64})
    with pytest.raises(ValueError,match='source'):module.claim(c)
    assert not list((tmp_path/'registry').glob('*/session-owner.intent.json'))


def test_no_ledger_or_registry_adoption_after_planned_construction_failure(tmp_path):
    c=configurations(tmp_path,max_messages=0)[0]
    with pytest.raises(ValueError):module.serve(c,io.BytesIO(),io.BytesIO())
    owner=Path(c['scope_registry'])/canonical_sha256(c['execution_scope'])
    assert json.loads((owner/'session-owner.result.json').read_text())['status']=='FAILED_RETAIN_NO_RESTART'
    with pytest.raises(ValueError,match='already reserved'):module.claim(c)
    with pytest.raises(FileExistsError):module.create_registry(Path(c['scope_registry']),Path(c['execution_plan']),c['plan_sha256'])


@pytest.mark.parametrize('stage',['intent','terminal'])
def test_planned_retention_failure_keeps_exclusive_owner(tmp_path,monkeypatch,stage):
    c=configurations(tmp_path)[0];original=module.write_once
    def fail(path,row):
        if path.name==('session-owner.intent.json' if stage=='intent' else 'session-owner.result.json'):raise OSError('injected retention failure')
        return original(path,row)
    monkeypatch.setattr(module,'write_once',fail)
    with pytest.raises(OSError):module.serve(c,io.BytesIO(),io.BytesIO())
    with pytest.raises(ValueError,match='already reserved'):module.claim(c)


def test_actual_plan_bound_stdio_computation_and_restart_denial(tmp_path):
    from evidence_calibration_tool_broker_v7 import COMPUTE
    c=configurations(tmp_path)[0];p=tmp_path/'configuration.json';p.write_text(json.dumps(c))
    wire=b''.join([rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'synthetic','version':'1'}},id=0),rpc('notifications/initialized',id=None),rpc('tools/call',{'name':COMPUTE,'arguments':{'code':'print(42)'}})])
    argv=[sys.executable,module.__file__,'--configuration',str(p)]
    r=subprocess.run(argv,input=wire,capture_output=True,timeout=10)
    assert r.returncode==0 and r.stderr==b''
    rows=[json.loads(row) for row in r.stdout.splitlines()]
    assert rows[-1]['result']['structuredContent']['result']['stdout']=='42\n'
    assert 'execution_scope' not in json.dumps(rows) and 'execution_plan' not in json.dumps(rows)
    again=subprocess.run(argv,input=wire,capture_output=True,timeout=10)
    assert again.returncode!=0 and again.stdout==b'' and b'already reserved' in again.stderr
