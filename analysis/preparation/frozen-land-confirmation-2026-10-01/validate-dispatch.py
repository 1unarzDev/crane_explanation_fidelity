"""Exercise frozen dispatch on invented cases with provider transport replaced locally."""
import importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'analysis/results/evidence-calibration-handoff-development/run_measurement.py'
spec=importlib.util.spec_from_file_location('frozen_dispatch',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=Path(__file__).resolve().parent/'dispatch-synthetic'
if out.exists(): raise RuntimeError('Use a new preparation directory; do not overwrite a retained run')
m.subprocess.run=lambda *a,**k:SimpleNamespace(stdout='SYNTHETIC-NO-PROVIDER')
seen=[]
def fake_call(**kwargs):
    payload=kwargs['payload'];seen.append(payload)
    rows=[dict(case_id=c['case_id'],primary_failure=False,primary_violations=[],factual_numeric_errors=[],required_units=[dict(unit_id='u00',communicated=True,quote='synthetic observation')]) for c in payload['cases']]
    kwargs['validate']({'annotations':rows})
    record={'status':m.VALID,'parsed_final':{'annotations':rows}}
    kwargs['output'].write_text(json.dumps(record))
    return record
m.call_once=fake_call
cases=[dict(case_id=f'synthetic-{episode}-{answer}',response_text='synthetic observation',reference=dict(robot_visible_evidence=dict(configuration_id=f'synthetic-episode-{episode}'),required_units={'u00':'observation'})) for episode in range(2) for answer in range(8)]
for slot in ['A','B']:
    records=m.execute(cases,out,slot,4,2,[],ROOT/'analysis/results/evidence-calibration-handoff-development/annotation-prompt-v5.md',True,'CONFIRMATION',900,'high')
    assert len(records)==2 and all(r['status']==m.VALID for r in records)
assert len(seen)==4 and all(len(p['cases'])==8 for p in seen)
assert all('method_id' not in json.dumps(p) and 'join-key' not in json.dumps(p) for p in seen)
summary=dict(synthetic_only=True,provider_calls=0,episodes=2,passes=['A','B'],answers_per_episode=8,checks=['episode grouping','A/B dispatch','exact IDs/quotes','no method key','900-second high-effort arguments'],scientific_files_modified=False)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
