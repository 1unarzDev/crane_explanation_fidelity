from collections import Counter
from analysis.hexar_external.confirmatory_v1.development_unique_methods import prepare
from analysis.hexar_external.confirmatory_v1.journal import fingerprint


def test_unique_method_plan_preserves_strong_prompt_and_one_request_per_alias_group():
    _,prompt_path,plan,lookup=prepare()
    assert len(lookup)==72 and plan['battery_cells']==108
    assert Counter(r['method'] for r in plan['requests'])=={'HX-PROMPT':36,'HX-CONTRACT':36}
    assert prompt_path.name=='prompt_calibration_v1.txt'
    for request in plan['requests']:
        entry=lookup[request['unique_request_id']]
        assert fingerprint(dict(packet=entry['packet'],implementation_binding=entry['implementation_binding']))==request['request_sha256']
        assert not entry['implementation_binding']['provider_runtime_qualified']
    for alias in plan['aliases']:
        entry=lookup[alias['unique_request_id']]
        assert (entry['method'],entry['episode_id'])==(alias['method'],alias['episode_id'])


def test_unique_executor_issues_36_fake_baseline_calls_and_closes_all_alias_groups(tmp_path,monkeypatch):
    import json
    from analysis.hexar_external.confirmatory_v1 import development_unique_methods as screen
    exe=tmp_path/'fake-codex'
    exe.write_text('''#!/usr/bin/env python3
import json,sys,pathlib
if '--version' in sys.argv:print('fake-cli-for-transport-test');sys.exit(0)
text=sys.stdin.read();payload=json.loads(text.split('UNTRUSTED_DATA_BEGIN\\n',1)[1].split('\\nUNTRUSTED_DATA_END',1)[0])
assert 'controller_runtime_observations' in payload['source_context']
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps({'answer':'Navigation software reported a bounded outcome.'}))
print(json.dumps({'type':'turn.completed'}))
''');exe.chmod(0o700)
    monkeypatch.setattr(screen.shutil,'which',lambda _:str(exe));monkeypatch.setattr(screen,'DEST',tmp_path/'run')
    screen.execute()
    report=json.loads((screen.DEST/'report.json').read_text())
    assert report['unique_attempts']==report['valid']==72 and report['baseline_calls']==36
    assert len(report['aliases'])==108
    assert len(list((screen.DEST/'journal').glob('*.claim.json')))==72
    assert len(list((screen.DEST/'journal').glob('*.outcome.json')))==72
    answers={a['unique_request_id']:a for a in report['answers']}
    for alias in report['aliases']:assert alias['unique_request_id'] in answers
    assert sum(a['model_calls'] for a in report['answers'])==36
