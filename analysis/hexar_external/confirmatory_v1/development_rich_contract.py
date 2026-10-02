"""Archive rich-interface deterministic development outputs and references.

This is an engineering run on permanently exposed episodes, not a prospective
semantic screen or a superiority test. Baseline/judge qualification is pending.
"""
import hashlib
import json
from pathlib import Path

from .journal import OneAttemptJournal, exclusive_json, fingerprint
from ..acquisition.navigation_references import build
from ..acquisition.navigation_contract import contract

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_contract_v1'
INPUT = ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v1.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    packets = json.loads(INPUT.read_text())
    if packets['phase'] != 'development_only' or packets['confirmatory_n'] != 0 or len(packets['packets']) != 54:
        raise ValueError('complete development-only packet set required')
    BASE.mkdir(parents=True,exist_ok=True)
    files = ['analysis/hexar_external/acquisition/navigation_contract.py',
             'analysis/hexar_external/acquisition/navigation_references.py',
             'analysis/hexar_external/study_v2.py',
             'analysis/maximal_supported_diagnosis.py',
             'analysis/realize_evidence_calibrated_explanation.py',
             'analysis/evidence_calibration.py', 'analysis/evidence_calibration_io.py',
             'docs/hexar_external/prompt_calibration_v1.txt',
             str(Path(__file__).relative_to(ROOT))]
    declaration = dict(schema='hexar-rich-contract-development-declaration/v1',phase='development_only',
        input_path=str(INPUT.relative_to(ROOT)),input_sha256=sha(INPUT),source_hashes={p:sha(ROOT/p) for p in files},
        independent_units_for_confirmation=0,alpha_consumed=0,contract_jobs=54,baseline_calls=0,judge_calls=0,
        exploratory_deterministic_assemblies_previously_inspected=True,
        purpose='archive development engineering assemblies; not a predeclared semantic qualification or superiority comparison',
        historical_pipeline_and_strengthened_baseline_changed=False)
    exclusive_json(BASE/'declaration.json',declaration)
    journal=OneAttemptJournal(BASE/'journal',fingerprint(declaration));results=[]
    for record in packets['packets']:
        job={k:record[k] for k in ('development_id','question_id','condition')}
        handle=fingerprint(job);destination=BASE/handle;destination.mkdir()
        request=dict(method_packet_sha256=fingerprint(record['method_packet']),source_hashes=declaration['source_hashes'])
        journal.claim(job,request)
        outcome=dict(status='TECHNICAL_FAILURE',development_job=job,semantic_qualification=False)
        try:
            # References are packet-only and archived before method assembly;
            # they do not become contract inputs or semantic scores.
            reference=build(record['method_packet']);exclusive_json(destination/'reference.json',reference)
            value=contract(record['method_packet'],handle,record['development_id'])
            exclusive_json(destination/'contract.json',value)
            outcome.update(status='VALID',answer=value['answer'],word_count=len(value['answer'].split()),
                final_clauses=len(value['realization']['final_clauses']),
                reference_sha256=sha(destination/'reference.json'),contract_sha256=sha(destination/'contract.json'))
        except Exception as exc:
            outcome['error']=type(exc).__name__+': '+str(exc)
        journal.finish(job,request,outcome);exclusive_json(destination/'outcome.json',outcome);results.append(outcome)
    report=dict(schema='hexar-rich-contract-development-report/v1',phase='development_only',results=results,
                valid=sum(r['status']=='VALID' for r in results),expected=54,confirmatory_n=0,alpha_consumed=0,
                baseline_or_judge_comparison='NOT_RUN',semantic_support_and_coverage_qualification=False,
                limits='Deterministic code acceptance is not independent semantic validation; template dependence and limited flexibility retained.')
    exclusive_json(BASE/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))


if __name__=='__main__':
    main()
