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
    'alpha_amendment.json': ['resolution_document','authoritative_allocation_id'],
    'freshness_ledger.json': ['independent_exposure_attestation'],
    'battery.json': ['new_episode_query_binding','closure_audit'],
    'endpoint.json': ['name','aggregation','required_units','missing_labels'],
    'comparator_freeze.json': ['baseline.model_version','baseline.backend_identity','baseline.temperature',
        'baseline.decoding','baseline.system_instructions','contract.complete_transitive_dependency_manifest',
        'contract.configuration','execution_adapter'],
    'cohort.json': ['records','generation_process','simulator_or_robot_version','seeds','independence_attestation','sampling_frame'],
    'fixed_n_decision.json': ['accepted_degradation_regime','scientific_justification','final_valid_n'],
    'technical_validity.json': ['machine_predicate_implementation'],
    'annotation_freeze.json': ['model_version','decoding','complete_system_instructions',
        'qualification_for_whole_recording_endpoint','blind_bank_builder','adjudication_implementation'],
    'analysis_plan.json': ['assumption_justification','interval_assumption_justification'],
}

REQUIRED_TOP_KEYS = {'alpha_amendment.json': ['schema',
                          'status',
                          'claim_id',
                          'proposed_alpha',
                          'bound_alpha',
                          'consumed_alpha',
                          'replication_alpha_protected',
                          'competing_claim',
                          'main_commit',
                          'resolution_document',
                          'authoritative_allocation_id',
                          'source_hashes'],
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


def audit(base=BASE, root=ROOT):
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
            if value is None or value == '' or value == [] or value == {}:
                errors.append(f'{name}: empty required field {key}')
        if data.get('status') != 'READY_FOR_FREEZE':
            errors.append(f'{name}: status not READY_FOR_FREEZE ({data.get("status")})')
        for field in fields:
            value = member(data, field)
            if value is None or value == '' or value == [] or value == {}:
                errors.append(f'{name}: missing required {field}')
        for collection in ('source_hashes','inherited_file_hashes'):
            for path, expected in data.get(collection, {}).items():
                try:
                    if digest(root/path) != expected:
                        errors.append(f'{name}: changed source {path}')
                except OSError:
                    errors.append(f'{name}: missing pinned source {path}')
    alpha = docs.get('alpha_amendment.json', {})
    try:
        shared_commit = subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()
        shared_ledger = subprocess.check_output(['git','show','main:manifests/study/diagnostic-sequential-error-ledger-v2.json'],cwd=root)
        local_ledger = (root/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_bytes()
        if shared_commit != alpha.get('main_commit') or shared_ledger != local_ledger:
            errors.append('alpha: shared main ledger/state diverged; reconcile explicitly before freeze')
    except (OSError, subprocess.CalledProcessError):
        errors.append('alpha: latest shared ledger/state could not be verified')
    if alpha.get('bound_alpha') != .01 or alpha.get('consumed_alpha') != 0 or alpha.get('replication_alpha_protected') != .02:
        errors.append('alpha: external .01 not prospectively bound, or protected budget changed')
    try:
        ledger = json.loads((root/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_text())
        allocation = next(a for a in ledger['allocations'] if a['allocation_id']==alpha.get('authoritative_allocation_id'))
        if allocation.get('campaign_id') != CLAIM or allocation.get('alpha') != .01 or allocation.get('status') != 'BOUND':
            errors.append('alpha: authoritative allocation belongs to another claim or is not bound')
        if ledger['program_alpha'] != .05 or sum(a['alpha'] for a in ledger['allocations']) > .05:
            errors.append('alpha: invalid cumulative budget')
        rep = next(a for a in ledger['allocations'] if a['allocation_id']=='selected-method-replication')
        if rep['alpha'] != .02 or rep.get('campaign_id') == CLAIM:
            errors.append('alpha: replication reserve borrowed')
        resolution = alpha['resolution_document']
        path = root/resolution['path']
        if digest(path) != resolution['sha256']:
            errors.append('alpha: resolution hash mismatch')
        if json.loads(path.read_text()).get('status') != 'MAIN_CLAIM_COMPLETED_OR_RETIRED_WITH_RESERVE_RELEASED':
            errors.append('alpha: main B2/B4 claim not explicitly resolved')
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        errors.append('alpha: ledger/resolution does not establish unique available external allocation')
    freshness = docs.get('freshness_ledger.json', {})
    exposed = {r['recording_id'] for r in freshness.get('records', []) if r.get('semantic_outputs_inspected')}
    original_split = json.loads((root/'data/hexar_external/audit/split.json').read_text())
    exposed.update(original_split['development'] + original_split['reserved'])
    original_raw_hashes = {r['sha256'] for r in json.loads((root/'data/hexar_external/audit/source_data_manifest.json').read_text())['files'] if 'bagfiles/' in r['path']}
    cohort = docs.get('cohort.json', {})
    records = cohort.get('records', [])
    fixed = docs.get('fixed_n_decision.json', {})
    n = fixed.get('final_valid_n')
    if type(n) is not int or n <= 0 or n % 6:
        errors.append('cohort: final N must be a positive multiple of six')
    elif len(records) != n:
        errors.append('cohort: selected recording count differs from fixed N')
    families = cohort.get('families', [])
    if set(families) != {'charging','dynamic_env','localization','manual_joystick','obstacle','success'}:
        errors.append('cohort: six original families required')
    if isinstance(n, int) and n > 0:
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
            errors.append('cohort: reused original recording bytes')
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
                confirmation_authorized=not errors,errors=errors,
                bound_by_audit=0,consumed_by_audit=0,semantic_outputs_generated=0,
                checked_hashes={p.name:digest(p) for p in sorted(base.glob('*.json'))
                                if p.name not in ('preconfirmation_audit.json','freeze_manifest.json','post_run_results.json')})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    result = audit()
    path = BASE/'preconfirmation_audit.json'
    if (BASE/'freeze_manifest.json').exists() and json.loads((BASE/'freeze_manifest.json').read_text()).get('status') == 'FROZEN':
        raise SystemExit('immutable freeze exists; use execution verification, never overwrite audit')
    path.write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:
        print(json.dumps({'status':'BLOCKED','errors':result['errors']},indent=2))
        raise SystemExit(1)
    if args.freeze:
        manifest = dict(schema='hexar-confirmatory-freeze/v1',status='FROZEN',confirmation_authorized=True,
                        semantic_n=0,audit_sha256=digest(path),
                        file_hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(BASE.glob('*.json'))
                                     if p.name not in ('freeze_manifest.json','post_run_results.json')},
                        commit_requirement='commit all listed files and manifest before generation; verifier checks committed bytes')
        # Existing candidate is a plan placeholder, never an executed freeze.
        (BASE/'freeze_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS; commit complete freeze before generation')

if __name__ == '__main__':
    main()
