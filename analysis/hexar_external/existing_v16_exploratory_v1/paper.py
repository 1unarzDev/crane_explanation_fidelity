"""Paper-ready tables/figure from the fixed exploratory results JSON."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def percent(value):return '—' if value is None else f'{100*value:.1f}%'
def effect(value):return '—' if value is None else f'{100*value:+.1f} percentage points'
def interval(value):return '—' if value is None else '['+', '.join(f'{100*x:+.1f}' for x in value)+'] pp'


def make(results,output):
    value=json.loads(Path(results).read_text());out=Path(output);out.mkdir(parents=True,exist_ok=False)
    p=value['primary'];cells=p['paired_cells'];c=value['components'];flows=value['flow']
    text=['# Exploratory evaluation on existing simulated HEXAR episodes','',
        f"The retained V16 bank contains 144 independently seeded TIAGo/Nav2-compatible simulated episodes, 24 per navigation family. We selected an outcome-independent balanced subset of 36 episodes (six per family) before generating new explanations, and applied the unchanged strengthened HX-PROMPT and current HX-CONTRACT to identical visible evidence and public useful-information requirements. The fixed battery contains three questions and three evidence conditions, with identical-request aliases yielding six unique generations per method per episode. Independent statistical N is 36, not the answer or judge-call count.",'',
        'Support and coverage were agent-assessed using blinded separate A/B calls and disagreement-only C adjudication. A whole-episode failure occurs when any battery cell contains unsupported material, overlicensed specificity or a mandatory useful-information omission. Unresolved labels and unfinished scheduled episodes remain unknown. This is exploratory development analysis; no confirmatory alpha was allocated or consumed.','',
        '| Family | Collected | Eligible | Scheduled | Both methods generated | Scoring closed | Complete paired endpoint | Missing/unresolved |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    text += ['| '+ ' | '.join(str(r[k]) for k in ('family','collected','eligible','scheduled','generated_both','closed_scoring','complete_pairs','missing_or_unresolved_pairs'))+' |' for r in flows]
    text+=['','| Outcome | HX-CONTRACT | Strengthened HX-PROMPT |','|---|---:|---:|',
        '| Whole-episode failure, complete pairs | '+percent(p['complete_case_failure_rates']['HX-CONTRACT'])+' | '+percent(p['complete_case_failure_rates']['HX-PROMPT'])+' |']
    for field,label in [('useful_supported_cells','Useful supported answer cells'),('unsupported_cells','Unsupported-material answer cells'),('overlicensed_cells','Overlicensed-specificity answer cells'),('required_unit_omission_cells','Required-unit omission cells')]:
        text.append('| '+label+' | '+' | '.join(f"{c[m][field]}/{c[m]['scheduled_battery_answer_cells']} scheduled" for m in ('HX-CONTRACT','HX-PROMPT'))+' |')
    text.append('| Mean episode required-unit recall (scored coverage) | '+' | '.join(percent(c[m]['mean_episode_required_unit_recall'])+f" (N={c[m]['coverage_episode_denominator']})" for m in ('HX-CONTRACT','HX-PROMPT'))+' |')
    text.append('| Mean words per unique valid answer | '+' | '.join('—' if c[m]['mean_unique_answer_words'] is None else f"{c[m]['mean_unique_answer_words']:.1f}" for m in ('HX-CONTRACT','HX-PROMPT'))+' |')
    text.append('| Within-episode distinct answer-text fraction | '+' | '.join(percent(c[m]['mean_within_episode_distinct_answer_text_fraction']) for m in ('HX-CONTRACT','HX-PROMPT'))+' |')
    text += ['',f"Complete paired endpoints were available for {p['complete_paired_n']}/36 scheduled episodes. The four paired cells were {cells['contract_pass_prompt_fail']} contract-success/prompt-failure, {cells['prompt_pass_contract_fail']} prompt-success/contract-failure, {cells['both_pass']} both-success and {cells['both_fail']} both-failure. The complete-case prompt-minus-contract failure difference was {effect(p['complete_case_risk_difference'])}; its fixed-family stratified descriptive bootstrap interval was {interval(p['complete_case_stratified_bootstrap_95_interval'])}. Full-scheduled missingness bounds were {interval(p['full_scheduled_observed_effect_bounds'])}.",'',
        f"The predeclared heterogeneous-episode paired e-mixture, applied conservatively to all scheduled episodes, returned one-sided exploratory e-value-derived p={p['exploratory_one_sided_e_value_derived_p']:.6g}. Its independent-episode uncertainty interval with the unknown-label envelope was {interval(p['independent_episode_95_interval_with_unknown_envelope'])}. This procedure tests a mean-effect null under independent paired episode outcomes; it does not assume pooled IID discordant signs. Secondary metrics, family summaries and evidence-condition analyses are descriptive, with no additional inferential p-values.",'',
        '| Family sensitivity | Complete episodes | Contract net wins | Failure difference |','|---|---:|---:|---:|']
    text += [f"| {f} | {r['complete']} | {r['net_wins']} | {effect(r['risk_difference'])} |" for f,r in p['family_sensitivity'].items()]
    text += ['', 'The comparison is limited to existing, development-exposed episodes in a restricted adapted simulated HEXAR domain and a small fixed-family sample. Randomized subset selection reduces outcome-based selection but does not establish broad robot-domain representativeness. Hosted model aliases and inherited CLI defaults do not identify immutable served model/system/decoding versions. Automated same-model judges may share errors or infer style despite hidden method IDs; no blinded human validation was performed. Unresolved labels and technical missingness limit precision and may be informative. Within-family bootstrap intervals can be optimistic with only six scheduled episodes per family; the independent-episode interval and missingness envelope are therefore also reported.','',
        'HX-CONTRACT uses deterministic constrained realization and can trade stylistic flexibility and optional detail for support discipline. Answer length and useful-unit coverage are reported so brevity cannot silently substitute for useful communication. No specific physical cause is established merely by controller configuration, boundary snapshots, commands or odometry; software success is not independently measured physical arrival.','',
        'The released physical-recording development comparison remains separate: twelve recordings, 324 generated answers, useful supported answer rates 100% versus 90.7%, descriptive +9.26 percentage points, seven contract-better recordings and five ties. Historical HEXAR navigation accuracy remains 49/54 (90.7%) on its original task. Neither value is a confirmatory p-value or an estimate of this simulated whole-episode endpoint. No universal superiority over HEXAR or improvement of its original published accuracy is claimed.','',
        f"Artifact status: {value['status']}. Raw returns, source/request hashes, immutable selected schedule and the full scheduled denominator are retained. Reproduce with `uv run --no-project --with numpy --with pyyaml python -m analysis.hexar_external.existing_v16_exploratory_v1.analyze --output <new-directory>`; render this section/figure using `uv run --no-project --with matplotlib --with numpy python -m analysis.hexar_external.existing_v16_exploratory_v1.paper --results <results.json> --output <new-directory>`. No provider calls occur during reproduction.",'']
    (out/'manuscript_section.md').write_text('\n'.join(text))
    (out/'claim_language.json').write_text(json.dumps(dict(status='EXPLORATORY_ONLY',allowed='In this exploratory comparison on the selected existing simulated episodes, report the observed effect, interval, exploratory p-value and missingness.',prohibited=['confirmed external superiority','CRANE is superior to HEXAR overall','improved HEXAR published navigation accuracy','fresh confirmatory N=36']),indent=2)+'\n')
    conditions=('intact','irrelevant_removal','diagnostic_removal');methods=('HX-CONTRACT','HX-PROMPT')
    fig,axes=plt.subplots(1,3,figsize=(11,3.5),sharey=True)
    fields=('useful_supported','unsupported','omission');titles=('Useful supported cells','Unsupported material','Required-unit omission')
    for ax,field,title in zip(axes,fields,titles):
        for i,m in enumerate(methods):
            rs=[next(r for r in value['evidence_conditions'] if r['method']==m and r['condition']==cond) for cond in conditions]
            y=[100*r[field]/r['scheduled_cells'] for r in rs]
            unknown_key='useful_unknown' if field=='useful_supported' else field+'_unknown'
            upper=[100*(r['unmeasured_cells']+r[unknown_key])/r['scheduled_cells'] for r in rs]
            ax.bar(np.arange(3)+(i-.5)*.36,y,width=.36,label=m,color=('#287d8e','#d1783b')[i],
                yerr=np.array([np.zeros(3),upper]),capsize=2,error_kw=dict(elinewidth=.8))
        ax.set_xticks(np.arange(3),['Intact','Irrelevant\nremoved','Diagnostic\nremoved']);ax.set_title(title);ax.set_ylim(0,105);ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('% of scheduled answer cells');axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle('Exploratory existing simulated episodes: scheduled independent N=36',fontsize=11)
    fig.tight_layout();fig.savefig(out/'evidence_conditions.svg');fig.savefig(out/'evidence_conditions.png',dpi=200);plt.close(fig)
    (out/'figure_caption.md').write_text('Evidence-condition summaries of the fixed nine-cell battery. Bars show known outcomes divided by all scheduled answer cells (108 per method/condition), including unmeasured cells in the denominator. Black lines show possible upper rates from unmeasured/unresolved labels, not sampling confidence intervals. Categories can overlap; unknown labels do not become supported passes. Questions, masks and aliases remain clustered within 36 independent episodes. Irrelevant-removal aliases reuse identical answers/labels. See the flow table and results JSON for missingness. These answer-cell summaries are descriptive, without independent-answer inference.\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();make(a.results,a.output)
