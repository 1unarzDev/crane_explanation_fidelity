#!/usr/bin/env python3
"""After registered continuation, preserve old blind cases and select only new episodes.
No joins or answer printing; no provider calls. Never run before FINAL complete.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--first-cases',type=Path,required=True);p.add_argument('--final-cases',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
f=json.loads(a.first_cases.read_text());g=json.loads(a.final_cases.read_text());old={c['case_id']:c for c in f['cases']};all_cases={c['case_id']:c for c in g['cases']}
assert len(old)==4800 and len(all_cases)==9600 and len(f['cases'])==len(old) and len(g['cases'])==len(all_cases)
assert set(old)<=set(all_cases) and f['source_assets']==g['source_assets']
assert all(old[k]==all_cases[k] for k in old),'First-look blind case changed'
new=[c for c in g['cases'] if c['case_id'] not in old]
old_configs={c['reference']['robot_visible_evidence']['configuration_id'] for c in old.values()};new_configs={c['reference']['robot_visible_evidence']['configuration_id'] for c in new}
assert len(old_configs)==600 and len(new_configs)==600 and not old_configs&new_configs
assert not a.output.exists(),'Will not overwrite continuation cases'
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(scope='CONFIRMATION',source_assets=g['source_assets'],cases=new),indent=2)+'\n')
print('Prepared 600 new independent episodes; retained first600 payloads match exactly.')
