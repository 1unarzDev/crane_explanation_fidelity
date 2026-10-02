"""Scoped offline acquisition qualification, never confirmation admission."""
import hashlib
import json
import math
from pathlib import Path
from ..confirmatory_v1.journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/acquisition'


def report():
    run_path=BASE/'development_episode_plan_v13_qualification_run.json'
    integrity_path=BASE/'controller_boundary_qualification_v13.json'
    plan_path=BASE/'development_episode_plan_v13.json'
    run=json.loads(run_path.read_text());integrity=json.loads(integrity_path.read_text());plan=json.loads(plan_path.read_text())
    if run['status']!='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED' or len(run['episodes'])!=6:
        raise ValueError('all six closed development attempts required')
    audits={r['development_id']:r for r in integrity['episodes']}
    planned={r['episode_id']:r for r in plan['records']};rows=[];sources=[Path(__file__),run_path,integrity_path,plan_path]
    for receipt in run['episodes']:
        uid=receipt['episode_id'];path=BASE/uid/'episode.json';episode=json.loads(path.read_text());sources.append(path)
        bank=BASE/'source_banks'/receipt['execution_source_bank_sha256']
        for name,expected in receipt['source_hashes'].items():
            relative=Path(name).relative_to('analysis/hexar_external/acquisition')
            if hashlib.sha256((bank/relative).read_bytes()).hexdigest()!=expected:
                raise ValueError('execution source bank changed')
        error=episode.get('measured_reset_error_m')
        checks=dict(offline_network=receipt.get('requested_network_mode')=='none' and receipt.get('observed_network_mode')=='none',
            execution_exit_zero=receipt['exit_code']==0,
            candidate_raw_and_interface_integrity=audits[uid]['candidate_integrity'] is True,
            measured_reset=type(error) in (int,float) and math.isfinite(error) and 0<=error<=.05,
            seed_matches_plan=episode['seed_hidden']==planned[uid]['seed']==receipt['seed_hidden'],
            accepted_goal=episode['accepted'] is True,
            no_method_or_judge_output=receipt['method_outputs_generated'] is False and receipt['judge_labels_generated'] is False)
        rows.append(dict(episode_id=uid,checks=checks,passed=all(checks.values()),
            measured_reset_error_m=error,terminal_action_status=episode.get('terminal_action_status'),
            navigation_result_used_as_exclusion=False))
    unique_ids=len({r['container_id'] for r in run['episodes']})==6 and all(r['container_id'] for r in run['episodes'])
    same_image=len({r['image_id'] for r in run['episodes']})==1
    same_bank=len({r['execution_source_bank_sha256'] for r in run['episodes']})==1
    passed=all(r['passed'] for r in rows) and unique_ids and same_image and same_bank
    return dict(schema='hexar-offline-acquisition-qualification/v1',phase='development_only',
        status='OFFLINE_SCOPE_PASSED_NOT_FULL_ACQUISITION_QUALIFICATION' if passed else 'FAILED_RETAINED',
        episodes=rows,distinct_container_ids=bool(unique_ids),same_image=same_image,same_source_bank=same_bank,
        image_id=run['image_id'],episode_n=6,confirmatory_N=0,alpha_consumed=0,
        full_acquisition_qualified=False,semantic_calls=0,
        scope='Six new development episodes demonstrate offline simulator operation, accepted goals, measured reset and existing candidate recording/interface integrity. Does not qualify final sampling population, technical-failure rate, family exposure or final validity thresholds.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__=='__main__':
    value=report();exclusive_json(BASE/'offline_qualification_v13.json',value);print(value['status'])
