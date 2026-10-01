#!/usr/bin/env python3
"""Generate paired development answers using unchanged strong B2 and retained B4 v5."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from run_evidence_calibration_b2_pilot import ROOT, _materialize, run
from realize_evidence_calibrated_explanation_v7 import realize

SCHEDULE = ROOT/"manifests/study/evidence-calibration-handoff-response-development-v2.json"
OUT = ROOT/"analysis/results/development/evidence-calibration-response-development-v1"
MODELS = ROOT/"model_outputs/evidence-calibration-response-development-v1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    schedule = json.loads(SCHEDULE.read_text())
    rows = schedule["cohorts"][0]["runs"][:args.limit]
    pilot = copy.deepcopy(json.loads((ROOT/"research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text()))
    pilot.update(pilot_id="handoff-response-development-v1", confirmation_alpha=0., development_only=True)
    pilot["selection"] = dict(episode_ids=[r["run_id"] for r in schedule["cohorts"][0]["runs"]],
                               selection_rule=schedule["selection_rule"], independent_unit="configuration")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"pilot.json").write_text(json.dumps(pilot,indent=2)+"\n")
    ontology = json.loads((ROOT/"configs/evidence_calibration_claim_contracts_v1.json").read_text())
    validation = dict(episodes=[])
    missing = []
    for row in rows:
        evaluator = ROOT/"data/evaluator_only/dev"/row["run_id"]
        if not (evaluator/"command-motion-independent-reference-v1.json").exists():
            missing.append(dict(run_id=row["run_id"],status="PHYSICAL_PREPROCESSING_PENDING")); continue
        summary = json.loads((evaluator/"navigation-reset-summary.json").read_text())
        valid = all(json.loads((evaluator/name).read_text())["accepted"] for name in
                    ["player-build-audit.json","scenario-binding-audit.json","response-binding.json"])
        valid &= summary["transport"]["endpointErrors"] == 0
        valid &= all(summary["actions"][k] == 0 for k in ("stale","rejected","crossEpisode"))
        valid &= all(summary["observations"][k] == 0 for k in ("stale","failed"))
        if not valid:
            missing.append(dict(run_id=row["run_id"],status="TECHNICALLY_INVALID_NO_METHOD_CALL"));continue
        record = dict(run_id=row["run_id"],condition_ids=[],condition_packet_sha256s=[])
        for level in range(4):
            condition = row["run_id"]+f"-E{level}"
            entry, _, family = _materialize(ROOT,pilot,schedule,condition)
            record["condition_ids"].append(condition)
            record["condition_packet_sha256s"].append(entry["condition"]["method_packet_sha256"])
            answer = realize(ontology,entry,dict(question_id=family+"-question-v1-development",
                            failure_premise=True,required_mechanism_families=["command_motion"]))
            answer["family"] = family
            path = MODELS/"b4-v7"/(condition+".json");path.parent.mkdir(parents=True,exist_ok=True)
            raw = json.dumps(answer,indent=2,sort_keys=True)+"\n"
            if path.exists() and path.read_text()!=raw:raise RuntimeError("Retained B4 differs")
            if not path.exists():path.write_text(raw)
        validation["episodes"].append(record)
    previous = OUT/"input-validation.json"
    if previous.exists():
        old = {r["run_id"]:r for r in json.loads(previous.read_text())["episodes"]}
        for r in validation["episodes"]:
            if r["run_id"] in old and old[r["run_id"]]!=r:raise RuntimeError("Old input changed")
    previous.write_text(json.dumps(validation,indent=2)+"\n")
    (OUT/"physical-missingness.json").write_text(json.dumps(dict(requested_n=len(rows),rows=missing),indent=2)+"\n")
    conditions = [c for r in validation["episodes"] for c in r["condition_ids"]]
    print(json.dumps(dict(independent_development_n=len(validation["episodes"]),b4_outputs=len(conditions))),flush=True)
    if args.prepare_only: return
    def execute(condition):
        call_args = argparse.Namespace(condition_id=condition,pilot=OUT/"pilot.json",schedule=SCHEDULE,
                   validation=previous,cache=ROOT/"model_outputs/caches/handoff-response-development-v1",
                   output_root=MODELS/"b2",timeout_seconds=300.)
        try:
            run(call_args)
            record = dict(condition_id=condition,status="VALID")
        except Exception as exc:
            record = dict(condition_id=condition,status="TECHNICAL_FAILURE",error=str(exc),retry_allowed=False)
        print(json.dumps(record),flush=True)
        return record
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute,conditions))
    (OUT/"execution-status.json").write_text(json.dumps(dict(development_only=True,results=results),indent=2)+"\n")


if __name__ == "__main__":main()
