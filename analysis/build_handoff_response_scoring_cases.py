#!/usr/bin/env python3
"""Prepare full-answer, method-blind DEVELOPMENT annotation for additional episodes."""
import argparse
import copy
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from run_evidence_calibration_b2_pilot import ROOT, _materialize

OUT = ROOT / "analysis/results/development/evidence-calibration-response-development-v1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUT)
    parser.add_argument("--b4-version", choices=["v6p2", "v7"], default="v7")
    args = parser.parse_args()
    output = args.output_root
    output.mkdir(parents=True, exist_ok=True)
    pilot = json.loads((OUT/"pilot.json").read_text())
    schedule = json.loads((ROOT/"manifests/study/evidence-calibration-handoff-response-development-v2.json").read_text())
    validation = json.loads((OUT/"input-validation.json").read_text())
    sources = json.loads((ROOT/"analysis/results/evidence-calibration-handoff-development/pilot-cases-v1.json").read_text())["source_assets"]
    cases, joins, missing = [], [], []
    for episode in validation["episodes"]:
        absent = [c for c in episode["condition_ids"] if not
                  (ROOT/"model_outputs/evidence-calibration-response-development-v1/b2"/(c+".json")).exists()]
        if absent:
            missing.append(dict(run_id=episode["run_id"], missing_conditions=absent,
                                disposition="INCOMPLETE_LADDER_AT_THIS_DEVELOPMENT_SNAPSHOT"))
            continue
        episode_reference = json.loads((ROOT/f"data/evaluator_only/dev/{episode['run_id']}/command-motion-independent-reference-v1.json").read_text())["result"]
        realized_family = "measured_response_recovery" if episode_reference["response_recovery_interval_s"] else "persistent_command_motion_discrepancy"
        for condition in episode["condition_ids"]:
            entry, _, family = _materialize(ROOT,pilot,schedule,condition)
            packet = copy.deepcopy(entry["method_packet"])
            evidence = packet["evidence"]
            units = ["state the observed navigation action state or outcome, preserving nonterminal outcome uncertainty"]
            if "behavior_tree_transitions" in evidence:
                if evidence["behavior_tree_transitions"]["execution_sequence"]["source_qualified_wait_recovery_count"]:
                    units.append("state the retained source-qualified recovery sequence")
                else: units.append("state that no source-qualified Wait recovery was observed")
            if "delivered_command_stream" in evidence: units.append("state the delivered command observation")
            if "command_motion_computation" in evidence:
                units.append("state the supported command-to-measured-motion discrepancy and interval")
                reference = json.loads((ROOT/f"data/evaluator_only/dev/{episode['run_id']}/command-motion-independent-reference-v1.json").read_text())
                if reference["result"]["response_recovery_interval_s"] is not None:
                    units.append("state the later measured-response recovery when supported")
            for value in evidence.values():
                if "samples" not in value: continue
                samples = value.pop("samples"); groups = {}
                for s in samples: groups.setdefault(math.floor(s["offset_s"]),[]).append(s["planar_speed_mps"])
                value["deterministic_raw_sample_summary"] = dict(sample_count=len(samples), window_seconds=1,
                    offset_range_s=[min(s["offset_s"] for s in samples),max(s["offset_s"] for s in samples)] if samples else None,
                    windows=[dict(interval_s=[i,i+1],count=len(v),min_speed_mps=min(v),max_speed_mps=max(v),median_speed_mps=statistics.median(v)) for i,v in sorted(groups.items())])
            for method, namespace in [("B2","evidence-calibration-response-development-v1"),
                                      ("B4"+args.b4_version,"evidence-calibration-response-development-v1")]:
                path = ROOT/"model_outputs"/namespace/("b2" if method=="B2" else {"v6p2":"b4-v6-p2", "v7":"b4-v7"}[args.b4_version])/(condition+".json")
                if not path.exists(): raise RuntimeError(f"Missing answer {path}; do not silently omit")
                answer = json.loads(path.read_text())
                identifier = "rp-"+hashlib.sha256(("handoff-response-blind-v1"+condition+method).encode()).hexdigest()[:32]
                cases.append(dict(case_id=identifier, response_text=answer["answer"], reference=dict(robot_visible_evidence=packet,
                    required_units={f"u{i:02}":u for i,u in enumerate(units)}, required_limitations=["do not identify a unique hidden physical cause", "chronology does not establish outcome causation"])))
                joins.append(dict(response_id=identifier, method_id=method, condition_id=condition,
                    configuration_id=entry["condition"]["configuration_id"], family=family, run_id=episode["run_id"],
                    realized_family=realized_family,
                    source_path=str(path.relative_to(ROOT)), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    random.Random(20260930).shuffle(cases)
    for name,value in [("blind-cases-v1.json",dict(scope="DEVELOPMENT_ONLY",cases=cases,source_assets=sources)),
                       ("join-key-v1.json",dict(scope="DEVELOPMENT_ONLY_NOT_SENT_TO_ANNOTATOR",entries=joins))]:
        path=output/name;raw=json.dumps(value,indent=2)+"\n"
        if path.exists() and path.read_text()!=raw:raise RuntimeError("Retained scoring inputs differ")
        if not path.exists():path.write_text(raw)
    (output/"scoring-missingness-v1.json").write_text(json.dumps(dict(scheduled_episode_n=len(validation["episodes"]),
        complete_paired_episode_n=len(validation["episodes"])-len(missing), exclusions=missing),indent=2)+"\n")
    print(json.dumps(dict(answers=len(cases),independent_episodes=len(validation["episodes"])-len(missing),method_key_in_payload=False)))


if __name__=="__main__":main()
