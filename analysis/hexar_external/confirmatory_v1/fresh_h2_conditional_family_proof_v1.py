"""Exact synthetic witnesses for a proposed fresh-data conditional family.

Not study analysis, allocation authority or activation. The general argument is
in the companion proposal; finite witnesses cannot prove operational assumptions.
"""
from fractions import Fraction as F
from pathlib import Path

from .journal import exclusive_json
from ..acquisition.raw_archive_v1 import digest

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1/fresh_h2_conditional_extension_proposal_v1'
ALPHA=F(1,100)


def family_false_rejection(h1_true,histories):
    """Histories have unconditional weight, gate, H2 truth and conditional size."""
    if sum(h['weight'] for h in histories)!=1:
        raise ValueError('complete history weights required')
    if any(h['weight']<0 or type(h['gate']) is not bool or type(h['h2_true']) is not bool
           or not 0<=h['h2_conditional_reject']<=1 for h in histories):
        raise ValueError('probability/truth/gate constraints invalid')
    gate=sum(h['weight'] for h in histories if h['gate'])
    if h1_true and gate>ALPHA:
        raise ValueError('H1 frozen level-.01 requirement violated')
    if any(h['h2_true'] and h['h2_conditional_reject']>ALPHA for h in histories):
        raise ValueError('fresh H2 conditional level-.01 requirement violated')
    # A rejecting gate is already a false rejection when H1 is true.
    false=gate if h1_true else sum(h['weight']*h['h2_conditional_reject']
                                 for h in histories if h['gate'] and h['h2_true'])
    assert false<=ALPHA
    return false


def witnesses():
    rows=[]
    for h1_true in (False,True):
        for gate_probability in ([F(0),F(1,10000),ALPHA] if h1_true else [F(0),ALPHA,F(1,2),F(1)]):
            for h2_true in (False,True):
                for h2_size in ([F(0),F(1,1000),ALPHA] if h2_true else [F(0),F(1,2),F(1)]):
                    histories=[dict(weight=gate_probability,gate=True,h2_true=h2_true,h2_conditional_reject=h2_size),
                        dict(weight=1-gate_probability,gate=False,h2_true=h2_true,h2_conditional_reject=h2_size)]
                    value=family_false_rejection(h1_true,histories)
                    rows.append(dict(h1_true=h1_true,gate_probability=str(gate_probability),
                        h2_true=h2_true,h2_conditional_size=str(h2_size),family_false_rejection=str(value)))
    # H2's truth can vary with the prospectively selected future population;
    # control applies only in histories where the selected H2 null is true.
    adaptive=[dict(weight=F(1,2),gate=True,h2_true=False,h2_conditional_reject=F(1)),
              dict(weight=F(1,4),gate=True,h2_true=True,h2_conditional_reject=ALPHA),
              dict(weight=F(1,4),gate=False,h2_true=True,h2_conditional_reject=ALPHA)]
    return rows,family_false_rejection(False,adaptive)


def execute():
    rows,adaptive=witnesses()
    # Selecting an observed significant test from 100 reused null tests is not
    # a fresh conditional-level procedure, despite each having marginal .01.
    invalid_selected=1-(1-ALPHA)**100
    assert invalid_selected>ALPHA
    value=dict(schema='hexar-fresh-h2-conditional-family-proof-witnesses/v1',phase='synthetic_design_only',
        status='EXACT_ALGEBRAIC_WITNESSES_PASSED_NOT_OPERATIONAL_OR_ALLOCATION_QUALIFICATION',
        alpha=str(ALPHA),rows=rows,regimes=len(rows),maximum_family_false_rejection=str(max(F(r['family_false_rejection']) for r in rows)),
        adaptive_truth_example_false_rejection=str(adaptive),
        invalid_reused_100_test_selection_probability=float(invalid_selected),
        general_proof_location='docs/hexar_external/confirmatory_v1/FRESH_H2_CONDITIONAL_EXTENSION_PROPOSAL.md',
        implementation_sha256=digest(Path(__file__)),provider_calls=0,robot_calls=0,
        actual_h1_results_read=False,actual_hexar_results_used=False,confirmatory_N=0,
        alpha_consumed=0,confirmation_authorized=False,ledger_modified=False,
        scope='Exact finite synthetic witnesses; actual conditional-level/freshness/H1 validity assumptions remain unqualified.')
    exclusive_json(BASE/'proof_witness_report.json',value)
    print({k:v for k,v in value.items() if k!='rows'},flush=True)
    return value


if __name__=='__main__':execute()
