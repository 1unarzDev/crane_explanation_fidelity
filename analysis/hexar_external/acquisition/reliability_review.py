"""Complete disposition of a fixed development acquisition reliability campaign.

Never accepts an in-progress run, omits a failed attempt or calls a provider.
Does not freeze a study or authorize confirmation acquisition.
"""
import argparse
import json
from pathlib import Path
import subprocess

from .audit_controller_batch_v3 import review
from .operational_validity_candidate import evaluate
from .plan import FAMILIES
from .technical_batch_candidate import ROOT, digest, verify_capture
from .technical_reliability import summarize
from ..confirmatory_v1.journal import exclusive_json


def schedule(plan, run):
    records = plan.get('records', [])
    receipts = run.get('episodes', [])
    if (plan.get('phase') != 'development' or plan.get('status') != 'DEVELOPMENT_ONLY'
            or run.get('phase') != 'development_only'
            or run.get('status') != 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED'
            or len(records) != 144 or len(receipts) != 144):
        raise ValueError('complete fixed 144-attempt development campaign required; live runs cannot be scored')
    if (len({r['episode_id'] for r in records}) != 144 or len({r['seed'] for r in records}) != 144
            or any(r['role'] != 'primary' for r in records)
            or any(sum(r['family'] == family for r in records) != 24 for family in FAMILIES)
            or [r['episode_id'] for r in receipts] != [r['episode_id'] for r in records]):
        raise ValueError('fixed schedule changed or incomplete')
    if any(r['method_outputs_generated'] is not False or r['judge_labels_generated'] is not False for r in receipts):
        raise ValueError('semantic exposure prohibited in this qualification')


def execute(plan_path, run_path, destination):
    plan = json.loads(plan_path.read_text())
    run = json.loads(run_path.read_text())
    schedule(plan, run)
    if run['plan_sha256'] != digest(plan_path):
        raise ValueError('closed run differs from declared schedule')
    declaration = plan['qualification_design']
    if digest(ROOT / declaration['path']) != declaration['sha256']:
        raise ValueError('prospective engineering qualification declaration changed')
    # Reserve the whole report namespace before any derived extraction.
    destination.mkdir(exist_ok=False)
    capture = {}
    allowed = []
    for receipt in run['episodes']:
        try:
            bags = verify_capture(ROOT, receipt, run['image_id'])
            capture[receipt['episode_id']] = dict(passed=True, error=None, bag_sha256s=bags)
            allowed.append(receipt)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            capture[receipt['episode_id']] = dict(passed=False, error=type(exc).__name__ + ': ' + str(exc))
    exclusive_json(destination / 'capture_review.json', capture)
    native_input = dict(run, episodes=allowed)
    exclusive_json(destination / 'native_inputs.json', native_input)
    base = ROOT / 'manifests/hexar_external/acquisition'
    banks = {r['execution_source_bank_sha256'] for r in allowed}
    native_rows = []
    if allowed:
        if len(banks) != 1:
            raise ValueError('qualified native extraction requires one executed source bank')
        bank = base / 'source_banks' / next(iter(banks))
        code = Path(__file__).with_name('reliability_native_batch.py')
        command = ['docker', 'run', '--rm', '--network', 'none', '--memory', '5g',
                   '-v', str(base) + ':/input', '-v', str(bank) + ':/bank:ro',
                   '-v', str(code) + ':/review.py:ro', '--entrypoint', 'bash', run['image_id'], '-lc',
                   'source /ws/install/setup.bash; python3 /review.py --root /input --bank /bank --run "$1"',
                   'native-review', '/input/' + str((destination / 'native_inputs.json').relative_to(base))]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=1800, check=True)
            native_rows = json.loads(result.stdout)
        except (subprocess.SubprocessError, ValueError) as exc:
            exclusive_json(destination / 'native_transport_failure.json', dict(error=str(exc)))
    exclusive_json(destination / 'native_review.json', native_rows)
    interface = review(plan_path)
    exclusive_json(destination / 'interface_review.json', interface)
    interfaces = {r['development_id']: r for r in interface['episodes']}
    natives = {r['episode_id']: r for r in native_rows}
    containers = [r.get('container_id') for r in run['episodes']]
    container_unique = bool(all(containers)) and len(set(containers)) == 144
    source_unique = len({r.get('execution_source_bank_sha256') for r in run['episodes']}) == 1
    all_bags = [sha for record in capture.values() for sha in record.get('bag_sha256s', [])]
    bag_unique = len(all_bags) == len(set(all_bags))
    rows = []
    for planned, receipt in zip(plan['records'], run['episodes']):
        uid = planned['episode_id']
        reasons = []
        if not capture[uid]['passed']:
            reasons.append('CAPTURE_REVIEW_FAILURE: ' + capture[uid]['error'])
        if not container_unique or not source_unique or not bag_unique:
            reasons.append('BATCH_CONTAINER_SOURCE_OR_BAG_IDENTITY_NOT_ESTABLISHED')
        native = natives.get(uid)
        if native is None or native['status'] != 'CLOSED_NATIVE_REVIEW':
            reasons.append('NATIVE_REVIEW_UNRESOLVED: ' + str(native.get('error') if native else 'missing'))
        try:
            episode = json.loads((base / uid / 'episode.json').read_text())
            predicate = evaluate(receipt, episode, planned, interfaces[uid],
                                 native['review'] if native and 'review' in native else {})
            reasons.extend(predicate['reasons'])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            reasons.append('OPERATIONAL_REVIEW_UNRESOLVED: ' + str(exc))
        rows.append(dict(episode_id=uid, family=planned['family'], technical_valid=not reasons,
                         reasons=reasons, method_outcomes_accessed=False))
    reliability = summarize(rows, FAMILIES)
    from ..confirmatory_v1.development_exposure import inventory, verify_current_inventory
    exposure = inventory(ROOT)
    verify_current_inventory(ROOT, exposure)
    exclusive_json(destination / 'exposure_inventory.json', exposure)
    sources = [plan_path, run_path, ROOT / declaration['path']]
    sources.extend(Path(__file__).parent / name for name in
                   ('reliability_review.py', 'reliability_native_batch.py',
                    'operational_validity_candidate.py', 'technical_reliability.py',
                    'technical_predicate.py', 'family_delivery.py', 'audit_controller_batch_v3.py'))
    report = dict(schema='hexar-development-acquisition-reliability/v1', phase='development_only',
        status='CANDIDATE_ACQUISITION_PROCESS_QUALIFIED_NOT_FINAL_ADMISSION'
            if reliability['engineering_criterion_passed'] else 'FAILED_QUALIFICATION_RETAINED',
        rows=rows, reliability=reliability, image_id=run['image_id'],
        source_hashes={str(p.resolve().relative_to(ROOT)): digest(p) for p in sources},
        evidence_hashes={p.name: digest(p) for p in destination.glob('*.json')},
        confirmatory_N=0, alpha_consumed=0, method_or_judge_calls=0,
        full_scientific_freeze=False, confirmation_authorized=False)
    exclusive_json(destination / 'report.json', report)
    print(report['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    execute(args.plan.resolve(), args.run.resolve(), args.output_dir.resolve())
