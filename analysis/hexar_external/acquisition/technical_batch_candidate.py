"""Reproducible outcome-blind development qualification of acquisition checks.

Rechecks actual files rather than trusting booleans in a saved review. This is
not the final confirmation adapter and cannot admit confirmation episodes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from .audit_controller_batch_v3 import review
from .plan import FAMILIES
from .technical_predicate import evaluate
from ..confirmatory_v1.development_exposure import load_exclusions
from ..confirmatory_v1.journal import exclusive_json

ROOT = Path(__file__).resolve().parents[3]
ACQUISITION = Path('analysis/hexar_external/acquisition')


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def rooted(root, name):
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    return path


def canonical_review_episodes(root, rows):
    """Bag audit paths may be absolute or repository-relative; bytes must match."""
    result = copy.deepcopy(rows)
    for row in result:
        for item in row.get('bag_integrity', {}).get('bag_hashes', []):
            item['path'] = str(rooted(root, item['path']).relative_to(root))
    return result


def verify_capture(root, receipt, expected_image):
    """Verify captured bytes, provenance identity and executed source closure."""
    if receipt['image_id'] != expected_image or receipt['fresh_container'] is not True:
        raise ValueError('wrong image or unestablished fresh container')
    sources = receipt['source_hashes']
    bank_id = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    if not sources or bank_id != receipt['execution_source_bank_sha256']:
        raise ValueError('executed source bank identity mismatch')
    bank = rooted(root, 'manifests/hexar_external/acquisition/source_banks/' + bank_id)
    for name, expected in sources.items():
        relative = Path(name).relative_to(ACQUISITION)
        if digest(rooted(bank, relative)) != expected:
            raise ValueError('executed source bytes changed: ' + name)
    folder = rooted(root, 'manifests/hexar_external/acquisition/' + receipt['episode_id'])
    if json.loads((folder / 'provenance.json').read_text()) != receipt:
        raise ValueError('run summary differs from captured provenance')
    paths = set()
    bags = []
    for item in receipt['raw_files']:
        path = rooted(root, item['path'])
        path.relative_to(folder)
        if path in paths or path.stat().st_size != item['size'] or digest(path) != item['sha256']:
            raise ValueError('duplicate or changed captured artifact: ' + item['path'])
        paths.add(path)
        if path.suffix == '.db3' and path.parent.name == 'raw':
            bags.append(item['sha256'])
    required = {folder / name for name in ('episode.json', 'controller_start.json',
                'controller_end.json', 'raw/metadata.yaml')}
    if not required <= paths or not bags:
        raise ValueError('required captured artifacts missing')
    return bags


def build(plan_path, run_path, review_path, exposure_pin, expected_image, root=ROOT):
    root = Path(root).resolve()
    plan_path, run_path, review_path = (rooted(root, path)
                                      for path in (plan_path, run_path, review_path))
    plan = json.loads(plan_path.read_text())
    run = json.loads(run_path.read_text())
    saved = json.loads(review_path.read_text())
    if (plan.get('phase') != 'development' or plan.get('status') != 'DEVELOPMENT_ONLY'
            or run.get('phase') != 'development_only'
            or run.get('status') != 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED'
            or run.get('plan_sha256') != digest(plan_path)):
        raise ValueError('closed development run with matching plan required')
    records = plan['records']
    receipts = run['episodes']
    if (len(records) != len(FAMILIES) or {r['family'] for r in records} != set(FAMILIES)
            or any(r['role'] != 'primary' for r in records)
            or len({r['episode_id'] for r in records}) != len(records)
            or len({r['seed'] for r in records}) != len(records)
            or [r['episode_id'] for r in receipts] != [r['episode_id'] for r in records]):
        raise ValueError('complete unique six-family development schedule required')
    hashes, identities, seeds = load_exclusions(root, exposure_pin, require_current=True)
    recomputed = review(plan_path)
    if (saved.get('plan_sha256') != digest(plan_path)
            or canonical_review_episodes(root, saved.get('episodes', []))
                != canonical_review_episodes(root, recomputed['episodes'])
            or saved.get('packets') != recomputed['packets']):
        raise ValueError('saved interface review not reproducible from current raw files')
    rows = []
    all_bags = []
    for planned, receipt, interface in zip(records, receipts, recomputed['episodes']):
        episode_path = plan_path.parent / planned['episode_id'] / 'episode.json'
        episode = json.loads(episode_path.read_text())
        bags = verify_capture(root, receipt, expected_image)
        if (receipt['episode_id'] not in identities or receipt['seed_hidden'] not in seeds
                or not set(bags) <= hashes):
            raise ValueError('development attempt not permanently excluded')
        result = evaluate(receipt, episode, planned, interface)
        rows.append(dict(episode_id=planned['episode_id'], family=planned['family'],
                         predicate=result, raw_and_source_bytes_verified=True,
                         permanently_excluded_from_confirmation=True))
        all_bags.extend(bags)
    containers = [r['container_id'] for r in receipts]
    batch_checks = dict(
        pinned_image=run['image_id'] == expected_image,
        distinct_containers=all(containers) and len(set(containers)) == len(containers),
        distinct_recording_bytes=len(set(all_bags)) == len(all_bags),
        same_executed_source_bank=len({r['execution_source_bank_sha256'] for r in receipts}) == 1,
        complete_interface=len(recomputed['packets']) == 54
            and all(r['candidate_integrity'] is True for r in recomputed['episodes']),
        every_episode_predicate=all(r['predicate']['valid'] for r in rows))
    sources = [plan_path, run_path, review_path, rooted(root, exposure_pin['path'])]
    sources.extend(Path(__file__).parent / name for name in
                   ('technical_batch_candidate.py', 'technical_predicate.py',
                    'family_delivery.py', 'reset_geometry.py', 'scenario_geometry.py',
                    'audit_controller_batch_v3.py'))
    return dict(schema='hexar-development-technical-batch-candidate/v1',
        phase='development_only',
        status='TECHNICAL_BATCH_SCOPE_PASSED_NOT_FINAL_ADMISSION'
            if all(batch_checks.values()) else 'FAILED_RETAINED',
        image_id=expected_image, batch_checks=batch_checks, episodes=rows,
        source_hashes={str(p.relative_to(root)): digest(p) for p in sources},
        full_acquisition_qualified=False, confirmatory_N=0, alpha_consumed=0,
        navigation_success_used_as_exclusion=False, method_or_judge_calls=0,
        scope='Reproducible development batch checks. Final adapter, invalid-rate planning, '
              'scientific freeze, runtime dependency closure and untouched cohort remain required.')


def main():
    parser = argparse.ArgumentParser()
    for field in ('plan', 'run', 'review', 'exposure', 'output'):
        parser.add_argument('--' + field, required=True, type=Path)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    pin = dict(path=str(args.exposure), sha256=digest(args.exposure))
    value = build(args.plan, args.run, args.review, pin, args.image)
    exclusive_json(args.output, value)
    print(value['status'])


if __name__ == '__main__':
    main()
