#!/usr/bin/env python3
"""Report whole-episode paired development estimates and independent-pass sensitivity."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from summarize_handoff_development_results import aggregate


def paired_interval(b, c, n, tail_probability=.0125):
    """Uniform >=95% Bonferroni projection; no outcome-dependent zero-case switch."""
    log_comb = [math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1) for j in range(n+1)]
    def bounds(k):
        def tail(p, upper):
            js = range(k,n+1) if upper else range(k+1)
            return math.fsum(math.exp(log_comb[j]+j*math.log(p)+(n-j)*math.log1p(-p)) for j in js)
        def root(upper):
            low,high = 0.,1.
            for _ in range(70):
                mid=(low+high)/2
                if (tail(mid,upper)<tail_probability) == upper:low=mid
                else:high=mid
            return (low+high)/2
        return (root(True) if k else 0., root(False) if k<n else 1.)
    bl,bu=bounds(b);cl,cu=bounds(c)
    return [bl-cu,bu-cl]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    args = parser.parse_args()
    joins = {r["response_id"]:r for r in json.loads((args.snapshot/"join-key-v1.json").read_text())["entries"]}
    b4_method = next(iter({j["method_id"] for j in joins.values()} - {"B2"}))
    passes = {}
    for slot in ("A","B"):
        rows = {}
        for p in sorted(args.annotations.glob(slot+"-batch-*.json")):
            if p.name.endswith("request.json"): continue
            record = json.loads(p.read_text())
            if record["status"] != "STRUCTURALLY_VALID_SUPPORT_RETURN": raise RuntimeError(f"Annotation technical failure: {p}")
            for r in record["parsed_final"]["annotations"]:
                if r["case_id"] in rows:raise RuntimeError("Duplicate annotation")
                rows[r["case_id"]] = r
        if set(rows)!=set(joins):raise RuntimeError(f"Incomplete annotation pass {slot}: {len(rows)}/{len(joins)}")
        passes[slot] = rows
    merged = {slot:[] for slot in ("A","B","conservative")}
    disagreements = []
    for identifier,j in joins.items():
        a,b = passes["A"][identifier],passes["B"][identifier]
        ua,ub = [{u["unit_id"]:u["communicated"] for u in r["required_units"]} for r in (a,b)]
        if set(ua)!=set(ub):raise RuntimeError("Unit inventories differ")
        if a["primary_failure"]!=b["primary_failure"] or ua!=ub:
            disagreements.append(dict(case_id=identifier,primary=a["primary_failure"]!=b["primary_failure"],coverage=sum(ua[u]!=ub[u] for u in ua)))
        for slot,r in (("A",a),("B",b),("conservative",a)):
            row=dict(configuration_id=j["configuration_id"],method=j["method_id"],family=j.get("realized_family",j["family"]),condition_id=j["condition_id"],
                primary_failure=(a["primary_failure"] or b["primary_failure"]) if slot=="conservative" else r["primary_failure"],
                covered=sum(ua[u] and ub[u] for u in ua) if slot=="conservative" else sum(ua.values()) if slot=="A" else sum(ub.values()),
                required=len(ua),primary_violations=list({(v["kind"],v["quote"]):v for rr in (a,b) for v in rr["primary_violations"]}.values()) if slot=="conservative" else r["primary_violations"],
                factual_numeric_errors=list({v["quote"]:v for rr in (a,b) for v in rr["factual_numeric_errors"]}.values()) if slot=="conservative" else r["factual_numeric_errors"])
            merged[slot].append(row)
    result=dict(development_only=True,confirmatory_alpha_spent=0.,independent_unit="configuration",
                method_versions=dict(B2="unchanged gpt-6-sol/high repository/tool-enabled",B4=b4_method),
                interval_method="Project simultaneous 97.5% exact Clopper-Pearson bounds for each discordant category (Bonferroni); >=95% coverage for all outcomes, including zero discordances.",
                pass_sensitivity={slot:aggregate(rows,b4_method=b4_method,interval_fn=paired_interval) for slot,rows in merged.items()},
                disagreements=disagreements,condition_rows=merged["conservative"],
                missingness=json.loads((args.snapshot/"scoring-missingness-v1.json").read_text()))
    result["decomposition"]={method:dict(primary_violation_kinds=dict(Counter(v["kind"] for r in merged["conservative"] if r["method"]==method for v in r["primary_violations"])),
        factual_numeric_error_conditions=sum(bool(r["factual_numeric_errors"]) for r in merged["conservative"] if r["method"]==method),
        evidence_levels={f"E{level}":dict(answers=len(rs),failures=sum(r["primary_failure"] for r in rs),covered=sum(r["covered"] for r in rs),required=sum(r["required"] for r in rs))
                         for level in range(4) for rs in [[r for r in merged["conservative"] if r["method"]==method and r["condition_id"].endswith(f"-E{level}")]]})
        for method in ("B2",b4_method)}
    complete=result["pass_sensitivity"]["conservative"]
    missingness=result["missingness"]
    eligible=missingness["scheduled_episode_n"]-len(missingness.get("physical_technical_exclusions",[]))
    unpaired=eligible-complete["independent_episode_n"]
    net=complete["B2_fails_B4_passes"]-complete["B4_fails_B2_passes"]
    missingness["eligible_after_physical_technical_exclusions"]=eligible
    missingness["unpaired_eligible_episodes"]=unpaired
    missingness["worst_case_full_eligible_population_risk_difference_bounds"]=[(net-unpaired)/eligible,(net+unpaired)/eligible]
    path=args.snapshot/"paired-result.json"
    if path.exists():
        old=json.loads(path.read_text())
        if "interval_method" not in old:
            legacy=args.snapshot/"paired-result-legacy-interval.json"
            if not legacy.exists():legacy.write_bytes(path.read_bytes())
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result["pass_sensitivity"]["conservative"],indent=2))


if __name__ == "__main__": main()
