"""Blinded assessment of retained unique v13 DEVELOPMENT outputs under the public numerical policy.

One A/B(+disagreement C) assessment per unique output; aliases reuse its result.
Technical method failures remain unresolved and never generate a repair call.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
from .journal import canonical,exclusive_json,fingerprint,OneAttemptJournal
from .rich_evaluator_v4 import PROMPT,SCHEMA
from .rich_adjudication import needs_c,resolve,endpoint_components
from .rich_blind_projection import project
from .unique_result_expansion import expand_outputs,expand_labels
from .development_judge_call_v4 import call
from ..acquisition.navigation_usefulness_v2 import public_packet,reference as build

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
DEST=BASE/'development_unique_scoring_v2'


def prepare():
    method_run=BASE/'development_unique_methods_v2'
    declaration=json.loads((method_run/'declaration.json').read_text())
    plan_path=method_run/'unique_request_plan.json';plan=json.loads(plan_path.read_text())
    methods_path=method_run/'report.json';methods=json.loads(methods_path.read_text())
    source=ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v13.json'
    if methods['phase']!='development_only' or methods['confirmatory_N']!=0 or methods['unique_attempts']!=72:
        raise ValueError('closed retained development unique-method report required')
    if fingerprint(plan)!=declaration['request_plan_sha256'] or hashlib.sha256(source.read_bytes()).hexdigest()!=declaration['source_packet_manifest_sha256']:
        raise ValueError('retained unique plan or packet source changed')
    cells=expand_outputs(plan,methods['answers'])
    packet_lookup={(r['development_id'],f'{r["question_id"]}-{r["condition"]}'):public_packet(r['method_packet']) for r in json.loads(source.read_text())['packets']}
    output_lookup={r['unique_request_id']:r for r in methods['answers']};byid={}
    for cell in cells:
        packet=packet_lookup[(cell['episode_id'],cell['job_id'])]
        if fingerprint(packet)!=cell['packet_sha256']:raise ValueError('aliased packet differs from original request')
        uid=cell['source_unique_request_id']
        payload=project(packet,build(packet),cell['answer']) if cell['status']=='VALID' else None
        entry=dict(unique_request_id=uid,episode_id=cell['episode_id'],method=cell['method'],payload=payload,
                   method_status=cell['status'],method_outcome_sha256=fingerprint(output_lookup[uid]))
        if uid in byid and byid[uid]!=entry:raise ValueError('identical method request produced differing scoring payloads')
        byid[uid]=entry
    return list(byid.values()),plan,methods_path,plan_path,source


def job(entry,slot):
    return dict(opaque_job=hashlib.sha256(canonical([entry['unique_request_id'],slot,'unique-development-scoring-v2'])).hexdigest(),slot=slot,payload=entry['payload'])


def summarize(entries,plan,attempts):
    labels={};components={}
    for entry in entries:
        uid=entry['unique_request_id']
        if entry['method_status']!='VALID':
            result=dict(status='UNRESOLVED',reason='unique_method_technical_failure',label=None)
        else:
            a,b=(attempts[job(entry,slot)['opaque_job']] for slot in ('A','B'))
            c=attempts.get(job(entry,'C')['opaque_job']);result=resolve(a,b,entry['payload'],c)
            if result['status']=='NEEDS_C':raise ValueError('adjudication not closed')
        labels[uid]=result;components[uid]=endpoint_components(result,entry['payload'])
    cells=expand_labels(plan,labels);episodes=[];counts=[0,0,0,0]
    for episode in sorted({entry['episode_id'] for entry in entries}):
        states={}
        for method in ('HX-CONTRACT','HX-PROMPT'):
            rows=[r['disposition']['status'] for r in cells if r['episode_id']==episode and r['method']==method]
            if len(rows)!=9:raise ValueError('all nine battery aliases required per episode/method')
            states[method]='FAIL' if 'FAIL' in rows else 'UNRESOLVED' if 'UNRESOLVED' in rows else 'PASS'
        cf=states['HX-CONTRACT']!='PASS';pf=states['HX-PROMPT']=='FAIL'
        cell=0 if not cf and pf else 1 if cf and not pf else 2 if not cf and not pf else 3
        counts[cell]+=1;episodes.append(dict(episode_id=episode,method_states=states,conservative_mapped_contract_failure=cf,conservative_mapped_prompt_failure=pf))
    return labels,components,cells,episodes,counts


def execute():
    entries,plan,methods,plan_path,source=prepare()
    prerequisite=BASE/'development_motion_screen_v1/report.json'
    if json.loads(prerequisite.read_text())['status']!='AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION':raise ValueError('authored evaluator prerequisite missing')
    valid=[e for e in entries if e['method_status']=='VALID'];jobs=[job(e,s) for e in valid for s in ('A','B')]
    random.Random(2026100108).shuffle(jobs);DEST.mkdir(exist_ok=True);exe=Path(shutil.which('codex')).resolve()
    sources=[Path(__file__),Path(__file__).with_name('development_judge_call_v4.py'),Path(__file__).with_name('rich_adjudication.py'),Path(__file__).with_name('rich_evaluator_v4.py'),Path(__file__).with_name('rich_evaluator_v3.py'),Path(__file__).with_name('motion_usefulness.py'),Path(__file__).with_name('measurement_rounding.py'),Path(__file__).with_name('rich_evaluator_v2.py'),Path(__file__).with_name('rich_evaluator_candidate.py'),Path(__file__).with_name('rich_blind_projection.py'),Path(__file__).with_name('unique_result_expansion.py'),ROOT/'analysis/hexar_external/acquisition/navigation_usefulness_v2.py',ROOT/'analysis/hexar_external/acquisition/navigation_references.py',methods,plan_path,source,prerequisite]
    declaration=dict(schema='hexar-development-unique-scoring/v1',phase='development_only',confirmatory_N=0,alpha_consumed=0,
        n_episodes=6,unique_outputs=len(entries),battery_cells=108,valid_method_outputs=len(valid),initial_calls=len(jobs),maximum_C_calls=len(valid),
        model='gpt-6-astra',reasoning_effort='high',prompt=PROMPT,output_schema=SCHEMA,cli_path=str(exe),cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        workers=2,timeout_seconds=360,technical_retries=0,quality_retries=0,provider_runtime_qualified=False,
        missing_method_outputs='Retain unresolved without judge call or regeneration; all aliases share the same missingness.',
        C_rule='One independent C only for two valid A/B component-vector disagreement. No previous labels or method/admin metadata supplied.',
        endpoint='Any definite failure among nine aliased cells -> FAIL; otherwise unresolved if any unknown; otherwise PASS. Identical cells share one generation and assessment.',
        mapping='Least favorable for superiority: unresolved contract fails; unresolved prompt succeeds.',
        criterion='All dispatched judgments valid and every unique output/alias has explicit closed disposition. Workflow completion does not qualify semantic accuracy or the final endpoint.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        initial_job_registry=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in jobs])
    exclusive_json(DEST/'declaration.json',declaration);journal=OneAttemptJournal(DEST/'journal',fingerprint(declaration))
    # Preserve exact dispatch-critical source bytes before any provider call.
    for path in sources:
        archive=DEST/'source_bank'/path.relative_to(ROOT);archive.parent.mkdir(parents=True,exist_ok=True)
        with archive.open('xb') as stream:stream.write(path.read_bytes())
    def dispatch(batch):
        def checked_call(j):
            if hashlib.sha256(exe.read_bytes()).hexdigest()!=declaration['cli_sha256']:raise ValueError('development CLI changed before scoring dispatch')
            for path in sources:
                if hashlib.sha256(path.read_bytes()).hexdigest()!=declaration['source_hashes'][str(path.relative_to(ROOT))]:raise ValueError('development scoring source changed before dispatch')
            return call(j,DEST,declaration,journal)
        with ThreadPoolExecutor(max_workers=2) as executor:return list(executor.map(checked_call,batch))
    initial=dispatch(jobs);attempts={r['opaque_job']:r for r in initial}
    C=[job(e,'C') for e in valid if needs_c(attempts[job(e,'A')['opaque_job']],attempts[job(e,'B')['opaque_job']],e['payload'])]
    random.Random(2026100109).shuffle(C)
    exclusive_json(DEST/'adjudication_registry.json',dict(schema='hexar-development-C-registry/v1',declaration_sha256=fingerprint(declaration),initial_outcomes_sha256=fingerprint(initial),jobs=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in C],previous_labels_supplied_to_C=False))
    attempts.update({r['opaque_job']:r for r in dispatch(C)})
    labels,components,cells,episodes,counts=summarize(entries,plan,attempts)
    report=dict(schema='hexar-development-unique-scoring-report/v1',phase='development_only',status='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED' if all(r['status']=='VALID' for r in attempts.values()) else 'TECHNICAL_JUDGE_FAILURES_RETAINED',
        initial_calls=len(jobs),C_calls=len(C),valid_judge_returns=sum(r['status']=='VALID' for r in attempts.values()),total_dispatched=len(attempts),
        unique_labels=labels,unique_endpoint_components=components,aliased_cells=cells,episode_states=episodes,conservative_mapped_development_cells=counts,
        unresolved_unique_outputs=sum(v['status']=='UNRESOLVED' for v in labels.values()),method_technical_failures=sum(e['method_status']!='VALID' for e in entries),
        attempts=list(attempts.values()),agent_assessed=True,human_validated=False,whole_recording_endpoint_qualified=False,
        superiority_test_performed=False,p_value=None,confirmatory_N=0,alpha_consumed=0)
    exclusive_json(DEST/'report.json',report);print(report['status'],report['valid_judge_returns'],report['C_calls'],report['unresolved_unique_outputs'])


if __name__=='__main__':execute()
