import copy
import json
from pathlib import Path
import pytest
import roboboat_full_crane_v2 as original
import roboboat_full_crane_v3 as candidate
from test_roboboat_full_crane_v2 import packet, timeout_packet


def explain(adapter,p,**kwargs):
    return adapter.explain(p,configuration_id='configuration',episode_id='episode',condition_id='condition',**kwargs)


@pytest.mark.parametrize('factory',[packet,timeout_packet])
def test_candidate_preserves_evidence_computation_support_selection_and_numeric_provenance(factory):
    p=factory();before=copy.deepcopy(p)
    old=explain(original,p);new=explain(candidate,p)
    assert p==before
    for name in ['condition_entry','numeric_source_bindings']:
        assert new[name]==old[name]
    for name in ['approved_claim_ids','required_non_entailment_ids']:
        assert new['diagnostic_result'][name]==old['diagnostic_result'][name]
    assert new['plan']['approved_numeric_values']==old['plan']['approved_numeric_values']
    for field in ['status','missing_required_claim_ids','unapproved_claim_ids','numeric_mismatches',
                  'missing_limitation_ids','represented_required_claim_ids']:
        assert new['realization']['audit'][field]==old['realization']['audit'][field]
    for a,b in zip(new['realization']['audit']['clause_audits'],old['realization']['audit']['clause_audits']):
        assert {k:v for k,v in a.items() if k!='response_span'}=={k:v for k,v in b.items() if k!='response_span'}
    text=json.dumps(new['realization'])
    assert 'why the boat stopped' not in text
    assert 'cause of motion;' not in text
    assert 'does not establish internal consumption, physical stopping, or a stopping cause' in text


def test_catalog_diff_is_only_prospectively_declared_language_repair():
    root=Path(__file__).resolve().parents[1]
    old=(root/'configs/roboboat_claim_contracts_v2_development.json').read_text()
    expected=old.replace('this observation does not establish internal consumption or why the boat stopped.',
                        'this configuration observation does not establish internal consumption, physical stopping, or a stopping cause.')
    expected=expected.replace('These observations do not identify the physical cause of motion; waves, current, wind and actuation remain unresolved.',
                              'These observations do not identify a unique physical cause; waves, current, wind and actuation remain unresolved.')
    assert (root/'configs/roboboat_claim_contracts_v3_development.json').read_text()==expected


def test_existing_verifier_still_rejects_nonfinite_candidate_numbers():
    p=packet();out=explain(candidate,p);altered=copy.deepcopy(out['candidate'])
    clause=next(c for c in altered['clauses'] if c['numeric_values'])
    clause['numeric_values'][0]['value']=float('nan')
    with pytest.raises(ValueError,match='finite'):explain(candidate,p,candidate=altered)
