#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 RUN_ID ROS_DOMAIN_ID ROS_TCP_PORT" >&2
    exit 2
fi
run_id="$1"
ros_domain_id="$2"
ros_port="$3"
if [[ ! "${run_id}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "RUN_ID may contain only letters, numbers, dot, underscore, and dash" >&2
    exit 2
fi
if [[ -z "${CRANE_SEED_BASE:-}" ]]; then
    echo "CRANE_SEED_BASE is required; do not append a duplicate --crane-seed flag" >&2
    exit 2
fi

astro_dir="${workspace_root}/packages/astro_dock"
crane_dir="${workspace_root}/packages/crane_ml"
player="${CRANE_PLAYER:-${crane_dir}/Builds/CRANE-Worker/CRANE.x86_64}"
bt_xml="${CRANE_NAV2_BT_XML:-${crane_dir}/Tools/Performance/nav2_land_progress_recovery.xml}"
nav2_params="${crane_dir}/Tools/Performance/nav2_land_fixture.yaml"
image="${CRANE_ROS_IMAGE:-lunarzdev/astro:cuda}"
scene="${CRANE_SCENE:-Land Vehicle Validation}"
command_flag="${CRANE_NAV2_COMMAND_FLAG:---crane-ros-ackermann-cmd-vel}"
lidar_frame="${CRANE_NAV2_LIDAR_FRAME:-lidar_link}"
data_split="${CRANE_DATA_SPLIT:-dev}"
if [[ "${data_split}" != "dev" && "${data_split}" != "final" ]]; then
    echo "CRANE_DATA_SPLIT must be dev or final: ${data_split}" >&2
    exit 2
fi
robot_parent="${workspace_root}/data/robot_visible/${data_split}/${run_id}"
evaluator_root="${workspace_root}/data/evaluator_only/${data_split}/${run_id}"
capture_name="crane-capture-${run_id}"

if [[ -e "${robot_parent}" || -e "${evaluator_root}" ]]; then
    echo "Refusing existing run path for ${run_id}" >&2
    exit 2
fi
if [[ "${bt_xml}" != "${crane_dir}"/* || ! -f "${bt_xml}" ]]; then
    echo "BT XML must be an existing file below packages/crane_ml: ${bt_xml}" >&2
    exit 2
fi
runtime_staging="$(mktemp -d -t crane-runtime-manifest-XXXXXXXX)"
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
python3 "${script_dir}/build_runtime_manifest.py" \
    --output "${runtime_manifest}" \
    --run-id "${run_id}" \
    --image "${image}" \
    --umbrella-checkout "${workspace_root}" \
    --crane-checkout "${crane_dir}" \
    --astro-checkout "${astro_dir}" \
    --nav2-params "${nav2_params}" \
    --bt-xml "${bt_xml}" \
    --player-provenance "${evaluator_root}/build-provenance.json" \
    --scene "${scene}" \
    --platform "turtlebot3-waffle-differential" \
    --nav2-profile "train-cpu" \
    --goal-distance-m "${CRANE_NAV2_GOAL_DISTANCE:-3.0}" \
    --action-duration-s "${CRANE_NAV2_ACTION_DURATION:-20}" \
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
CRANE_NAV2_BT_XML="${bt_xml}" \
bash "${crane_dir}/Tools/Performance/run_land_nav2_fixture.sh"

cleanup
trap - EXIT INT TERM
