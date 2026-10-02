"""Resolve exact command-count flags against full raw permitted samples, deterministically."""
import json
import re
from pathlib import Path
from run_evidence_calibration_b2_pilot import ROOT, _materialize


def main():
    base=ROOT/"analysis/results/development/evidence-calibration-extension-v1"
    joins={r["response_id"]:r for r in json.loads((base/"join-key-v1.json").read_text())["entries"]}
    pilot=json.loads((base/"pilot.json").read_text())
    schedule=json.loads((ROOT/"research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    rows=[]
    for path in sorted((base/"annotations-v2").glob("A-batch-*.json")):
        if path.name.endswith(".request.json"): continue
        for r in json.loads(path.read_text())["parsed_final"]["annotations"]:
            for flag in r["factual_numeric_errors"]:
                q=flag["quote"]
                match=re.search(r"delivered (\d+) (?:motion commands above 0\.1 m/s|commands at 0\.26 m/s|nonzero speed commands)",q)
                if not match: continue
                entry,_,_=_materialize(ROOT,pilot,schedule,joins[r["case_id"]]["condition_id"])
                samples=entry["method_packet"]["evidence"]["delivered_command_stream"]["samples"]
                if "above 0.1" in q: count=sum(s["planar_speed_mps"]>.1 for s in samples)
                elif "at 0.26" in q: count=sum(abs(s["planar_speed_mps"]-.26)<1e-9 for s in samples)
                else: count=sum(s["planar_speed_mps"]!=0 for s in samples)
                rows.append(dict(case_id=r["case_id"],condition_id=joins[r["case_id"]]["condition_id"],
                    quote=q,asserted_count=int(match[1]),raw_permitted_sample_count=count,
                    exact_count_supported=int(match[1])==count, annotation_error_cause="Summary omitted exact per-value counts; raw evidence supplied to B2 contains them"))
    result=dict(scope="DEVELOPMENT_ONLY_SECONDARY_CORRECTION",primary_endpoint_changed=False,
                original_annotations_preserved=True, deterministic_count_checks=rows,
                exact_count_flags_vindicated=sum(r["exact_count_supported"] for r in rows),
                remaining_noncount_flags_require_full_answer_interpretation=True)
    path=ROOT/"manifests/analysis/evidence-calibration-handoff-secondary-count-checks-v1.json"
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(dict(checks=len(rows),vindicated=result["exact_count_flags_vindicated"],primary_endpoint_changed=False)))


if __name__=="__main__":main()
