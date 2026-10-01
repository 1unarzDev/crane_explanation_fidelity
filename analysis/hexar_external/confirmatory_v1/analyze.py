"""Frozen fixed-N analysis. Refuses development data or uncommitted freezes."""
import argparse
import json
import subprocess
from pathlib import Path
try:
    from .audit import BASE, ROOT, CLAIM, digest
    from .statistics import summary, cp_bounds
    from .heterogeneous_statistics import summarize as e_summary
    from .mixture_statistics import summary as mixture_summary
except ImportError:
    from audit import BASE, ROOT, CLAIM, digest
    from statistics import summary, cp_bounds
    from analysis.hexar_external.confirmatory_v1.heterogeneous_statistics import summarize as e_summary
    from analysis.hexar_external.confirmatory_v1.mixture_statistics import summary as mixture_summary

METHODS = ('HX-CONTRACT', 'HX-PROMPT')


def committed(path):
    relative = str(path.relative_to(ROOT))
    try:
        return subprocess.check_output(['git','show',f'HEAD:{relative}'],cwd=ROOT,stderr=subprocess.DEVNULL) == path.read_bytes()
    except subprocess.CalledProcessError:
        return False


def verify_freeze():
    freeze = json.loads((BASE/'freeze_manifest.json').read_text())
    if freeze.get('status') != 'FROZEN' or freeze.get('acquisition_authorized') is not True:
        raise ValueError('no authorized confirmatory freeze')
    if not committed(BASE/'freeze_manifest.json'):
        raise ValueError('freeze must be committed before generation')
    for file, expected in freeze['file_hashes'].items():
        path = ROOT/file
        if digest(path) != expected or not committed(path):
            raise ValueError('uncommitted or changed frozen file: '+file)
    deps = json.loads((BASE/'runtime_dependencies.json').read_text())
    for file, expected in deps['files'].items():
        if digest(ROOT/file) != expected or not committed(ROOT/file):
            raise ValueError('runtime changed: '+file)
    from analysis.hexar_external.confirmatory_v1.gatekeeping import load_pinned, validate_family, activation_errors
    alpha=json.loads((BASE/'alpha_amendment.json').read_text())
    pin=alpha['sequence_document']
    ledger=json.loads((ROOT/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_text())
    family=validate_family(load_pinned(ROOT,pin['path'],pin['sha256']),ledger)
    attestation=json.loads((BASE/'h1_gate_attestation.json').read_text())
    if attestation.get('h2_freeze_path')!=str((BASE/'freeze_manifest.json').relative_to(ROOT)) or attestation.get('raw_cohort_seal_path')!=str((BASE/'raw_cohort_seal.json').relative_to(ROOT)):
        raise ValueError('activation refers to another acquisition freeze or raw cohort path')
    if freeze.get('sequence_document')!=pin:
        raise ValueError('acquisition freeze and alpha amendment pin different families')
    if attestation.get('h2_freeze_sha256')!=digest(BASE/'freeze_manifest.json'):
        raise ValueError('activation refers to another H2 freeze')
    errors=activation_errors(ROOT,family,attestation)
    if errors:raise ValueError('; '.join(errors))
    return freeze


def analyze(bundle, cohort, battery, freeze_sha256, plan=None):
    if bundle.get('claim_id') != CLAIM or bundle.get('freeze_sha256') != freeze_sha256:
        raise ValueError('wrong claim or freeze; development cannot enter confirmation')
    if bundle.get('blind_scoring_complete') is not True or bundle.get('agent_assessed') is not True:
        raise ValueError('scoring disposition not closed')
    if bundle.get('semantic_generation_after_committed_freeze') is not True:
        raise ValueError('generation chronology not established')
    records = cohort['records']
    byid = {r['recording_id']:r for r in records}
    if len(byid) != len(records):
        raise ValueError('duplicate physical recordings')
    expected = {(r['recording_id'],m,q['question_id'],c)
                for r in records for m in METHODS
                for q in battery['questions_by_family'][r['family']]
                for c in battery['evidence_conditions']}
    if 'unique_request_policy' in battery:
        from analysis.hexar_external.confirmatory_v1.unique_analysis_binding import verify
        verify(bundle,expected,freeze_sha256)
    jobs = {}
    for job in bundle['jobs']:
        key = (job['recording_id'],job['method'],job['question_id'],job['condition'])
        if key not in expected or key in jobs or type(job.get('attempt_count')) is not int or job['attempt_count'] != 1:
            raise ValueError('extra/duplicate job or retry')
        if job.get('blind_disposition_closed') is not True:
            raise ValueError('unclosed blinded scoring disposition')
        for field in ('unsupported_material','overlicensed_specificity','missing_required_unit'):
            if field not in job:
                raise ValueError('every endpoint component requires an explicit disposition')
            if job.get(field) is not None and type(job[field]) is not bool:
                raise ValueError('endpoint components must be bool or unresolved null')
        if 'response_sha256' not in job or 'scoring_artifact_sha256' not in job:
            raise ValueError('job provenance missing')
        jobs[key] = job
    if set(jobs) != expected:
        raise ValueError('incomplete scheduled jobs; represent every technical failure explicitly')
    cells, family_cells, unresolved, endpoints = [0]*4, {}, 0, []
    unidentified_endpoints = 0
    risk_difference_bounds = [0., 0.]
    for rid, record in byid.items():
        failures, failure_bounds = {}, {}
        for method in METHODS:
            method_jobs = [v for k,v in jobs.items() if k[0]==rid and k[1]==method]
            if len(method_jobs) != 9:
                raise ValueError('nine frozen battery jobs per method/recording required')
            components = [j.get(f) for j in method_jobs for f in
                          ('unsupported_material','overlicensed_specificity','missing_required_unit')]
            missing = any(x is None for x in components)
            if missing:
                unresolved += 1
            if any(x is True for x in components):
                failure_bounds[method] = (True, True)
            elif missing:
                failure_bounds[method] = (False, True)
            else:
                failure_bounds[method] = (False, False)
            unidentified_endpoints += failure_bounds[method][0] != failure_bounds[method][1]
            failures[method] = failure_bounds[method][1 if method=='HX-CONTRACT' else 0]
        cl, cu = failure_bounds['HX-CONTRACT']
        pl, pu = failure_bounds['HX-PROMPT']
        risk_difference_bounds[0] += (int(pl)-int(cu))/len(records)
        risk_difference_bounds[1] += (int(pu)-int(cl))/len(records)
        cf, pf = failures['HX-CONTRACT'], failures['HX-PROMPT']
        cell = 0 if not cf and pf else 1 if cf and not pf else 2 if not cf and not pf else 3
        cells[cell] += 1
        family = record['family']
        family_cells.setdefault(family,[0]*4)[cell] += 1
        endpoints.append(dict(recording_id=rid,family=family,contract_failure=cf,prompt_failure=pf,
                              observed_contract_failure_bounds=list(failure_bounds['HX-CONTRACT']),
                              observed_prompt_failure_bounds=list(failure_bounds['HX-PROMPT'])))
    if plan is None:
        # Historical offline design path. Terminal CLI always supplies its
        # frozen plan and never calculates a second primary test alongside it.
        overall = summary(*cells)
        lower, upper = 0., 0.
        for counts in family_cells.values():
            n = sum(counts)
            fl, fu = cp_bounds(counts[0],n,.005/len(family_cells))
            ul, uu = cp_bounds(counts[1],n,.005/len(family_cells))
            lower += n/len(records)*(fl-uu)
            upper += n/len(records)*(fu-ul)
        overall.update(one_sided_99_lower_bound=lower,two_sided_98_interval=[lower,upper],
                       interval_method='stratified Bonferroni marginal exact binomial; >=99% lower / >=98% symmetric coverage; IID within family; not test inversion')
    else:
        if plan.get('primary_procedure')=='fixed_n_uniform_paired_mixture':
            support=plan.get('mixture_support')
            if (plan.get('alpha')!=.01 or plan.get('mixture_density')!='uniform'
                    or type(support) is not list or support!=[0,1]
                    or any(type(x) not in (int,float) for x in support) or 'betting_fraction' in plan):
                raise ValueError('uniform mixture configuration must be prospectively fixed')
            f,u,ss,ff=cells;n=sum(cells)
            value=mixture_summary(f,u,n)
            overall=dict(value,procedure='fixed_n_uniform_paired_mixture',
                both_success=ss,both_failure=ff,contract_failure_rate=(u+ff)/n,
                prompt_failure_rate=(f+ff)/n,
                prompt_minus_contract_failure_risk_difference=(f-u)/n,
                conservative_one_sided_p=value['one_sided_p_value'],
                one_sided_99_lower_bound=value['one_sided_lower'],
                two_sided_98_interval=value['two_sided_interval'],
                interval_method='inversion of the same uniform paired mixture; directed decimal bounds; independent nonidentical pairs')
        elif plan.get('primary_procedure')=='fixed_n_paired_e' and plan.get('betting_fraction')==.4:
            overall=e_summary(*cells,fraction=plan['betting_fraction'])
        else:
            raise ValueError('unrecognized frozen primary procedure; no post-run test selection')
    overall.update(
        effect_and_failure_rate_scope='least-favorable mapped agent-assessed endpoint',
        symmetric_interval_target='population effect of the least-favorable mapped endpoint; not latent complete-label effect',
        lower_bound_complete_label_interpretation='also conservative for complete-label population effect by episode-wise monotonicity',
        upper_bound_complete_label_valid=not bool(unidentified_endpoints))
    primary_p=overall.get('conservative_one_sided_p',overall.get('one_sided_exact_p'))
    # A printed float p can round onto .01 from above. The mixture decision is
    # made with its exact rational comparison, never that rounded display.
    rejects=overall.get('reject',primary_p<=.01)
    family_reports = {f:dict(favorable=c[0],unfavorable=c[1],both_success=c[2],both_failure=c[3],
                            n=sum(c),risk_difference=(c[0]-c[1])/sum(c)) for f,c in family_cells.items()}
    leave_one_out = {f:((cells[0]-c[0])-(cells[1]-c[1]))/(len(records)-sum(c)) for f,c in family_cells.items()}
    return dict(schema='hexar-confirmatory-results/v1',status='COMPLETED',claim_id=CLAIM,
                confirmatory_n=len(records),primary=overall,recording_endpoints=endpoints,
                method_recordings_with_missing_components=unresolved,conservative_missing_mapping=True,
                method_recordings_with_unidentified_endpoint=unidentified_endpoints,
                full_cohort_missingness_effect_bounds=risk_difference_bounds,
                missingness_bounds_interpretation='identification bounds for the realized cohort complete-label effect; not a population confidence interval',
                secondary_metrics=bundle.get('secondary_metrics','NOT_SUPPLIED_IN_CANDIDATE_BUNDLE'),
                judge_pass_sensitivity=bundle.get('judge_pass_sensitivity','NOT_SUPPLIED_IN_CANDIDATE_BUNDLE'),
                family_descriptive=family_reports,leave_one_family_out_descriptive=leave_one_out,
                superiority=rejects,
                interval_and_test_disagreement_possible=plan is None,
                claim=('On a prospectively defined adapted simulated HEXAR external benchmark, CRANE contracts significantly outperformed a strengthened HEXAR-derived explanation baseline on the frozen agent-assessed whole-episode evidence-calibration endpoint.'
                       if rejects else
                       'The prospective adapted simulated HEXAR evidence-calibration comparison did not establish CRANE superiority on the agent-assessed whole-episode endpoint at one-sided alpha .01.'),
                original_hexar_navigation_accuracy='49/54 separately; not this endpoint')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    verify_freeze()
    bundle = json.loads(args.bundle.read_text())
    if not bundle.get('secondary_metrics') or not bundle.get('judge_pass_sensitivity'):
        raise ValueError('complete secondary and judge-pass reporting required')
    cohort=json.loads((BASE/'cohort.json').read_text())
    seal=json.loads((BASE/'raw_cohort_seal.json').read_text())
    if seal['status']!='SEALED' or seal['freeze_sha256']!=digest(BASE/'freeze_manifest.json'):
        raise ValueError('raw cohort not sealed under this freeze')
    cohort['records']=seal['records']
    from analysis.hexar_external.confirmatory_v1.journal import OneAttemptJournal
    terminal=OneAttemptJournal(BASE/'terminal_analysis_journal',digest(BASE/'freeze_manifest.json'))
    identity={'bundle_sha256':digest(args.bundle),'raw_cohort_seal_sha256':digest(BASE/'raw_cohort_seal.json'),
              'analysis_plan_sha256':digest(BASE/'analysis_plan.json')}
    terminal.claim('single-terminal-primary-analysis',identity)
    result = analyze(bundle,cohort,
                     json.loads((BASE/'battery.json').read_text()),digest(BASE/'freeze_manifest.json'),json.loads((BASE/'analysis_plan.json').read_text()))
    result['immutable_input_bundle_sha256'] = digest(args.bundle)
    result['freeze_sha256'] = digest(BASE/'freeze_manifest.json')
    with args.output.open('x') as stream:
        stream.write(json.dumps(result,indent=2)+'\n')
    terminal.finish('single-terminal-primary-analysis',identity,{'status':'VALID','result_path':str(args.output),'result_sha256':digest(args.output)})

if __name__ == '__main__':
    main()
