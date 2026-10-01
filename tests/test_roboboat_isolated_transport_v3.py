"""Inherited transport/successor tests against actual fresh implementation."""
import pytest
import roboboat_isolated_transport_v3 as transport
import run_roboboat_full_response_safety_amendment_v2 as amendment
import test_roboboat_isolated_transport_v2 as prior_transport_tests
import test_roboboat_full_response_safety_amendment_v1 as prior_amendment_tests


@pytest.mark.parametrize('name',[name for name in vars(prior_transport_tests) if name.startswith('test_')])
def test_inherited_transport_contract(name,tmp_path,monkeypatch):
    monkeypatch.setattr(prior_transport_tests,'transport',transport)
    getattr(prior_transport_tests,name)(tmp_path,monkeypatch)


@pytest.mark.parametrize('name',[name for name in vars(prior_amendment_tests) if name.startswith('test_')])
def test_inherited_one_shot_amendment_contract(name,tmp_path,monkeypatch):
    monkeypatch.setattr(prior_amendment_tests,'amendment',amendment)
    function=getattr(prior_amendment_tests,name)
    if 'monkeypatch' in function.__code__.co_varnames:function(tmp_path,monkeypatch)
    else:function(tmp_path)


def test_registered_decoded_safe_receipt_admitted_and_wrong_schema_rejected(tmp_path,monkeypatch):
    import json,hashlib
    from pathlib import Path
    import run_roboboat_full_population_inventory_v3 as inventory
    from test_roboboat_full_population_responses_v2 import fixture
    registry,captures,decl=fixture(tmp_path)
    d=amendment.original.prepare(registry,captures,decl,allow_completed_subset=True)
    root=tmp_path/'responses';root.mkdir()
    amendment_path=tmp_path/'amendment.json';amendment.prepare(decl,root,amendment_path)
    (root/'transport-amendment-bindings.json').write_text(json.dumps({
        'schema':'roboboat-response-operational-amendments/v1','quality_reissues':0,
        'amendments':[inventory.binding(amendment_path)]}))
    def caller(cache,role,work,prompt,model,effort,schema,**kwargs):
        request={'transport':'marine-isolated-login-cli/v3-decoded-safe-errors','role':role,'model':model,'effort':effort,
            'prompt':prompt,'schema':schema,'allow_tools':True,'timeout_s':300,
            'workspace_files':{p.relative_to(work).as_posix():inventory.digest(p) for p in work.rglob('*') if p.is_file()},
            'transport_sha256':inventory.digest(Path(transport.__file__)),
            'isolation_source_sha256':d['transport']['sha256']}
        key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
        raw={'request':request,'status':'valid','attempt_count':1,'return_code':0,'cache_key':key,
            'parsed_final':{'answer':'Constructed supported answer.'},'latency_s':0}
        cache.mkdir(parents=True,exist_ok=True);(cache/(key+'.json')).write_text(json.dumps(raw))
        return raw
    e=d['entries'][0];amendment.original.execute(e,d,decl,root,caller=caller)
    answer=json.loads((root/'responses'/e['id']/'B2.json').read_text())
    assert inventory.provider_receipt(e,d,decl,root,answer)[0].exists()
    a=json.loads(amendment_path.read_text());a['schema']='roboboat-full-response-transport-safety-amendment/v1'
    amendment_path.write_text(json.dumps(a))
    (root/'transport-amendment-bindings.json').write_text(json.dumps({
        'schema':'roboboat-response-operational-amendments/v1','quality_reissues':0,
        'amendments':[inventory.binding(amendment_path)]}))
    with pytest.raises(ValueError,match='mismatch'):
        inventory.provider_receipt(e,d,decl,root,answer)
