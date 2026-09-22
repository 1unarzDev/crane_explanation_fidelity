# RoboBoat dynamics validation

Status: the ROS body-axis/sign contract passes on the original manual plant. Unity physics and
hydrodynamic parameters remain unchanged.

The production `TwistStamped` boundary was exercised with ±0.2 surge, sway, and yaw requests plus
zero-command coast intervals. The reproducible launcher and analyzer are
`packages/crane_ml/Tools/Performance/run_roboboat_command_response.sh` and
`roboboat_command_response_fixture.py`.

Authoritative results are summarized in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md). On the final
manual-preserving build, +0.2 produces +1.107 m/s surge, +0.959 m/s sway, and +0.788 rad/s yaw on
their intended axes. This validates ROS mapping but proves the boundary is normalized effort, not
closed-loop desired velocity.

No physics coefficient, mass, inertia, drag, buoyancy, water, thrust, scene, environment, manual
controller, input binding, mixer, or thruster source changed. Gate 1 still needs formal
multi-amplitude latency, saturation, and stopping-distance/time measurements.
