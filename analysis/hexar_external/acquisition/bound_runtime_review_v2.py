"""Versioned path-normalized terminal review of development provenance.

Uses the previously qualified raw/native/interface checks, never explanations.
This cannot review an incomplete run or authorize confirmation acquisition.
"""
import argparse
import json
from pathlib import Path
import subprocess

from .audit_controller_batch_v3 import review as interface_review
from .operational_validity_candidate import evaluate
from .plan import FAMILIES
from .technical_batch_candidate import ROOT, digest, verify_capture
from ..confirmatory_v1.development_exposure import inventory, verify_current_inventory
from ..confirmatory_v1.journal import exclusive_json


EXPECTED_IMAGE = 'sha256:4eea187f76d80c5750e167347b6994d0d5e12a9c1183ea27a2f991187f3b9cbd'


def execute(plan_path, run_path, destination):
    plan_path, run_path, destination = (Path(p).resolve() for p in (plan_path, run_path, destination))
    for p in (plan_path, run_path, destination):
        p.relative_to(ROOT.resolve())
    plan, run = (json.loads(p.read_text()) for p in (plan_path, run_path))
    if (plan.get('phase')!='development' or plan.get('status')!='DEVELOPMENT_ONLY'
            or run.get('schema')!='hexar-bound-runtime-development-qualification/v1'
            or run.get('image_id')!=EXPECTED_IMAGE
            or run.get('phase')!='development_only'
            or run.get('status')!='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED'
            or run.get('acquisition_phase')!='development_adapter_qualification'
            or run.get('acquisition_binding_sha256')!=digest(plan_path)
            or run.get('plan_sha256')!=digest(plan_path)):
        raise ValueError('complete declared development bound-runtime run required')
    records, receipts = plan['records'], run['episodes']
    if (len(records)!=6 or len(receipts)!=6
            or {r['family'] for r in records}!=set(FAMILIES)
            or any(r['role']!='primary' for r in records)
            or len({r['seed'] for r in records})!=6
            or [r['episode_id'] for r in records]!=[r['episode_id'] for r in receipts]):
        raise ValueError('all six allocated development attempts must be retained')
    declaration=plan['qualification_design']
    if digest(ROOT/declaration['path'])!=declaration['sha256']:
        raise ValueError('predeclared qualification design changed')
    destination.mkdir(exist_ok=False)
    capture, allowed = {}, []
    base=ROOT/'manifests/hexar_external/acquisition'
    for record, receipt in zip(records, receipts):
        uid=record['episode_id']
        try:
            bags=verify_capture(ROOT,receipt,run['image_id'])
            folder=base/uid
            intent=json.loads((folder/'acquisition_intent.json').read_text())
            episode=json.loads((folder/'episode.json').read_text())
            expected=dict(schema='hexar-bound-acquisition-intent/v1',phase='development_adapter_qualification',
                acquisition_binding_sha256=digest(plan_path),episode_id=uid,family_hidden=record['family'],
                seed_hidden=record['seed'],method_outputs_permitted=False)
            if intent!=expected or episode.get('schema')!='hexar-bound-episode-runtime/v2' or episode.get('semantic_outputs_generated') is not False or episode.get('phase')!=expected['phase'] or episode.get('acquisition_binding_sha256')!=digest(plan_path):
                raise ValueError('prelaunch intent and driver phase/binding differ')
            if (receipt.get('acquisition_phase')!=expected['phase']
                    or receipt.get('acquisition_binding_sha256')!=digest(plan_path)
                    or receipt.get('method_outputs_generated') is not False
                    or receipt.get('judge_labels_generated') is not False):
                raise ValueError('host receipt phase/binding/semantic scope differs')
            claim_path=ROOT/receipt['launch_claim_path']
            if claim_path.resolve()!= (base/(uid+'.launch_claim.json')).resolve() or digest(claim_path)!=receipt['launch_claim_sha256']:
                raise ValueError('prelaunch host claim missing or changed')
            claim=json.loads(claim_path.read_text())
            if (claim.get('phase')!=expected['phase'] or claim.get('acquisition_binding_sha256')!=digest(plan_path)
                    or claim.get('allocated')!=record or claim.get('launch_limit')!=1
                    or claim.get('method_or_judge_calls_permitted') is not False
                    or claim['command'][-6:]!=['/acquisition/run_bound_episode_v1.sh',record['family'],str(record['seed']),uid,
                                             expected['phase'],digest(plan_path)]):
                raise ValueError('host launch claim differs from prospective allocation')
            capture[uid]=dict(passed=True,error=None,bag_sha256s=bags,launch_claim_sha256=digest(claim_path))
            allowed.append(receipt)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            capture[uid]=dict(passed=False,error=type(exc).__name__+': '+str(exc),bag_sha256s=[])
    exclusive_json(destination/'capture_review.json',capture)
    exclusive_json(destination/'native_inputs.json',dict(run,episodes=allowed))
    banks={r['execution_source_bank_sha256'] for r in allowed}
    native_rows=[]
    if allowed:
        if len(banks)!=1:raise ValueError('one executed native source bank required')
        bank=base/'source_banks'/next(iter(banks))
        code=Path(__file__).with_name('reliability_native_batch.py')
        command=['docker','run','--rm','--network','none','--memory','5g',
            '-v',str(base)+':/input','-v',str(bank)+':/bank:ro','-v',str(code)+':/review.py:ro',
            '--entrypoint','bash',run['image_id'],'-lc',
            'source /ws/install/setup.bash; python3 /review.py --root /input --bank /bank --run "$1"',
            'native-review','/input/'+str((destination/'native_inputs.json').relative_to(base))]
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=1800,check=True)
            native_rows=json.loads(result.stdout)
        except (subprocess.SubprocessError,ValueError) as exc:
            exclusive_json(destination/'native_transport_failure.json',dict(error=str(exc)))
    exclusive_json(destination/'native_review.json',native_rows)
    interfaces=interface_review(plan_path)
    exclusive_json(destination/'interface_review.json',interfaces)
    by_interface={r['development_id']:r for r in interfaces['episodes']}
    by_native={r['episode_id']:r for r in native_rows}
    rows=[]
    containers=[r.get('container_id') for r in receipts]
    bags=[h for r in capture.values() for h in r['bag_sha256s']]
    distinct=all(containers) and len(set(containers))==6 and len(bags)==len(set(bags))
    for record, receipt in zip(records,receipts):
        uid=record['episode_id'];reasons=[]
        if not capture[uid]['passed']:reasons.append('CAPTURE_BINDING: '+capture[uid]['error'])
        if not distinct:reasons.append('CONTAINER_OR_RAW_IDENTITY_NOT_UNIQUE')
        native=by_native.get(uid)
        if native is None or native['status']!='CLOSED_NATIVE_REVIEW':reasons.append('NATIVE_REVIEW_UNRESOLVED')
        try:
            episode=json.loads((base/uid/'episode.json').read_text())
            verdict=evaluate(receipt,episode,record,by_interface[uid],native.get('review',{}) if native else {})
            reasons.extend(verdict['reasons'])
        except (OSError,ValueError,KeyError,TypeError) as exc:reasons.append('OPERATIONAL_REVIEW: '+str(exc))
        rows.append(dict(episode_id=uid,family=record['family'],technical_valid=not reasons,
                         reasons=reasons,method_outcomes_accessed=False))
    exposure=inventory(ROOT);verify_current_inventory(ROOT,exposure)
    exclusive_json(destination/'exposure_inventory.json',exposure)
    sources=[plan_path,run_path,ROOT/declaration['path']]
    sources.extend(Path(__file__).with_name(name) for name in
        ('bound_runtime_review_v2.py','bound_runtime_review_v1.py','reliability_native_batch.py','audit_controller_batch_v3.py',
         'operational_validity_candidate.py','technical_predicate.py','family_delivery.py'))
    report=dict(schema='hexar-bound-runtime-development-review/v2',phase='development_only',
        status='BOUND_PROVENANCE_RUNTIME_SCOPE_QUALIFIED_NOT_FINAL_ADMISSION'
            if all(r['technical_valid'] for r in rows) else 'FAILED_QUALIFICATION_RETAINED',
        rows=rows,image_id=run['image_id'],plan_sha256=digest(plan_path),
        source_hashes={str(p.relative_to(ROOT)):digest(p) for p in sources},
        evidence_hashes={name:digest(destination/name) for name in ('capture_review.json','native_inputs.json',
                'native_review.json','interface_review.json','exposure_inventory.json')},
        method_or_judge_calls=0,confirmatory_N=0,alpha_consumed=0,confirmation_authorized=False,
        scope='New development episodes qualify prelaunch phase/binding provenance and unchanged raw checks; '
              'production host admission/raw schedule/review/export/sealing/scientific freeze remain pending.')
    exclusive_json(destination/'report.json',report)
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args();print(execute(args.plan,args.run,args.output_dir)['status'])
