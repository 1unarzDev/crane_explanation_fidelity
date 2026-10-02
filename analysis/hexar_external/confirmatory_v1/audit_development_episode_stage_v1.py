"""Read-only closed-stage transport and prerequisite reproduction; no dispatch."""
import hashlib
from pathlib import Path

from .journal import fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .streaming_registry_shards_v1 import verify, read_shard
from .development_registered_backend import transcript_policy
from .request_binding import parse_answer
from .rich_evaluator_v4 import validate
from .strict_json import load
from ..acquisition.raw_archive_v1 import digest


def audit_stage(folder, binding, stage):
    folder=Path(folder)
    # Never open or close live/partial journals as a recovery action.
    completed=load_artifact(folder/'completion_receipt.json')
    declaration=load_artifact(folder/'stage_declaration.json')
    receipt=load_artifact(folder/'pre_dispatch_receipt.json')
    outcomes=load_artifact(folder/'closed_outcomes.json')
    if (declaration.get('phase')!='development_qualification' or declaration.get('binding_sha256')!=binding
            or declaration.get('stage')!=stage or completed.get('phase')!='development_qualification'
            or completed.get('stage')!=stage or completed.get('confirmation_authorized') is not False
            or completed.get('confirmatory_N')!=0 or declaration.get('confirmation_authorized') is not False):
        raise ValueError('explicit closed development stage binding required')
    if (completed['stage_declaration_sha256']!=digest(folder/'stage_declaration.json')
            or receipt['stage_declaration_sha256']!=completed['stage_declaration_sha256']
            or completed['pre_dispatch_receipt_sha256']!=digest(folder/'pre_dispatch_receipt.json')
            or completed['closed_outcomes_sha256']!=digest(folder/'closed_outcomes.json')
            or receipt['prerequisite_sha256']!=fingerprint(declaration['prerequisites'])
            or receipt['provider_calls_started'] is not False):
        raise ValueError('stage chronology/hash receipts changed')
    for path,sha in declaration['prerequisites'].items():
        if digest(Path(path))!=sha:raise ValueError('retained stage prerequisite changed')
    expected=declaration['exact_job_ids']
    if (expected!=sorted(set(expected)) or set(outcomes)!=set(expected)
            or completed['complete_job_ids']!=expected or completed['attempts']!=len(expected)
            or completed['valid']!=sum(r['status']=='VALID' for r in outcomes.values())):
        raise ValueError('closed complete stage identities/accounting differ')
    if not expected:
        if receipt['index_sha256'] is not None or (folder/'payloads').exists() or (folder/'attempts').exists():
            raise ValueError('empty stage contains unplanned dispatch artifacts')
        return dict(stage=stage,attempts=0,valid=0,source_receipt_sha256=digest(folder/'completion_receipt.json'))
    index=verify(folder/'payloads',receipt['index_sha256'])
    if (index['stage']!=stage or index['binding_sha256']!=binding or index['phase']!='development_qualification'
            or load_artifact(folder/'attempts/phase_index.json')!=index
            or sorted(j for shard in index['shards'] for j in shard['job_ids'])!=expected):
        raise ValueError('sealed stage payload/root membership changed')
    plain_jobs=[];attempts=0
    for item in index['shards']:
        reg=read_shard(folder/'payloads',item,index['maximum_shard_bytes'])
        root=folder/'attempts'/item['path'].removesuffix('.json')
        if load_artifact(root/'registered_jobs.json')!=reg:raise ValueError('execution shard changed')
        handles=set()
        for row in reg['jobs']:
            plain_jobs.append(dict(job_id=row['job_id'],request=row['request']))
            identity=dict(opaque_job=row['job_id']);handle=fingerprint(dict(freeze_sha256=binding,job=identity));handles.add(handle)
            claim=load_artifact(root/'journal'/(handle+'.claim.json'))
            closed=load_artifact(root/'journal'/(handle+'.outcome.json'))
            expected_claim=dict(schema='hexar-one-attempt/v1',freeze_sha256=binding,job=identity,
                request_sha256=fingerprint(dict(registry_sha256=fingerprint(reg),request_sha256=row['request_sha256'])),attempt_count=1)
            if claim!=expected_claim or closed['attempt']!=expected_claim or closed['outcome']!=outcomes[row['job_id']]:
                raise ValueError('single-attempt raw/outcome identity changed')
            outcome=closed['outcome'];raw={}
            if set(outcome['raw_sha256'])!={'raw_response.json','stdout.bin','stderr.bin'}:
                raise ValueError('complete original transport bytes required')
            for name,sha in outcome['raw_sha256'].items():
                raw[name]=(root/fingerprint(identity)/name).read_bytes()
                if hashlib.sha256(raw[name]).hexdigest()!=sha:raise ValueError('retained raw bytes changed')
            if outcome['status']=='VALID':
                parsed=load(raw['raw_response.json'],row['request']['maximum_response_bytes'])
                if row['request']['role']=='judge':parsed=validate(parsed,row['request']['payload'])
                else:parse_answer(parsed)
                if parsed!=outcome['parsed']:raise ValueError('raw/parsed outcome changed')
                if row['request']['role']!='contract' and not transcript_policy(raw['stdout.bin'],0):
                    raise ValueError('valid CLI transcript violates retained tool/turn policy')
                if row['request']['role']=='contract' and load(raw['stdout.bin'])['answer']!=parsed['answer']:
                    raise ValueError('retained deterministic contract answer changed')
            elif outcome['status'] not in ('TECHNICAL_FAILURE','INDETERMINATE_AFTER_CRASH'):
                raise ValueError('unclosed raw outcome')
            attempts+=1
        for suffix in ('claim','outcome'):
            if {p.name.removesuffix('.'+suffix+'.json') for p in (root/'journal').glob('*.'+suffix+'.json')}!=handles:
                raise ValueError('extra or pending stage journal')
    if fingerprint(sorted(plain_jobs,key=lambda j:j['job_id']))!=declaration['exact_jobs_sha256'] or attempts!=len(expected):
        raise ValueError('pre-dispatch request fingerprint/accounting changed')
    return dict(stage=stage,attempts=attempts,valid=completed['valid'],source_receipt_sha256=digest(folder/'completion_receipt.json'),
        canonical_index_sha256=receipt['index_sha256'],raw_attempts_verified=attempts,provider_calls=0)
