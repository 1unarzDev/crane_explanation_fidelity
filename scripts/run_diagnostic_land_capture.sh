#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

print_config=0
if [[ "${1:-}" == "--print-config" ]]; then
    print_config=1
    shift
fi
if [[ $# -ne 5 ]]; then
    echo "Usage: $0 [--print-config] RUN_ID ROS_DOMAIN_ID ROS_TCP_PORT CATALOG LAYOUT" >&2
    exit 2
fi

run_id="$1"
ros_domain_id="$2"
ros_port="$3"
catalog="$4"
layout="$5"
if [[ ! "${run_id}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "RUN_ID may contain only letters, numbers, dot, underscore, and dash" >&2
    exit 2
fi
if [[ ! "${ros_domain_id}" =~ ^[0-9]+$ || ! "${ros_port}" =~ ^[0-9]+$ ]]; then
    echo "ROS_DOMAIN_ID and ROS_TCP_PORT must be integers" >&2
    exit 2
fi
if [[ "${catalog}" != "v4" && "${catalog}" != "v5" && "${catalog}" != "v6" && "${catalog}" != "v7" && "${catalog}" != "v8" && "${catalog}" != "v9" && "${catalog}" != "v10" ]]; then
    echo "Only versioned diagnostic catalogs v4 through v10 are supported: ${catalog}" >&2
    exit 2
fi
if [[ "${catalog}" == "v6" && -z "${CRANE_HANDOFF_PHYSICAL_SCHEDULE:-}" && "${CRANE_ALLOW_RESERVED_PHYSICAL_CAPTURE:-0}" != "1" && "${CRANE_ALLOW_CAUSAL_RESTRAINT_CAPTURE:-0}" != "1" && "${CRANE_ALLOW_CONTRACT_COMPLETE_V2_CAPTURE:-0}" != "1" ]]; then
    echo "v6 is a physical-evidence reserve; set CRANE_ALLOW_RESERVED_PHYSICAL_CAPTURE=1 for an explicitly declared development capture" >&2
    exit 2
fi
if [[ "${catalog}" == "v8" && "${CRANE_ALLOW_CAUSAL_RESTRAINT_CAPTURE:-0}" != "1" ]]; then
    echo "v8 is reserved for the causal-restraint successor; explicit schedule activation is required" >&2
    exit 2
fi

astro_dir="${workspace_root}/packages/astro_dock"
crane_dir="${workspace_root}/packages/crane_ml"
catalog_file="${crane_dir}/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_${catalog}.json"
nav2_params="${crane_dir}/Tools/Performance/nav2_land_proving_ground_fixture.yaml"
bt_xml="${crane_dir}/Tools/Performance/nav2_land_progress_recovery.xml"
scene="TurtleBot3 Warehouse Validation"
command_flag="--crane-ros-differential-cmd-vel"
lidar_frame="base_scan"
goal_distance_m="18.0"
action_duration_s="100"
data_split="${CRANE_DATA_SPLIT:-dev}"
proving_ground_mobility_hold_after="${CRANE_PROVING_GROUND_MOBILITY_HOLD_AFTER:--1}"
proving_ground_mobility_release_after="${CRANE_PROVING_GROUND_MOBILITY_RELEASE_AFTER:--1}"
causal_restraint_stage="${CRANE_CAUSAL_RESTRAINT_STAGE:-}"
causal_restraint_schedule="${workspace_root}/research/explanation_fidelity/experiment_configs/prospective/explicit-causal-restraint-successor-v1-schedule.json"
contract_complete_v2="${CRANE_ALLOW_CONTRACT_COMPLETE_V2_CAPTURE:-0}"
contract_complete_v2_schedule="${workspace_root}/research/explanation_fidelity/experiment_configs/prospective/contract-complete-diagnostic-communication-v2-pilot-schedule.json"

if [[ "${data_split}" != "dev" && !( "${data_split}" == "final" && "${catalog}" == "v10" && -n "${CRANE_HANDOFF_CANDIDATE_SCHEDULE:-}" ) ]]; then
    echo "Diagnostic held-out/final capture is not authorized before protocol freeze" >&2
    exit 2
fi
layout_metadata_text="$(python3 - "${catalog_file}" "${layout}" "${catalog}" "${run_id}" \
    "${CRANE_ALLOW_CAUSAL_RESTRAINT_CAPTURE:-0}" "${causal_restraint_stage}" \
    "${causal_restraint_schedule}" "${proving_ground_mobility_hold_after}" \
    "${proving_ground_mobility_release_after}" "${contract_complete_v2}" \
    "${contract_complete_v2_schedule}" "${CRANE_HANDOFF_PHYSICAL_SCHEDULE:-}" "${CRANE_HANDOFF_CANDIDATE_SCHEDULE:-}" <<'PY'
import json
import sys

catalog_path, layout_id, catalog_id, run_id, successor, stage, schedule_path, hold, release, contract_v2, contract_schedule_path, handoff_path, candidate_path = sys.argv[1:]
catalog = json.load(open(catalog_path, encoding="utf-8"))
matches = [item for item in catalog.get("layouts", []) if item.get("id") == layout_id]
if len(matches) != 1:
    raise SystemExit(f"layout must resolve exactly once in catalog: {layout_id}")
layout = matches[0]
if layout.get("studySplit") == "confirmatory":
    raise SystemExit("confirmatory layouts are sealed until protocol freeze")
expected_splits = {
    "v4": "development",
    "v5": "candidate-v2-development",
    "v6": "command-motion-confirmation-reserve",
    "v7": "contract-limit-v4-development",
    "v9": "handoff-response-development",
}
if successor == "1" and contract_v2 == "1":
    raise SystemExit("causal-restraint and contract-complete capture activations are mutually exclusive")
if candidate_path:
    import hashlib
    schedule = json.load(open(candidate_path, encoding="utf-8"))
    if (schedule.get("schema") != "crane-handoff-fresh-candidates/v1"
            or schedule.get("development_use") is not False
            or hashlib.sha256(open(catalog_path,"rb").read()).hexdigest() != schedule["catalog_sha256"]):
        raise SystemExit("invalid fresh candidate physical allocation")
    rows = [r for r in schedule["configurations"] if r["run_id"] == run_id]
    if (len(rows)!=1 or catalog_id != "v10" or rows[0]["layout_id"] != layout_id
            or layout["studySplit"] != "handoff-" + rows[0]["stage"] + "-candidate"):
        raise SystemExit("fresh candidate identity/split differs")
elif handoff_path:
    import hashlib
    schedule = json.load(open(handoff_path, encoding="utf-8"))
    if (schedule.get("schema") != "crane-handoff-physical-allocation/v1"
            or schedule.get("status") != "PHYSICAL_ONLY_SEMANTIC_FREEZE_PENDING"
            or schedule.get("user_authorized_reassignment") is not True
            or schedule.get("development_use") is not False
            or hashlib.sha256(open(catalog_path, "rb").read()).hexdigest() != schedule["catalog_sha256"]):
        raise SystemExit("invalid handoff physical-only allocation")
    matches = [row for row in schedule["configurations"] if row["run_id"] == run_id]
    if len(matches) != 1:
        raise SystemExit("run absent or duplicated in handoff allocation")
    row = matches[0]
    if (row["layout_id"] != layout_id or row["catalog_id"] != catalog_id
            or row["mobility_hold_after_s"] != float(hold)
            or row["mobility_release_after_s"] != float(release)):
        raise SystemExit("handoff layout/timing mismatch")
elif contract_v2 == "1":
    if catalog_id != "v6":
        raise SystemExit("contract-complete v2 pilot requires catalog v6")
    schedule = json.load(open(contract_schedule_path, encoding="utf-8"))
    scheduled_matches = [item for item in schedule["configurations"] if item["run_id"] == run_id]
    if len(scheduled_matches) != 1:
        raise SystemExit("run is absent or duplicated in the frozen contract-complete v2 pilot")
    scheduled = scheduled_matches[0]
    if scheduled["catalog_id"] != catalog_id or scheduled["layout_id"] != layout_id:
        raise SystemExit("catalog/layout differs from the frozen contract-complete v2 schedule")
    if float(scheduled["mobility_hold_after_s"]) != float(hold) or float(scheduled["mobility_release_after_s"]) != float(release):
        raise SystemExit("mobility timing differs from the frozen contract-complete v2 schedule")
elif successor == "1" and catalog_id in {"v6", "v8"}:
    if stage not in {"pilot", "discovery", "replication"}:
        raise SystemExit("causal-restraint capture requires an explicit valid stage")
    schedule = json.load(open(schedule_path, encoding="utf-8"))
    scheduled_matches = [
        item for item in schedule["stages"][stage] if item["run_id"] == run_id
    ]
    if len(scheduled_matches) != 1:
        raise SystemExit("run is absent or duplicated in the frozen causal-restraint stage")
    scheduled = scheduled_matches[0]
    if scheduled["catalog_id"] != catalog_id or scheduled["layout_id"] != layout_id:
        raise SystemExit("catalog/layout differs from the frozen causal-restraint schedule")
    if float(scheduled["mobility_hold_after_s"]) != float(hold) or float(
        scheduled["mobility_release_after_s"]
    ) != float(release):
        raise SystemExit("mobility timing differs from the frozen causal-restraint schedule")
else:
    expected_split = expected_splits[catalog_id]
    if layout.get("studySplit") != expected_split:
        raise SystemExit("layout is calibration-only or outside the active diagnostic scope")
if layout.get("diagnosticMechanism") not in {"connected-detour", "nominal-clear-route"}:
    raise SystemExit("layout is calibration-only or outside the active diagnostic scope")
print(layout["seed"])
print(layout["diagnosticMechanism"])
PY
)"
mapfile -t layout_metadata <<<"${layout_metadata_text}"
layout_seed="${layout_metadata[0]}"

python3 - "${proving_ground_mobility_hold_after}" \
    "${proving_ground_mobility_release_after}" <<'PY'
import math
import sys

hold, release = map(float, sys.argv[1:])
if not math.isfinite(hold) or not math.isfinite(release):
    raise SystemExit("Proving-ground mobility boundaries must be finite")
if hold < 0.0 and release >= 0.0:
    raise SystemExit("Proving-ground mobility release requires a configured hold boundary")
if release >= 0.0 and release <= hold:
    raise SystemExit("Proving-ground mobility release must occur after the hold begins")
PY

unity_extra_args="${CRANE_NAV2_UNITY_EXTRA_ARGS:-}"
for incompatible_flag in \
    --crane-land-blocker \
    --crane-land-blocker-enable-after \
    --crane-land-blocker-remove-after \
    --crane-land-mobility-hold-after \
    --crane-land-mobility-release-after; do
    if [[ " ${unity_extra_args} " == *" ${incompatible_flag} "* || \
          " ${unity_extra_args} " == *" ${incompatible_flag}="* ]]; then
        echo "Proving-ground layouts cannot be combined with legacy corridor interventions: ${incompatible_flag}" >&2
        exit 2
    fi
done

if [[ ${print_config} -eq 1 ]]; then
    python3 - "${run_id}" "${ros_domain_id}" "${ros_port}" "${catalog}" "${layout}" \
        "${layout_seed}" "${layout_metadata[1]}" \
        "${proving_ground_mobility_hold_after}" \
        "${proving_ground_mobility_release_after}" <<'PY'
import json
import sys

run_id, domain, port, catalog, layout, layout_seed, mechanism, hold, release = sys.argv[1:]
print(json.dumps({
    "schema": "crane-diagnostic-land-capture-config/v1",
    "run_id": run_id,
    "ros_domain_id": int(domain),
    "ros_tcp_port": int(port),
    "catalog": catalog,
    "layout": layout,
    "layout_seed": int(layout_seed),
    "diagnostic_mechanism": mechanism,
    "data_split": "dev",
    "scene": "TurtleBot3 Warehouse Validation",
    "nav2_params": "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
    "bt_xml": "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml",
    "command_flag": "--crane-ros-differential-cmd-vel",
    "lidar_frame": "base_scan",
    "goal_distance_m": 18.0,
    "action_duration_s": 100,
    "runtime_manifest_builder": "scripts/build_diagnostic_runtime_manifest.py",
    "proving_ground_mobility_hold_after_s": float(hold),
    "proving_ground_mobility_release_after_s": float(release),
}, sort_keys=True))
PY
    exit 0
fi

player="${CRANE_PLAYER:-${crane_dir}/Builds/CRANE-Worker/CRANE.x86_64}"
image="${CRANE_ROS_IMAGE:-lunarzdev/astro:cuda}"
expected_build_manifest_sha256="${CRANE_EXPECTED_BUILD_MANIFEST_SHA256:-}"
expected_managed_assemblies_sha256="${CRANE_EXPECTED_MANAGED_ASSEMBLIES_SHA256:-}"
robot_parent="${workspace_root}/data/robot_visible/${data_split}/${run_id}"
evaluator_root="${workspace_root}/data/evaluator_only/${data_split}/${run_id}"
capture_name="crane-capture-${run_id}"

if [[ -z "${expected_build_manifest_sha256}" || -z "${expected_managed_assemblies_sha256}" ]]; then
    echo "Actual runs require prospectively pinned CRANE_EXPECTED_BUILD_MANIFEST_SHA256 and CRANE_EXPECTED_MANAGED_ASSEMBLIES_SHA256" >&2
    exit 2
fi

if [[ -e "${robot_parent}" || -e "${evaluator_root}" ]]; then
    echo "Refusing existing run path for ${run_id}" >&2
    exit 1
fi
for required in "${player}" "${catalog_file}" "${nav2_params}" "${bt_xml}"; do
    if [[ ! -f "${required}" ]]; then
        echo "Required capture artifact is absent: ${required}" >&2
        exit 1
    fi
done

runtime_staging="$(mktemp -d -t crane-diagnostic-runtime-XXXXXXXX)"
runtime_manifest="${runtime_staging}/runtime-manifest.json"

cleanup() {
    if docker inspect "${capture_name}" >/dev/null 2>&1; then
        docker logs "${capture_name}" >"${robot_parent}/capture.log" 2>&1 || true
        docker stop --time 10 "${capture_name}" >/dev/null 2>&1 || true
    fi
    if [[ -d "${runtime_staging}" ]]; then
        rm -r "${runtime_staging}"
    fi
}
trap cleanup EXIT INT TERM

mkdir -p "${robot_parent}" "${evaluator_root}"
python3 "${script_dir}/record_build_provenance.py" \
    --player "${player}" --checkout "${crane_dir}" \
    --output "${evaluator_root}/build-provenance.json"
python3 "${workspace_root}/analysis/validate_diagnostic_player_build.py" \
    --provenance "${evaluator_root}/build-provenance.json" \
    --checkout "${crane_dir}" \
    --player "${player}" \
    --catalog "${catalog_file}" \
    --expected-build-manifest-sha256 "${expected_build_manifest_sha256}" \
    --expected-managed-assemblies-sha256 "${expected_managed_assemblies_sha256}" \
    --output "${evaluator_root}/player-build-audit.json"
python3 "${script_dir}/build_diagnostic_runtime_manifest.py" \
    --output "${runtime_manifest}" \
    --run-id "${run_id}" \
    --image "${image}" \
    --umbrella-checkout "${workspace_root}" \
    --crane-checkout "${crane_dir}" \
    --astro-checkout "${astro_dir}" \
    --nav2-params "${nav2_params}" \
    --bt-xml "${bt_xml}" \
    --environment-catalog "${catalog_file}" \
    --player-provenance "${evaluator_root}/build-provenance.json" \
    --scene "${scene}" \
    --platform "turtlebot3-waffle-differential" \
    --nav2-profile "train-cpu" \
    --goal-distance-m "${goal_distance_m}" \
    --action-duration-s "${action_duration_s}" \
    --command-flag="${command_flag}" \
    --lidar-frame "${lidar_frame}"

bt_container="/workspace/crane_sim/${bt_xml#"${crane_dir}/"}"
docker run -d --rm --name "${capture_name}" --network host --ipc host \
    -e ROS_DOMAIN_ID="${ros_domain_id}" \
    -v "${astro_dir}:/workspace/astro_dock:ro" \
    -v "${crane_dir}:/workspace/crane_sim:ro" \
    -v "${robot_parent}:/robot-visible" \
    -v "${runtime_manifest}:/runtime-manifest.json:ro" \
    "${image}" bash -lc \
    'source /opt/ros/jazzy/setup.bash; source /workspace/astro_dock/install/setup.bash; exec /workspace/astro_dock/install/lib/crane_explain_ros/capture --output /robot-visible/capture --episode-id '"${run_id}"'-worker-0 --run-id '"${run_id}"' --bt-xml '"${bt_container}"' --runtime-manifest /runtime-manifest.json' \
    >"${robot_parent}/capture.container-id"
sleep 2
if ! docker inspect "${capture_name}" >/dev/null 2>&1; then
    echo "Capture container exited before fixture startup" >&2
    exit 1
fi

fixture_status=0
CRANE_ASTRO_DOCK="${astro_dir}" \
CRANE_RUN_ID="${run_id}" \
CRANE_RESULT_ROOT="${evaluator_root}" \
CRANE_ROS_DOMAIN_ID="${ros_domain_id}" \
CRANE_ROS_PORT="${ros_port}" \
CRANE_PLAYER="${player}" \
CRANE_SEED_BASE="${layout_seed}" \
CRANE_PROVING_GROUND_CATALOG="${catalog}" \
CRANE_PROVING_GROUND_LAYOUT="${layout}" \
CRANE_NAV2_BT_XML="${bt_xml}" \
CRANE_NAV2_UNITY_EXTRA_ARGS="--crane-land-proving-ground-mobility-hold-after ${proving_ground_mobility_hold_after} --crane-land-proving-ground-mobility-release-after ${proving_ground_mobility_release_after} ${unity_extra_args}" \
bash "${crane_dir}/Tools/Performance/run_land_proving_ground_nav2_fixture.sh" || fixture_status=$?

truth_path="${evaluator_root}/worker-0/land-evaluator-truth.json"
binding_audit="${evaluator_root}/scenario-binding-audit.json"
if [[ ! -f "${truth_path}" ]]; then
    echo "Missing evaluator truth required for scenario-binding admission: ${truth_path}" >&2
    exit 1
fi
python3 "${workspace_root}/analysis/validate_land_scenario_binding.py" \
    --truth "${truth_path}" \
    --catalog "${catalog_file}" \
    --catalog-id "${catalog}" \
    --layout "${layout}" \
    --expected-mobility-hold-after "${proving_ground_mobility_hold_after}" \
    --expected-mobility-release-after "${proving_ground_mobility_release_after}" \
    --output "${binding_audit}"

python3 - "${evaluator_root}/navigation-reset-summary.json" "${fixture_status}" \
    "${evaluator_root}/fixture-exit-status.json" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
status_text = sys.argv[2]
output_path = Path(sys.argv[3])
if not summary_path.is_file():
    raise SystemExit(f"fixture summary is absent after fixture exit: {summary_path}")
summary = json.loads(summary_path.read_text(encoding="utf-8"))
payload = {
    "schema": "crane-diagnostic-fixture-exit-status/v1",
    "fixture_exit_status": int(str(status_text)),
    "fixture_valid_flag": summary.get("valid"),
    "expected_navigation_status": summary.get("expectedNavigationStatus"),
    "expected_outcome_observed": summary.get("expectedOutcomeObserved"),
    "interpretation": (
        "The shared fixture exit includes its generic expected-navigation-status check. "
        "Recording validity, exact scenario binding, and fault-induction success are "
        "evaluated separately for the diagnostic pilot."
    ),
}
output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

cleanup
trap - EXIT INT TERM
