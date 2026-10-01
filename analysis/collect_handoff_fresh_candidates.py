#!/usr/bin/env python3
"""Collect ordered fresh physical candidates without any semantic method outputs.

Candidate evidence may be checked for technical admission but is reserved from
method/measurement development. Confirmation design remains to be frozen.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from record_build_provenance import managed_assembly_record
from validate_land_scenario_binding import validate_binding

SCHEDULE = ROOT / "manifests/study/evidence-calibration-handoff-fresh-candidates-v1.json"
CATALOG = ROOT / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v10.json"
PLAYER = ROOT / "packages/crane_ml/Builds/Handoff-Confirmation/CRANE.x86_64"
OUT = ROOT / "data/evaluator_only/analysis/handoff-fresh-candidate-collection-v1"


def prepare():
    schedule=json.loads(SCHEDULE.read_text())
    schedule["cohorts"]=[dict(runs=[r for r in schedule["configurations"] if r["stage"]=="confirmation"])]
    schedule["qualification_player"]=str(PLAYER)
    schedule["expected_build_manifest_sha256"]=hashlib.sha256((PLAYER.parent/"crane-build-manifest.json").read_bytes()).hexdigest()
    schedule["expected_managed_assemblies_sha256"]=managed_assembly_record(PLAYER)["sha256"]
    for row in schedule["cohorts"][0]["runs"]:
        row["ros_domain_id"]=95
        row["ros_tcp_port"]=12795
    return schedule


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    schedule = prepare()
    OUT.mkdir(parents=True, exist_ok=True)
    flags = dict(responseAfterSeconds="after", responseReleaseAfterSeconds="release",
                 responseGain="gain", responseRecoveredGain="recovered-gain",
                 responsePeriodSeconds="period", responseDuty="duty")
    for row in schedule["cohorts"][0]["runs"][:args.limit]:
        result = OUT / (row["run_id"]+".json")
        if result.exists():
            print(result.read_text(), flush=True)
            continue
        log = OUT / (row["run_id"]+".log")
        extra = " ".join(f"--crane-land-response-{flags[k]} {v}" for k, v in row["evaluator_response"].items())
        env = dict(os.environ, CRANE_PLAYER=str(PLAYER), CRANE_NAV2_UNITY_EXTRA_ARGS=extra,
                   CRANE_HANDOFF_CANDIDATE_SCHEDULE=str(SCHEDULE), CRANE_DATA_SPLIT="final",
                   CRANE_EXPECTED_BUILD_MANIFEST_SHA256=schedule["expected_build_manifest_sha256"],
                   CRANE_EXPECTED_MANAGED_ASSEMBLIES_SHA256=schedule["expected_managed_assemblies_sha256"])
        started = time.time()
        evaluator = ROOT / "data/evaluator_only/final" / row["run_id"]
        resumed_export = log.exists()
        if resumed_export:
            # Resume export of a completed recording; never launch it again.
            if not (evaluator/"fixture-exit-status.json").exists():
                raise RuntimeError("Unresolved collection attempt; no physical retry")
            started = log.stat().st_mtime
            run = SimpleNamespace(returncode=0)
        else:
            with log.open("x") as sink:
                run = subprocess.run(["bash", str(ROOT/"scripts/run_diagnostic_land_capture.sh"),
                           row["run_id"], str(row["ros_domain_id"]), str(row["ros_tcp_port"]),
                           "v10", row["layout_id"]], cwd=ROOT, env=env, stdout=sink, stderr=subprocess.STDOUT)
        record = dict(run_id=row["run_id"], return_code=run.returncode,
                      duration_s=None if resumed_export else time.time()-started,
                      export_resumed=resumed_export, development_only=False, study_stage="CONFIRMATION_CANDIDATE_PHYSICAL_ONLY", semantic_outputs=0, retry_allowed=False)
        if run.returncode == 0:
            truth = json.loads((evaluator/"worker-0/land-evaluator-truth.json").read_text())
            binding = validate_binding(truth, json.loads(CATALOG.read_text()),
                        catalog_sha256=schedule["catalog_sha256"], catalog_id="v10",
                        layout_id=row["layout_id"], expected_response_profile=row["evaluator_response"])
            (evaluator/"response-binding.json").write_text(json.dumps(binding,indent=2)+"\n")
            record["response_binding_accepted"] = binding["accepted"]
            summary = json.loads((evaluator/"navigation-reset-summary.json").read_text())
            technical_checks = {"response_binding": binding["accepted"],
                "scenario_binding": json.loads((evaluator/"scenario-binding-audit.json").read_text())["accepted"],
                "build_binding": json.loads((evaluator/"player-build-audit.json").read_text())["accepted"],
                "endpoint_errors": summary["transport"]["endpointErrors"] == 0,
                "transport_actions": all(summary["actions"][k] == 0 for k in ("stale", "rejected", "crossEpisode")),
                "observations": all(summary["observations"][k] == 0 for k in ("stale", "failed"))}
            record["technical_checks"] = technical_checks
            record["technical_valid"] = all(technical_checks.values())
            robot = ROOT / "data/robot_visible/final" / row["run_id"]
            export = robot / "command-motion-diagnostic-v3.json"
            visible_config = robot/"capture/nav2_config.yaml"
            shutil.copyfile(ROOT/"packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml", visible_config)
            subprocess.run([sys.executable, str(ROOT/"analysis/export_command_motion_diagnostic.py"),
                "--events", str(robot/"capture/events.jsonl"), "--capture-manifest", str(robot/"capture/manifest.json"),
                "--runtime-manifest", str(robot/"capture/runtime_manifest.json"),
                "--bt-xml", str(robot/"capture/behavior_tree.xml"),
                "--nav2-config", str(visible_config),
                "--diagnostic-config", str(ROOT/"configs/diagnostic_command_motion_low_speed_v1.json"),
                "--episode-id", row["run_id"], "--allow-active-at-declared-cutoff", "--output", str(export)], check=True)
            subprocess.run([sys.executable, str(ROOT/"analysis/reference_command_motion.py"), str(export),
                            "--output", str(evaluator/"command-motion-independent-reference-v1.json")], check=True)
            record["preprocessing_complete"] = True
        result.write_text(json.dumps(record, indent=2)+"\n")
        print(json.dumps(record), flush=True)
        if run.returncode: break


if __name__ == "__main__": main()
