"""Declared synthetic capacity screen; never dispatches a provider or robot."""
import copy
import resource
import time
from pathlib import Path

from .streaming_registry_shards_v1 import write_sorted,verify
from .journal import exclusive_json,fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .seal_cohort import committed
from ..acquisition.raw_archive_v1 import digest

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1/development_streaming_capacity_v1'


def execute():
    declaration=load_artifact(BASE/'declaration.json')
    if (declaration['phase']!='synthetic_development_capacity_only' or declaration['provider_calls']!=0
            or declaration['confirmatory_N']!=0 or not committed(ROOT,BASE/'declaration.json')):
        raise ValueError('committed synthetic no-dispatch capacity declaration required')
    for name,sha in declaration['source_hashes'].items():
        if digest(ROOT/name)!=sha or not committed(ROOT,ROOT/name):raise ValueError('declared capacity source changed')
    if (BASE/'report.json').exists():raise ValueError('terminal capacity result retained; no reissue')
    source=load_artifact(ROOT/declaration['template_registry_path'])
    templates=source['jobs']
    if len(templates)!=144 or any(r['request']['role']!='judge' for r in templates):
        raise ValueError('complete inspected 144-judge development request templates required')
    def jobs():
        for i in range(declaration['synthetic_job_count']):
            yield dict(job_id=f'synthetic-capacity-{i:08d}',request=copy.deepcopy(templates[i%len(templates)]['request']))
    started=time.monotonic()
    index=write_sorted(BASE/'payloads',fingerprint(declaration),'development_qualification','initial_judges',jobs(),
        declaration['maximum_shard_bytes'],declaration['maximum_shard_jobs'])
    built=time.monotonic()-started
    check_start=time.monotonic();verify(BASE/'payloads',fingerprint(index));verified=time.monotonic()-check_start
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    criterion=peak<=declaration['maximum_peak_rss_bytes'] and built+verified<=declaration['maximum_wall_seconds']
    report=dict(schema='hexar-streaming-synthetic-capacity-report/v1',phase='synthetic_development_capacity_only',
        status='SYNTHETIC_STREAMING_CAPACITY_PASSED_NOT_FINAL_ADAPTER_QUALIFICATION' if criterion else 'FAILED_CAPACITY_SCREEN_RETAINED',
        declaration_sha256=digest(BASE/'declaration.json'),index_sha256=digest(BASE/'payloads/index.json'),
        canonical_index_sha256=fingerprint(index),synthetic_jobs=index['total_jobs'],shards=len(index['shards']),
        total_payload_bytes=sum(r['bytes'] for r in index['shards']),largest_shard_bytes=max(r['bytes'] for r in index['shards']),
        peak_rss_bytes=peak,build_and_first_verification_seconds=built,second_verification_seconds=verified,
        complete_registry_sha256=index['complete_registry_sha256'],provider_calls=0,robot_calls=0,
        episodes_generated=0,method_outputs_generated=0,judge_outputs_generated=0,confirmatory_N=0,alpha_consumed=0,
        confirmation_authorized=False,significance_test_performed=False,
        scope='Repeated inspected request templates with synthetic sorted identities; payload/index/memory capacity only.')
    for name,sha in declaration['source_hashes'].items():
        if digest(ROOT/name)!=sha:raise ValueError('declared capacity source changed during screen')
    exclusive_json(BASE/'report.json',report);print(report,flush=True);return report


if __name__=='__main__':execute()
