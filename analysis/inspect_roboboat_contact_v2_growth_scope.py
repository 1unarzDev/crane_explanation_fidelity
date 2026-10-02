#!/usr/bin/env python3
"""Independent primitive audit of the retained growth-scope failure; no rescore."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inspect():
    declaration=ROOT/'docs/roboboat_terminal_evidence/contact_policy_response_declaration_v2.json'
    d=json.loads(declaration.read_text())
    e=next(e for e in d['entries'] if e['episode']=='boat-terminal-settling-002' and e['level']=='L2')
    packet_path=ROOT/e['packet']['path'];p=json.loads(packet_path.read_text());task=p['task'];rows=p['post_result']
    start=rows[0]['simSeconds'];end=start+task['dwell_s'];last=next(o for o in reversed(rows) if o['simSeconds']<=end)
    first=rows[0];ret=p['return_observation'];g=task['goal']
    def distance(row):return math.sqrt((row['x']-g['x'])**2+(row['y']-g['y'])**2)
    near_growth=distance(last)-distance(ret);dwell_growth=distance(last)-distance(first)
    result={'schema':'roboboat-contact-v2-growth-scope-reference/v1','packet_path':str(packet_path.relative_to(ROOT)),'packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),'reference_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'declared_dwell_s':[start,end],'actual_last_dwell_sample_s':last['simSeconds'],'result_adjacent':{'time_s':ret['simSeconds'],'position_error_m':distance(ret)},'first_dwell_sample':{'time_s':first['simSeconds'],'position_error_m':distance(first)},'last_dwell_sample':{'time_s':last['simSeconds'],'position_error_m':distance(last)},'result_adjacent_to_last_growth_m':near_growth,'first_to_last_dwell_growth_m':dwell_growth,'rounded_growths_m':{'result_adjacent_to_last':f'{near_growth:.4f}','first_to_last_dwell':f'{dwell_growth:.4f}'},'growth_difference_m':dwell_growth-near_growth,'return_observation_precedes_dwell_s':start-ret['simSeconds'],'fixed_position_tolerance_m':task['position_tolerance_m'],'physical_dwell_position_outcome_changed_by_growth_reference':False,'cause_identified':False,'judge_label_overridden':False,'strict_score_revised':False,'material_primary_qualified':False,'interpretation':'The retained answer says growth through the dwell but the quoted number matches the pre-dwell result-adjacent-to-last interval. Both judge passes identify that endpoint mismatch. Its approximately 0.000145 m difference and 0.020 s offset do not change observed position compliance, partial-information coverage, unknown contact or supported task outcome. A strict all-assertion score difference is therefore not evidence of a material useful-outcome advantage. Materiality cannot be qualified or primary-promoted post hoc.','new_configuration_n':0,'confirmation_n':0,'alpha_consumed':0}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=inspect()
    if a.output.exists():
        if json.loads(a.output.read_text())!=r:raise ValueError('retained reference differs')
    else:a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('rounded_growths_m','growth_difference_m','return_observation_precedes_dwell_s')},indent=2))
