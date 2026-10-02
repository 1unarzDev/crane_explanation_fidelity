#!/usr/bin/env python3
"""Twelve additional independent DEVELOPMENT episodes using the unchanged strong B2.

Selection is earliest valid source order within each of two mechanism strata, after
excluding the initial pilot. Prepared hashes precede every model call. No fresh
physical candidate or protected replication configuration is used here.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import sys

from run_evidence_calibration_b2_pilot import ROOT, _materialize, run
from realize_evidence_calibrated_explanation_v3 import realize

OUT = ROOT / "analysis/results/development/evidence-calibration-extension-v1"
SCHEDULE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json"


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    old = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
    schedule = json.loads(SCHEDULE.read_text())
    selected = []
    for family in ("persistent-discrepancy", "transient-compensation"):
        candidates = [r for r in schedule["cohorts"][0]["runs"] if r["family"] == family
                      and r["run_id"] not in old["selection"]["episode_ids"]
                      and (ROOT / f"data/robot_visible/dev/{r['run_id']}/command-motion-diagnostic-v3.json").exists()
                      and (ROOT / f"data/evaluator_only/dev/{r['run_id']}/command-motion-independent-reference-v1.json").exists()]
        selected.extend(candidates[:6])
    assert len(selected) == 12
    pilot = copy.deepcopy(old)
    pilot.update(pilot_id="evidence-calibration-development-extension-v1", independent_episode_count=12,
                 confirmation_alpha=0., status="DEVELOPMENT_ONLY_AUTHORIZED_BY_HANDOFF")
    pilot["selection"] = dict(episode_ids=[r["run_id"] for r in selected],
                             selection_rule=__doc__, independent_unit="configuration")
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
    validation = dict(episodes=[])
    b4 = ROOT / "model_outputs/evidence-calibration-development-extension-v1/b4"
    b4.mkdir(parents=True, exist_ok=True)
    for row in selected:
        record = dict(run_id=row["run_id"], condition_ids=[], condition_packet_sha256s=[])
        for level in range(4):
            condition_id = row["run_id"] + f"-E{level}"
            entry, _, family = _materialize(ROOT, pilot, schedule, condition_id)
            record["condition_ids"].append(condition_id)
            record["condition_packet_sha256s"].append(entry["condition"]["method_packet_sha256"])
            answer = realize(ontology, entry, dict(question_id=family+"-question-v1-development",
                              failure_premise=True, required_mechanism_families=["command_motion"]))
            answer["family"] = family
            path = b4 / (condition_id + ".json")
            raw = json.dumps(answer, indent=2, sort_keys=True)+"\n"
            if path.exists() and path.read_text() != raw:
                raise RuntimeError("Existing development output differs")
            if not path.exists(): path.write_text(raw)
        validation["episodes"].append(record)
    for name, obj in (("pilot.json", pilot), ("input-validation.json", validation)):
        raw = json.dumps(obj, indent=2, sort_keys=True)+"\n"
        path = OUT / name
        if path.exists() and path.read_text() != raw: raise RuntimeError("Selection changed")
        if not path.exists(): path.write_text(raw)
    return validation


def main():
    validation = prepare()
    conditions = [c for r in validation["episodes"] for c in r["condition_ids"]]
    print(json.dumps(dict(development_episodes=12, b4_outputs=48, selected_conditions=conditions)), flush=True)
    b2 = ROOT / "model_outputs/evidence-calibration-development-extension-v1/b2"
    def execute(condition):
        args = argparse.Namespace(condition_id=condition, pilot=OUT/"pilot.json", schedule=SCHEDULE,
                    validation=OUT/"input-validation.json", cache=ROOT/"model_outputs/caches/handoff-development-extension-v1",
                    output_root=b2, timeout_seconds=300.)
        try:
            result = run(args)
            print(json.dumps(dict(condition_id=condition, status="VALID", method="B2")), flush=True)
            return dict(condition_id=condition, status="VALID")
        except Exception as exc:
            record = dict(condition_id=condition, status="TECHNICAL_FAILURE", error=str(exc), retry_allowed=False)
            path = OUT / (condition+"-failure.json")
            if not path.exists(): path.write_text(json.dumps(record,indent=2)+"\n")
            print(json.dumps(record), flush=True)
            return record
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, conditions))
    (OUT/"execution-status.json").write_text(json.dumps(dict(development_only=True, results=results),indent=2)+"\n")


if __name__ == "__main__": main()
