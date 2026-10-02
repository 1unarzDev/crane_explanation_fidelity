#!/usr/bin/env python3
"""Prepare identical request for a terminal scoreless annotation failure only.
Use after registered dispatch, after coordinator verifies original process exited.
No model dispatch, score inspection/printing, semantic retry, or artifact overwrite.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--failed-record',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=json.loads(a.failed_record.read_text());payload=json.loads(a.request.read_text())
assert r['status']=='FAILED_NO_RETRY' and 'parsed_final' not in r,'Only scoreless failed annotation may resume'
assert payload['scope']=='CONFIRMATION' and payload['independent_annotation_pass'] in ['A','B']
assert len(payload['cases'])==8 and len({c['reference']['robot_visible_evidence']['configuration_id'] for c in payload['cases']})==1
assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(dict(scope='CONFIRMATION',source_assets=payload['shared_exact_source_assets'],cases=payload['cases']),indent=2)+'\n')
print('Prepared identical blinded payload; original failure remains retained. Preserve episode order on dispatch.')
