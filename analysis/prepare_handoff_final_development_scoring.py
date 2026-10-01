#!/usr/bin/env python3
"""Bind unchanged answers from 42 paired development configurations for final scoring."""
import json,copy,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];base=root/'analysis/results/evidence-calibration-handoff-development'
out=root/'analysis/results/development/evidence-calibration-final-v7-development-v1';out.mkdir(exist_ok=True)
initial=json.loads((base/'initial-paired-development-final-v2.json').read_text())
wanted={(r['condition_id'],r['method']):r for r in initial['condition_rows'] if r['paired_complete_episode'] and r['method'] in ['B2','B4v5'] and r['family'] in ['persistent_command_motion_discrepancy','measured_response_recovery']}
refs={}
for name in ['all-development-cases-v1.json','corrected-review-cases-v2.json','initial-v5-cases-v2.json']:
 for c in json.loads((base/name).read_text())['cases']:refs[c['case_id']]=c
joins0=json.loads((base/'development-join-key-v3.json').read_text())['entries'];cases=[];joins=[]
for j in joins0:
 key=(j['condition_id'],j['method_id'])
 if key not in wanted:continue
 c=copy.deepcopy(refs[j['response_id']]);r=wanted[key];j=copy.deepcopy(j);j['family']=r['family']
 cases.append(c);joins.append(j)
ext=root/'analysis/results/development/evidence-calibration-extension-v1'
cases+=json.loads((ext/'blind-cases-v1.json').read_text())['cases'];joins+=json.loads((ext/'join-key-v1.json').read_text())['entries']
new=root/'analysis/results/development/evidence-calibration-response-development-v1/full-v7-snapshot'
cases+=json.loads((new/'blind-cases-v1.json').read_text())['cases'];joins+=json.loads((new/'join-key-v1.json').read_text())['entries']
byid={c['case_id']:c for c in cases}
for j in joins:
 if j['method_id']=='B4v5':
  p=root/'model_outputs/evidence-calibration-retained-development-v7/b4'/ (j['condition_id']+'.json')
  answer=json.loads(p.read_text())['answer'];assert byid[j['response_id']]['response_text']==answer
  j['method_id']='B4v7';j['source_path']=str(p.relative_to(root));j['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
assert len(cases)==336,(len(cases),len(joins))
assert len({j['configuration_id'] for j in joins})==42
for c in cases:
 packet=c['reference']['robot_visible_evidence'];identity=next(j['configuration_id'] for j in joins if j['response_id']==c['case_id'])
 if 'configuration_id' in packet:assert packet['configuration_id']==identity
 else:packet['configuration_id']=identity
sources=json.loads((base/'pilot-cases-v1.json').read_text())['source_assets']
for name,d in [('blind-cases-v1.json',dict(scope='DEVELOPMENT_ONLY',cases=cases,source_assets=sources)),('join-key-v1.json',dict(scope='DEVELOPMENT_ONLY_NOT_SENT_TO_ANNOTATOR',entries=joins)),('scoring-missingness-v1.json',dict(scheduled_episode_n=48,complete_paired_episode_n=42,physical_technical_exclusions=['handoff-response-dev-003'],model_technical_exclusions=['cm-land-conf-042','cm-land-conf-061','handoff-response-dev-004','handoff-response-dev-012','handoff-response-dev-023'],retry_count=0))]:
 p=out/name;raw=json.dumps(d,indent=2)+'\n'
 if p.exists() and p.read_text()!=raw:raise RuntimeError('Retained scoring inputs differ')
 if not p.exists():p.write_text(raw)
print(len(cases),len(joins))
