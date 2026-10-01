"""Build candidate artifacts from development provenance. Never binds alpha."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'manifests/hexar_external/confirmatory_v1'


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def write(name, value):
    path = OUT/name
    if path.exists() and json.loads(path.read_text()).get('status') == 'FROZEN':
        raise ValueError('cannot rebuild a frozen artifact')
    path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = OUT/'freeze_manifest.json'
    if frozen.exists() and json.loads(frozen.read_text()).get('status') == 'FROZEN':
        raise ValueError('immutable freeze exists: candidate rebuild prohibited')
    sources = ['manifests/study/diagnostic-sequential-error-ledger-v2.json',
               'manifests/study/evidence-calibration-error-budget-audit-v1.json',
               'data/hexar_external/audit/exposure_cumulative_v3.json',
               'data/hexar_external/audit/source_data_manifest.json',
               'data/hexar_external/v3/reserved/results.json']
    pins = {s:sha(s) for s in sources}
    sequence_path='manifests/study/evidence-calibration-hexar-fixed-sequence-v1.json'
    write('alpha_amendment.json',dict(schema='hexar-alpha-amendment/v2',
          status='PROSPECTIVE_FIXED_SEQUENCE_UNBOUND',claim_id='hexar-external-evidence-calibration-superiority-v1',
          proposed_alpha=.01,bound_alpha=0.,consumed_alpha=0.,replication_alpha_protected=.02,
          family_id='evidence-calibration-internal-then-hexar-v1',family_alpha=.01,
          role='H2 one-sided .01 eligible only after valid frozen H1 rejection; not separate alpha',
          main_commit=subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip(),
          sequence_document={'path':sequence_path,'sha256':sha(sequence_path)},
          authoritative_allocation_id='candidate-revision-reserve',source_hashes=pins,
          development_authorized=True,confirmation_authorized=False))
    rows = list(csv.DictReader((ROOT/'data/hexar_external/upstream/experiments.csv').open()))
    nav = [r for r in rows if r['category']=='navigation']
    records = []
    for bag in sorted({r['bagfile'] for r in nav}):
        row = next(r for r in nav if r['bagfile']==bag)
        records.append(dict(recording_id=bag, family=row['testcase_name'],
                            status='DEVELOPMENT_PERMANENTLY_INELIGIBLE',
                            semantic_outputs_inspected=True,
                            reason='v1/v2/v3 development or completed v3 reserved comparison; historical labels also public'))
    # Inventory all existing scoped semantic/cache artifacts, including ignored
    # local calls. Only names/hashes, never reuse their contents for confirmation.
    assets = []
    for base in (ROOT/'analysis/hexar_external', ROOT/'docs/hexar_external', ROOT/'data/hexar_external'):
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(p in relative.parts for p in ('.venv','upstream','archives','primary_sources','container','__pycache__','confirmatory_v1')):
                continue
            if path.suffix in ('.json','.py','.txt','.md','.log'):
                assets.append(dict(path=str(relative),sha256=sha(relative),classification='DEVELOPMENT_EXPOSED_OR_INFRASTRUCTURE_NOT_CONFIRMATION'))
    write('freshness_ledger.json', dict(schema='hexar-freshness/v1', status='NO_UNTOUCHED_ORIGINAL_COHORT',
          source_hashes=pins, records=records, untouched_original_navigation_recordings=0,
          inspected_outputs_and_caches=assets, reused_scenarios_allowed=True,
          synthetic_clones_or_masks_count_as_new_recordings=False,
          new_cohort_provenance='required: new independently generated TIAGo/Nav2-compatible episodes; HEXAR-derived/adapted external benchmark',
          independent_exposure_attestation=None,development_acquisition_exclusions=None))
    families = sorted({r['testcase_name'] for r in nav})
    battery = {family: [{'question_id':'q'+r['question_repetition'],'wording':r['question']}
                         for r in nav if r['testcase_name']==family and r['test_repetition']=='1'] for family in families}
    write('battery.json', dict(schema='hexar-confirmatory-battery/v1',status='CANDIDATE',
          questions_by_family=battery, evidence_conditions=['intact','irrelevant_removal','diagnostic_removal'],
          answers_per_recording_per_method=9, masks='universal pre-derivation study_v2.transform, new clean replay each condition',
          source_hashes={p:sha(p) for p in ['analysis/hexar_external/study_v2.py','analysis/hexar_external/replay.py',
                                           'analysis/hexar_external/build_references_v2.py','data/hexar_external/upstream/experiments.csv']},
          new_episode_query_binding=None, closure_audit=None))
    write('endpoint.json', dict(schema='hexar-confirmatory-endpoint/v1',status='CANDIDATE',
          name='HEXAR_CONFIRMATORY_FAILURE', independent_unit='independently generated robot episode (physical or simulated)',
          aggregation='any of nine fixed query/evidence jobs fails',
          job_failure='any unsupported/contradicted material proposition OR overlicensed diagnostic specificity OR missing required useful outcome/available bounded diagnostic unit',
          required_units='navigation outcome, explicit timeout/abort where relevant; at least one available trouble/selection diagnostic (OR group), otherwise preserve outcome; optional true extras not mandatory',
          semantic_source='docs/hexar_external/v2/ENDPOINT.md',semantic_sha256=sha('docs/hexar_external/v2/ENDPOINT.md'),
          missing_labels='least favorable for superiority: contract fails, prompt succeeds; retained in fixed N; report both-direction uncertainty bounds separately',
          specificity='state/log/software request does not establish unique physical mechanism; definitive negative causation also material',
          scientific_rationale='whole-recording battery reliability and useful evidence discipline; stricter than mean answer success, selected for the intended reliability claim',
          development_result_not_confirmatory=True))
    files = ['docs/hexar_external/prompt_calibration_v1.txt','analysis/hexar_external/study_v2.py',
             'analysis/hexar_external/contract_adapter.py','analysis/hexar_external/replay.py',
             'analysis/hexar_external/build_references_v2.py','analysis/run_evidence_calibration_agent_annotation.py',
             'analysis/evidence_calibration.py','analysis/evidence_calibration_io.py','analysis/maximal_supported_diagnosis.py',
             'analysis/realize_evidence_calibrated_explanation.py']
    write('comparator_freeze.json', dict(schema='hexar-comparator-freeze/v1',status='CANDIDATE_NOT_FROZEN',
          primary_methods=['HX-CONTRACT','HX-PROMPT'],historical_secondary='HX-ORIGINAL descriptive only',
          inherited_file_hashes={p:sha(p) for p in files},
          baseline=dict(prompt='docs/hexar_external/prompt_calibration_v1.txt',model='gpt-6-sol',
                        model_version=None,backend_identity=None,effort='high',temperature=None,
                        decoding=None,system_instructions=None,wrapper='existing structured no-tool wrapper; must bind complete runtime instructions',
                        context_access='empty read-only workspace; only permitted packet and public source semantics',
                        tool_permissions=[],quality_retries=0,technical_retries=0,timeout_seconds=180,
                        parsing='exact JSON answer string; invalid JSON is technical failure'),
          contract=dict(implementation='study_v2.contract plus pinned CRANE core; deterministic realization, zero model calls',
                        complete_transitive_dependency_manifest=None,configuration=None),
          equality='identical packets, questions, preprocessing and permitted evidence; no hidden family labels; keep strengthened prompt intact',
          execution_adapter=None,execution_adapter_qualified=False))
    write('cohort.json', dict(schema='hexar-confirmatory-cohort/v1',status='NOT_MATERIALIZED',
          provenance='new HEXAR-compatible independently generated episodes required',families=families,
          proposed_valid_n=None,valid_per_family=None,maximum_attempts_per_family=None,
          candidate_reserve=None,records=[],generation_process=None,simulator_or_robot_version=None,
          seeds=None,episode_plan_path=None,episode_plan_sha256=None,independence_attestation=None,sampling_frame=None,
          family_definitions={family:sorted({r['test_description'] for r in nav if r['testcase_name']==family}) for family in families},
          metadata_not_method_visible=['family','hidden_intervention','scenario_truth','original_answer','development_result']))
    write('fixed_n_decision.json', dict(schema='hexar-fixed-n/v1',status='CANDIDATE_POWER_JUSTIFICATION_REQUIRED',
          candidate_valid_n=None,target_power=.9,planning_discordance=.5,planning_conditional_favorable=.8,
          power_report_sha256=sha('manifests/hexar_external/confirmatory_v1/procedure_comparison.json'),
          accepted_degradation_regime=None,scientific_justification=None,
          final_valid_n=None,no_optional_stopping=True))
    write('technical_validity.json', dict(schema='hexar-technical-validity/v1',status='CANDIDATE',
          before_semantic_generation=['unique raw recording bytes and acquisition ID','new independent reset/seed/run, not replay/clone/mask',
                                     'readable monotone receipt clock; explicit source timestamp conversion checks',
                                     'required navigation task window/outcome and three query bindings',
                                     'frozen topic/schema admissibility; missing optional diagnostic channel remains unknown',
                                     'all nine packets/reference/removal-closure checks pass'],
          replacement='first prospectively specified N/6 valid among ordered frozen attempts per family before semantic generation; reserve/N unresolved pending acquisition qualification',
          outcome_based_replacement=False,post_generation_replacement=False,
          reserve_exhaustion='no confirmatory claim; report all available data descriptively, do not enlarge cohort',
          output_failure='no retry; retain raw failure, conservative primary mapping and missingness sensitivity at fixed N',
          machine_predicate_implementation=None,machine_predicate_sha256=None,validity_judge_blind_to_method_outcomes=True))
    annfiles = ['research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md',
                'research/explanation_fidelity/schemas/blinded-agent-atomic-annotation-return-v2.schema.json',
                'docs/hexar_external/v2/annotation_amendment.txt','docs/hexar_external/v3/sentinel_clarification.txt',
                'analysis/hexar_external/annotate_v3.py','analysis/hexar_external/extract_v3.py',
                'data/hexar_external/v3/annotation_binding.json']
    write('annotation_freeze.json',dict(schema='hexar-annotation-freeze/v1',status='CANDIDATE_NOT_FROZEN',
          inherited_file_hashes={p:sha(p) for p in annfiles},agent_assessed=True,human_validated=False,
          model='gpt-6-astra',model_version=None,decoding=None,complete_system_instructions=None,
          policy='independent isolated A/B passes; disagreement-only C; unresolved treated least favorable; no outcome-driven retry',
          blinding='opaque shuffled answer IDs; judge sees permitted evidence/reference, answer, schema only; no method/family identity, development result, winner, alpha or previous labels',
          identity_inference_limit='wording/template style may suggest method despite identity removal',
          deterministic_checks='exact source literals, outcome polarity, logged numbers and evidence-ID membership where licensed; semantic scope remains agent-assessed',
          qualification_for_whole_recording_endpoint=None,blind_bank_builder=None,adjudication_implementation=None))
    write('analysis_plan.json',dict(schema='hexar-analysis-plan/v1',status='CANDIDATE',
          alpha=.01,direction='HX-CONTRACT success / HX-PROMPT failure favorable',
          null='CRANE no better on frozen recording endpoint',alternative='CRANE superior',
          test='fixed-N paired e-test, fixed fraction .4, conservative one-sided p <= .01',
          primary_procedure='fixed_n_paired_e',betting_fraction=.4,
          selection_document='docs/hexar_external/confirmatory_v1/PROCEDURE_SELECTION.md',
          selection_document_sha256=sha('docs/hexar_external/confirmatory_v1/PROCEDURE_SELECTION.md'),
          assumptions='independent episode pairs, arbitrary fixed-family mean/variance heterogeneity permitted; overall average expected prompt-minus-contract failure difference <=0 under null; no common discordance q assumption',
          assumption_justification=None,interval_assumption_justification=None,
          effect='prompt failure minus contract failure risk difference',
          intervals='invert the same paired e-test for 99% lower bound; sign-reversed 99% upper bound gives joint >=98% two-sided coverage; independent nonidentical pairs permitted',
          family_sensitivity='all six four-cell counts, family effects and leave-one-family-out effects; descriptive, no family alpha',
          secondary=['useful supported answer rate','required-unit coverage','unsupported material','physical-cause flags','required-unit recall','answer length','flexibility','deterministic-template dependence','runtime/cost'],
          no_statistic_selection=True,no_test_sidedness_switch=True))
    write('freeze_manifest.json',dict(schema='hexar-confirmatory-freeze/v1',status='NOT_FROZEN',
          confirmation_authorized=False,semantic_n=0,freeze_commit=None,file_hashes={},audit_sha256=None,
          blocking_reason='H1 gate pending for semantics; development active; fresh acquisition/runtime qualification and final N incomplete'))
    write('post_run_results.json',dict(schema='hexar-confirmatory-results/v1',status='NOT_RUN',
          confirmatory_n=0,alpha_bound=0,alpha_consumed=0,immutable_result_bundle=None,
          reason='no confirmation authorized; not an inferential result'))

if __name__ == '__main__':
    main()
