import json
import hashlib
from pathlib import Path
import pytest
import run_roboboat_full_population_inventory_v2 as inventory
import run_roboboat_full_population_responses_v2 as responses
import run_roboboat_full_response_safety_amendment_v1 as safety
from test_roboboat_full_population_responses_v2 import fixture


def population(tmp_path, *, fail=False, safe_transport=False):
    registry,captures,path=fixture(tmp_path)
    d=responses.prepare(registry,captures,path,allow_completed_subset=True)
    root=tmp_path/'responses'
    if safe_transport:
        root.mkdir()
        amendment=tmp_path/'safety-amendment.json'
        safety.prepare(path,root,amendment)
        (root/'transport-amendment-bindings.json').write_text(json.dumps({
            'schema':'roboboat-response-operational-amendments/v1','quality_reissues':0,
            'method_sources_unchanged':True,'amendments':[inventory.binding(amendment)]}))
    def caller(cache,role,work,prompt,model,effort,schema,**kwargs):
        if fail: raise RuntimeError('construction timeout')
        request={'transport':'marine-isolated-login-cli/v1','role':role,'model':model,'effort':effort,
                 'prompt':prompt,'schema':schema,'allow_tools':True,
                 'workspace_files':{p.relative_to(work).as_posix():inventory.digest(p) for p in work.rglob('*') if p.is_file()},
                 'transport_sha256':d['transport']['sha256']}
        if safe_transport:
            request.update(transport='marine-isolated-login-cli/v2-safe-errors',timeout_s=300,
                transport_sha256=inventory.digest(Path(safety.safe.__file__)),
                isolation_source_sha256=d['transport']['sha256'])
        key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
        raw={'request':request,'status':'valid','attempt_count':1,'return_code':0,'cache_key':key,
             'parsed_final':{'answer':'Construction baseline answer.'},'latency_s':0}
        cache.mkdir(parents=True,exist_ok=True);(cache/(key+'.json')).write_text(json.dumps(raw))
        return raw
    for entry in d['entries']: responses.execute(entry,d,path,root,caller=caller)
    return path,root,d


def test_safe_transport_receipts_require_predeclared_operational_amendment(tmp_path):
    path,root,d=population(tmp_path,safe_transport=True)
    result=inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')
    assert result['method_answer_counts']=={'B2':3,'B4':3}
    deps={Path(b['path']).name for b in result['dependencies']}
    assert 'safety-amendment.json' in deps and 'roboboat_isolated_transport_v2.py' in deps


def test_safe_receipt_without_amendment_refuses_source_admission(tmp_path):
    path,root,d=population(tmp_path,safe_transport=True)
    (root/'transport-amendment-bindings.json').unlink()
    with pytest.raises(FileNotFoundError):
        inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')


@pytest.mark.parametrize('attack',['answer','attempts','role'])
def test_b2_raw_provider_receipt_tampering_is_rejected(tmp_path,attack):
    path,root,d=population(tmp_path)
    entry=d['entries'][0];answer=root/'responses'/entry['id']/'B2.json'
    value=json.loads(answer.read_text());raw_path=root/'calls'/(value['cache_key']+'.json')
    raw=json.loads(raw_path.read_text())
    if attack=='answer':raw['parsed_final']['answer']='fabricated response'
    elif attack=='attempts':raw['attempt_count']=2
    else:raw['request']['role']='different-condition'
    raw_path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='provider receipt'):
        inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')


def rebind_candidate(root,entry):
    folder=root/'responses'/entry['id']; terminal=folder/'response-terminal.json'
    t=json.loads(terminal.read_text())
    t['B4_candidate']=inventory.binding(folder/'B4.json')
    t['retained_outputs']['B4.json']=t['B4_candidate']
    terminal.write_text(json.dumps(t))


