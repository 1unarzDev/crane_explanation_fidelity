set -euo pipefail
set +u
source /ws/install/setup.bash
set -u
export CYCLONEDDS_URI=file:///provenance/cyclonedds.xml
export HEXAR_EPISODE_SEED=1489732681 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export PATH=/acquisition/bin:$PATH LIBGL_ALWAYS_SOFTWARE=1 GAZEBO_MODEL_DATABASE_URI=''
xvfb-run -a ros2 launch tiago_gazebo tiago_gazebo.launch.py is_public_sim:=True arm_type:=no-arm navigation:=True moveit:=False rviz:=False gzclient:=False tuck_arm:=False world_name:=home > /provenance/runtime.log 2>&1 &
launch_pid=$!
trap 'kill -INT "$launch_pid" 2>/dev/null || true' EXIT
python3 /acquisition/wait_ready.py --timeout 90 > /provenance/readiness.log 2>&1
python3 /acquisition/controller_probe.py --output /provenance/observed_controller.json
