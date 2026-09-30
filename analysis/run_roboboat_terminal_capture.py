#!/usr/bin/env python3
"""Ordered one-worker, immutable-attempt boat capture. No DVC/shared Git mutation."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'

def atomic(path, value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-root',required=True,type=Path);p.add_argument('--limit',type=int,default=6)
    p.add_argument('--registry',type=Path,default=DOC/'pilot_registry_v1.json');a=p.parse_args()
    registry=json.loads(a.registry.read_text())
    a.output_root.mkdir(parents=True,exist_ok=True)
    for row in registry['rows'][:a.limit]:
        out=a.output_root/row['id']; record=out/'capture-attempt.json'
        if record.exists():
            saved=json.loads(record.read_text())
            if saved['status']=='complete':continue
            raise RuntimeError('Retained incomplete/failed attempt cannot be retried')
        out.mkdir(exist_ok=False)
        env={**os.environ,'CRANE_RUN_ID':row['id'],'CRANE_ROS_PORT':'10481','CRANE_ROS_DOMAIN_ID':'181',
             'CRANE_RESULT_ROOT':str(out),'CRANE_PLAYER':'/home/lunarz/worktrees/roboboat-docking/packages/crane_ml/Builds/CRANE-RoboBoat-Bow/CRANE.x86_64',
             'CRANE_ASTRO_DOCK':'/home/lunarz/crane_explain/packages/astro_dock',
             'CRANE_NOGRAPHICS':'0','CRANE_DURATION':'290','CRANE_WARMUP':'3',
             'CRANE_NAV2_ACTION_DURATION':'270','CRANE_NAV2_POST_RESULT_DURATION':'8',
             'CRANE_NAV2_PARAMS':str(ROOT/'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'),
             'CRANE_NAV2_ACTION_MODE':row['action_mode'],'CRANE_NAV2_PROFILE':'train-gpu',
             'CRANE_NAV2_CONTROLLER_EXTRA_ARGS':f"-p goal_checker.xy_goal_tolerance:={row['internal_xy_tolerance_m']}",
             'CRANE_NAV2_GOAL_X':'0.8641434','CRANE_NAV2_GOAL_Y':'-27.586906','CRANE_NAV2_GOAL_YAW':'1.5707963267948966',
             'CRANE_DOCKING_EVALUATOR':'1','CRANE_SEED_BASE':str(row['seed'])}
        if registry.get('capture_runtime_parameters'):
            env['CRANE_CAPTURE_RUNTIME_PARAMETERS']='1'
        if row['action_mode']=='follow-path':
            name='roboboat_terminal_shifted_path_v1.json' if row['shape']=='shifted-known' else 'roboboat_far_dock_known_path.json'
            env['CRANE_NAV2_PATH_FILE']=str(ROOT/'packages/crane_ml/Tools/Performance'/name)
        cmd=[str(ROOT/'scripts/run_roboboat_hidden_render.sh'),str(ROOT/'packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh')]
        before={'status':'running','row':row,'command':cmd,'launch_values':{k:v for k,v in env.items() if k.startswith('CRANE_')},'started_unix':time.time(),
                'registry_sha256':hashlib.sha256(a.registry.read_bytes()).hexdigest(),
                'player_sha256':hashlib.sha256(Path(env['CRANE_PLAYER']).read_bytes()).hexdigest(),
                'config_sha256':hashlib.sha256(Path(env['CRANE_NAV2_PARAMS']).read_bytes()).hexdigest()}
        atomic(record,before)
        with (out/'launcher.log').open('w') as log:
            result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
        before.update(return_code=result.returncode,finished_unix=time.time(),status='complete' if result.returncode==0 else 'technical-failure')
        atomic(record,before); print(row['id'],before['status'],flush=True)
        if result.returncode:raise SystemExit(result.returncode)
if __name__=='__main__':main()
