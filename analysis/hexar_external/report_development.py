#!/usr/bin/env python3
"""Package historical metrics and development evidence; never infer an unqualified effect."""
import csv
import json
from pathlib import Path
import statistics
from audit_release import ROOT,sha,write

def main():
    out=ROOT/'data/hexar_external/reports';out.mkdir(exist_ok=True)
    historical=json.loads((ROOT/'data/hexar_external/audit/historical_results.json').read_text())
    labels={'explanation':'HEXAR','explanation_no_components':'LLM baseline','explanation_trigger_all':'No reasoning module'}
    lines=['| Released method | All accuracy | Navigation accuracy | Navigation wrong-info |',
        '|---|---:|---:|---:|']
    for method in ('explanation','explanation_trigger_all','explanation_no_components'):
        all_=historical['methods'][method]['all'];nav=historical['methods'][method]['by_module']['navigation']
        lines.append(f"| {labels[method]} | {all_['accuracy']['positive']}/{all_['n']} ({all_['accuracy']['rate']:.1%}) | {nav['accuracy']['positive']}/{nav['n']} ({nav['accuracy']['rate']:.1%}) | {nav['has_wrong_info']['positive']}/{nav['n']} |")
    (ROOT/'docs/hexar_external/RESULT_TABLE.md').write_text('# Category A: released historical annotations\n\n'+'\n'.join(lines)+'\n\nThese are the authors\' majority-label metrics, not the new evidence-support endpoint. No new experimental improvement is inferred.\n')
    responses=[json.loads(p.read_text()) for p in (ROOT/'data/hexar_external/development/responses').glob('*.json')]
    methods={}
    for m in ('HX-ORIGINAL','HX-PROMPT','HX-CONTRACT'):
        rs=[r for r in responses if r['method']==m];valid=[r for r in rs if r['status']=='VALID']
        identical=[]
        for q in ('q1','q2','q3'):
            a=next(r for r in valid if r['question_id']==q and r['condition']=='intact')['answer']
            b=next(r for r in valid if r['question_id']==q and r['condition']=='irrelevant_removal')['answer']
            identical.append(a==b)
        methods[m]={'responses':len(rs),'valid':len(valid),'technical_failures':len(rs)-len(valid),
            'model_calls':sum(r['model_calls'] for r in valid),'template_responses':sum(r['template'] for r in valid),
            'fallback_responses':sum(r['fallback'] for r in valid),'mean_words':statistics.mean(len(r['answer'].split()) for r in valid),
            'mean_end_to_end_ms':statistics.mean(r['end_to_end_ms'] for r in valid),
            'intact_irrelevant_exact_text_match':sum(identical),'exact_match_pairs':3,
            'semantic_consistency_assessed':False,'qualified_primary_success':None,
            'unsupported_causal_rate':None,'coverage':None,'unnecessary_abstention':None,'cost_usd':None}
    qualification=json.loads((ROOT/'data/hexar_external/qualification/qualification-result.json').read_text())
    parity=json.loads((ROOT/'data/hexar_external/replay/native-parity.json').read_text())
    compact={k:v for k,v in parity.items() if not k.endswith('snapshot')}
    write(out/'native_parity_summary.json',{**compact,'raw_parity_file_sha256':sha(ROOT/'data/hexar_external/replay/native-parity.json'),
        'dispatch_trace_sha256':sha(ROOT/'data/hexar_external/replay/native-dispatch-trace.json'),
        'container_digest':'ros:humble-ros-core@sha256:d2bbb43b75b4b73b0552fcedf0aa195d8e9bdd21fe50c02e5c0a791951a55f8e'})
    write(out/'development_summary.json',{'schema':'hexar-development-report/v1','independent_recordings':1,'questions':3,'conditions':3,
        'category':'B_AND_C_DEVELOPMENT_ONLY','methods':methods,'qualification_status':qualification['status'],
        'primary_paired_effect':None,'confidence_interval':None,'p_value':None,'alpha_consumed':0,
        'interpretation':'First bounded development execution completed; no qualified endpoint effect or population inference.',
        'gate':'External qualification field gate failed in both passes; do not score or promote this batch.'})
    # An evidence-level figure, explicitly NOT a performance plot.
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['svg.hashsalt']='hexar-evidence-development-v1'
    import matplotlib.pyplot as plt
    import numpy as np
    matrix=np.array([[1,1,1],[1,1,1],[1,1,0],[0,0,0]])
    fig,ax=plt.subplots(figsize=(7,3.2),layout='constrained')
    ax.imshow(matrix,cmap='Blues',vmin=0,vmax=1,aspect='auto')
    ax.set_xticks(range(3),['Intact','Irrelevant evidence\nremoved','Manual evidence\nremoved'])
    ax.set_yticks(range(4),['Reported navigation timeout','Controller progress failures','Recorded manual state','Verified physical cause'])
    for i in range(4):
        for j in range(3):ax.text(j,i,'supported' if matrix[i,j] else 'unknown',ha='center',va='center',color='white' if matrix[i,j] else 'black',fontsize=9)
    ax.tick_params(axis='x',labelsize=9)
    ax.set_title('One released execution; three information conditions',fontsize=11)
    fig.savefig(ROOT/'docs/hexar_external/EVIDENCE_FIGURE.svg',metadata={'Date':None})
    svg=ROOT/'docs/hexar_external/EVIDENCE_FIGURE.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    fig.savefig(ROOT/'docs/hexar_external/EVIDENCE_FIGURE.png',dpi=160);plt.close(fig)
    # Sensitivity is planning information, not an allocated test or observed power.
    from math import comb
    n=12
    exact=lambda k: min(1.,2*sum(comb(n,i) for i in range(k,n+1))/2**n)
    cutoff=next(k for k in range(n//2+1,n+1) if exact(k)<=.01)
    power=sum(comb(n,k)*.8**k*.2**(n-k) for k in range(cutoff,n+1))
    write(out/'precision_sensitivity.json',{'schema':'hexar-planning-sensitivity/v1','not_observed_pilot_power':True,
        'not_authorized_test':True,'reserved_recordings':12,'known_situation_families':6,
        'maximum_discovery_alpha_in_main_ledger':.01,'allocated_external_alpha':0,
        'optimistic_independent_recording_sign_test':{'assuming_all_12_discordant_and_independent':True,'positive_recordings_needed':cutoff,'two_sided_p':exact(cutoff),'power_if_positive_probability_0_8':power},
        'conservative_six_family_sign_reversal':{'smallest_two_sided_p':2/2**6,'cannot_reach_alpha_0_01':True},
        'limitation':'Actual endpoint discordance is unknown because qualification failed. Fixed known-family conditioning and family generalization require different assumptions; no clustering switch is authorized.'})
    print(json.dumps({'responses':len(responses),'qualification':qualification['status'],'primary_effect':None,'methods':methods},indent=2))
if __name__=='__main__':main()
