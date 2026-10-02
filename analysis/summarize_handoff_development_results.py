#!/usr/bin/env python3
"""Whole-episode DEVELOPMENT paired results, two-pass sensitivity, and power decision."""
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
from power_evidence_calibration_handoff import power, required_n

ROOT = Path(__file__).resolve().parents[1]
INITIAL = ROOT / "analysis/results/evidence-calibration-handoff-development"
EXTENSION = ROOT / "analysis/results/development/evidence-calibration-extension-v1"
spec = importlib.util.spec_from_file_location("development_intervals", INITIAL/"compare_and_merge.py")
intervals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intervals)


def load_pass(slot, expected):
    values = {}
    for p in sorted((EXTENSION/"annotations-v2").glob(slot+"-batch-*.json")):
        if p.name.endswith(".request.json"): continue
        record = json.loads(p.read_text())
        if record["status"] != "STRUCTURALLY_VALID_SUPPORT_RETURN":
            raise RuntimeError(f"Annotation failure retained: {p}")
        for row in record["parsed_final"]["annotations"]:
            if row["case_id"] in values: raise RuntimeError("Duplicate annotation")
            values[row["case_id"]] = row
    if set(values) != expected: raise RuntimeError(f"Incomplete pass {slot}: {len(values)}/{len(expected)}")
    return values


def aggregate(rows, b4_method="B4v5", interval_fn=None):
    episodes = {}
    for r in rows:
        key = (r["configuration_id"], r["method"])
        e = episodes.setdefault(key,dict(configuration_id=r["configuration_id"], method=r["method"],
                    family=r["family"], failure=False, covered=0, required=0, conditions=0))
        e["failure"] |= r["primary_failure"]
        e["covered"] += r["covered"]
        e["required"] += r["required"]
        e["conditions"] += 1
    if any(e["conditions"] != 4 for e in episodes.values()): raise RuntimeError("Incomplete primary ladder")
    by_method = {m:{e["configuration_id"]:e for e in episodes.values() if e["method"]==m} for m in ("B2",b4_method)}
    ids = set(by_method["B2"])
    if ids != set(by_method[b4_method]): raise RuntimeError("Unpaired configurations")
    n = len(ids)
    b = sum(by_method["B2"][i]["failure"] and not by_method[b4_method][i]["failure"] for i in ids)
    c = sum(by_method[b4_method][i]["failure"] and not by_method["B2"][i]["failure"] for i in ids)
    m = b+c
    report = dict(independent_episode_n=n, mechanism_balance=dict(Counter(e["family"] for e in by_method["B2"].values())),
                  methods={}, B2_fails_B4_passes=b,B4_fails_B2_passes=c,
                  paired_risk_difference_B2_minus_B4=(b-c)/n,
                  conservative_whole_episode_95_ci=(interval_fn or intervals.paired_interval)(b,c,n),
                  descriptive_exact_one_sided_p=sum(math.comb(m,k) for k in range(b,m+1))/2**m if m else 1.,
                  descriptive_exact_two_sided_p=min(1.,2*sum(math.comb(m,k) for k in range(min(b,c)+1))/2**m) if m else 1.,
                  episode_rows=list(episodes.values()))
    for method,es in by_method.items():
        covered=sum(e["covered"] for e in es.values());required=sum(e["required"] for e in es.values())
        report["methods"][method]=dict(failures=sum(e["failure"] for e in es.values()),failure_rate=sum(e["failure"] for e in es.values())/n,
                                      covered_units=covered,required_units=required,unit_coverage=covered/required,
                                      mean_episode_coverage=sum(e["covered"]/e["required"] for e in es.values())/n)
    report["mean_episode_coverage_difference_B4_minus_B2"] = report["methods"][b4_method]["mean_episode_coverage"]-report["methods"]["B2"]["mean_episode_coverage"]
    return report


