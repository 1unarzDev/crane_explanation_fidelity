#!/bin/bash
# Inside an isolated, fresh container. This cannot run confirmation.
set -euo pipefail
family=${1:?family}; seed=${2:?seed}; episode_id=${3:?episode id}
[[ "$family" =~ ^(success|obstacle|dynamic_env|localization|charging|manual_joystick)$ ]] || exit 64
[[ "$episode_id" =~ ^hexar-tiago-dev-[a-z_]+-[0-9]+$ ]] || exit 64
[[ "$seed" =~ ^[0-9]+$ ]] || exit 64
output_dir=/provenance/$episode_id
[[ ! -e "$output_dir" ]] || exit 73
mkdir "$output_dir"
set +u
source /ws/install/setup.bash
set -u
export HEXAR_EPISODE_SEED="$seed" RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export PATH=/acquisition/bin:$PATH LIBGL_ALWAYS_SOFTWARE=1 GAZEBO_MODEL_DATABASE_URI=''
# Each run starts fresh processes; reused qualification containers are disallowed by host runner.
xvfb-run -a ros2 launch tiago_gazebo tiago_gazebo.launch.py is_public_sim:=True arm_type:=no-arm navigation:=True moveit:=False rviz:=False gzclient:=False tuck_arm:=False world_name:=home > "$output_dir/runtime.log" 2>&1 &
launch_pid=$!
recorder_pid=''
cleanup() {
 if [[ -n "$recorder_pid" ]]; then
  kill -INT "$recorder_pid" 2>/dev/null || true
  for ((attempt=0; attempt<40; attempt++)); do
   kill -0 "$recorder_pid" 2>/dev/null || break
   sleep .25
  done
  kill -TERM "$recorder_pid" 2>/dev/null || true
  wait "$recorder_pid" 2>/dev/null || true
 fi
 kill -INT "$launch_pid" 2>/dev/null || true
}
trap cleanup EXIT
# Readiness is measured, never inferred from a sleep.
python3 /acquisition/wait_ready.py --timeout 90 > "$output_dir/readiness.log" 2>&1
ros2 bag record --include-hidden-topics -o "$output_dir/raw" /clock /rosout /tf /tf_static /scan_raw /mobile_base_controller/odom /amcl_pose /task_info /joy_priority /power/is_charging /cmd_vel /mobile_base_controller/cmd_vel_out /navigate_to_pose/_action/status /hexar_acquisition/navigation_goal > "$output_dir/recorder.log" 2>&1 &
recorder_pid=$!
python3 /acquisition/episode_driver.py --family "$family" --seed "$seed" --timeout 35 --output "$output_dir/episode.json" > "$output_dir/driver.log" 2>&1
python3 /acquisition/probe_ros.py --duration 5 --output "$output_dir/runtime_probe.json"
