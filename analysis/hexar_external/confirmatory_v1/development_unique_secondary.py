"""Secondary development summaries with unique-request and missingness bounds."""
import hashlib
import json
from pathlib import Path
from statistics import median

from .journal import exclusive_json
from .unique_result_expansion import expand_outputs
from ..acquisition.navigation_references import build as reference

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'


def summarize_method(outputs, labels, required):
    n=len(outputs)
    if n<1:raise ValueError('all planned unique outputs required')
    passed=unresolved=material=material_possible=specific=specific_possible=0
    complete=complete_possible=covered=covered_possible=total=unknown=0
    for output in outputs:
        uid=output['unique_request_id'];state=labels[uid];label=state['label'];units=set(required[uid])
        total+=len(units);passed+=state['status']=='PASS';unresolved+=state['status']=='UNRESOLVED'
        if label is None:
            unknown+=1;material_possible+=1;specific_possible+=1
            complete_possible+=1;covered_possible+=len(units)
            continue
        seen=set(label['covered_units'])&units
        covered+=len(seen);covered_possible+=len(seen)
        complete+=units<=seen;complete_possible+=units<=seen
        ambiguous=bool(label['ambiguous_spans'])
        material+=label['unsupported_material'];specific+=label['overlicensed_specificity']
        # Union, so definite unsupported plus ambiguous material never counts twice.
        material_possible+=bool(label['unsupported_material'] or ambiguous)
        specific_possible+=bool(label['overlicensed_specificity'] or ambiguous)
    valid=[r for r in outputs if r['status']=='VALID'];words=[r['word_count'] for r in valid]
    return dict(planned_unique_outputs=n,valid_outputs=len(valid),unknown_labels=unknown,
        useful_supported_answer_rate_bounds=[passed/n,(passed+unresolved)/n],
        unsupported_material_rate_bounds=[material/n,material_possible/n],
        overlicensed_specificity_rate_bounds=[specific/n,specific_possible/n],
        complete_required_unit_coverage_bounds=[complete/n,complete_possible/n],
        required_unit_recall_bounds=[covered/total,covered_possible/total] if total else None,
        word_count_valid_returns_only=dict(minimum=min(words),maximum=max(words),median=median(words),mean=sum(words)/len(words)) if words else None,
        word_allowance_excesses=sum(not r['output_word_allowance_met'] for r in valid),
        model_calls=sum(r['model_calls'] for r in outputs),
        generation_wall_seconds_sum=sum(r['latency_seconds'] for r in outputs),
        cost_usd=None)


def report():
    method_path=BASE/'development_unique_methods_v1/report.json'
    plan_path=BASE/'development_unique_methods_v1/unique_request_plan.json'
    score_path=BASE/'development_unique_scoring_v1/report.json'
    source_path=ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v12_v2.json'
    methods=json.loads(method_path.read_text());plan=json.loads(plan_path.read_text());score=json.loads(score_path.read_text())
    expand_outputs(plan,methods['answers'])
    if score['status']!='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED':raise ValueError('terminal scoring workflow required')
    packets={(r['development_id'],r['closure']['packet_sha256']):r['method_packet'] for r in json.loads(source_path.read_text())['packets']}
    required={r['unique_request_id']:[u['unit_id'] for u in reference(packets[(r['episode_id'],r['packet_sha256'])])['required_units']] for r in plan['requests']}
    summaries=[]
    for method in ('HX-CONTRACT','HX-PROMPT'):
        outputs=[r for r in methods['answers'] if r['method']==method]
        if len(outputs)!=36 or len({r['episode_id'] for r in outputs})!=6:raise ValueError('six exposed episodes and 36 unique requests required')
        summaries.append(dict(method=method,**summarize_method(outputs,score['unique_labels'],required),
            deterministic_constrained_realization=method=='HX-CONTRACT',
            answer_flexibility='not quantified; deterministic rendering constrains wording and optional detail' if method=='HX-CONTRACT' else 'not quantified; stochastic prompted realization'))
    sources=(Path(__file__),method_path,plan_path,score_path,source_path)
    return dict(schema='hexar-development-unique-secondary/v1',phase='development_only',
        independent_episodes=6,confirmatory_N=0,alpha_consumed=0,agent_assessed=True,human_validated=False,
        annotation_accuracy_qualified=False,inference_performed=False,methods=summaries,
        denominator='36 predeclared unique requests per method, including the timeout; aliases do not add observations or repeat cost.',
        bounds='Descriptive agent-label/missing-output bounds, not confidence intervals or guarantees of latent annotation accuracy.',
        physical_cause_flags='No dedicated physical-cause label; do not equate all specificity flags with physical causes.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__=='__main__':
    value=report();exclusive_json(BASE/'development_unique_secondary_v1.json',value)
    for row in value['methods']:print(row['method'],row['useful_supported_answer_rate_bounds'],row['complete_required_unit_coverage_bounds'])
