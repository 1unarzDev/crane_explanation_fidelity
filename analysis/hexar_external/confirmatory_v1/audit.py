"""Fail-closed pre-confirmation audit. Does not allocate or generate outputs."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'manifests/hexar_external/confirmatory_v1'
CLAIM = 'hexar-external-evidence-calibration-superiority-v1'
REQUIRED = {
    'alpha_amendment.json': ['sequence_document','authoritative_allocation_id'],
    'freshness_ledger.json': ['independent_exposure_attestation','development_acquisition_exclusions'],
    'battery.json': ['new_episode_query_binding','closure_audit'],
    'endpoint.json': ['name','aggregation','required_units','missing_labels'],
    'comparator_freeze.json': ['baseline.model_version','baseline.backend_identity','baseline.temperature',
        'baseline.decoding','baseline.system_instructions','contract.complete_transitive_dependency_manifest',
        'contract.configuration','execution_adapter'],
    'cohort.json': ['records','generation_process','simulator_or_robot_version','seeds','independence_attestation','sampling_frame','episode_plan_path','episode_plan_sha256'],
    'fixed_n_decision.json': ['accepted_degradation_regime','scientific_justification','final_valid_n'],
    'technical_validity.json': ['machine_predicate_implementation','machine_predicate_sha256'],
    'annotation_freeze.json': ['model_version','decoding','complete_system_instructions',
        'qualification_for_whole_recording_endpoint','blind_bank_builder','adjudication_implementation'],
    'analysis_plan.json': ['assumption_justification','interval_assumption_justification'],
}

REQUIRED_TOP_KEYS = {'alpha_amendment.json': ['schema','status','claim_id','proposed_alpha','bound_alpha','consumed_alpha','replication_alpha_protected','family_id','family_alpha','role','main_commit','sequence_document','authoritative_allocation_id','source_hashes','development_authorized','confirmation_authorized'],
 'freshness_ledger.json': ['schema',
                           'status',
                           'source_hashes',
                           'records',
                           'untouched_original_navigation_recordings',
                           'inspected_outputs_and_caches',
                           'reused_scenarios_allowed',
                           'synthetic_clones_or_masks_count_as_new_recordings',
                           'new_cohort_provenance',
                           'independent_exposure_attestation'],
 'battery.json': ['schema',
                  'status',
                  'questions_by_family',
                  'evidence_conditions',
                  'answers_per_recording_per_method',
                  'masks',
                  'source_hashes',
                  'new_episode_query_binding',
                  'closure_audit'],
 'endpoint.json': ['schema',
                   'status',
                   'name',
                   'independent_unit',
                   'aggregation',
                   'job_failure',
                   'required_units',
                   'semantic_source',
                   'semantic_sha256',
                   'missing_labels',
                   'specificity',
                   'scientific_rationale',
                   'development_result_not_confirmatory'],
 'comparator_freeze.json': ['schema',
                            'status',
                            'primary_methods',
                            'historical_secondary',
                            'inherited_file_hashes',
                            'baseline',
                            'contract',
                            'equality',
                            'execution_adapter',
                            'execution_adapter_qualified'],
 'cohort.json': ['schema',
                 'status',
                 'provenance',
                 'families',
                 'proposed_valid_n',
                 'valid_per_family',
                 'maximum_attempts_per_family',
                 'candidate_reserve',
                 'records',
                 'generation_process',
                 'simulator_or_robot_version',
                 'seeds',
                 'independence_attestation',
                 'sampling_frame',
                 'family_definitions',
                 'metadata_not_method_visible'],
 'fixed_n_decision.json': ['schema',
                           'status',
                           'candidate_valid_n',
                           'target_power',
                           'planning_discordance',
                           'planning_conditional_favorable',
                           'power_report_sha256',
                           'accepted_degradation_regime',
                           'scientific_justification',
                           'final_valid_n',
                           'no_optional_stopping'],
 'technical_validity.json': ['schema',
                             'status',
                             'before_semantic_generation',
                             'replacement',
                             'outcome_based_replacement',
                             'post_generation_replacement',
                             'reserve_exhaustion',
                             'output_failure',
                             'machine_predicate_implementation',
                             'validity_judge_blind_to_method_outcomes'],
 'annotation_freeze.json': ['schema',
                            'status',
                            'inherited_file_hashes',
                            'agent_assessed',
                            'human_validated',
                            'model',
                            'model_version',
                            'decoding',
                            'complete_system_instructions',
                            'policy',
                            'blinding',
                            'identity_inference_limit',
                            'deterministic_checks',
                            'qualification_for_whole_recording_endpoint',
                            'blind_bank_builder',
                            'adjudication_implementation'],
 'analysis_plan.json': ['schema',
                        'status',
                        'alpha',
                        'direction',
                        'null',
                        'alternative',
                        'test',
                        'assumptions',
                        'assumption_justification',
                        'interval_assumption_justification',
                        'effect',
                        'intervals',
                        'family_sensitivity',
                        'secondary',
                        'no_statistic_selection',
                        'no_test_sidedness_switch']}

REQUIRED_NESTED_KEYS = {'comparator_freeze.json': {'baseline': ['prompt',
                                         'model',
                                         'model_version',
                                         'backend_identity',
                                         'effort',
                                         'temperature',
                                         'decoding',
                                         'system_instructions',
                                         'wrapper',
                                         'context_access',
                                         'tool_permissions',
                                         'quality_retries',
                                         'technical_retries',
                                         'timeout_seconds',
                                         'parsing'],
                            'contract': ['implementation',
                                         'complete_transitive_dependency_manifest',
                                         'configuration']}}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member(data, dotted):
    for key in dotted.split('.'):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def acquisition_file_hashes(base,root,scientific_binding):
    """Seal full scientific/runtime closure; later activation and raw seal are separate."""
    excluded={'freeze_manifest.json','post_run_results.json','h1_gate_attestation.json','raw_cohort_seal.json'}
    files={str(p.relative_to(root)):digest(p) for p in sorted(base.glob('*.json')) if p.name not in excluded}
    for path,expected in scientific_binding['files'].items():
        if digest(root/path)!=expected:
            raise ValueError('scientific file changed before acquisition freeze: '+path)
        files[path]=expected
    return files


def audit(base=BASE, root=ROOT, stage="semantic"):
    if stage not in ("acquisition", "semantic"):
        raise ValueError("unknown admission stage")
    errors, docs = [], {}
    for name, fields in REQUIRED.items():
        try:
            data = json.loads((base/name).read_text())
            if not isinstance(data, dict):
                raise ValueError('artifact must be an object')
            docs[name] = data
        except (OSError, ValueError) as exc:
            errors.append(f'{name}: missing/invalid artifact: {exc}')
            continue
        for key in REQUIRED_TOP_KEYS[name]:
            if key not in data:
                errors.append(f'{name}: missing required field {key}')
        for parent, keys in REQUIRED_NESTED_KEYS.get(name, {}).items():
            for key in keys:
                value = member(data, parent+'.'+key)
                if value is None or value == '' or value == {} or (value == [] and key != 'tool_permissions'):
                    errors.append(f'{name}: missing required nested {parent}.{key}')
        for key, value in data.items():
            if name=='cohort.json' and key=='records':
                continue
            if value is None or value == '' or value == [] or value == {}:
                errors.append(f'{name}: empty required field {key}')
        if data.get('status') != 'READY_FOR_FREEZE':
            errors.append(f'{name}: status not READY_FOR_FREEZE ({data.get("status")})')
        for field in fields:
            if name=='cohort.json' and field=='records':
                continue
            value = member(data, field)
            if value is None or value == '' or value == [] or value == {}:
                errors.append(f'{name}: missing required {field}')
        for collection in ('source_hashes','inherited_file_hashes'):
            for path, expected in data.get(collection, {}).items():
                try:
                    # A consumed H1 legitimately updates the allocation ledger
                    # after acquisition freeze. Preserve the original audit
                    # snapshot while validating the live ledger/gate below.
                    if stage=='semantic' and path=='manifests/study/diagnostic-sequential-error-ledger-v2.json':
                        main_commit=json.loads((base/'alpha_amendment.json').read_text())['main_commit']
                        historical=subprocess.check_output(['git','show',main_commit+':'+path],cwd=root)
                        actual=hashlib.sha256(historical).hexdigest()
                    else:
                        actual=digest(root/path)
                    if actual != expected:
                        errors.append(f'{name}: changed source {path}')
                except (OSError,KeyError,ValueError,subprocess.CalledProcessError):
                    errors.append(f'{name}: missing pinned source {path}')
    alpha = docs.get('alpha_amendment.json', {})
    try:
        shared_commit = subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()
        shared_ledger = subprocess.check_output(['git','show','main:manifests/study/diagnostic-sequential-error-ledger-v2.json'],cwd=root)
        local_ledger = (root/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_bytes()
        if (stage=='acquisition' and shared_commit != alpha.get('main_commit')) or shared_ledger != local_ledger:
            errors.append('alpha: shared main ledger/state diverged; reconcile explicitly before freeze')
    except (OSError, subprocess.CalledProcessError):
        errors.append('alpha: latest shared ledger/state could not be verified')
    try:
        from analysis.hexar_external.confirmatory_v1.gatekeeping import load_pinned, validate_family, validate_scientific_binding, activation_errors
        ledger=json.loads((root/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_text())
        pin=alpha['sequence_document']
        family=validate_family(load_pinned(root,pin['path'],pin['sha256']),ledger)
        if family.get('status')=='FROZEN':
            validate_scientific_binding(root,family)
        if stage=='semantic':
            shared_family=subprocess.check_output(['git','show','main:'+pin['path']],cwd=root,stderr=subprocess.DEVNULL)
            if hashlib.sha256(shared_family).hexdigest()!=pin['sha256']:
                errors.append('family amendment not reconciled with authoritative main')
            attestation=json.loads((base/'h1_gate_attestation.json').read_text())
            if attestation.get('h2_freeze_path')!=str((base/'freeze_manifest.json').relative_to(root)) or attestation.get('raw_cohort_seal_path')!=str((base/'raw_cohort_seal.json').relative_to(root)):
                errors.append('alpha/gate: activation points to another acquisition freeze or raw seal')
            errors.extend(activation_errors(root,family,attestation))
        # Acquisition freeze requires a predeclared order, not an H1 outcome.
        # Final combined family binding still precedes H1 semantic confirmation.
    except (OSError,ValueError,KeyError,TypeError,StopIteration,subprocess.CalledProcessError) as exc:
        errors.append('alpha/gate: '+str(exc))
    freshness = docs.get('freshness_ledger.json', {})
    exposed = {r['recording_id'] for r in freshness.get('records', []) if r.get('semantic_outputs_inspected')}
    original_split = json.loads((root/'data/hexar_external/audit/split.json').read_text())
    exposed.update(original_split['development'] + original_split['reserved'])
    original_raw_hashes = {r['sha256'] for r in json.loads((root/'data/hexar_external/audit/source_data_manifest.json').read_text())['files'] if 'bagfiles/' in r['path']}
    dev_ids,dev_seeds=set(),set()
    try:
        from analysis.hexar_external.confirmatory_v1.development_exposure import load_exclusions
        dev_hashes,dev_ids,dev_seeds=load_exclusions(root,freshness['development_acquisition_exclusions'],require_current=True)
        original_raw_hashes.update(dev_hashes)
    except (OSError,KeyError,TypeError,ValueError) as exc:
        errors.append('freshness: development acquisition exclusion inventory missing/invalid: '+str(exc))
    cohort = docs.get('cohort.json', {})
    records = cohort.get('records', [])
    if stage=='semantic':
        try:
            seal=json.loads((base/'raw_cohort_seal.json').read_text())
            freeze_path=base/'freeze_manifest.json'
            if seal['status']!='SEALED' or seal['freeze_sha256']!=digest(freeze_path) or seal['semantic_outputs_generated'] is not False:
                raise ValueError('invalid raw cohort seal')
            records=seal['records']
        except (OSError,KeyError,ValueError) as exc:
            errors.append('cohort seal: '+str(exc))
    fixed = docs.get('fixed_n_decision.json', {})
    n = fixed.get('final_valid_n')
    if type(n) is not int or n <= 0 or n % 6:
        errors.append('cohort: final N must be a positive multiple of six')
    elif stage=='semantic' and len(records) != n:
        errors.append('cohort: selected recording count differs from fixed N')
    families = cohort.get('families', [])
    if set(families) != {'charging','dynamic_env','localization','manual_joystick','obstacle','success'}:
        errors.append('cohort: six original families required')
    if stage=='semantic' and isinstance(n, int) and n > 0:
        for family in families:
            if sum(r.get('family')==family for r in records) != n//6:
                errors.append(f'cohort: unbalanced {family}')
    ids, hashes, acquisitions, seeds = set(), set(), set(), set()
    for record in records:
        for key, values in [('recording_id',ids),('raw_sha256',hashes),('acquisition_id',acquisitions),('seed',seeds)]:
            value = record.get(key)
            if value is None or value in values:
                errors.append(f'cohort: missing/duplicate {key}')
            values.add(value)
        if record.get('raw_sha256') in original_raw_hashes:
            errors.append('cohort: reused development recording bytes')
        if record.get('acquisition_id') in dev_ids or record.get('seed') in dev_seeds:
            errors.append('cohort: reused development acquisition identity/seed')
        if record.get('recording_id') in exposed or record.get('semantic_outputs_inspected') is not False:
            errors.append('cohort: exposed or exposure status unknown')
        if record.get('technical_valid') is not True or record.get('independent_reset') is not True:
            errors.append('cohort: validity/independent reset not established')
        try:
            if digest(root/record['raw_path']) != record['raw_sha256']:
                errors.append('cohort: raw hash mismatch')
        except (OSError, KeyError, TypeError):
            errors.append('cohort: missing raw recording')
    battery = docs.get('battery.json', {})
    if battery.get('evidence_conditions') != ['intact','irrelevant_removal','diagnostic_removal'] or battery.get('answers_per_recording_per_method') != 9:
        errors.append('battery: fixed nine-job conditions missing/changed')
    for family in families:
        qs = battery.get('questions_by_family', {}).get(family, [])
        if len(qs) != 3 or {q.get('question_id') for q in qs} != {'q1','q2','q3'} or any(not q.get('wording') for q in qs):
            errors.append('battery: three frozen query wordings missing for '+family)
    comparator = docs.get('comparator_freeze.json', {})
    if comparator.get('execution_adapter_qualified') is not True:
        errors.append('execution: no qualified confirmatory exactly-once adapter')
    for method in ('baseline',):
        config = comparator.get(method, {})
        if config.get('quality_retries') != 0 or config.get('technical_retries') != 0 or config.get('tool_permissions') != []:
            errors.append('execution: retry/tool policy changed')
    policy = docs.get('technical_validity.json', {})
    if policy.get('outcome_based_replacement') is not False or policy.get('post_generation_replacement') is not False:
        errors.append('validity: outcome-driven/post-generation replacement forbidden')
    plan = docs.get('analysis_plan.json', {})
    if plan.get('no_statistic_selection') is not True or plan.get('no_test_sidedness_switch') is not True:
        errors.append('analysis: test-selection/sidedness prohibition missing')
    if plan.get('alpha') != .01:
        errors.append('analysis: alpha/sidedness not prospectively .01')
    if fixed.get('no_optional_stopping') is not True:
        errors.append('analysis: fixed-N stopping policy missing')
    # A plan's content hashes must cover every runtime dependency, not just the
    # inherited development files. It is separate from the candidate manifest.
    try:
        deps = json.loads((base/'runtime_dependencies.json').read_text())
        if not deps.get('files') or deps.get('complete_transitive_closure') is not True:
            errors.append('runtime: transitive closure not attested')
        for file, expected in deps.get('files', {}).items():
            if digest(root/file) != expected:
                errors.append(f'runtime: changed dependency {file}')
    except (OSError, ValueError, KeyError):
        errors.append('runtime: complete dependency manifest missing/invalid')
    return dict(schema='hexar-preconfirmation-audit/v1',passed=not errors,
                stage=stage,acquisition_authorized=not errors,
                confirmation_authorized=not errors and stage=='semantic',development_authorized=True,errors=errors,
                bound_by_audit=0,consumed_by_audit=0,semantic_outputs_generated=0,
                checked_hashes={p.name:digest(p) for p in sorted(base.glob('*.json'))
                                if p.name not in ('preconfirmation_audit.json','freeze_manifest.json','post_run_results.json')})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--stage',choices=['acquisition','semantic'],default='semantic')
    args = parser.parse_args()
    result = audit(stage=args.stage)
    path = BASE/'preconfirmation_audit.json'
    if (BASE/'freeze_manifest.json').exists() and json.loads((BASE/'freeze_manifest.json').read_text()).get('status') == 'FROZEN':
        raise SystemExit('immutable freeze exists; use execution verification, never overwrite audit')
    path.write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:
        print(json.dumps({'status':'BLOCKED','errors':result['errors']},indent=2))
        raise SystemExit(1)
    if args.freeze:
        pin=json.loads((BASE/'alpha_amendment.json').read_text())['sequence_document']
        from analysis.hexar_external.confirmatory_v1.gatekeeping import load_pinned, validate_scientific_binding
        family=load_pinned(ROOT,pin['path'],pin['sha256'])
        if family.get('status')!='FROZEN' or family.get('bound_alpha')!=.01:
            raise SystemExit('acquisition freeze requires the already-bound frozen family')
        scientific_binding=validate_scientific_binding(ROOT,family)
        shared=subprocess.check_output(['git','show','main:'+pin['path']],cwd=ROOT,stderr=subprocess.DEVNULL)
        if hashlib.sha256(shared).hexdigest()!=pin['sha256']:
            raise SystemExit('reconcile ordered-family amendment with main before freeze')
    if args.freeze and args.stage=='semantic':
        raise SystemExit('semantic admission cannot rewrite acquisition freeze; use hash-bound H1 gate attestation')
    if args.freeze:
        file_hashes=acquisition_file_hashes(BASE,ROOT,scientific_binding)
        file_hashes[pin['path']]=pin['sha256']
        h2_binding=family['sequence'][1]
        file_hashes[h2_binding['protocol_binding_path']]=h2_binding['protocol_binding_sha256']
        manifest = dict(schema='hexar-confirmatory-freeze/v1',status='FROZEN',confirmation_authorized=False,acquisition_authorized=True,
                        semantic_n=0,audit_sha256=digest(path),
                        sequence_document=pin,
                        file_hashes=file_hashes,
                        commit_requirement='commit all listed files and manifest before generation; verifier checks committed bytes')
        # Existing candidate is a plan placeholder, never an executed freeze.
        (BASE/'freeze_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS; commit complete freeze before generation')

if __name__ == '__main__':
    main()
