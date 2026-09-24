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
if [[ "${catalog}" != "v4" ]]; then
    echo "Only the versioned diagnostic catalog v4 is supported: ${catalog}" >&2
    exit 2
fi

astro_dir="${workspace_root}/packages/astro_dock"
crane_dir="${workspace_root}/packages/crane_ml"
catalog_file="${crane_dir}/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v4.json"
nav2_params="${crane_dir}/Tools/Performance/nav2_land_proving_ground_fixture.yaml"
bt_xml="${crane_dir}/Tools/Performance/nav2_roboboat_distance_replanning.xml"
scene="TurtleBot3 Warehouse Validation"
command_flag="--crane-ros-differential-cmd-vel"
lidar_frame="base_scan"
goal_distance_m="18.0"
action_duration_s="100"
data_split="${CRANE_DATA_SPLIT:-dev}"

if [[ "${data_split}" != "dev" ]]; then
    echo "Diagnostic held-out/final capture is not authorized before protocol freeze" >&2
    exit 2
fi
layout_metadata_text="$(python3 - "${catalog_file}" "${layout}" <<'PY'
import json
import sys

catalog_path, layout_id = sys.argv[1:]
catalog = json.load(open(catalog_path, encoding="utf-8"))
matches = [item for item in catalog.get("layouts", []) if item.get("id") == layout_id]
if len(matches) != 1:
    raise SystemExit(f"layout must resolve exactly once in catalog: {layout_id}")
layout = matches[0]
if layout.get("studySplit") == "confirmatory":
    raise SystemExit("confirmatory layouts are sealed until protocol freeze")
if layout.get("studySplit") != "development":
    raise SystemExit("layout is calibration-only or outside the active diagnostic scope")
if layout.get("diagnosticMechanism") not in {"connected-detour", "nominal-clear-route"}:
    raise SystemExit("layout is calibration-only or outside the active diagnostic scope")
print(layout["seed"])
print(layout["diagnosticMechanism"])
PY
)"
mapfile -t layout_metadata <<<"${layout_metadata_text}"
layout_seed="${layout_metadata[0]}"

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
        "${layout_seed}" "${layout_metadata[1]}" <<'PY'
import json
import sys

run_id, domain, port, catalog, layout, layout_seed, mechanism = sys.argv[1:]
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
    "bt_xml": "packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml",
    "command_flag": "--crane-ros-differential-cmd-vel",
    "lidar_frame": "base_scan",
    "goal_distance_m": 18.0,
    "action_duration_s": 100,
    "runtime_manifest_builder": "scripts/build_diagnostic_runtime_manifest.py",
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

CRANE_ASTRO_DOCK="${astro_dir}" \
CRANE_RUN_ID="${run_id}" \
CRANE_RESULT_ROOT="${evaluator_root}" \
CRANE_ROS_DOMAIN_ID="${ros_domain_id}" \
CRANE_ROS_PORT="${ros_port}" \
CRANE_PLAYER="${player}" \
CRANE_SEED_BASE="${layout_seed}" \
CRANE_PROVING_GROUND_CATALOG="${catalog}" \
CRANE_PROVING_GROUND_LAYOUT="${layout}" \
bash "${crane_dir}/Tools/Performance/run_land_proving_ground_nav2_fixture.sh"

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
    --output "${binding_audit}"

cleanup
trap - EXIT INT TERM
