"""Enumerate the actual pinned simulator map using the captured sampler.

Development-only, offline, no robot episodes or semantic provider calls.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys


def native(sampler_dir):
    sys.path.insert(0, str(sampler_dir))
    sampler = importlib.import_module('sampling')
    np, math = sampler.np, sampler.math
    config = sampler.yaml.safe_load(sampler.MAP.read_text())
    pgm = sampler.MAP.parent / config['image']
    pixels = sampler.read_pgm(pgm)
    resolution = config['resolution']
    radius = math.ceil(.6 / resolution)
    candidates = []
    for row in range(radius, pixels.shape[0] - radius):
        for col in range(radius, pixels.shape[1] - radius):
            x = config['origin'][0] + (col + .5) * resolution
            y = config['origin'][1] + (pixels.shape[0] - row - .5) * resolution
            if (-6 <= x <= 1.2 and -.5 <= y <= 2.0
                    and np.all(pixels[row-radius:row+radius+1, col-radius:col+radius+1] >= 254)):
                candidates.append((x, y))
    if not candidates:
        raise ValueError('empty sampling population')
    coordinates = np.asarray(candidates)
    counts = []
    for start in coordinates:
        distances = np.sqrt(np.sum((coordinates - start) ** 2, axis=1))
        counts.append(int(np.count_nonzero((distances >= 3) & (distances <= 5.5))))
    # Check the enumeration against actual captured sampler outputs. This is
    # compatibility checking, not a replacement implementation for acquisition.
    positions = {tuple(point): index for index, point in enumerate(candidates)}
    for seed in (0, 1, 42, 3244494810, 2**32 - 1):
        sampled = sampler.sample(seed)
        if (sampled['candidate_start_n'] != len(candidates)
                or sampled['candidate_goal_n'] != counts[positions[tuple(sampled['start_xy'])]]
                or tuple(sampled['goal_xy']) not in positions):
            raise ValueError('enumeration differs from captured sampler')
    return dict(candidate_start_n=len(candidates), minimum_eligible_goals=min(counts),
        maximum_eligible_goals=max(counts), starts_without_eligible_goal=counts.count(0),
        image_shape=list(pixels.shape), resolution_m=resolution, origin=config['origin'],
        clearance_m=.6, distance_limits_m=[3, 5.5], sampling_bounds_xy=[-6, 1.2, -.5, 2.0],
        map_yaml_sha256=hashlib.sha256(sampler.MAP.read_bytes()).hexdigest(),
        map_pgm_sha256=hashlib.sha256(pgm.read_bytes()).hexdigest(),
        sampling_source_sha256=hashlib.sha256((sampler_dir / 'sampling.py').read_bytes()).hexdigest(),
        compatibility_seed_checks=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-sampler', type=Path)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--prior', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.native_sampler:
        print(json.dumps(native(args.native_sampler)))
        return
    if not all((args.run, args.prior, args.output)):
        parser.error('host mode requires --run, --prior and --output')
    from .technical_batch_candidate import ROOT, digest, verify_capture
    from ..confirmatory_v1.journal import exclusive_json
    run = json.loads(args.run.read_text())
    if run.get('phase') != 'development_only' or run.get('status') != 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED':
        raise ValueError('closed development source bank required')
    receipt = run['episodes'][0]
    verify_capture(ROOT, receipt, run['image_id'])
    bank = ROOT / 'manifests/hexar_external/acquisition/source_banks' / receipt['execution_source_bank_sha256']
    command = ['docker', 'run', '--rm', '--network', 'none',
               '-v', str(bank) + ':/captured_sampler:ro',
               '-v', str(Path(__file__).resolve()) + ':/enumerate.py:ro',
               '--entrypoint', 'python3', run['image_id'], '/enumerate.py',
               '--native-sampler', '/captured_sampler']
    result = subprocess.run(command, capture_output=True, text=True, timeout=90, check=True)
    value = json.loads(result.stdout)
    prior = json.loads(args.prior.read_text())
    for key in value:
        if key != 'compatibility_seed_checks' and prior.get(key) != value[key]:
            raise ValueError('prior enumeration does not reproduce: ' + key)
    value.update(schema='hexar-sampling-frame-enumeration-candidate/v2',
        phase='development_only', image_id=run['image_id'],
        source_bank_sha256=receipt['execution_source_bank_sha256'],
        source_hashes={str(path.resolve().relative_to(ROOT)): digest(path)
                       for path in (Path(__file__), args.run, args.prior)},
        prior_enumeration_reproduced=True, qualified_for_confirmation=False,
        confirmatory_N=0, alpha_consumed=0)
    exclusive_json(args.output, value)
    print('SAMPLING_FRAME_REPRODUCED_NOT_FULL_QUALIFICATION')


if __name__ == '__main__':
    main()
