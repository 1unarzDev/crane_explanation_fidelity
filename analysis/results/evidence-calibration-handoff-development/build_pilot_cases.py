#!/usr/bin/env python3
"""Development scorer inputs: full answers, deterministic sample summaries, no method key/truth."""
import copy,hashlib,json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
source=ROOT/'model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/support-packets-neutral-v2-v1.json'
bank=json.loads(source.read_text())['records'];cases=[];assets={}
for x in bank:
 f=x['packet']['forms'][0];vis=copy.deepcopy(f['robot_visible_evidence'])
 for a in vis.pop('exact_source_assets'):
  if a['asset_id']!='tools/inspect_evidence_calibration_packet.py':assets[a['asset_id']]=a
 for role,value in vis['evidence'].items():
  if 'samples' not in value:continue
  samples=value.pop('samples');groups={}
  for row in samples:groups.setdefault(math.floor(row['offset_s']),[]).append(row['planar_speed_mps'])
  value['deterministic_raw_sample_summary']={'sample_count':len(samples),'window_seconds':1,'offset_range_s':[samples[0]['offset_s'],samples[-1]['offset_s']] if samples else None,'windows':[{'interval_s':[i,i+1],'count':len(v),'min_speed_mps':min(v),'max_speed_mps':max(v),'median_speed_mps':statistics.median(v)} for i,v in sorted(groups.items())]}
 units={f'u{i:02}':u['unit_prompt'] for i,u in enumerate(f['required_unit_coverage'])}
 cases.append({'case_id':x['opaque_response_id'],'reference':{'robot_visible_evidence':vis,'required_units':units,'required_limitations':[l['limitation_prompt'] for l in f['limitation_preservation']]},'response_text':x['packet']['response_text']})
result={'scope':'DEVELOPMENT_ONLY','source_packet_bank_path':str(source.relative_to(ROOT)),'source_bank_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sample_summary':'All samples retained in source bank; numeric count/min/max/median in every 1s bin deterministically computed, full validated primitive measurements retained; hidden evaluator facts and method key omitted.','cases':cases,'source_assets':list(assets.values())}
(HERE/'pilot-cases-v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(len(cases),'bytes',sum(len(json.dumps(c)) for c in cases))
