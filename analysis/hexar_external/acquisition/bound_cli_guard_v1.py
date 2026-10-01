"""Check allocations against the exact qualified shell prefix before ROS."""
import hashlib
import re
import subprocess
from pathlib import Path

PREFIX_SHA256='b3ad522fbea2b31368f9af4fbeec1688e0fd386e617c2692679582ab54db6568'


def prefix(path):
    value=Path(path).read_text().split('output_dir=',1)[0]
    if hashlib.sha256(value.encode()).hexdigest()!=PREFIX_SHA256:
        raise ValueError('qualified lexical shell guard changed; requalify before dispatch')
    return value


def compatible(record,phase,binding):
    patterns=dict(development_adapter_qualification=r'hexar-tiago-dev-[a-z_]+-[0-9]+',
                  raw_confirmation=r'hexar-tiago-confirm-[0-9a-f]{16}-[a-z_]+-[0-9]+')
    return (phase in patterns and type(binding) is str and re.fullmatch('[0-9a-f]{64}',binding) is not None
        and type(record.get('episode_id')) is str and re.fullmatch(patterns[phase],record['episode_id']) is not None
        and record.get('family') in ('success','obstacle','dynamic_env','localization','charging','manual_joystick')
        and type(record.get('seed')) is int and record['seed']>=0)


def verify_allocations(path,records,phase,binding):
    prefix(path)
    if not records or any(not compatible(r,phase,binding) for r in records):
        raise ValueError('allocated identity/family/seed/binding violates qualified shell guard')
    return True


def probe(path,records,phase,binding):
    verify_allocations(path,records,phase,binding);script=prefix(path);rows=[]
    for record in records:
        result=subprocess.run(['bash','-c',script,'lexical-guard',record['family'],str(record['seed']),
            record['episode_id'],phase,binding],capture_output=True,timeout=5)
        if result.returncode!=0 or result.stdout or result.stderr:
            raise ValueError('exact lexical shell prefix rejected allocated episode: '+record['episode_id'])
        rows.append(dict(episode_id=record['episode_id'],returncode=result.returncode))
    return dict(schema='hexar-qualified-shell-lexical-preflight/v1',passed=True,
        prefix_sha256=PREFIX_SHA256,rows=rows,robot_or_native_launches=0,method_or_judge_calls=0,
        scope='Exact hash-bound prefix ends before output_dir/mkdir, ROS or recording; allocation validation only.')
