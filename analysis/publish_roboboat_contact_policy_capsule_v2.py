#!/usr/bin/env python3
"""Publish fully reproduced contact-repair development with isolated intake only."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import subprocess
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from diagnostic_batch_pipeline import initialize,claim,complete
from analyze_roboboat_contact_policy_support_v2 import analyze,OUT,DECLARATION,PLAN


def validate_result(result,reproduced):
    if result!=reproduced:raise ValueError('released analysis does not reproduce')
    if (result.get('schema')!='roboboat-contact-policy-support-results/v2'
        or result.get('missing_annotations')!=[] or len(result.get('rows',[]))!=12
        or result.get('new_independent_configuration_n')!=0
        or result.get('confirmation_n')!=0 or result.get('replication_n')!=0
        or result.get('alpha_consumed')!=0 or result.get('paired_cluster_effect_estimated') is not False):
        raise ValueError('complete development-only result required')


def safe_members(paths,root=ROOT):
    files=sorted(set(paths))
    for p in files:
        p.relative_to(root)
        if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            raise ValueError('capsule must contain only isolated regular files')
    return files


def main():
    result_path=OUT/'development-results-v2.json'
    result=json.loads(result_path.read_text());validate_result(result,analyze())
    capsule=OUT/'publication/development-capsule-contact-comparison-v2.tar.gz'
    if capsule.exists():raise ValueError('immutable capsule exists')
    roots=[OUT,ROOT/'artifacts/roboboat-contact-policy-comparison-v2',ROOT/'artifacts/roboboat-contact-policy-inventory-v2',ROOT/'artifacts/roboboat-contact-policy-v2',ROOT/'artifacts/roboboat-contact-scope-v3',ROOT/'artifacts/roboboat-terminal-settling-v1']
    files=[]
    for root in roots:
        files += [p for p in root.rglob('*') if p.is_file() and 'publication' not in p.parts and not p.name.endswith('.lock')]
    files += [p for p in DOC.rglob('*') if p.is_file()]
    files += list((ROOT/'analysis').glob('*roboboat*.py'))
    files += list((ROOT/'tests').glob('test_roboboat*.py'))
    for declaration in (DECLARATION,PLAN,DOC/'contact_policy_response_declaration_v2.json',DOC/'contact_policy_inventory_declaration_v2.json',DOC/'contact_policy_qualification_freeze_v2.json',DOC/'contact_scope_qualification_freeze_v3.json'):
        value=json.loads(declaration.read_text())
        for b in value.get('dependencies',[])+value.get('method_sources',[]):
            p=ROOT/b['path']
            if digest(p)!=b['sha256']:raise ValueError('capsule dependency changed: '+b['path'])
            files.append(p)
    files=safe_members(files)
    capsule.parent.mkdir(parents=True,exist_ok=True);staging=capsule.with_suffix('.tmp')
    with staging.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as tar:
                for p in files:
                    info=tar.gettarinfo(str(p),str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                    with p.open('rb') as f:tar.addfile(info,f)
    staging.replace(capsule)
    with tarfile.open(capsule,'r:gz') as tar:
        members=tar.getmembers();names=[m.name for m in members]
        if len(names)!=len(set(names)) or len(names)!=len(files):raise ValueError('duplicate or missing archive members')
        for member in members:
            path=Path(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts:raise ValueError('unsafe archive member')
            if tar.extractfile(member).read()!=(ROOT/path).read_bytes():raise ValueError('archive member differs from bound source')
    sha=digest(capsule);identity=hashlib.sha256(('marine-contact-comparison-v2:'+sha).encode()).hexdigest()
    plan={'schema':'crane-diagnostic-batch-plan/v1','plan_id':'roboboat-contact-comparison-v2-development-intake','pool_limits':{'publication':1},'registered_looks':{},'scientific_role':'complete inspected development replay intake, not an inferential scientific look','jobs':[{'job_id':'boat-contact-comparison-v2-intake','request_identity':identity,'pool':'publication','dependencies':[],'sequence_index':0,'arm':'boat-terminal-exploratory'}]}
    manifest={'schema':'crane-diagnostic-batch-artifact-manifest/v1','job_id':'boat-contact-comparison-v2-intake','request_identity':identity,'visibility':'mixed-separated-development-capsule-evaluator-only-never-a-method-input','artifacts':[{'path':str(capsule),'bytes':capsule.stat().st_size,'sha256':sha}],'file_count':len(files),'analysis_reproduced':True,'annotation_completion':'complete-agent-assessed-development-support; material-primary-mapping-unqualified','human_validation':False,'shared_dvc_pointer_updated':False,'new_configuration_n':0,'confirmation_n_added':0,'replication_n_added':0,'alpha_consumed':0,'failed_qualifications_retained':True,'source_integration_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()}
    plan_path=DOC/'publication_intake_plan_contact-comparison-v2.json';ledger=DOC/'publication_intake_ledger_contact-comparison-v2.json';manifest_path=DOC/'publication_artifact_manifest_contact-comparison-v2.json'
    save(plan_path,plan);save(manifest_path,manifest)
    initialize(plan_path,ledger);job=claim(ledger,'publication','marine-contact-comparison-intake',300)
    assert job['job_id']==manifest['job_id']
    print(complete(ledger,job['job_id'],'marine-contact-comparison-intake',manifest_path))
    print(json.dumps({'sha256':sha,'bytes':capsule.stat().st_size,'file_count':len(files)}))


if __name__=='__main__':main()