def test_actual_full_inventory_prepare_and_qualified_generic_execution(tmp_path):
    path,root,d=population(tmp_path)
    bank=tmp_path/'bank'; declaration=tmp_path/'inventory.json'
    result=inventory.prepare(path,root,bank,declaration)
    assert result['schema']=='roboboat-full-population-inventory-declaration/v2'
    assert result['method_answer_counts']=={'B2':3,'B4':3}
    joins=json.loads((bank/'evaluator-join.json').read_text())['entries']
    b4=[j for j in joins if j['method']=='B4']
    assert all(j['answer_provenance']['kind']=='FULL_CRANE_V2_TERMINAL_BOUND_ZERO_MODEL' for j in b4)
    assert all('full_pipeline' in j['answer_provenance'] for j in b4)
    calls=[]
    def executor(case,slot,freeze,out):
        calls.append((case['case_id'],slot))
        assert set(case)=={'case_id','response_text'}
        return {'validation':{'status':'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}
    inventory.run(declaration,bank,executor=executor)
    inventory.run(declaration,bank,executor=executor)
    assert len(calls)==result['unique_answer_texts']*2


def test_baseline_failures_retained_without_dropping_full_b4(tmp_path):
    path,root,d=population(tmp_path,fail=True)
    result=inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')
    assert result['method_answer_counts']=={'B2':0,'B4':3}
    ledger=json.loads((tmp_path/'bank/response-accounting.json').read_text())
    assert all(e['method_call_status']=='TECHNICAL_RESPONSE_FAILURE' for e in ledger['entries'])
    assert all(e['methods']['B2']=='MISSING_ANSWER' for e in ledger['entries'])
    assert len(result['missing_source_paths'])==3


@pytest.mark.parametrize('attack',['answer','method','generation'])
def test_full_candidate_tampering_even_rebound_terminal_fails_actual_admission(tmp_path,attack):
    path,root,d=population(tmp_path);entry=d['entries'][0]
    candidate=root/'responses'/entry['id']/'B4.json'; value=json.loads(candidate.read_text())
    if attack=='answer': value['answer']='Fabricated answer.'
    elif attack=='method': value['method']='legacy-renderer'
    else: value['generation_provenance']['candidate_generation']['method']='legacy-renderer'
    candidate.write_text(json.dumps(value));rebind_candidate(root,entry)
    with pytest.raises(ValueError,match='full B4|full pipeline|candidate differs'):
        inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')


def test_missing_terminal_never_admits_orphan_answers(tmp_path):
    path,root,d=population(tmp_path)
    (root/'responses'/d['entries'][0]['id']/'response-terminal.json').unlink()
    result=inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')
    assert result['method_answer_counts']=={'B2':2,'B4':2}
    ledger=json.loads((tmp_path/'bank/response-accounting.json').read_text())
    assert ledger['entries'][0]['methods']['B4']=='ORPHAN_ANSWER_UNBOUND_TERMINAL_EXCLUDED'


def test_source_snapshot_tamper_precedes_extractor_calls(tmp_path):
    path,root,d=population(tmp_path)
    Path(d['method_sources'][0]['snapshot']['path']).write_text('{}')
    with pytest.raises(ValueError,match='bound input'):
        inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')


@pytest.mark.parametrize('attack',['source-closure','geometry-id','generation-intent'])
def test_declared_interface_and_geometry_mismatch_refused(tmp_path,attack):
    path,root,d=population(tmp_path)
    if attack=='source-closure': d['method_sources'].pop()
    elif attack=='geometry-id':d['entries'][0]['cluster_id']='foreign-geometry'
    else:d['entries'][0]['candidate_generation']['generator']='legacy-renderer.py'
    path.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='closure mismatch|identity mismatch|generation intent mismatch'):
        inventory.prepare(path,root,tmp_path/'bank',tmp_path/'inventory.json')


def test_extraction_failure_retained_no_quality_retry(tmp_path):
    path,root,d=population(tmp_path)
    bank=tmp_path/'bank';decl=tmp_path/'inventory.json'
    inventory.prepare(path,root,bank,decl);calls=[]
    def fail(*args):calls.append(1);raise RuntimeError('construction extraction failure')
    first=inventory.run(decl,bank,executor=fail)
    second=inventory.run(decl,bank,executor=fail)
    assert first==second
    assert first['failed_extraction_attempts']==len(calls)>0
    assert first['quality_retries']==0
