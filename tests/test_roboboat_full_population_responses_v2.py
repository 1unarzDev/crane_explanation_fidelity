import json
from pathlib import Path
import subprocess
import sys
import pytest
import run_roboboat_full_population_responses_v2 as runner
from test_roboboat_population_responses_v1 import fixture as old_fixture
from test_roboboat_population_v1 import clean_capture


def fixture(tmp_path):
    registry,captures,path=old_fixture(tmp_path)
    capture=captures/'new-1'
    terminal=json.loads((capture/'capture-attempt.json').read_text())
    terminal['return_code']=0
    (capture/'capture-attempt.json').write_text(json.dumps(terminal))
    summary,worker,physical=clean_capture()
    summary['expectedNavigationStatus']='succeeded'
    for name,value in [('navigation-reset-summary.json',summary),('worker-0/result.json',worker),
                       ('fixture-summary.json',physical),('runtime-parameters.json',{})]:
        target=capture/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value))
    return registry,captures,path


def test_prepare_admits_complete_valid_rows_with_explicit_subset_and_immutable_closure(tmp_path):
    registry,captures,path=fixture(tmp_path)
    with pytest.raises(ValueError,match='incomplete'):runner.prepare(registry,captures,path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    assert len(declaration['entries'])==3
    assert [item['status'] for item in declaration['capture_accounting']]==['VALID_DEVELOPMENT','TECHNICAL_FAILURE','PENDING']
    names={item['relative_path'] for item in declaration['method_sources']}
    assert {'analysis/roboboat_full_crane_v2.py','configs/roboboat_claim_contracts_v2_development.json',
            'analysis/evidence_calibration.py','analysis/roboboat_temporal_renderer_v4.py'}<=names
    assert declaration['B2']['model']=='gpt-6-astra'
    assert declaration['quality_retries']==declaration['confirmation_n']==0
    with pytest.raises(ValueError,match='immutable'):runner.prepare(registry,captures,path,allow_completed_subset=True)


@pytest.mark.parametrize('missing',['worker-0/result.json','runtime-parameters.json','method_packets/L2.json'])
def test_incomplete_valid_capture_refused(tmp_path,missing):
    registry,captures,path=fixture(tmp_path)
    (captures/'new-1'/missing).unlink()
    with pytest.raises((ValueError,FileNotFoundError)):runner.prepare(registry,captures,path,allow_completed_subset=True)


def test_declared_valid_but_stale_capture_refused(tmp_path):
    registry,captures,path=fixture(tmp_path)
    worker=captures/'new-1/worker-0/result.json'
    value=json.loads(worker.read_text());value['staleObservations']=1;worker.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='strict capture admission'):
        runner.prepare(registry,captures,path,allow_completed_subset=True)


