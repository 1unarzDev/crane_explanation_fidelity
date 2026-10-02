import copy
from collections import Counter
from analysis.hexar_external.confirmatory_v1.development_full_battery_scoring import prepare,job,summarize


def test_full_battery_preserves_all_methods_queries_masks_and_blinds_payloads():
    entries,*_=prepare()
    assert len(entries)==108
    assert Counter(e['identity']['method'] for e in entries)=={'HX-CONTRACT':54,'HX-PROMPT':54}
    assert len({e['identity']['episode'] for e in entries})==6
    assert len({job(e,s)['opaque_job'] for e in entries for s in ('A','B','C')})==324
    assert all(set(e['payload'])=={'question','visible_evidence','required_units','answer'} for e in entries)


def test_whole_episode_failure_and_unresolved_mapping_are_clustered_and_conservative():
    payload=dict(answer='An ambiguous navigation statement.',required_units=[])
    entries=[dict(identity=dict(job_id=f'e1-q{i}-{method}',method=method,episode='e1'),payload=copy.deepcopy(payload)) for i in range(9) for method in ('HX-CONTRACT','HX-PROMPT')]
    attempts={}
    for e in entries:
        parsed=dict(unsupported_material=False,overlicensed_specificity=False,covered_units=[],rationale='fixture',unsupported_spans=[],overlicensed_spans=[],ambiguous_spans=['An ambiguous navigation statement.'] if e['identity']['method']=='HX-PROMPT' else [])
        for slot in ('A','B'):attempts[job(e,slot)['opaque_job']]=dict(status='VALID',parsed=parsed)
    labels,episodes,cells=summarize(entries,attempts)
    assert len(labels)==18 and len(episodes)==1
    assert episodes[0]['method_states']=={'HX-CONTRACT':'PASS','HX-PROMPT':'UNRESOLVED'}
    assert cells['both_succeed']==1 and cells['contract_succeeds_prompt_fails']==0
    # Reversing the unresolved method cannot favor CRANE.
    for e in entries:
        for slot in ('A','B'):
            attempts[job(e,slot)['opaque_job']]['parsed']={**attempts[job(e,slot)['opaque_job']]['parsed'],'ambiguous_spans':['An ambiguous navigation statement.'] if e['identity']['method']=='HX-CONTRACT' else []}
    _,episodes,cells=summarize(entries,attempts)
    assert cells['prompt_succeeds_contract_fails']==1


def test_full_executor_closes_initial_and_blinded_C_calls_with_fake_cli(tmp_path,monkeypatch):
    import json
    from analysis.hexar_external.confirmatory_v1 import development_full_battery_scoring as screen
    executable=tmp_path/'fake-codex';counter=tmp_path/'counter.json'
    executable.write_text('''#!/usr/bin/env python3
import json,sys,pathlib,hashlib,fcntl
if '--version' in sys.argv:print('fake-cli-for-unit-test');sys.exit(0)
text=sys.stdin.read();raw=text.split('UNTRUSTED_DATA_BEGIN\\n',1)[1].split('\\nUNTRUSTED_DATA_END',1)[0];payload=json.loads(raw)
assert set(payload)=={'question','visible_evidence','required_units','answer'}
key=hashlib.sha256(raw.encode()).hexdigest()
with open(COUNTER,'a+') as stream:
 fcntl.flock(stream,fcntl.LOCK_EX);stream.seek(0);data=stream.read();counts=json.loads(data) if data else {};counts[key]=counts.get(key,0)+1;failure=counts[key]%2==0;stream.seek(0);stream.truncate();json.dump(counts,stream)
value=dict(unsupported_material=failure,overlicensed_specificity=False,covered_units=[u['unit_id'] for u in payload['required_units']],rationale='Fake transport only.',unsupported_spans=[payload['answer']] if failure else [],overlicensed_spans=[],ambiguous_spans=[])
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(value))
print(json.dumps({'type':'turn.completed'}))
'''.replace('COUNTER',repr(str(counter))))
    executable.chmod(0o700)
    monkeypatch.setattr(screen.shutil,'which',lambda _:str(executable))
    monkeypatch.setattr(screen,'DEST',tmp_path/'screen')
    screen.execute()
    report=json.loads((screen.DEST/'report.json').read_text())
    assert report['status']=='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED'
    assert report['initial_calls']==216 and report['C_calls']>0
    assert report['valid_returns']==report['total_dispatched']==216+report['C_calls']
    assert len(report['answer_labels'])==108 and len(report['episode_states'])==6
    assert len(list((screen.DEST/'journal').glob('*.claim.json')))==report['total_dispatched']
    assert len(list((screen.DEST/'journal').glob('*.outcome.json')))==report['total_dispatched']
    assert not json.loads((screen.DEST/'adjudication_registry.json').read_text())['previous_labels_supplied_to_C']
    assert not report['superiority_test_performed'] and report['p_value'] is None
