#!/usr/bin/env python3
"""One-shot isolated development intake; no main/shared DVC integration."""
import gzip
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path
from verify_roboboat_material_qualification_v3 import ROOT, DOC, OUT, verify, digest
from publish_roboboat_contact_policy_capsule_v2 import safe_members
from diagnostic_batch_pipeline import initialize, claim, complete


def main():
    verified = verify()
    capsule = OUT / 'publication/development-capsule-material-qualification-v3.tar.gz'
    if capsule.exists():
        raise ValueError('immutable capsule already exists')
    files = []
    for root in [OUT, ROOT / 'artifacts/roboboat-material-qualification-v2', ROOT / 'artifacts/roboboat-material-qualification-fixtures-v2']:
        files += [p for p in root.rglob('*') if p.is_file() and 'publication' not in p.parts and not p.name.endswith('.lock')]
    files += [p for p in DOC.glob('*material*') if p.is_file()]
    files += [DOC / name for name in ['MATERIAL_ENDPOINT_V2.md', 'MATERIAL_QUALIFICATION_V3_RESULTS.md', 'STATUS.md', 'HANDOFF.md', 'MANUSCRIPT_SECTION.md']]
    files += [Path(__file__).resolve(), ROOT / 'analysis/verify_roboboat_material_qualification_v3.py', ROOT / 'analysis/publish_roboboat_contact_policy_capsule_v2.py', ROOT / 'analysis/diagnostic_batch_pipeline.py']
    freeze = json.loads((DOC / 'material_qualification_operational_freeze_v3.json').read_text())
    files += [ROOT / b['path'] for b in freeze['dependencies']]
    files += [ROOT / 'tests/test_roboboat_material_endpoint_v2.py', ROOT / 'tests/test_roboboat_qualification_boolean_fields_v2.py']
    files = safe_members(files)
    capsule.parent.mkdir(parents=True, exist_ok=True)
    staging = capsule.with_suffix('.tmp')
    with staging.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as compressed, tarfile.open(fileobj=compressed, mode='w') as tar:
        for p in files:
            info = tar.gettarinfo(str(p), str(p.relative_to(ROOT)))
            info.uid = info.gid = 0; info.uname = info.gname = ''; info.mtime = 0
            with p.open('rb') as f:
                tar.addfile(info, f)
    staging.replace(capsule)
    with tarfile.open(capsule, 'r:gz') as tar:
        members = tar.getmembers()
        if len(members) != len(files) or len({m.name for m in members}) != len(files):
            raise ValueError('archive member count differs')
        for member in members:
            p = Path(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or tar.extractfile(member).read() != (ROOT / p).read_bytes():
                raise ValueError('unsafe or changed archive member')
    sha = digest(capsule)
    identity = hashlib.sha256(('marine-material-qualification-v3:' + sha).encode()).hexdigest()
    job_id = 'boat-material-qualification-v3-intake'
    plan = {'schema':'crane-diagnostic-batch-plan/v1','plan_id':job_id,'pool_limits':{'publication':1},'registered_looks':{},'scientific_role':'bounded construction qualification development intake; zero inferential looks','jobs':[{'job_id':job_id,'request_identity':identity,'pool':'publication','dependencies':[],'sequence_index':0,'arm':'boat-terminal-exploratory'}]}
    manifest = {'schema':'crane-diagnostic-batch-artifact-manifest/v1','job_id':job_id,'request_identity':identity,'visibility':'evaluator-only-never-mount-wholesale-to-methods','artifacts':[{'path':str(capsule),'bytes':capsule.stat().st_size,'sha256':sha}],'file_count':len(files),'verified':verified,'source_integration_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'shared_dvc_pointer_updated':False,'alpha_consumed':0,'human_validation':False}
    plan_path = DOC / 'publication_intake_plan_material-qualification-v3.json'
    ledger = DOC / 'publication_intake_ledger_material-qualification-v3.json'
    manifest_path = DOC / 'publication_artifact_manifest_material-qualification-v3.json'
    for path, value in [(plan_path, plan), (manifest_path, manifest)]:
        with path.open('x') as f:
            f.write(json.dumps(value, indent=2) + '\n')
    initialize(plan_path, ledger)
    job = claim(ledger, 'publication', 'marine-material-qualification-intake', 300)
    assert job['job_id'] == job_id
    print(complete(ledger, job_id, 'marine-material-qualification-intake', manifest_path))
    print(json.dumps({'sha256':sha,'bytes':capsule.stat().st_size,'file_count':len(files)}))


if __name__ == '__main__':
    main()
