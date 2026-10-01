"""Seal outcome-blind raw episode selection after committed acquisition freeze.

Raw records refer to per-attempt machine-validity receipts. No answers or judge
labels are read. Replayed original raw recordings and duplicate attempts fail.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from .journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def committed(root,path):
    return subprocess.check_output(['git','show','HEAD:'+str(Path(path).relative_to(root))],cwd=root)==Path(path).read_bytes()


def select(attempts,per_family,families,raw_root,original_hashes):
    if type(per_family) is not int or per_family<=0:
        raise ValueError('positive frozen per-family N required')
    groups={f:[] for f in families}; seen={k:set() for k in ('acquisition_id','seed','raw_sha256')}
    for attempt in attempts:
        if attempt['family'] not in groups:raise ValueError('undeclared family')
        for key,values in seen.items():
            value=attempt[key]
            if value in values:raise ValueError('duplicate '+key)
            values.add(value)
        if attempt['raw_sha256'] in original_hashes:raise ValueError('original development recording reused')
        raw=Path(raw_root)/attempt['raw_path']
        if digest(raw)!=attempt['raw_sha256']:raise ValueError('raw acquisition hash mismatch')
        if attempt['semantic_outputs_generated'] is not False or attempt['independent_reset'] is not True:
            raise ValueError('semantic exposure/reset violation')
        receipt=Path(raw_root)/attempt['validity_receipt_path']
        if digest(receipt)!=attempt['validity_receipt_sha256']:raise ValueError('validity receipt changed')
        validity=json.loads(receipt.read_text())
        if validity['method_outcomes_accessed'] is not False or type(validity['technical_valid']) is not bool:
            raise ValueError('technical disposition not outcome-blind')
        if validity.get('validity_predicate_sha256')!=attempt.get('validity_predicate_sha256') or not validity.get('validity_predicate_sha256'):
            raise ValueError('validity predicate identity missing/changed')
        if validity['acquisition_id']!=attempt['acquisition_id'] or validity['raw_sha256']!=attempt['raw_sha256']:
            raise ValueError('receipt belongs to other attempt')
        groups[attempt['family']].append((attempt,validity['technical_valid']))
    selected=[]; dispositions=[]
    for family,records in groups.items():
        records.sort(key=lambda item:item[0]['attempt_order'])
        if [r[0]['attempt_order'] for r in records]!=list(range(1,len(records)+1)):
            raise ValueError('nonconsecutive/duplicate acquisition order')
        valid=[a for a,v in records if v]
        if len(valid)<per_family:raise ValueError('reserve exhausted: no confirmatory cohort')
        selected.extend({**a,'technical_valid':True,'semantic_outputs_inspected':False} for a in valid[:per_family])
        dispositions.extend(dict(acquisition_id=a['acquisition_id'],family=family,
                                 disposition='SELECTED' if a in valid[:per_family] else 'RESERVE_NOT_SELECTED' if v else 'TECHNICAL_INVALID') for a,v in records)
    return selected,dispositions


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempts',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    base=ROOT/'manifests/hexar_external/confirmatory_v1'
    frozen=base/'freeze_manifest.json';freeze=json.loads(frozen.read_text())
    if freeze.get('status')!='FROZEN' or freeze.get('acquisition_authorized') is not True or not committed(ROOT,frozen):
        raise ValueError('committed acquisition freeze required')
    for name,expected in freeze['file_hashes'].items():
        if digest(ROOT/name)!=expected or not committed(ROOT,ROOT/name):raise ValueError('frozen file changed')
    cohort=json.loads((base/'cohort.json').read_text());n=json.loads((base/'fixed_n_decision.json').read_text())['final_valid_n']
    source=json.loads((ROOT/'data/hexar_external/audit/source_data_manifest.json').read_text())
    original={r['sha256'] for r in source['files'] if 'bagfiles/' in r['path']}
    attempts=json.loads(args.attempts.read_text())
    if attempts['phase']!='confirmation' or attempts['freeze_sha256']!=digest(frozen):
        raise ValueError('attempt schedule was not bound to acquisition freeze')
    if attempts['episode_plan_sha256']!=cohort['episode_plan_sha256']:
        raise ValueError('attempts use another acquisition schedule')
    validity=json.loads((base/'technical_validity.json').read_text())
    for attempt in attempts['attempts']:
        if attempt.get('validity_predicate_sha256')!=validity['machine_predicate_sha256']:
            raise ValueError('attempt uses unfrozen validity predicate')
    selected,dispositions=select(attempts['attempts'],n//6,cohort['families'],ROOT,original)
    if len(attempts['attempts'])>cohort['maximum_attempts_per_family']*6:raise ValueError('unfrozen reserve expansion')
    for family in cohort['families']:
        if sum(a['family']==family for a in attempts['attempts'])>cohort['maximum_attempts_per_family']:raise ValueError('family reserve expanded')
    # This is a separate immutable seal; the acquisition freeze is never edited.
    exclusive_json(args.output,dict(schema='hexar-raw-cohort-seal/v1',status='SEALED',freeze_sha256=digest(frozen),
                                    attempt_manifest_sha256=digest(args.attempts),records=selected,
                                    dispositions=dispositions,n=n,semantic_outputs_generated=False))

if __name__=='__main__':main()
