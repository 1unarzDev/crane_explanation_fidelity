"""Inventory development acquisitions for permanent confirmation exclusion.

This does not relabel or modify acquisition receipts. Each version is exclusively
created after qualification; later development needs a new snapshot before freeze.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root=ROOT):
    base=Path(root)/'manifests/hexar_external/acquisition'
    records=[];planned=[]
    for path in sorted(base.glob('development_episode_plan*.json')):
        data=json.loads(path.read_text())
        if data.get('phase')!='development' or 'records' not in data:continue
        planned.extend(dict(acquisition_id=r['episode_id'],seed=r['seed'],plan_path=str(path.relative_to(root)),
                            plan_sha256=digest(path)) for r in data['records'])
    for path in sorted(base.glob('hexar-tiago-dev-*/provenance.json')):
        data=json.loads(path.read_text())
        raw=[r for r in data.get('raw_files',[]) if '/raw/' in r['path']]
        for item in raw:
            if digest(Path(root)/item['path'])!=item['sha256']:
                raise ValueError('development raw artifact changed: '+item['path'])
        records.append(dict(acquisition_id=data['episode_id'],seed=data['seed_hidden'],
                            provenance_path=str(path.relative_to(root)),provenance_sha256=digest(path),
                            raw_sha256s=[r['sha256'] for r in raw],eligible_for_confirmation=False,
                            reason='designated development acquisition, regardless of whether semantic outputs were generated'))
    return dict(schema='hexar-development-exposure/v1',phase='development_only',confirmatory_n=0,
                records=records,original_exposed_recordings=18,
                source_sha256=digest(__file__),
                planned_development_acquisitions=planned,
                must_refresh_before_freeze=True,
                scope='All acquired development attempts, including technical failures, are permanently excluded. Original bags remain excluded by the original source manifest.')


def verify_current_inventory(root,value):
    """Fail closed on development acquired/planned after the pinned snapshot.

    Hashing existing raw artifacts also rejects changed receipts or bags. A
    fresh snapshot is required after development; updating a snapshot after a
    scientific freeze cannot silently modify the frozen eligibility boundary.
    """
    current=inventory(root)
    for key in ('records','planned_development_acquisitions'):
        frozen={json.dumps(r,sort_keys=True) for r in value.get(key,[])}
        actual={json.dumps(r,sort_keys=True) for r in current[key]}
        if frozen!=actual:
            raise ValueError('development exposure inventory stale: '+key)


def load_exclusions(root,pin,require_current=False):
    path=Path(root)/pin['path']
    if digest(path)!=pin['sha256']:raise ValueError('development exposure ledger changed')
    value=json.loads(path.read_text())
    if value.get('schema')!='hexar-development-exposure/v1' or value.get('phase')!='development_only' or not value.get('records'):
        raise ValueError('development exposure inventory incomplete')
    if require_current:
        verify_current_inventory(root,value)
    hashes,identities,seeds=set(),set(),set()
    for r in value['records']:
        if r.get('eligible_for_confirmation') is not False:
            raise ValueError('development episode marked eligible')
        hashes.update(r['raw_sha256s']);identities.add(r['acquisition_id']);seeds.add(r['seed'])
    for r in value.get('planned_development_acquisitions',[]):
        identities.add(r['acquisition_id']);seeds.add(r['seed'])
    return hashes,identities,seeds


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    value=inventory();exclusive_json(args.output,value)
    print(json.dumps(dict(status='DEVELOPMENT_PERMANENTLY_EXCLUDED',attempts=len(value['records']),confirmatory_n=0)))


if __name__=='__main__':main()
