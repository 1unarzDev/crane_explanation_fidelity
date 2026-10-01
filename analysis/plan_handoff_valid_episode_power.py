#!/usr/bin/env python3
"""Prospective valid-episode power sensitivity; no confirmation is frozen here."""
import json
from pathlib import Path
from power_evidence_calibration_handoff import power


def main():
    scenarios=[(0.,0.),(.005,0.),(.01,0.),(.02,.005),(.025,.025),(.03,.005),(.035,.01),(.045,.02),(.07,.045)]
    rows=[]
    for b,c in scenarios:
        rows.append(dict(b2_only=b,b4_only=c,risk_difference=b-c,
            powers={str(n):{s:power(n,b,c,0.,s) if b+c else 0. for s in ['one-sided','two-sided']} for n in [640,800,1200,1600]}))
    record=dict(development_only=True,confirmatory_freeze=False,alpha=.01,
        candidate_valid_n=1200,not_selected_or_frozen=True,
        practical_effect_target=.025,
        independent_unit='fresh episode/configuration',
        assumptions='IID independent configuration sampling from a prospectively specified population. Counts are valid complete episode pairs; no masks or judge passes add N. No positive pilot effect is assumed.',
        rationale='1200 valid pairs provide >=80% power for a 2.5 percentage-point reduction across opposing-discordance probabilities 0.005 through 0.020; at 0.045 opposing discordance power is only 56%, so 1200 is not universally adequate. Smaller effects and the null remain explicit sensitivity scenarios. This does not predict a positive effect.',
        attrition='Acquired cap and technical stopping rule remain to be specified; technical missingness may be associated with task difficulty. Report worst-case missing-pair bounds, not merely independent-thinning power.',
        useful_coverage='Success additionally requires a prospectively frozen useful-coverage criterion; this calculation covers superiority only.',early_futility_design=dict(first_look_n=600,maximum_n=1200,rule='Stop only if first600 have zero paired discordances. No early positive result. Otherwise finish1200 and use the original exact test.',
            validity='For every alpha threshold, study rejection is a subset of the fixed1200 exact-test rejection event; study p=1 if stopped, otherwise final exact p. No alpha spent on the futility look.',
            interval='Two predeclared possible terminal looks: Bonferroni CP category tail.00625 yields >=97.5% coverage per look and >=95% over both look-specific intervals.',
            rows=[dict(b2_only=b,b4_only=c,power=power(1200,b,c,0.,"one-sided")-(1-b-c)**600*power(600,b,c,0.,"one-sided") if b+c else 0.,probability_zero_discordance_early_stop=(1-b-c)**600) for b,c in scenarios]),rows=rows)
    out=Path('manifests/analysis/evidence-calibration-handoff-valid-n-power-candidate-v2.json')
    out.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