def test_full_b4_generation_and_baseline_equal_source_workspace(tmp_path):
    registry,captures,path=fixture(tmp_path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    calls=[]
    def caller(cache,role,work,prompt,model,effort,schema,**kwargs):
        names={item.relative_to(work).as_posix() for item in work.rglob('*') if item.is_file()}
        assert names=={'evidence.json','effective-configuration.yaml','configuration-basis.json',
                       *[item['relative_path'] for item in declaration['method_sources']]}
        assert not any(token in name.lower() for name in names for token in ('evaluator','reference_','candidate_outputs','b4.json','full-pipeline'))
        assert model=='gpt-6-astra' and effort=='high'
        assert kwargs=={'allow_tools':True,'timeout':300}
        assert 'reuse' in prompt and 'full CRANE' in prompt
        script='''import sys,json;sys.path.insert(0,'analysis');import roboboat_full_crane_v2 as m
assert m.CATALOG.is_file()
r=m.explain(json.load(open('evidence.json')),configuration_id='c',episode_id='e',condition_id='q')
assert r['schema']=='roboboat-full-crane/v2-development'
assert r['realization']['final_response']
print(r['realization']['final_response'])'''
        completed=subprocess.run([sys.executable,'-B','-c',script],cwd=work,capture_output=True,text=True,check=True)
        calls.append(role)
        return {'parsed_final':{'answer':completed.stdout.strip()},'cache_key':'mock-'+role,'latency_s':0}
    output=tmp_path/'responses'
    runner.run(path,output,workers=2,caller=caller)
    runner.run(path,output,workers=2,caller=caller)
    assert sorted(calls)==['new-1-L0','new-1-L1','new-1-L2']
    full=json.loads((output/'responses/new-1-L0/full-pipeline-B4.json').read_text())
    b4=json.loads((output/'responses/new-1-L0/B4.json').read_text())
    assert b4['answer']==full['realization']['final_response']
    assert b4['model_calls']==0
    assert 'diagnostic_result' in full and 'numeric_source_bindings' in full
    terminal=json.loads((output/'responses/new-1-L0/response-terminal.json').read_text())
    assert terminal['status']=='COMPLETE_RESPONSE_SUPPORT_UNJUDGED'


@pytest.mark.parametrize('target',['packet','snapshot'])
def test_preflight_tamper_refuses_all_calls(tmp_path,target):
    registry,captures,path=fixture(tmp_path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    changed=Path(declaration['entries'][0]['packet']['path']) if target=='packet' else Path(declaration['method_sources'][0]['snapshot']['path'])
    changed.write_text('{}')
    with pytest.raises(ValueError,match='bound input'):
        runner.run(path,tmp_path/'output',caller=lambda *a,**k:pytest.fail('unexpected provider'))


def test_unresolved_intent_and_failed_response_never_retry(tmp_path):
    registry,captures,path=fixture(tmp_path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    output=tmp_path/'output';calls=[]
    def fail(*args,**kwargs):calls.append(1);raise RuntimeError('mock timeout')
    entry=declaration['entries'][0]
    first=runner.execute(entry,declaration,path,output,caller=fail)
    assert first['status']=='TECHNICAL_RESPONSE_FAILURE'
    assert runner.execute(entry,declaration,path,output,caller=fail)==first
    assert len(calls)==1
    assert (output/'responses/new-1-L0/B4.json').exists()
    (output/'intents/new-1-L1.json').write_text('{}')
    with pytest.raises(FileExistsError):runner.execute(declaration['entries'][1],declaration,path,output,caller=fail)


def test_prior_same_interface_entries_skipped(tmp_path):
    registry,captures,path=fixture(tmp_path)
    runner.prepare(registry,captures,path,allow_completed_subset=True)
    second=runner.prepare(registry,captures,tmp_path/'second.json',allow_completed_subset=True,prior_declarations=[path])
    assert second['entries']==[]
    assert len(second['prior_declarations'])==1


def test_terminal_binds_full_b4_candidate_and_original_generation_sources(tmp_path):
    registry,captures,path=fixture(tmp_path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    result=runner.execute(declaration['entries'][0],declaration,path,tmp_path/'output',
        caller=lambda *a,**k:{'parsed_final':{'answer':'mock answer'},'cache_key':'mock','latency_s':0})
    candidate=json.loads(runner.checked(result['B4_candidate']).read_text())
    assert candidate['generation_provenance']['candidate_generation']==declaration['entries'][0]['candidate_generation']
    assert candidate['generation_provenance']['declaration_sha256']==runner.digest(path)
    assert len(candidate['generation_provenance']['source_snapshots'])==len(declaration['method_sources'])
    assert set(result['retained_outputs'])=={'B2.json','B4.json','full-pipeline-B4.json'}


def test_in_memory_declaration_mutation_and_orphan_output_refused(tmp_path):
    registry,captures,path=fixture(tmp_path)
    declaration=runner.prepare(registry,captures,path,allow_completed_subset=True)
    altered={**declaration,'timeout_s':301}
    with pytest.raises(ValueError,match='in-memory declaration'):
        runner.execute(declaration['entries'][0],altered,path,tmp_path/'output')
    output=tmp_path/'output';(output/'responses/new-1-L0').mkdir(parents=True)
    with pytest.raises(RuntimeError,match='unresolved response output'):
        runner.execute(declaration['entries'][0],declaration,path,output)
