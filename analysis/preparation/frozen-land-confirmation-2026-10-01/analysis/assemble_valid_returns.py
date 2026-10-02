#!/usr/bin/env python3
"""Assemble explicitly chosen valid returns after release; no implicit retry selection.
List original or FIRST-valid technical replacement record for every episode/pass.
Retain failures in their original directory, never delete or overwrite records.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--selected-paths',type=Path,required=True);p.add_argument('--cases',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists(),'Fresh assembly directory required'
expected={c['case_id'] for c in json.loads(a.cases.read_text())['cases']};seen={'A':set(),'B':set()};copies=[]
for line in a.selected_paths.read_text().splitlines():
 if not line.strip():continue
 source=Path(line);record=json.loads(source.read_text());slot=source.name.split('-batch-',1)[0]
 assert slot in seen and record['status']=='STRUCTURALLY_VALID_SUPPORT_RETURN'
 ids={r['case_id'] for r in record['parsed_final']['annotations']}
 assert len(ids)==len(record['parsed_final']['annotations']) and ids<=expected and not ids&seen[slot]
 seen[slot]|=ids;copies.append((slot,source,hashlib.sha256(source.read_bytes()).hexdigest()))
assert all(ids==expected for ids in seen.values()),'Incomplete pass'
a.output.mkdir(parents=True)
provenance=[]
for i,(slot,source,sha) in enumerate(copies):
 dest=a.output/f'{slot}-batch-{i:05d}.json';shutil.copyfile(source,dest);provenance.append(dict(source=str(source),sha256=sha,destination=dest.name))
(a.output/'assembly-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Both complete blinded passes assembled without duplicated or replaced valid scores.')
