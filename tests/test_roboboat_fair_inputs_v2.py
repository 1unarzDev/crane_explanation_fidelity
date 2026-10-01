"""Meaningful common-input parity and treatment/privacy checks; no method calls."""
import copy
import json
from pathlib import Path
import shutil
import pytest
import prepare_roboboat_fair_inputs_v2 as prep

SNAPSHOT=prep.ROOT/'artifacts/roboboat-fair-development-inputs-v2-001/input-snapshot.json'


def pair():
    r=json.loads(SNAPSHOT.read_text());return r,r['entries'][0]


def copied_b4(tmp_path):
    r,e=pair();work=tmp_path/'b4';shutil.copytree(e['B4_private_workspace'],work)
    return r,e,work


def test_all_eligible_conditions_have_identical_common_inputs_and_private_treatment_stays_out_of_baseline():
    r=prep.verify(SNAPSHOT)
    assert r['prepared_conditions']==3*r['eligible_recordings']==27
    assert len(r['capture_accounting']['rows'])==48
    assert r['methods_executed']is False and r['call_readiness']is False and r['model_calls']==0
    e=r['entries'][0];m=prep.common.verify(e['common_manifest']['path']);b2=Path(m['workspace']);b4=Path(e['B4_private_workspace'])
    assert not (b2/'analysis/roboboat_full_crane_v3.py').exists()
    assert not (b2/'configs/roboboat_claim_contracts_v3_development.json').exists()
    assert (b4/'analysis/roboboat_full_crane_v3.py').read_bytes()==prep.METHOD.read_bytes()
    assert (b4/'configs/roboboat_claim_contracts_v3_development.json').read_bytes()==prep.CATALOG.read_bytes()


def test_changed_evidence_cannot_silently_give_one_method_different_runtime_information(tmp_path):
    r,e,work=copied_b4(tmp_path);p=work/'evidence.json';p.chmod(0o644);d=json.loads(p.read_text());d['action']['status']='aborted';p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='unequal method-visible'):prep.verify_pair(e['common_manifest']['path'],r['private_B4_sources'],work)


def test_no_precomputed_answer_or_evaluator_file_can_enter_b4_inputs(tmp_path):
    r,e,work=copied_b4(tmp_path);(work/'B4.json').write_text('{"answer":"precomputed"}')
    with pytest.raises(ValueError,match='undeclared'):prep.verify_pair(e['common_manifest']['path'],r['private_B4_sources'],work)


def test_incomplete_treatment_cannot_be_mislabelled_full_crane(tmp_path):
    r,e,work=copied_b4(tmp_path);private=copy.deepcopy(r['private_B4_sources']);item=next(i for i in private if i['relative_path']=='analysis/realize_evidence_calibrated_explanation.py');private.remove(item);(work/item['relative_path']).unlink()
    with pytest.raises(ValueError,match='exact full B4'):prep.verify_pair(e['common_manifest']['path'],private,work)


def test_one_evidence_level_cannot_be_omitted_from_all_eligible_snapshot(tmp_path):
    r,e=pair();r['entries'].pop();p=tmp_path/'snapshot.json';p.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='all eligible'):prep.verify(p)


def test_raw_failure_pending_denominator_cannot_disappear(tmp_path):
    r,e=pair();r['capture_accounting']['rows'].pop();p=tmp_path/'snapshot.json';p.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='capture accounting changed'):prep.verify(p)
