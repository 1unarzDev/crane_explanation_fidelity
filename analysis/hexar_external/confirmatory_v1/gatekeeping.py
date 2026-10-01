"""Fixed-sequence verification. Development and acquisition need no H1 result."""
import hashlib
import json
from pathlib import Path

FAMILY_PATH='manifests/study/evidence-calibration-hexar-fixed-sequence-v1.json'
FAMILY_ID='evidence-calibration-internal-then-hexar-v1'
H2='hexar-external-evidence-calibration-superiority-v1'


def load_pinned(root,path,expected):
    raw=(Path(root)/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('gate artifact hash mismatch: '+path)
    return json.loads(raw)


def validate_family(family,ledger):
    if family['family_id']!=FAMILY_ID or family['family_alpha']!=.01:
        raise ValueError('wrong discovery family')
    if family['previously_consumed_alpha']!=.02 or family['protected_replication_alpha']!=.02:
        raise ValueError('historical/protected alpha changed')
    seq=family['sequence']
    if len(seq)!=2 or [h['hypothesis_id'] for h in seq]!=['H1','H2'] or [h['order'] for h in seq]!=[1,2]:
        raise ValueError('fixed sequence reordered/expanded')
    if seq[0]['claim_id']!='b4-versus-b2-evidence-calibration-primary' or seq[1]['claim_id']!=H2:
        raise ValueError('wrong claims')
    if any(h['alpha']!=.01 for h in seq) or seq[1]['sidedness']!='one-sided':
        raise ValueError('wrong local threshold/sidedness')
    allocations={a['allocation_id']:a for a in ledger['allocations']}
    if ledger['program_alpha']!=.05 or ledger['consumed_alpha']<.02 or sum(a['alpha'] for a in allocations.values())>.05+1e-12:
        raise ValueError('invalid program budget')
    if allocations['candidate-v1-confirmation']['alpha']!=.02 or allocations['candidate-v1-confirmation']['status']!='CONSUMED':
        raise ValueError('historical consumption changed')
    if allocations['selected-method-replication']['alpha']!=.02 or allocations['selected-method-replication'].get('campaign_id')==FAMILY_ID:
        raise ValueError('replication reserve borrowed')
    if allocations['candidate-revision-reserve']['alpha']!=.01:
        raise ValueError('wrong ordered-family allocation')
    return family


def activation_errors(root,family,attestation):
    """Checks sealed H1 result; never accepts a bare reject flag as evidence."""
    errors=[]
    try:
        if family['status']!='FROZEN' or family['bound_alpha']!=.01:
            raise ValueError('ordered family not frozen/bound')
        if attestation['family_id']!=FAMILY_ID or attestation['h2_claim_id']!=H2:
            raise ValueError('wrong gate identity')
        h1=family['sequence'][0]
        h2=family['sequence'][1]
        if attestation.get('h2_freeze_sha256')!=h2.get('freeze_sha256') or not h2.get('freeze_sha256'):
            raise ValueError('gate not bound to H2 acquisition freeze')
        h2freeze=load_pinned(root,h2['freeze_path'],h2['freeze_sha256'])
        seal=load_pinned(root,attestation['raw_cohort_seal_path'],attestation['raw_cohort_seal_sha256'])
        if h2freeze.get('status')!='FROZEN' or seal.get('status')!='SEALED' or seal.get('freeze_sha256')!=h2['freeze_sha256']:
            raise ValueError('H2 freeze/raw cohort seal invalid')
        freeze=load_pinned(root,h1['freeze_path'],h1['freeze_sha256'])
        result=load_pinned(root,attestation['h1_result_path'],attestation['h1_result_sha256'])
        if freeze['status']!='FROZEN' or result['status']!='COMPLETED' or result['confirmatory'] is not True:
            raise ValueError('H1 not frozen/valid complete confirmation')
        if result['claim_id']!=h1['claim_id'] or result['freeze_sha256']!=h1['freeze_sha256']:
            raise ValueError('H1 result uses another protocol')
        if result['procedure_valid'] is not True or result['reject_null'] is not True:
            raise ValueError('H1 failed validity or did not reject; sequence terminates')
        # The adapter interpreting H1's own terminal rule must be qualified and
        # bound; H1 may be sequential or fixed and its sidedness is not H2's.
        if result['decision_rule_sha256']!=freeze['decision_rule_sha256']:
            raise ValueError('H1 decision rule changed')
        if freeze['alpha']!=.01 or result['alpha']!=.01:
            raise ValueError('H1 threshold does not match ordered family')
        if attestation['h1_rule_reexecution_passed'] is not True or not attestation['h1_rule_reexecution_artifact_sha256']:
            raise ValueError('H1 terminal decision has not been independently recomputed')
        recomputation=load_pinned(root,attestation['h1_rule_reexecution_artifact_path'],attestation['h1_rule_reexecution_artifact_sha256'])
        if recomputation.get('passed') is not True or recomputation.get('reject_null') is not True or recomputation.get('h1_result_sha256')!=attestation['h1_result_sha256'] or recomputation.get('decision_rule_sha256')!=freeze['decision_rule_sha256']:
            raise ValueError('independent H1 decision recomputation does not match terminal result/rule')
    except (OSError,KeyError,TypeError,ValueError) as exc:
        errors.append('H2 semantic activation: '+str(exc))
    return errors
