"""Retained development replay of bounded episode scoring; no new semantic calls."""
import copy
from pathlib import Path

from .episode_scoring_archives_v1 import scoring_artifacts,write_episode,read_episode,close_episode,cohort_index,bounded
from .blinded_scoring_workflow import select_C
from .journal import exclusive_json,fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .development_registered_pipeline_audit import audit
from ..acquisition.raw_archive_v1 import digest

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'manifests/hexar_external/confirmatory_v1/development_registered_pipeline_v3'
DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_episode_scoring_replay_v1'


def run():
    archive_audit=audit(SOURCE)
    source_declaration=load_artifact(SOURCE/'declaration.json')
    source_report=load_artifact(SOURCE/'report.json')
    if source_report['phase']!='development_only' or source_report['confirmatory_N']!=0:
        raise ValueError('already exposed development results only')
    plan=load_artifact(SOURCE/'unique_method_plan.json');neutral=load_artifact(SOURCE/'neutral_reference_registry.json')
    outputs=load_artifact(SOURCE/'method_outputs.json');old_private=load_artifact(SOURCE/'sealed_method_linkage.json')
    old_result=load_artifact(SOURCE/'closed_dispositions.json')
    mapping={r['unique_request_id']:r for r in old_private['entries']}
    outcomes={}
    for stage in ('initial_judges','adjudication_judges'):
        registry=load_artifact(SOURCE/(stage+'_registry.json'))
        for row in registry['jobs']:
            handle=fingerprint(dict(freeze_sha256=fingerprint(source_declaration),job=dict(opaque_job=row['job_id'])))
            outcomes[row['job_id']]=load_artifact(SOURCE/stage/'journal'/(handle+'.outcome.json'))['outcome']
    sources={str((SOURCE/name).relative_to(ROOT)):digest(SOURCE/name) for name in
        ('report.json','unique_method_plan.json','neutral_reference_registry.json','method_outputs.json',
         'sealed_method_linkage.json','closed_dispositions.json','archive_verification.json')}
    binding=fingerprint(dict(phase='retained_development_replay',source_hashes=sources))
    # Fixed public replay bytes are not a future study blinding key. No new
    # response/judgment is solicited; original payloads/labels remain development.
    replay_key=bytes.fromhex('3f'*32)
    DEST.mkdir(exist_ok=False);records=[];paired=[0,0,0,0];rows=[];max_size=0
    for episode in sorted({r['episode_id'] for r in plan['requests']}):
        subplan=copy.deepcopy(plan)
        subplan['requests']=[r for r in plan['requests'] if r['episode_id']==episode]
        subplan['aliases']=[r for r in plan['aliases'] if r['episode_id']==episode]
        subplan.update(unique_requests=12,battery_cells=18)
        subneutral=dict(neutral,entries=[r for r in neutral['entries'] if r['episode_id']==episode])
        suboutputs=[r for r in outputs if r['episode_id']==episode]
        artifacts=scoring_artifacts(subneutral,subplan,suboutputs,replay_key,2026100101)
        folder=DEST/fingerprint(['episode',episode]);index=write_episode(folder,artifacts,binding,'development_qualification')
        _,retained=read_episode(folder,fingerprint(index),binding,'development_qualification')
        private=retained['sealed_method_linkage.json'];public=retained['public_scoring_plan.json']
        initial={};reserved={}
        for row in private['entries']:
            old=mapping[row['unique_request_id']]
            if row['method_status']!=old['method_status']:raise ValueError('retained method disposition changed')
            for slot,new_id in row['opaque_slots'].items():
                original_id=old['opaque_slots'][slot]
                if original_id in outcomes:(reserved if slot=='C' else initial)[new_id]=outcomes[original_id]
        selected=select_C(public,initial);C={r['opaque_job']:reserved[r['opaque_job']] for r in selected}
        closed=close_episode(retained,initial,C)
        for uid,label in closed['labels'].items():
            if label!=old_result['labels'][uid]:raise ValueError('episode partition altered retained semantic disposition')
        old_endpoint=next(r for r in old_result['recording_endpoints'] if r['recording_id']==episode)
        if closed['recording_endpoints']!=[old_endpoint]:raise ValueError('whole-episode endpoint changed')
        old_jobs=[r for r in old_result['jobs'] if r['recording_id']==episode]
        if closed['jobs']!=old_jobs:raise ValueError('battery aliases, unknowns or scoring provenance changed')
        paired=[a+b for a,b in zip(paired,closed['paired_counts'])]
        exclusive_json(folder/'closed_dispositions.json',closed)
        max_size=max(max_size,max(p['bytes'] for p in index['files'].values()),len(bounded(closed)))
        records.append(dict(episode_id=episode,relative_path=folder.name,episode_index_sha256=fingerprint(index)))
        rows.append(dict(episode_id=episode,unique_outputs=12,battery_cells=18,C=len(C)))
    index=cohort_index(records,binding,'development_qualification');exclusive_json(DEST/'cohort_index.json',index)
    if paired!=old_result['paired_counts']:raise ValueError('partition changed paired counts')
    synthetic=cohort_index([dict(episode_id=f'synthetic-{i}',relative_path=f'episode-{i}',
        episode_index_sha256=fingerprint(['synthetic',i])) for i in range(3072)],'a'*64,'development_qualification')
    if audit(SOURCE)!=archive_audit:raise ValueError('original retained archive changed during replay')
    report=dict(original_archive_audit=archive_audit,schema='hexar-episode-scoring-development-replay/v1',phase='development_only',
        status='RETAINED_EPISODE_SCORING_REPRODUCED_NOT_FINAL_ADAPTER_QUALIFICATION',source_hashes=sources,
        rows=rows,paired_counts_reproduced=paired,largest_complete_episode_artifact_bytes=max_size,
        cohort_index_bytes=len(bounded(index)),synthetic_3072_pointer_index_bytes=len(bounded(synthetic)),
        synthetic_rows_are_capacity_test_only=True,provider_calls=0,method_outputs_generated=0,judgments_generated=0,
        confirmatory_N=0,alpha_consumed=0,confirmation_authorized=False,significance_test_performed=False,
        agent_assessed=True,human_validated=False,
        implementation_hashes={str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__),Path(__file__).with_name('episode_scoring_archives_v1.py'))})
    exclusive_json(DEST/'report.json',report);return report


if __name__=='__main__':
    value=run();print({k:v for k,v in value.items() if k not in ('source_hashes','rows','implementation_hashes')})
