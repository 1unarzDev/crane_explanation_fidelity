"""Fixed-sequence verification. Development and acquisition need no H1 result."""
import hashlib
import json
from pathlib import Path

FAMILY_PATH='manifests/study/evidence-calibration-hexar-fixed-sequence-v1.json'
FAMILY_ID='evidence-calibration-internal-then-hexar-v1'
H2='hexar-external-evidence-calibration-superiority-v1'
LEDGER_PATH='manifests/study/diagnostic-sequential-error-ledger-v2.json'
BASE_PATH='manifests/hexar_external/confirmatory_v1'
SCIENTIFIC_FILES={BASE_PATH+'/'+name for name in (
    'battery.json','endpoint.json','comparator_freeze.json','cohort.json',
    'fixed_n_decision.json','technical_validity.json','annotation_freeze.json',
    'analysis_plan.json','runtime_dependencies.json')}



def load_pinned(root,path,expected):
    raw=(Path(root)/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('gate artifact hash mismatch: '+path)
    value=json.loads(raw)
    if not isinstance(value,dict):
        raise ValueError('gate artifact must be an object: '+path)
    return value


def validate_family(family,ledger,activation=False):
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
    if len(allocations)!=len(ledger['allocations']):
        raise ValueError('duplicate program allocation')
    consumed=sum(a['alpha'] for a in allocations.values() if a['status']=='CONSUMED')
    if ledger['program_alpha']!=.05 or ledger['consumed_alpha']<.02 or abs(ledger['consumed_alpha']-consumed)>1e-12 or abs(sum(a['alpha'] for a in allocations.values())-.05)>1e-12:
        raise ValueError('invalid program budget')
    if allocations['candidate-v1-confirmation']['alpha']!=.02 or allocations['candidate-v1-confirmation']['status']!='CONSUMED':
        raise ValueError('historical consumption changed')
    if allocations['selected-method-replication']['alpha']!=.02 or allocations['selected-method-replication'].get('campaign_id')==FAMILY_ID:
        raise ValueError('replication reserve borrowed')
    if allocations['candidate-revision-reserve']['alpha']!=.01 or allocations['candidate-revision-reserve'].get('role')!='candidate':
        raise ValueError('wrong ordered-family allocation')
    allocation=allocations['candidate-revision-reserve']
    if family.get('allocation_id')!='candidate-revision-reserve':
        raise ValueError('wrong family allocation identity')
    if allocation.get('campaign_id') not in (None,FAMILY_ID):
        raise ValueError('discovery allocation assigned to another family')
    if activation and (allocation.get('campaign_id')!=FAMILY_ID or allocation.get('status')!='CONSUMED' or not allocation.get('consumed_at')):
        raise ValueError('ordered family not assigned/consumed in authoritative ledger')
    return family


def validate_scientific_binding(root,family,h2freeze=None):
    h2=family['sequence'][1]
    binding=load_pinned(root,h2['protocol_binding_path'],h2['protocol_binding_sha256'])
    files=binding.get('files',{})
    if not isinstance(files,dict) or binding.get('status')!='FROZEN' or binding.get('claim_id')!=H2 or not SCIENTIFIC_FILES.issubset(files):
        raise ValueError('H2 scientific protocol binding incomplete or wrong claim')
    deps=load_pinned(root,BASE_PATH+'/runtime_dependencies.json',files[BASE_PATH+'/runtime_dependencies.json'])
    if deps.get('complete_transitive_closure') is not True or not isinstance(deps.get('files'),dict) or not deps['files']:
        raise ValueError('H2 scientific runtime closure missing')
    if any(files.get(p)!=h for p,h in deps['files'].items()):
        raise ValueError('H2 scientific binding omits runtime dependency')
    for path,expected in files.items():
        if path in (FAMILY_PATH,LEDGER_PATH,BASE_PATH+'/alpha_amendment.json',BASE_PATH+'/freeze_manifest.json'):
            raise ValueError('circular or mutable allocation artifact in scientific binding')
        if hashlib.sha256((Path(root)/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('changed H2 scientific protocol: '+path)
        if h2freeze is not None and h2freeze.get('file_hashes',{}).get(path)!=expected:
            raise ValueError('H2 acquisition freeze changes family-bound scientific protocol')
    return binding


def activation_errors(root,family,attestation):
    """Checks sealed H1 result; never accepts a bare reject flag as evidence."""
    errors=[]
    try:
        ledger=json.loads((Path(root)/LEDGER_PATH).read_text())
        validate_family(family,ledger,activation=True)
        if family['status']!='FROZEN' or family['bound_alpha']!=.01:
            raise ValueError('ordered family not frozen/bound')
        if attestation['family_id']!=FAMILY_ID or attestation['h2_claim_id']!=H2:
            raise ValueError('wrong gate identity')
        h1=family['sequence'][0]
        h2=family['sequence'][1]
        h2_freeze_sha=attestation['h2_freeze_sha256']
        h2freeze=load_pinned(root,attestation['h2_freeze_path'],h2_freeze_sha)
        # Family binds H2's scientific file set, not the acquisition freeze
        # hash: the acquisition freeze itself binds the family, so demanding
        # both hashes in each other would create an impossible circular hash.
        validate_scientific_binding(root,family,h2freeze)
        pin=h2freeze.get('sequence_document',{})
        if pin.get('path')!=FAMILY_PATH or load_pinned(root,pin['path'],pin['sha256'])!=family:
            raise ValueError('H2 acquisition freeze does not pin the activated family')
        seal=load_pinned(root,attestation['raw_cohort_seal_path'],attestation['raw_cohort_seal_sha256'])
        if h2freeze.get('status')!='FROZEN' or seal.get('status')!='SEALED' or seal.get('freeze_sha256')!=h2_freeze_sha:
            raise ValueError('H2 freeze/raw cohort seal invalid')
        freeze=load_pinned(root,h1['freeze_path'],h1['freeze_sha256'])
        result=load_pinned(root,attestation['h1_result_path'],attestation['h1_result_sha256'])
        if freeze['status']!='FROZEN' or result['status']!='COMPLETED' or result['confirmatory'] is not True:
            raise ValueError('H1 not frozen/valid complete confirmation')
        if result['claim_id']!=h1['claim_id'] or result['freeze_sha256']!=h1['freeze_sha256']:
            raise ValueError('H1 result uses another protocol')
        if result.get('family_sha256')!=pin['sha256'] or result.get('family_bound_before_first_semantic_dispatch') is not True:
            raise ValueError('H1 execution did not prospectively bind this ordered family')
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
