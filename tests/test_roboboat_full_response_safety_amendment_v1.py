import json
from pathlib import Path

import pytest
import run_roboboat_full_response_safety_amendment_v1 as amendment
from test_roboboat_full_population_responses_v2 import fixture


def setup(tmp_path):
    registry,captures,decl=fixture(tmp_path)
    d=amendment.original.prepare(registry,captures,decl,allow_completed_subset=True)
    output=tmp_path/'output'
    return d,decl,output,tmp_path/'amendment.json'


def test_only_never_attempted_entries_resume_no_failed_request_reissue(tmp_path,monkeypatch):
    d,decl,out,path=setup(tmp_path)
    def fail(*a,**kw):raise RuntimeError('retained original timeout')
    old=amendment.original.execute(d['entries'][0],d,decl,out,caller=fail)
    terminal=out/'responses'/d['entries'][0]['id']/'response-terminal.json'
    old_bytes=terminal.read_bytes()
    a=amendment.prepare(decl,out,path)
    assert a['untouched_entry_ids']==[e['id'] for e in d['entries'][1:]]
    assert a['settings_unchanged']['timeout_s']==300 and a['reissued_entries']==[]
    calls=[]
    def caller(cache,role,*args,**kwargs):
        calls.append(role);assert kwargs['timeout']==300
        return {'status':'valid','attempt_count':1,'parsed_final':{'answer':'supported'},'cache_key':role,'latency_s':0}
    monkeypatch.setattr(amendment.safe,'call',caller)
    amendment.run(path)
    assert sorted(calls)==sorted(a['untouched_entry_ids'])
    assert terminal.read_bytes()==old_bytes
    assert old['status']=='TECHNICAL_RESPONSE_FAILURE'


def test_unresolved_prior_intent_refuses_amendment(tmp_path):
    d,decl,out,path=setup(tmp_path)
    intent=out/'intents'/(d['entries'][0]['id']+'.json');intent.parent.mkdir(parents=True)
    intent.write_text('{}')
    with pytest.raises(ValueError,match='unresolved'):amendment.prepare(decl,out,path)


def test_retained_terminal_tamper_prevents_new_calls(tmp_path,monkeypatch):
    d,decl,out,path=setup(tmp_path)
    amendment.original.execute(d['entries'][0],d,decl,out,caller=lambda *a,**kw:{
        'parsed_final':{'answer':'supported'},'cache_key':'old','latency_s':0})
    a=amendment.prepare(decl,out,path)
    Path(a['retained_terminals'][0]['path']).write_text('{}')
    monkeypatch.setattr(amendment.safe,'call',lambda *a,**kw:pytest.fail('unexpected call'))
    with pytest.raises(ValueError,match='bound input'):amendment.run(path)
