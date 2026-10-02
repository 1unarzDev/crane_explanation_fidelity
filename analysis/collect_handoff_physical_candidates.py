#!/usr/bin/env python3
"""Collect first four prospectively allocated physical candidates, without semantic calls.

Captured records remain in the legacy dev storage namespace for compatibility, but the
allocation forbids their use for development, measurement tuning, or effect estimation.
Failures are retained and never retried. This does not declare confirmatory statistical N.
"""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE = ROOT / "manifests/study/evidence-calibration-handoff-physical-allocation-v1.json"
OUTPUT = ROOT / "data/evaluator_only/analysis/handoff-physical-candidates-v1"


def main():
    schedule = json.loads(SCHEDULE.read_text())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for row in schedule["configurations"][:4]:
        result = OUTPUT / (row["run_id"] + ".json")
        if result.exists():
            print(json.dumps(json.loads(result.read_text())), flush=True)
            continue
        log = OUTPUT / (row["run_id"] + ".log")
        if log.exists():
            raise RuntimeError("Unresolved previous physical intent; no retry")
        env = dict(os.environ, CRANE_HANDOFF_PHYSICAL_SCHEDULE=str(SCHEDULE),
                   CRANE_PLAYER=schedule["qualification_player"],
                   CRANE_EXPECTED_BUILD_MANIFEST_SHA256=schedule["expected_build_manifest_sha256"],
                   CRANE_EXPECTED_MANAGED_ASSEMBLIES_SHA256=schedule["expected_managed_assemblies_sha256"],
                   CRANE_PROVING_GROUND_MOBILITY_HOLD_AFTER=str(row["mobility_hold_after_s"]),
                   CRANE_PROVING_GROUND_MOBILITY_RELEASE_AFTER=str(row["mobility_release_after_s"]))
        started = time.time()
        with log.open("x") as sink:
            run = subprocess.run(["bash", str(ROOT / "scripts/run_diagnostic_land_capture.sh"),
                                  row["run_id"], str(row["ros_domain_id"]), str(row["ros_tcp_port"]),
                                  row["catalog_id"], row["layout_id"]], env=env, cwd=ROOT,
                                 stdout=sink, stderr=subprocess.STDOUT)
        record = dict(run_id=row["run_id"], return_code=run.returncode,
                      duration_s=time.time()-started, physical_only=True,
                      semantic_calls=0, development_use=False, confirmation_independent_n=0,
                      replication_independent_n=0, retry_allowed=False)
        result.write_text(json.dumps(record, indent=2)+"\n")
        print(json.dumps(record), flush=True)
        if run.returncode:
            break


if __name__ == "__main__":
    main()
