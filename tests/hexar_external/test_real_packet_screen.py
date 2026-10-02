from collections import Counter
from analysis.hexar_external.confirmatory_v1.development_real_packet_screen import prepare


def test_predeclared_complete_intact_battery_is_blinded_and_balanced():
    jobs, _, _ = prepare()
    assert len(jobs)==72
    assert len({j['opaque_job'] for j in jobs})==72
    assert Counter(j['administrative_join']['method'] for j in jobs)=={'HX-PROMPT':36,'HX-CONTRACT':36}
    assert Counter(j['slot'] for j in jobs)=={'A':36,'B':36}
    assert len({j['administrative_join']['job_id'] for j in jobs})==18
    for job in jobs:
        assert set(job['payload'])=={'question','visible_evidence','required_units','answer'}
        assert not {'method','slot','opaque_job','expected','administrative_join'} & set(job['payload'])


def test_repaired_executor_closes_every_exact_claim_with_fake_cli(tmp_path,monkeypatch):
    import json
    from analysis.hexar_external.confirmatory_v1 import development_real_packet_screen_v2 as screen
    executable=tmp_path/'fake-codex'
    executable.write_text('''#!/usr/bin/env python3
import json,sys,pathlib
if '--version' in sys.argv:print('fake-cli-for-unit-test');sys.exit(0)
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(dict(unsupported_material=False,overlicensed_specificity=False,covered_units=[],rationale='Fake transport only.')))
print(json.dumps({'type':'turn.completed'}))
''')
    executable.chmod(0o700)
    monkeypatch.setattr(screen.shutil,'which',lambda _:str(executable))
    monkeypatch.setattr(screen,'DEST',tmp_path/'screen')
    screen.execute()
    result=json.loads((screen.DEST/'report.json').read_text())
    assert result['status']=='REPEATABILITY_PASSED_NOT_ACCURACY_QUALIFIED'
    assert result['valid_returns']==72 and result['exact_answer_agreements']==36
    assert len(list((screen.DEST/'journal').glob('*.claim.json')))==72
    assert len(list((screen.DEST/'journal').glob('*.outcome.json')))==72
