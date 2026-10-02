"""Deterministic retained-artifact exploratory reporting; no provider calls."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import numpy as np
from .inventory import ROOT, FAMILIES
from ..confirmatory_v1.journal import fingerprint
from ..confirmatory_v1.episode_scoring_archives_v1 import read_episode, close_episode
from ..confirmatory_v1.registered_attempt_executor_v2 import load_artifact
from ..confirmatory_v1.audit_development_episode_stage_v1 import audit_stage
from ..confirmatory_v1.mixture_interval_v3 import summary
from ..acquisition.raw_archive_v1 import digest
from .usage import collect as collect_usage

BASE=ROOT/'manifests/hexar_external/existing_v16_exploratory_v1'
METHODS=('HX-CONTRACT','HX-PROMPT')


def paired_cell(cf,pf):
    return 0 if not cf and pf else 1 if cf and not pf else 2 if not cf and not pf else 3


def paired_report(rows):
    n=len(rows);complete=[];worst=[0]*4;best=[0]*4;cells=[0]*4
    for r in rows:
        c,p=(r['states'][m] for m in METHODS)
        worst[paired_cell(c!='PASS',p=='FAIL')]+=1
        best[paired_cell(c=='FAIL',p!='PASS')]+=1
        if c!='UNRESOLVED' and p!='UNRESOLVED':
            cells[paired_cell(c=='FAIL',p=='FAIL')]+=1;complete.append(r)
    low=summary(worst[0],worst[1],n,alpha=.025)
    high=summary(best[0],best[1],n,alpha=.025)
    rng=np.random.default_rng(2026100202);draw=np.zeros(20000,dtype=np.int64);complete_n=len(complete)
    for f in FAMILIES:
        vals=np.array([int(r['states']['HX-PROMPT']=='FAIL')-int(r['states']['HX-CONTRACT']=='FAIL') for r in complete if r['family']==f])
        if len(vals):draw+=rng.choice(vals,(20000,len(vals))).sum(axis=1)
    if complete_n:draw=draw/complete_n
    return dict(scheduled_n=n,complete_paired_n=complete_n,unknown_paired_n=n-complete_n,
        paired_cells=dict(contract_pass_prompt_fail=cells[0],prompt_pass_contract_fail=cells[1],both_pass=cells[2],both_fail=cells[3]),
        complete_case_failure_rates={m:sum(r['states'][m]=='FAIL' for r in complete)/complete_n if complete_n else None for m in METHODS},
        full_scheduled_failure_bounds={m:[sum(r['states'][m]=='FAIL' for r in rows)/n,sum(r['states'][m]!='PASS' for r in rows)/n] for m in METHODS},
        complete_case_risk_difference=(cells[0]-cells[1])/complete_n if complete_n else None,
        full_scheduled_observed_effect_bounds=[(worst[0]-worst[1])/n,(best[0]-best[1])/n],
        full_scheduled_conservative_mixture_evidence=low['evidence_exact'],
        exploratory_one_sided_e_value_derived_p=low['one_sided_p_value'],
        exploratory_p_exact=low['p_exact'],
        independent_episode_95_interval_with_unknown_envelope=[low['one_sided_lower'],high['two_sided_interval'][1]],
        complete_case_stratified_bootstrap_95_interval=np.quantile(draw,[.025,.975]).tolist() if complete_n else None,
        inference_assumptions='Independent latent paired episode outcomes under fixed methods/instrument and balanced selected population; mean-effect null. Unknown mapping bounds pointwise. Provider/measurement drift and dependence can invalidate these assumptions.',
        bootstrap_note='Within-family episode resampling preserves complete-case family sizes; exploratory descriptive interval, small samples and informative missingness limit interpretation.',
        family_sensitivity={f:dict(complete=sum(r['family']==f for r in complete),scheduled=sum(r['family']==f for r in rows),
            failure_rates={m:sum(r['states'][m]=='FAIL' for r in complete if r['family']==f)/sum(r['family']==f for r in complete) if any(r['family']==f for r in complete) else None for m in METHODS},
            risk_difference=sum(int(r['states']['HX-PROMPT']=='FAIL')-int(r['states']['HX-CONTRACT']=='FAIL') for r in complete if r['family']==f)/sum(r['family']==f for r in complete) if any(r['family']==f for r in complete) else None,
            net_wins=sum(int(r['states']['HX-PROMPT']=='FAIL')-int(r['states']['HX-CONTRACT']=='FAIL') for r in complete if r['family']==f)) for f in FAMILIES})


def collect(base=BASE):
    base=Path(base);d=load_artifact(base/'declaration.json');inv=load_artifact(base/'inventory.json');binding=fingerprint(d)
    if d['analysis_status']!='EXPLORATORY_NOT_CONFIRMATORY' or d['confirmatory_N']!=0 or d['alpha_consumed']!=0:
        raise ValueError('explicit existing-episode exploratory plan required')
    for path,sha in d['source_hashes'].items():
        if digest(ROOT/path)!=sha or digest(base/'source_archive'/path)!=sha:raise ValueError('bound exploratory source changed: '+path)
    rows=[];jobs=[];method_rows=[];stages=[];hashes={str(base/'declaration.json'):digest(base/'declaration.json')};baseline_calls=0
    for r in d['records']:
        folder=base/r['relative_path'];states={m:'UNRESOLVED' for m in METHODS};generated={m:False for m in METHODS};closed=None
        if (folder/'methods/completion_receipt.json').exists():
            outcomes=load_artifact(folder/'methods/closed_outcomes.json');plan=load_artifact(folder/'unique_method_plan.json')
            generated={m:all(outcomes[v['unique_request_id']]['status']=='VALID' for v in plan['requests'] if v['method']==m) for m in METHODS}
            baseline_calls+=sum(v['method']=='HX-PROMPT' for v in plan['requests'])
        if (folder/'closed_dispositions.json').exists():
            for stage in ('methods','initial_judges','adjudication_judges'):
                stages.append(dict(episode_id=r['episode_id'],**audit_stage(folder/stage,binding,stage)))
            idx=load_artifact(folder/'scoring/episode_index.json')
            _,art=read_episode(folder/'scoring',fingerprint(idx),binding,'development_qualification')
            initial=load_artifact(folder/'initial_judges/closed_outcomes.json');C=load_artifact(folder/'adjudication_judges/closed_outcomes.json')
            closed=close_episode(art,initial,C)
            if closed!=load_artifact(folder/'closed_dispositions.json'):raise ValueError('retained episode disposition differs')
            for o in art['method_outputs.json']:
                original=outcomes[o['unique_request_id']]
                if o['status']!=original['status'] or o['answer']!=(original['parsed']['answer'] if original['status']=='VALID' else None):
                    raise ValueError('scored answer differs from original method return')
            states=closed['recording_endpoints'][0]['method_states']
            ref={e['job_id']:e['reference'] for e in art['neutral_reference_registry.json']['entries']}
            for j in closed['jobs']:
                label=closed['labels'][j['source_unique_request_id']]['label']
                units=ref[j['question_id']+'-'+j['condition']]['required_units'];covered=set(label['covered_units']) if label else set()
                jobs.append(dict(episode_id=r['episode_id'],family=r['family'],**j,
                    label_resolved=label is not None and not label['ambiguous_spans'],
                    required_units=len(units),covered_units=sum(u['unit_id'] in covered for u in units) if label else None,
                    required_unit_ids=[u['unit_id'] for u in units],covered_unit_ids=sorted(covered) if label else None,
                    unsupported_spans=label['unsupported_spans'] if label else None,
                    overlicensed_spans=label['overlicensed_spans'] if label else None,
                    ambiguous_spans=label['ambiguous_spans'] if label else None))
            method_rows.extend(dict(family=r['family'],**o) for o in art['method_outputs.json'])
            hashes[str(folder/'closed_dispositions.json')]=digest(folder/'closed_dispositions.json')
        rows.append(dict(episode_id=r['episode_id'],family=r['family'],states=states,generated=generated,closed=closed is not None))
    flow=[]
    for f in FAMILIES:
        rs=[r for r in rows if r['family']==f];src=inv['counts_by_family'][f]
        flow.append(dict(family=f,collected=src['collected'],eligible=src['eligible'],scheduled=len(rs),
            generated_both=sum(all(r['generated'].values()) for r in rs),closed_scoring=sum(r['closed'] for r in rs),
            complete_pairs=sum(all(s!='UNRESOLVED' for s in r['states'].values()) for r in rs),
            missing_or_unresolved_pairs=sum(any(s=='UNRESOLVED' for s in r['states'].values()) for r in rs),
            excluded=src['collected']-src['eligible'],eligible_not_selected=src['eligible']-len(rs)))
    components={};conditions=[]
    for m in METHODS:
        selected=[j for j in jobs if j['method']==m];answers=[o for o in method_rows if o['method']==m and o['status']=='VALID']
        fractions=[]
        text_diversity=[]
        for uid in sorted({j['episode_id'] for j in selected}):
            js=[j for j in selected if j['episode_id']==uid]
            if all(j['covered_units'] is not None for j in js):fractions.append(sum(j['covered_units'] for j in js)/sum(j['required_units'] for j in js))
        for uid in sorted({o['episode_id'] for o in answers}):
            strings=[' '.join(o['answer'].split()) for o in answers if o['episode_id']==uid]
            text_diversity.append(len(set(strings))/len(strings))
        components[m]=dict(battery_answer_cells=len(selected),resolved_cell_labels=sum(j['label_resolved'] for j in selected),
            scheduled_battery_answer_cells=9*len(rows),unmeasured_battery_answer_cells=9*len(rows)-len(selected),
            unsupported_cells=sum(j['unsupported_material'] is True for j in selected),
            overlicensed_cells=sum(j['overlicensed_specificity'] is True for j in selected),
            required_unit_omission_cells=sum(j['missing_required_unit'] is True for j in selected),
            useful_supported_cells=sum(all(j[k] is False for k in ('unsupported_material','overlicensed_specificity','missing_required_unit')) for j in selected),
            mean_episode_required_unit_recall=mean(fractions) if fractions else None,coverage_episode_denominator=len(fractions),
            coverage_by_required_unit={u:dict(required_cells=sum(u in j['required_unit_ids'] for j in selected),
                known_covered_cells=sum(j['covered_unit_ids'] is not None and u in j['covered_unit_ids'] for j in selected),
                unknown_label_cells=sum(j['covered_unit_ids'] is None and u in j['required_unit_ids'] for j in selected))
                for u in sorted({u for j in selected for u in j['required_unit_ids']})},
            unique_valid_answers=len(answers),mean_unique_answer_words=mean(len(o['answer'].split()) for o in answers) if answers else None,
            mean_within_episode_distinct_answer_text_fraction=mean(text_diversity) if text_diversity else None,
            text_diversity_note='Exact whitespace-normalized answer variation across unique requests; descriptive, not a validated stylistic flexibility or quality measure.',
            deterministic_realization=m=='HX-CONTRACT',baseline_model_calls_in_completed_method_stages=baseline_calls if m=='HX-PROMPT' else 0)
        for condition in ('intact','irrelevant_removal','diagnostic_removal'):
            js=[j for j in selected if j['condition']==condition];den=len(js)
            conditions.append(dict(method=m,condition=condition,cells=den,
                scheduled_cells=3*len(rows),unmeasured_cells=3*len(rows)-den,
                unsupported=sum(j['unsupported_material'] is True for j in js),overlicensed=sum(j['overlicensed_specificity'] is True for j in js),
                omission=sum(j['missing_required_unit'] is True for j in js),
                useful_supported=sum(all(j[k] is False for k in ('unsupported_material','overlicensed_specificity','missing_required_unit')) for j in js),
                useful_unknown=sum(any(j[k] is None for k in ('unsupported_material','overlicensed_specificity','missing_required_unit')) and not any(j[k] is True for k in ('unsupported_material','overlicensed_specificity','missing_required_unit')) for j in js),
                unsupported_unknown=sum(j['unsupported_material'] is None for j in js),
                omission_unknown=sum(j['missing_required_unit'] is None for j in js),
                unresolved=sum(any(j[k] is None for k in ('unsupported_material','overlicensed_specificity','missing_required_unit')) for j in js)))
    return dict(schema='hexar-existing-v16-exploratory-results/v1',status='TERMINAL' if (base/'report.json').exists() else 'PARTIAL_SNAPSHOT',
        exploratory=True,confirmatory=False,agent_assessed=True,human_validated=False,alpha_consumed=0,
        flow=flow,primary=paired_report(rows),components=components,evidence_conditions=conditions,episode_rows=rows,
        answer_cells=jobs,method_outputs=method_rows,raw_stage_audits=stages,input_hashes=hashes,
        provider_usage=collect_usage(base),
        bank_separation='V16 only; V15/V20 and released physical recordings not pooled.',
        deterministic_check_scope='Input/source/packet hashes, finite numerical references, contract approved numeric binding, output schema and literal quotation consistency. Semantic support/coverage and baseline numerical phrasing remain agent-assessed; no general natural-language numerical proof is claimed.',
        provider_identity_limit='Hosted aliases and inherited CLI defaults; immutable served backend/system/decoding identity unavailable.')


def write_csv(path,rows):
    if not rows:return
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def export(base,output):
    value=collect(base);out=Path(output);out.mkdir(parents=True,exist_ok=False)
    (out/'results.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    write_csv(out/'cohort_flow.csv',value['flow']);write_csv(out/'evidence_conditions.csv',value['evidence_conditions'])
    write_csv(out/'episode_outcomes.csv',[dict(episode_id=r['episode_id'],family=r['family'],**r['states']) for r in value['episode_rows']])
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=BASE);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    v=export(a.base,a.output);print(json.dumps({k:v['primary'][k] for k in ('scheduled_n','complete_paired_n','paired_cells','complete_case_risk_difference','exploratory_one_sided_e_value_derived_p')},indent=2))
