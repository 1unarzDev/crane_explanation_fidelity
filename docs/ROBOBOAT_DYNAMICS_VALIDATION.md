# RoboBoat dynamics validation

Status: Gate 1 passes for the corrected Nav2 interface. Unity physics and hydrodynamic parameters
remain unchanged.

The production `TwistStamped` boundary was exercised with ±0.2 surge, sway, and yaw requests plus
zero-command coast intervals. The reproducible launcher and analyzer are
`packages/crane_ml/Tools/Performance/run_roboboat_command_response.sh` and
`roboboat_command_response_fixture.py`.

The baseline torque-mode response made every tested nonzero yaw request saturate the shafts near
100 rad/s. Velocity mode restored monotonic shaft/body response. A ROS-only PI adapter closes the
loop on measured FLU body velocity at FixedUpdate; translational feedforward is linear in desired
velocity, yaw retains the measured square-root inverse, and bounded translational integral action
removes mixed-axis static error. The accepted full fixture at `linear Ki=0.10` produced tails of
+0.170/-0.139 m/s surge, +0.165/-0.164 m/s sway for +/-0.2 requests, and
0.180/0.160/0.169 for a combined 0.15 surge/sway/yaw request. The corresponding artifact is
`PerformanceResults/roboboat-body-velocity-controller-pi010-1`.

No physics coefficient, mass, inertia, drag, buoyancy, water, force law, scene, environment,
manual-controller source, input binding, or mixer changed. Full manual stick retains the configured
shaft-speed top end; partial stick now requests proportional shaft speed instead of immediately
saturating torque. The focused editor contract suite passes 4/4. Gate 1 is complete; longer path
tests remain responsible for exposing sustained mixed-axis behavior.
