#!/usr/bin/env python3
"""Publish an isolated development capsule through the existing coordinator intake API."""
import argparse,gzip,hashlib,json,tarfile
from pathlib import Path
from diagnostic_batch_pipeline import initialize,claim,complete
from build_roboboat_terminal_batch import save
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/roboboat_terminal_evidence'

def publication_gate(result,version,expected_answers):
    if version=='atomic-v1':
        if (result.get('schema')!='roboboat-atomic-missing-judgment-development-sensitivity/v1'
            or result.get('accounted_original_answers')!=expected_answers
            or len(result['rows'])!=expected_answers
            or result.get('finalized_answers',0)+result.get('unavailable_judgments',0)!=expected_answers
            or len(result['missing_annotations'])!=result.get('unavailable_judgments')
            or result.get('original_complete_bank_score_released') is not False):
            raise RuntimeError('retained-failure capsule needs complete explicit judgment accounting')
    elif result['missing_annotations'] or len(result['rows'])!=expected_answers:
        raise RuntimeError('incomplete comparison cannot publish a completed capsule')

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact-root',type=Path,required=True)
    p.add_argument('--version',choices=('v1','v3','atomic-v1'),default='v1')
    p.add_argument('--results-file',default='comparison-results.json')
    p.add_argument('--expected-answers',type=int,default=18)
    p.add_argument('--additional-artifact-root',type=Path,action='append',default=[])
    a=p.parse_args();a.artifact_root=a.artifact_root.resolve()
    result=json.loads((a.artifact_root/a.results_file).read_text())
    publication_gate(result,a.version,a.expected_answers)
    if a.version=='atomic-v1':
        disposition=DOC/'marine_atomic_timeout_disposition_v1.json'
        if hashlib.sha256(disposition.read_bytes()).hexdigest()!=result['disposition_sha256']:
            raise RuntimeError('retained-failure disposition changed')
    capsule=a.artifact_root/f'publication/development-capsule-{a.version}.tar.gz'
    capsule.parent.mkdir(parents=True,exist_ok=True)
    if capsule.exists():raise RuntimeError('immutable capsule already exists')
    files=sorted(p for p in a.artifact_root.rglob('*') if p.is_file() and 'publication' not in p.parts and not p.name.endswith('.lock'))
    for additional in a.additional_artifact_root:
        files+=sorted(p for p in additional.resolve().rglob('*') if p.is_file() and 'publication' not in p.parts and not p.name.endswith('.lock'))
    files+=sorted(p for p in DOC.rglob('*') if p.is_file() and p.suffix!='.png')
    files+=sorted(p for p in (ROOT/'analysis').glob('*roboboat*.py'))
    staging=capsule.with_suffix('.tmp')
    with staging.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as tar:
                for path in files:
                    info=tar.gettarinfo(str(path),str(path.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                    with path.open('rb') as f:tar.addfile(info,f)
    staging.replace(capsule)
    sha=hashlib.sha256(capsule.read_bytes()).hexdigest()
    identity=hashlib.sha256((f'marine-development-intake-{a.version}:'+sha).encode()).hexdigest()
    plan={'schema':'crane-diagnostic-batch-plan/v1','plan_id':f'roboboat-terminal-development-intake-{a.version}',
          'pool_limits':{'publication':1},'registered_looks':{},
          'scientific_role':'post-execution development artifact intake; not a prospective scientific look',
          'jobs':[{'job_id':'boat-terminal-capsule-intake','request_identity':identity,'pool':'publication','dependencies':[],'sequence_index':0,'arm':'boat-terminal-exploratory'}]}
    plan_path=DOC/f'publication_intake_plan_{a.version}.json';ledger=DOC/f'publication_intake_ledger_{a.version}.json'
    manifest_path=DOC/f'publication_artifact_manifest_{a.version}.json'
    save(plan_path,plan)
    save(manifest_path,{'schema':'crane-diagnostic-batch-artifact-manifest/v1','job_id':'boat-terminal-capsule-intake','request_identity':identity,
       'visibility':'mixed-separated-development-capsule-evaluator-only-not-a-method-input',
       'artifacts':[{'path':str(capsule.resolve()),'bytes':capsule.stat().st_size,'sha256':sha}],
       'file_count':len(files),'shared_dvc_pointer_updated':False,'confirmation_n_added':0,'alpha_consumed':0.,
       'annotation_completion':'retained-timeout-complete-accounting-not-complete-annotation' if a.version=='atomic-v1' else 'complete-development-annotation'})
    initialize(plan_path,ledger);job=claim(ledger,'publication','marine-intake-worker',300)
    assert job['job_id']=='boat-terminal-capsule-intake'
    print(complete(ledger,job['job_id'],'marine-intake-worker',manifest_path))
if __name__=='__main__':main()