def main():
    initial=json.loads((INITIAL/"initial-paired-development-final-v2.json").read_text())
    joins={r["response_id"]:r for r in json.loads((EXTENSION/"join-key-v1.json").read_text())["entries"]}
    a,b=[load_pass(slot,set(joins)) for slot in ("A","B")]
    disagreements=[]
    extension_rows={slot:[] for slot in ("A","B","conservative")}
    for identifier,e in joins.items():
        aa,bb=a[identifier],b[identifier]
        ua={u["unit_id"]:u["communicated"] for u in aa["required_units"]}
        ub={u["unit_id"]:u["communicated"] for u in bb["required_units"]}
        if set(ua)!=set(ub):raise RuntimeError("Annotation units differ")
        if aa["primary_failure"]!=bb["primary_failure"] or ua!=ub:
            disagreements.append(dict(case_id=identifier,primary=aa["primary_failure"]!=bb["primary_failure"],
                                      coverage_unit_count=sum(ua[u]!=ub[u] for u in ua)))
        for slot,r in (("A",aa),("B",bb),("conservative",aa)):
            covered=sum(ua[u] and ub[u] for u in ua) if slot=="conservative" else sum(u["communicated"] for u in r["required_units"])
            failure=aa["primary_failure"] or bb["primary_failure"] if slot=="conservative" else r["primary_failure"]
            extension_rows[slot].append(dict(configuration_id=e["configuration_id"],method=e["method_id"],family=e["family"],
                condition_id=e["condition_id"],primary_failure=failure,covered=covered,required=len(ua),
                primary_violations=r["primary_violations"],factual_numeric_errors=r["factual_numeric_errors"]))
    initial_rows=[dict(configuration_id=r["configuration_id"],method=r["method"],family=r["family"],condition_id=r["condition_id"],
            primary_failure=r["primary_failure"],covered=r["covered_units"],required=r["required_unit_count"],
            primary_violations=r["primary_violations"],factual_numeric_errors=r["factual_numeric_errors"])
        for r in initial["condition_rows"] if r["paired_complete_episode"] and r["method"] in ("B2","B4v5")
        and r["family"] in ("persistent_command_motion_discrepancy","measured_response_recovery")]
    primary=aggregate(initial_rows+extension_rows["conservative"])
    scenarios=[(0.,0.),(.01,0.),(.02,.005),(.03,.005),(.05,.01),(.10,.02)]
    power_rows=[dict(b2_only=b,b4_only=c,invalid=.10,alpha=.01,
                   power_for_80_acquired_primary=power(80,b,c,.1,"one-sided") if b+c else .0,
                   acquired_primary_n_for_80pct=required_n(b,c,.1,"one-sided",.8) if b+c and b>c else None)
                for b,c in scenarios]
    levels={}
    for method in ("B2","B4v5"):
        for level in range(4):
            rs=[r for r in initial_rows+extension_rows["conservative"] if r["method"]==method and r["condition_id"].endswith(f"-E{level}")]
            levels[f"{method}/E{level}"]=dict(condition_n=len(rs),failures=sum(r["primary_failure"] for r in rs),covered=sum(r["covered"] for r in rs),required=sum(r["required"] for r in rs))
    n=primary["independent_episode_n"]
    complete_rows=initial_rows+extension_rows["conservative"]
    decomposition={method:dict(
        mechanistic_or_diagnostic_violation_counts=dict(Counter(v["kind"] for r in complete_rows
            if r["method"]==method for v in r["primary_violations"])),
        automated_factual_numeric_flag_conditions_secondary_unverified=sum(bool(r["factual_numeric_errors"]) for r in complete_rows if r["method"]==method),
        overclaiming_or_unsupported_specificity_conditions=sum(bool(r["primary_violations"]) for r in complete_rows if r["method"]==method))
        for method in ("B2","B4v5")}
    count_checks=json.loads((ROOT/"manifests/analysis/evidence-calibration-handoff-secondary-count-checks-v1.json").read_text())
    report=dict(scope="DEVELOPMENT_ONLY",primary=primary,decomposition=decomposition,
        secondary_deterministic_count_corrections=count_checks,
        extension={slot:aggregate(rs) for slot,rs in extension_rows.items()},
        combined_pass_sensitivity={slot:aggregate(initial_rows+rs) for slot,rs in extension_rows.items()},
        disagreement_cases=disagreements, evidence_levels=levels, power=power_rows,
        missingness=dict(scheduled_primary_episode_n=24,complete_primary_episode_n=n,
            whole_episode_exclusions=["cm-land-conf-042","cm-land-conf-061"],retry_count=0,
            full_population_effect_bounds_allowing_arbitrary_missing_pair_outcomes=[(primary["B2_fails_B4_passes"]-primary["B4_fails_B2_passes"]-(24-n))/24,
                                                                               (primary["B2_fails_B4_passes"]-primary["B4_fails_B2_passes"]+(24-n))/24]),
        declaration=dict(confirmation_executed=False,confirmation_n=0,alpha_spent_this_handoff=0.,
                         program_alpha_previously_consumed=.02,candidate_alpha_available=.01,replication_alpha_protected=.02),
        qualification="30 targeted fresh synthetic cases; two automated passes; reviewed references and original failures preserved",
        human_validation_claimed=False,judge_limitation="Repeated same-model annotations can share systematic errors; prompt changed only during development",
        decision="No observed B4 superiority. Do not freeze or consume alpha for an underpowered comparison based on a nonexistent favorable development effect.")
    output=ROOT/"manifests/analysis/evidence-calibration-handoff-paired-development-result-v1.json"
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(primary={k:v for k,v in primary.items() if k!="episode_rows"},
                         disagreements=len(disagreements),decomposition=decomposition,
                         output=str(output.relative_to(ROOT))),indent=2))


if __name__=="__main__":main()
