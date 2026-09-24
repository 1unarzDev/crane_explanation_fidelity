#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"
scratch="$(mktemp -d /tmp/crane-submission-reproduction-XXXXXX)"
trap 'rm -rf "${scratch}"' EXIT

cd "${workspace_root}"

required=(
  data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json
  data/robot_visible/dev/diagnostic-land-dev-004/geometric-route-diagnostic-v2.json
  data/evaluator_only/dev/diagnostic-land-dev-004/independent-plan-geometry-reference.json
  data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json
)
for path in "${required[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing governed artifact: ${path}" >&2
    echo "Configure the private DVC remote and run scripts/dvc_r2_sync.sh pull." >&2
    exit 1
  fi
done

scripts/check_data_governance.sh
scripts/build_paper.sh >"${scratch}/paper-build.log" 2>&1
python3 scripts/audit_submission_readiness.py --category short \
  >"${scratch}/submission-readiness.json"

PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python3 analysis/export_geometric_route_diagnostic.py \
  data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json \
  --episode-id diagnostic-land-dev-004 \
  --nav2-config packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml \
  --bt-xml packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml \
  --robot-radius 0.22 --inflation-radius 0.55 --deadline-seconds 100 \
  --computation-version geometric-route-restriction-v2 \
  --output "${scratch}/geometric-route-diagnostic-v2.json"

python3 analysis/reference_land_plan_geometry.py \
  data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json \
  --episode-id diagnostic-land-dev-004 \
  --output "${scratch}/independent-plan-geometry-reference.json"

PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python3 analysis/recompute_command_motion_diagnostic.py \
  data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json \
  --output "${scratch}/command-motion-recomputed.json"

cmp "${scratch}/geometric-route-diagnostic-v2.json" \
  data/robot_visible/dev/diagnostic-land-dev-004/geometric-route-diagnostic-v2.json
cmp "${scratch}/independent-plan-geometry-reference.json" \
  data/evaluator_only/dev/diagnostic-land-dev-004/independent-plan-geometry-reference.json

python3 - "${scratch}/command-motion-recomputed.json" \
  data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json <<'PY'
import json
import sys

recomputed = json.load(open(sys.argv[1], encoding="utf-8"))
retained = json.load(open(sys.argv[2], encoding="utf-8"))
if recomputed["diagnostic_result"] != retained["diagnostic_result"]:
    raise SystemExit("command-motion diagnostic does not match retained result")
if recomputed["final_answer"] != retained["final_answer"]:
    raise SystemExit("command-motion answer does not match retained answer")
PY

python3 - "${scratch}/submission-readiness.json" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
if result["status"] != "PASS":
    raise SystemExit("submission readiness did not pass")
print(json.dumps({
    "status": "PASS",
    "paper_pages": result["checks"]["pages"],
    "paper_sha256": result["pdf_sha256"],
    "land_diagnostic": "byte-identical",
    "land_independent_reference": "byte-identical",
    "command_motion_diagnostic": "semantically identical after blind recomputation",
}, indent=2, sort_keys=True))
PY
