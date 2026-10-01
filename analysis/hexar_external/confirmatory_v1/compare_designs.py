"""Prospective procedure comparison, not empirical significance testing."""
import json
import platform
from pathlib import Path
from .statistics import exact_power
from .heterogeneous_statistics import power

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'


def main():
    rows=[]
    for d in (.2,.35,.5,.65):
        for q in (.65,.7,.75,.8,.85):
            for fraction in (.3,.4,.5,.6):
                required=next((n for n in range(6,721,6) if power(n,d,q,fraction=fraction)>=.9),None)
                rows.append(dict(discordance=d,favorable_given_discordance=q,
                                 recording_risk_difference=d*(2*q-1),fixed_fraction=fraction,
                                 e_test_power_72=power(72,d,q,fraction=fraction),
                                 e_test_power_96=power(96,d,q,fraction=fraction),
                                 exact_conditional_power_72=exact_power(72,d,q),
                                 required_balanced_n_90=required))
    report=dict(schema='hexar-prospective-procedure-comparison/v1',status='DESIGN_ONLY_NO_OUTPUTS',
                alpha=.01,target_power=.9,python=platform.python_version(),rows=rows,
                proposed_primary='fixed-N paired e-test at prospectively fixed fraction .4',
                planning_example_n=96,selected_n=None,not_yet_frozen=True,
                why='controls average-risk null under independent nonidentical family distributions; common-q conditional assumption is not established',
                primary_exact_mcnemar=False,
                no_post_outcome_procedure_selection=True)
    (BASE/'procedure_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Paired procedure selection before confirmation','',
           '**Candidate design amendment; no freeze or alpha allocation.** No confirmatory outcomes exist.','',
           'The initial leading test was exact conditional McNemar. Balanced families are allowed to have different discordance directions; its common conditional-sign assumption is not established for the desired overall average-risk null. Rather than assert that assumption, the proposed primary is a fixed-N paired e-test at fraction λ=.4. It controls the one-sided .01 average-risk null under independent, potentially nonidentical episode distributions. This is a conservative finite-sample test, not exact McNemar. Its rejection probability is calculated exactly for power planning.','',
           '| Discordance | Favorable conditional | Recording effect | McNemar power at 72 (its model) | E-test power at 72 | E-test power at 96 | E-test N for 90% |',
           '|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['fixed_fraction']==.4:
            lines.append(f'| {r["discordance"]:.2f} | {r["favorable_given_discordance"]:.2f} | {r["recording_risk_difference"]:.3f} | {r["exact_conditional_power_72"]:.3f} | {r["e_test_power_72"]:.3f} | {r["e_test_power_96"]:.3f} | {r["required_balanced_n_90"] or ">720"} |')
    lines += ['', 'At d=.50/q=.80, λ=.4 gives about 75% power at 72 and at least 90% first at balanced N=96. This supplies a 16-valid-episodes-per-family planning example if that regime is accepted; final N remains unset until acquisition qualification. A smaller recording effect can require much larger N; neither 72 nor 96 is automatically adequate. The full JSON also evaluates λ=.3/.5/.6 as prospective design sensitivity, never outcome-dependent tuning. Selecting λ=.4 and N is an a priori decision that must be bound with the protocol; no mixture, maximum over tests, or second confirmatory McNemar test is authorized.','',
              'Let Dᵢ = HX-PROMPT failure − HX-CONTRACT failure ∈ {−1,0,1}. For any fixed μ∈[−1,1] define','',
              '`E(μ) = ∏ᵢ [1 + λ(Dᵢ − μ)/(1 + |μ|)]`.','',
              'Every factor is positive for 0<λ<1. Under H₀: average E[Dᵢ]≤μ and independence, E[E(μ)] equals the product of factor expectations. AM–GM bounds that product by `[1 + λ(average E[Dᵢ] − μ)/(1 + |μ|)]ᴺ ≤ 1`. Markov therefore bounds P(E(μ)≥100) by .01. This proof permits arbitrary fixed-family means, discordance rates and variances. It does not permit dependent episodes. Fixed N and λ are required; no optional stopping claim is made.','',
              'Report p=min(1,1/E(0)), both failure rates, the four paired cells and absolute risk difference. Each factor decreases in μ, so invert E(μ)≥100 for a one-sided 99% lower bound. Invert the sign-reversed procedure at .01 for the upper bound; the union bound gives a two-sided interval with at least 98% coverage. The lower bound and the primary test correspond to the same conservative procedure. Full-cohort unresolved outcomes are mapped least favorably; monotonicity prevents missingness from helping CRANE.','',
              'The original exact-power report remains available as conditional-model planning, not the new procedure\'s power. The hypothesis, endpoint, methods and alpha are unchanged. Primary procedure selection is recorded before any confirmation, never chosen from its outcomes.']
    (ROOT/'docs/hexar_external/confirmatory_v1/PROCEDURE_SELECTION.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
