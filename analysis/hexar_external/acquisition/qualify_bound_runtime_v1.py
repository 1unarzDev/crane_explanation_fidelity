"""Qualify the bound raw-runtime adapter using new DEVELOPMENT episodes only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import time
from ..confirmatory_v1.journal import exclusive_json

ROOT = Path(__file__).resolve().parents[3]
ACQUISITION = Path(__file__).resolve().parent
OUT = ROOT / 'manifests/hexar_external/acquisition'
# Each offline container has its own network namespace. A fixed bounded DDS
# domain avoids 70+ordinal exceeding practical ROS/DDS domain limits at large N.
ROS_DOMAIN_ID = 70

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def run(plan_path, image):
    plan = json.loads(plan_path.read_text())
    if plan['phase'] != 'development' or plan['status'] != 'DEVELOPMENT_ONLY':
        raise ValueError('This qualification runner never admits confirmation')
    # A repeated identity must fail before launching anything or writing into a
    # prior episode folder. Earlier versions only let the container reject it,
    # then could overwrite host receipts in that existing folder.
    records=plan['records']
    if not records or len({r['episode_id'] for r in records}) != len(records) or len({r['seed'] for r in records}) != len(records):
        raise ValueError('unique development episode identities and seeds required')
    if any((OUT/r['episode_id']).exists() or (OUT/(r['episode_id']+'.launch_claim.json')).exists() for r in records):
        raise ValueError('prior development episode identity exists; preserve its complete receipt')
    dest = plan_path.with_name(plan_path.stem + '_qualification_run.json')
    if dest.exists() or plan_path.with_name(plan_path.stem + '_preflight.log').exists():
        raise ValueError('prior qualification run exists; no reissue')
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in ACQUISITION.rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    source_bank_hash = hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest()
    source_bank = OUT / 'source_banks' / source_bank_hash
    if not source_bank.exists():
        source_bank.parent.mkdir(exist_ok=True)
        shutil.copytree(ACQUISITION, source_bank, ignore=shutil.ignore_patterns('__pycache__'))
    for original, expected in source_hashes.items():
        relative = Path(original).relative_to(ACQUISITION.relative_to(ROOT))
        if sha(source_bank / relative) != expected:
            raise ValueError('source snapshot hash mismatch')
    image_id = subprocess.check_output(['docker', 'inspect', '--format', '{{.Id}}', image], text=True).strip()
    preflight = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '-v', str(source_bank)+':/acquisition:ro', '--entrypoint', 'bash', image_id, '-lc', 'source /ws/install/setup.bash; python3 /acquisition/bound_episode_driver_v2.py --help'],capture_output=True,text=True)
    preflight_path = plan_path.with_name(plan_path.stem + '_preflight.log')
    with preflight_path.open('x') as stream:
        stream.write(preflight.stdout+preflight.stderr)
    if preflight.returncode:
        raise ValueError('native runtime imports/CLI qualification failed before any episode')
    summary = {'schema': 'hexar-bound-runtime-development-qualification/v1', 'status': 'IN_PROGRESS', 'image_id': image_id,
               'phase': 'development_only', 'plan_sha256': sha(plan_path), 'episodes': [],
               'semantic_outputs_generated': False, 'full_acquisition_qualified': False,
               'acquisition_phase': 'development_adapter_qualification', 'acquisition_binding_sha256': sha(plan_path)}
    dest.write_text(json.dumps(summary, indent=2) + '\n')
    for record in (r for r in plan['records'] if r['role'] == 'primary'):
        episode_id = record['episode_id']
        name = 'crane-' + episode_id
        command = ['docker', 'run', '--name', name, '--label', 'org.crane.scope=hexar-development',
                   '--network', 'none',
                   '--cpus', '3', '--memory', '5g', '--memory-swap', '6g', '--shm-size', '1g',
                   '-e', 'ROS_DOMAIN_ID=' + str(ROS_DOMAIN_ID),
                   '-v', str(source_bank) + ':/acquisition:ro', '-v', str(OUT) + ':/provenance',
                   '--entrypoint', '/bin/bash', image_id, '/acquisition/run_bound_episode_v1.sh',
                   record['family'], str(record['seed']), episode_id,
                   'development_adapter_qualification', sha(plan_path)]
        exclusive_json(OUT/(episode_id+'.launch_claim.json'), dict(schema='hexar-bound-raw-launch-claim/v1',
            phase='development_adapter_qualification', acquisition_binding_sha256=sha(plan_path),
            allocated=record, command=command, launch_limit=1, method_or_judge_calls_permitted=False))
        start = time.time()
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=230)
            code, output = result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'kill', name], capture_output=True)
            code, output = 124, 'TECHNICAL_INVALIDITY: container wall-clock limit'
        subprocess.run(['docker', 'run', '--rm', '-v', str(OUT) + ':/provenance', '--entrypoint', 'chown', image_id,
                        '-R', f'{os.getuid()}:{os.getgid()}', '/provenance'], capture_output=True)
        folder = OUT / episode_id
        folder.mkdir(exist_ok=True)
        (folder / 'host_execution.log').write_text(output)
        inspected = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True)
        info = json.loads(inspected.stdout)[0] if inspected.returncode == 0 else {}
        metadata = {'episode_id': episode_id, 'family_hidden': record['family'], 'seed_hidden': record['seed'],
                    'container_id': info.get('Id'), 'image_id': image_id, 'fresh_container': True,
                    'acquisition_phase': 'development_adapter_qualification', 'acquisition_binding_sha256': sha(plan_path),
                    'launch_claim_path': str((OUT/(episode_id+'.launch_claim.json')).relative_to(ROOT)),
                    'launch_claim_sha256': sha(OUT/(episode_id+'.launch_claim.json')),
                    'requested_network_mode': 'none',
                    'observed_network_mode': info.get('HostConfig', {}).get('NetworkMode'),
                    'requested_ros_domain_id': ROS_DOMAIN_ID,
                    'observed_ros_domain_id': next((item.split('=',1)[1] for item in info.get('Config',{}).get('Env',[]) if item.startswith('ROS_DOMAIN_ID=')),None),
                    'exit_code': code, 'wall_seconds': time.time() - start, 'raw_files': [],
                    'method_outputs_generated': False, 'judge_labels_generated': False,
                    'technical_validity': 'NOT_YET_ADJUDICATED',
                    'source_hashes': source_hashes, 'execution_source_bank_sha256': source_bank_hash}
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                metadata['raw_files'].append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': path.stat().st_size})
        (folder / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
        summary['episodes'].append(metadata)
        summary['status'] = 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED' if len(summary['episodes']) == sum(r['role']=='primary' for r in plan['records']) else 'IN_PROGRESS'
        dest.write_text(json.dumps(summary, indent=2) + '\n')
        # Never rerun an unfavorable valid result or substitute a reserve automatically.
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--image', default='crane-hexar-tiago:qualification-v1')
    args = parser.parse_args()
    result = run(args.plan, args.image)
    print(result['status'])
