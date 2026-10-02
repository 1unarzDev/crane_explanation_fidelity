"""All retained v11 development answers, blinded A/B + planned disagreement C.

Episode-level descriptive endpoint engineering; no p-value or confirmation.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
from .journal import canonical,exclusive_json,fingerprint,OneAttemptJournal
from .rich_evaluator_v3 import PROMPT,SCHEMA
from .rich_adjudication import needs_c,resolve
from .rich_blind_projection import project
from .development_judge_call import call
from ..acquisition.navigation_references import build

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
DEST=BASE/'development_full_battery_scoring_v1'


def prepare():
    methods=BASE/'development_rich_methods_v1/report.json'
    packets=ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v2.json'
    lookup={f'{r["development_id"]}-{r["question_id"]}-{r["condition"]}':r for r in json.loads(packets.read_text())['packets']}
    answers=json.loads(methods.read_text())['answers'];entries=[]
    for answer in answers:
        packet=lookup[answer['job_id']]['method_packet']
        if answer['status']!='VALID' or hashlib.sha256(answer['answer'].encode()).hexdigest()!=answer['answer_sha256'] or fingerprint(packet)!=answer['packet_sha256']:
            raise ValueError('retained answer/evidence hash required')
        row=lookup[answer['job_id']]
        entries.append(dict(identity=dict(job_id=answer['job_id'],method=answer['method'],episode=row['development_id']),
                            payload=project(packet,build(packet),answer['answer'])))
    identities={(e['identity']['job_id'],e['identity']['method']) for e in entries}
    if len(entries)!=108 or len(identities)!=108:raise ValueError('complete fixed six-episode 108-answer battery required')
    for episode in {e['identity']['episode'] for e in entries}:
        for method in ('HX-PROMPT','HX-CONTRACT'):
            if sum(e['identity']['episode']==episode and e['identity']['method']==method for e in entries)!=9:
                raise ValueError('exactly nine jobs per method/episode required')
    return entries,methods,packets


def job(entry,slot):
    return dict(opaque_job=hashlib.sha256(canonical([entry['identity'],slot,'full-battery-development-v1'])).hexdigest(),
                slot=slot,payload=entry['payload'])


def summarize(entries,attempts):
    answer_rows=[]
    for entry in entries:
        a,b=(attempts[job(entry,slot)['opaque_job']] for slot in ('A','B'))
        c=attempts.get(job(entry,'C')['opaque_job'])
        result=resolve(a,b,entry['payload'],c)
        if result['status']=='NEEDS_C':raise ValueError('adjudication phase did not close')
        answer_rows.append(dict(**entry['identity'],**result,attempt_ids={slot:job(entry,slot)['opaque_job'] for slot in ('A','B','C') if job(entry,slot)['opaque_job'] in attempts}))
    episodes=[];cells=dict(contract_succeeds_prompt_fails=0,prompt_succeeds_contract_fails=0,both_succeed=0,both_fail=0)
    for episode in sorted({e['identity']['episode'] for e in entries}):
        states={}
        for method in ('HX-CONTRACT','HX-PROMPT'):
            labels=[r['status'] for r in answer_rows if r['episode']==episode and r['method']==method]
            states[method]='FAIL' if 'FAIL' in labels else 'UNRESOLVED' if 'UNRESOLVED' in labels else 'PASS'
        # Predeclared least-favorable mapping, not an asserted complete-label truth.
        cf=states['HX-CONTRACT']!='PASS';pf=states['HX-PROMPT']=='FAIL'
        key='both_fail' if cf and pf else 'both_succeed' if not cf and not pf else 'prompt_succeeds_contract_fails' if cf else 'contract_succeeds_prompt_fails'
        cells[key]+=1;episodes.append(dict(episode=episode,method_states=states,conservative_mapped_contract_failure=cf,conservative_mapped_prompt_failure=pf))
    return answer_rows,episodes,cells


def execute():
    entries,methods,packets=prepare()
    prerequisite=BASE/'development_rich_evaluator_screen_v3/report.json'
    if json.loads(prerequisite.read_text())['status']!='AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION':raise ValueError('span/ambiguity authored screen missing')
    DEST.mkdir(exist_ok=True);exe=Path(shutil.which('codex')).resolve()
    jobs=[job(e,slot) for e in entries for slot in ('A','B')];random.Random(2026100401).shuffle(jobs)
    sources=[Path(__file__),Path(__file__).with_name('development_judge_call.py'),Path(__file__).with_name('rich_adjudication.py'),
             Path(__file__).with_name('rich_evaluator_v3.py'),Path(__file__).with_name('rich_evaluator_v2.py'),Path(__file__).with_name('rich_evaluator_candidate.py'),
             Path(__file__).with_name('rich_blind_projection.py'),Path(__file__).with_name('blind_bank.py'),ROOT/'analysis/hexar_external/acquisition/navigation_references.py',methods,packets,prerequisite]
    declaration=dict(schema='hexar-development-full-battery-scoring/v1',phase='development_only',confirmatory_N=0,alpha_consumed=0,
        n_episodes=6,n_answers=108,n_initial_calls=216,maximum_C_calls=108,model='gpt-6-astra',reasoning_effort='high',
        prompt=PROMPT,output_schema=SCHEMA,cli_path=str(exe),cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),
        cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),workers=2,timeout_seconds=360,technical_retries=0,quality_retries=0,
        provider_runtime_qualified=False,agent_assessed=True,human_validated=False,
        criterion='All dispatched calls structurally valid; C only for two valid initial labels with different complete component vectors. Unresolved semantic ambiguity retained. Workflow completion is not semantic accuracy qualification.',
        endpoint='Any of nine fixed jobs definitively fails -> episode FAIL; otherwise any unresolved -> UNRESOLVED; otherwise PASS.',
        unresolved_mapping='Least favorable: unresolved CRANE fails and unresolved HX-PROMPT succeeds. Display unmapped states and conservative mapped cells separately.',
        accuracy_qualification_claim=False,superiority_test_authorized=False,old_calls_not_reissued=True,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        initial_job_registry=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in jobs])
    exclusive_json(DEST/'declaration.json',declaration);journal=OneAttemptJournal(DEST/'journal',fingerprint(declaration))
    def dispatch(batch):
        with ThreadPoolExecutor(max_workers=2) as executor:return list(executor.map(lambda j:call(j,DEST,declaration,journal),batch))
    initial=dispatch(jobs);attempts={r['opaque_job']:r for r in initial}
    C=[job(e,'C') for e in entries if needs_c(attempts[job(e,'A')['opaque_job']],attempts[job(e,'B')['opaque_job']],e['payload'])]
    random.Random(2026100402).shuffle(C)
    exclusive_json(DEST/'adjudication_registry.json',dict(schema='hexar-development-C-registry/v1',selection_rule='two valid initial component-vector disagreement only',
        declaration_sha256=fingerprint(declaration),initial_outcomes_sha256=fingerprint(initial),jobs=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in C],previous_labels_supplied_to_C=False))
    additional=dispatch(C);attempts.update({r['opaque_job']:r for r in additional})
    labels,episodes,cells=summarize(entries,attempts)
    all_valid=all(r['status']=='VALID' for r in attempts.values())
    report=dict(schema='hexar-development-full-battery-report/v1',status='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED' if all_valid else 'TECHNICAL_FAILURES_RETAINED',
        initial_calls=216,C_calls=len(C),valid_returns=sum(r['status']=='VALID' for r in attempts.values()),total_dispatched=len(attempts),
        answer_labels=labels,episode_states=episodes,conservative_mapped_development_cells=cells,attempts=list(attempts.values()),
        unresolved_answers=sum(r['status']=='UNRESOLVED' for r in labels),agent_assessed=True,human_validated=False,
        whole_recording_endpoint_qualified=False,superiority_test_performed=False,p_value=None,confirmatory_N=0,alpha_consumed=0)
    exclusive_json(DEST/'report.json',report);print(report['status'],report['valid_returns'],report['C_calls'],report['unresolved_answers'])


if __name__=='__main__':execute()
