"""Development-only fixed-domain runtime review; no confirmation admission."""
import hashlib
import json
import math
from pathlib import Path
from .plan import FAMILIES
from ..confirmatory_v1.journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/acquisition'


def domain_checks(receipt):
    return dict(offline_network=receipt.get('requested_network_mode')=='none' and receipt.get('observed_network_mode')=='none',
        requested_domain_70=type(receipt.get('requested_ros_domain_id')) is int and receipt['requested_ros_domain_id']==70,
        observed_domain_70=receipt.get('observed_ros_domain_id')=='70')


def report():
    run_path=BASE/'development_episode_plan_v14_qualification_run.json'
    integrity_path=BASE/'controller_boundary_qualification_v14_v3.json'
    plan_path=BASE/'development_episode_plan_v14.json'
    run=json.loads(run_path.read_text());integrity=json.loads(integrity_path.read_text());plan=json.loads(plan_path.read_text())
    if (run['status']!='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED' or len(run['episodes'])!=6
            or plan['phase']!='development' or integrity['phase']!='development_only'):
        raise ValueError('six closed development attempts and retained integrity report required')
    audits={r['development_id']:r for r in integrity['episodes']};planned={r['episode_id']:r for r in plan['records']}
    if set(audits)!=set(planned) or {r['family'] for r in plan['records']}!=set(FAMILIES):
        raise ValueError('complete six-family closed schedule required')
    rows=[];sources=[Path(__file__),run_path,integrity_path,plan_path]
    for receipt in run['episodes']:
        uid=receipt['episode_id'];path=BASE/uid/'episode.json';sources.extend([path,BASE/uid/'provenance.json'])
        episode=json.loads(path.read_text());bank=BASE/'source_banks'/receipt['execution_source_bank_sha256']
        for name,expected in receipt['source_hashes'].items():
            relative=Path(name).relative_to('analysis/hexar_external/acquisition')
            if hashlib.sha256((bank/relative).read_bytes()).hexdigest()!=expected:raise ValueError('executed source bank changed')
        for raw in receipt['raw_files']:
            data=ROOT/raw['path'];digest=hashlib.sha256()
            with data.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            if digest.hexdigest()!=raw['sha256']:raise ValueError('captured artifact changed: '+raw['path'])
        error=episode.get('measured_reset_error_m')
        checks=dict(domain_checks(receipt),execution_exit_zero=receipt['exit_code']==0,
            raw_and_interface_integrity=audits[uid]['candidate_integrity'] is True,
            measured_reset=type(error) in (int,float) and math.isfinite(error) and 0<=error<=.05,
            applied_seed_matches_plan=audits[uid].get('bag_integrity',{}).get('seed_applied_matches_plan') is True
                and episode['seed_hidden']==planned[uid]['seed']==receipt['seed_hidden'],
            accepted_goal=episode['accepted'] is True,
            no_method_or_judge_output=receipt['method_outputs_generated'] is False and receipt['judge_labels_generated'] is False)
        rows.append(dict(episode_id=uid,checks=checks,passed=all(checks.values()),
            measured_reset_error_m=error,terminal_action_status=episode.get('terminal_action_status'),
            navigation_result_used_as_exclusion=False))
    distinct=len({r['container_id'] for r in run['episodes']})==6 and all(r['container_id'] for r in run['episodes'])
    same_image=len({r['image_id'] for r in run['episodes']})==1
    same_bank=len({r['execution_source_bank_sha256'] for r in run['episodes']})==1
    passed=all(r['passed'] for r in rows) and distinct and same_image and same_bank
    return dict(schema='hexar-fixed-offline-domain-qualification/v2',phase='development_only',
        status='FIXED_DOMAIN_SCOPE_PASSED_NOT_FULL_ACQUISITION_QUALIFICATION' if passed else 'FAILED_RETAINED',
        episodes=rows,distinct_containers=bool(distinct),same_image=same_image,same_source_bank=same_bank,
        image_id=run['image_id'],full_acquisition_qualified=False,confirmatory_N=0,alpha_consumed=0,
        scope='Actual six-family Gazebo/Nav2 operation at fixed DDS domain 70 in separate offline containers. Raw/source/reset/seed/interface checks pass without excluding navigation failures. Final population, family exposure, technical-invalidity rates and predicates remain to qualify.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__=='__main__':
    value=report();exclusive_json(BASE/'offline_domain_qualification_v14_v2.json',value);print(value['status'])
