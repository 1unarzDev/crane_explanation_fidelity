#!/usr/bin/env python3
"""Wait for the registered 600-pair barrier, then score both passes with eight workers each."""
import json,subprocess,time,sys,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
freeze=root/'manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json'
assert hashlib.sha256(freeze.read_bytes()).hexdigest()=='77e0c6ac4f8da3eccfeeb5ed31990d504a907953f63e8c19822e4e0c4e540ac2'
f=json.loads(freeze.read_text())
base=root/'analysis/results/confirmation'/f['study_id']
while True:
 try:a=json.loads((base/'execution-accounting-FIRST.json').read_text())
 except (FileNotFoundError,json.JSONDecodeError):a={}
 if a.get('complete') and a.get('complete_paired_episode_n')==f['first_look_n']:break
 time.sleep(30)
look=base/('look-'+str(f['first_look_n']))
returns=look/'blind-returns-v1'
assert not returns.exists(), 'Existing annotation outputs: stop instead of replacing or retrying valid labels'
subprocess.run([sys.executable,str(root/'analysis/build_handoff_confirmation_scoring_cases.py'),'--freeze',str(freeze),'--look','FIRST'],cwd=root,check=True)
common=[sys.executable,str(root/'analysis/results/evidence-calibration-handoff-development/run_measurement.py'),'--cases',str(look/'blind-cases-v1.json'),'--output',str(returns),'--workers','8','--prompt',str(root/'analysis/results/evidence-calibration-handoff-development/annotation-prompt-v5.md'),'--group-by-episode','--scope','CONFIRMATION','--timeout-seconds','900','--reasoning-effort','high']
processes=[subprocess.Popen(common+['--slot',slot],cwd=root) for slot in ['A','B']]
statuses=[p.wait() for p in processes]
assert statuses==[0,0], 'Scoring process failed; retain outputs without automatic retries'
subprocess.run([sys.executable,str(root/'analysis/analyze_handoff_frozen_confirmation.py'),'--freeze',str(freeze),'--annotations',str(returns),'--look','FIRST'],cwd=root,check=True)
