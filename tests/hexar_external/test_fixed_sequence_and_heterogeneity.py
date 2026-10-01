import copy
import itertools
import json
import math
from pathlib import Path
import pytest
from analysis.hexar_external.confirmatory_v1 import gatekeeping as gate
from analysis.hexar_external.confirmatory_v1 import heterogeneous_statistics as stat
from analysis.hexar_external.confirmatory_v1 import audit

ROOT=Path(__file__).resolve().parents[2]


def test_unbound_family_permits_development_but_not_activation():
    family=json.loads((ROOT/gate.FAMILY_PATH).read_text())
    ledger=json.loads((ROOT/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_text())
    assert gate.validate_family(family,ledger)['development_authorized']
    assert gate.activation_errors(ROOT,family,{})
    assert family['bound_alpha']==family['consumed_alpha']==0
    bad=copy.deepcopy(family);bad['sequence'].reverse()
    with pytest.raises(ValueError):gate.validate_family(bad,ledger)


def test_strong_sequence_control_arbitrary_dependence():
    # Every false rejection requires the first true null's rejection; enumerate
    # all truth configurations and raw decisions, without independence.
    for true_null in itertools.product((False,True),repeat=2):
        for decision in itertools.product((False,True),repeat=2):
            declared=(decision[0],decision[0] and decision[1])
            if any(t and r for t,r in zip(true_null,declared)):
                first=next(i for i,t in enumerate(true_null) if t)
                assert decision[first]


def test_e_expectation_under_heterogeneous_average_null():
    # Individual positive/negative means are allowed; their average is <=0.
    probabilities=[(.65,.15,.2),(.1,.7,.2),(.25,.35,.4)]
    expected=0.;false_reject=0.
    for outcomes in itertools.product((-1,0,1),repeat=3):
        prob=math.prod(p[{1:0,-1:1,0:2}[d]] for p,d in zip(probabilities,outcomes))
        loge=stat.log_evalue(outcomes.count(1),outcomes.count(-1),outcomes.count(0),fraction=.4)
        expected+=prob*math.exp(loge)
        false_reject+=prob*(loge>=math.log(100))
    assert expected<=1 and false_reject<=.01


def test_power_matches_direct_multinomial_and_test_interval():
    n=15;d=.5;q=.8;total=0.
    for f in range(n+1):
        for u in range(n-f+1):
            t=n-f-u
            if stat.log_evalue(f,u,t,fraction=.4)>=math.log(100):
                total+=math.factorial(n)/(math.factorial(f)*math.factorial(u)*math.factorial(t))*(d*q)**f*(d*(1-q))**u*(1-d)**t
    assert stat.power(n,d,q,fraction=.4)==pytest.approx(total)
    assert stat.power(72,.5,.8,fraction=.4)<.8
    assert stat.power(96,.5,.8,fraction=.4)>.9
    value=stat.summarize(40,5,45,6,fraction=.4)
    assert value['conservative_one_sided_p']<.01
    assert value['one_sided_99_lower_bound']>0
    assert value['two_sided_98_interval'][0]<=value['prompt_minus_contract_failure_risk_difference']<=value['two_sided_98_interval'][1]


def test_missingness_monotonicity_and_mu_monotonicity():
    assert stat.log_evalue(10,2,4,fraction=.4)>stat.log_evalue(9,3,4,fraction=.4)
    curve=[stat.log_evalue(10,2,4,mu=mu,fraction=.4) for mu in (-1,-.5,0,.5,1)]
    assert curve==sorted(curve,reverse=True)


def test_acquisition_audit_does_not_require_h1_rejection():
    result=audit.audit(stage='acquisition')
    assert result['development_authorized']
    assert not result['passed'] # unresolved acquisition/runtime qualification
    assert not any('H2 semantic activation' in e for e in result['errors'])
    assert any('model_version' in e for e in result['errors'])


def test_raw_selection_first_valid_without_method_outcomes(tmp_path):
    from analysis.hexar_external.confirmatory_v1.seal_cohort import select,digest
    attempts=[]
    for i,valid in enumerate((False,True,True),1):
        raw=tmp_path/f'raw-{i}';raw.write_bytes(bytes([i]))
        receipt=tmp_path/f'validity-{i}.json'
        receipt.write_text(json.dumps(dict(acquisition_id=f'acq-{i}',raw_sha256=digest(raw),technical_valid=valid,method_outcomes_accessed=False,validity_predicate_sha256='test-predicate')))
        attempts.append(dict(acquisition_id=f'acq-{i}',seed=i,raw_sha256=digest(raw),raw_path=raw.name,
                             family='success',attempt_order=i,validity_predicate_sha256='test-predicate',semantic_outputs_generated=False,independent_reset=True,
                             validity_receipt_path=receipt.name,validity_receipt_sha256=digest(receipt)))
    records,disposition=select(attempts,1,['success'],tmp_path,set())
    assert records[0]['acquisition_id']=='acq-2'
    assert [x['disposition'] for x in disposition]==['TECHNICAL_INVALID','SELECTED','RESERVE_NOT_SELECTED']
    with pytest.raises(ValueError,match='reserve exhausted'):select(attempts,3,['success'],tmp_path,set())
    bad=copy.deepcopy(attempts);bad[0]['semantic_outputs_generated']=True
    with pytest.raises(ValueError,match='semantic exposure'):select(bad,1,['success'],tmp_path,set())
    with pytest.raises(ValueError,match='development recording'):select(attempts,1,['success'],tmp_path,{attempts[0]['raw_sha256']})


def test_gate_requires_hash_bound_valid_recomputed_rejection(tmp_path):
    import hashlib
    def store(name,value):
        p=tmp_path/name;p.write_text(json.dumps(value));return hashlib.sha256(p.read_bytes()).hexdigest()
    family=json.loads((ROOT/gate.FAMILY_PATH).read_text())
    family['status']='FROZEN';family['bound_alpha']=.01
    family['sequence'][0]['freeze_path']='h1freeze.json'
    fh=store('h1freeze.json',dict(status='FROZEN',decision_rule_sha256='rule',alpha=.01))
    family['sequence'][0]['freeze_sha256']=fh
    h2h=store('h2freeze.json',dict(status='FROZEN'))
    family['sequence'][1]['freeze_path']='h2freeze.json';family['sequence'][1]['freeze_sha256']=h2h
    sh=store('cohortseal.json',dict(status='SEALED',freeze_sha256=h2h))
    result=dict(status='COMPLETED',confirmatory=True,claim_id=family['sequence'][0]['claim_id'],freeze_sha256=fh,
                procedure_valid=True,reject_null=True,decision_rule_sha256='rule',alpha=.01)
    rh=store('h1result.json',result)
    vh=store('reexecuted.json',dict(passed=True,reject_null=True,h1_result_sha256=rh,decision_rule_sha256='rule'))
    attestation=dict(family_id=gate.FAMILY_ID,h2_claim_id=gate.H2,h1_result_path='h1result.json',h1_result_sha256=rh,
                     h1_rule_reexecution_passed=True,h1_rule_reexecution_artifact_path='reexecuted.json',
                     h1_rule_reexecution_artifact_sha256=vh,h2_freeze_sha256=h2h,raw_cohort_seal_path='cohortseal.json',raw_cohort_seal_sha256=sh)
    assert not gate.activation_errors(tmp_path,family,attestation)
    result['reject_null']=False;attestation['h1_result_sha256']=store('h1result.json',result)
    assert any('did not reject' in e for e in gate.activation_errors(tmp_path,family,attestation))
    (tmp_path/'h1result.json').write_text('{}')
    assert any('hash mismatch' in e for e in gate.activation_errors(tmp_path,family,attestation))


def test_provider_request_requires_explicit_settings_and_strict_output():
    from analysis.hexar_external.confirmatory_v1 import request_binding as binding
    from analysis.hexar_external.confirmatory_v1.blind_bank import PACKET_KEYS
    packet={k:{} for k in PACKET_KEYS}
    settings=dict(provider='test-provider',model='test-model',model_version='snapshot-test',temperature=0.,top_p=1.,
                  max_output_tokens=100,seed=7,system_instructions='test system',tool_permissions=[],repository_access='none',
                  context_access='packet_only',quality_retries=0,technical_retries=0,timeout_seconds=180,
                  output_schema={'answer':'string'})
    bound=binding.bind(packet,'strong prompt fixture',settings)
    assert not bound['transport_qualified']
    packet['evidence']['test']=True
    assert bound['request']['messages'][2]['content']['evidence']=={}
    settings['model_version']=None
    with pytest.raises(ValueError,match='model_version'):binding.bind(packet,'prompt',settings)
    assert binding.parse_answer({'answer':' retained exact text '})==' retained exact text '
    for value in ({'answer':1},{'answer':''},{'answer':'x','other':'field'}):
        with pytest.raises(ValueError):binding.parse_answer(value)


def test_nested_blinding_metadata_is_rejected():
    from analysis.hexar_external.confirmatory_v1 import blind_bank
    entry=dict(recording_id='dev',method='HX-PROMPT',question_id='q1',condition='intact',answer='raw answer',
               method_packet={k:{} for k in blind_bank.PACKET_KEYS},reference={k:[] for k in blind_bank.REFERENCE_KEYS})
    entry['method_packet']['evidence']={'nested':[{'expected_winner':'contract'}]}
    with pytest.raises(ValueError,match='nested'):blind_bank.build([entry],b'x'*32,1)
