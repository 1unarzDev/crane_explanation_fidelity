# RoboBoat dynamics validation

Status: Gate 1 and the complete navigation/docking progression pass without changing the Unity
physical model, hydrodynamics, mixer, or manual controller.

The production `TwistStamped` boundary was exercised with positive and negative 0.2 surge, sway,
and yaw requests, combined commands, and zero-command coast intervals. The reproducible launcher
and analyzer are `packages/crane_ml/Tools/Performance/run_roboboat_command_response.sh` and
`roboboat_command_response_fixture.py`.

At the ROS boundary, `linear.x`, `linear.y`, and `angular.z` are desired FLU body surge (m/s),
sway (m/s), and counter-clockwise yaw rate (rad/s). `ROSOmniXCommand` clamps translation and yaw
to +/-1 in their respective units, runs at the 50 Hz Unity physics boundary, and zeros commands
after 25 ticks (0.5 simulated seconds). It uses linear feedforward 0.21, translation Kp/Ki
0.1/0.1 with 0.2 integral-effort limit, yaw square-root feedforward 0.24, and yaw Kp 0.05.

The accepted response fixture produced steady tails of +0.170/-0.139 m/s surge,
+0.165/-0.164 m/s sway for +/-0.2 requests, approximately +/-0.208 rad/s yaw, and
0.180/0.160/0.169 for a combined 0.15 surge/sway/yaw request. A higher translation Kp of 0.5 was
unstable and was rejected. Current long routes show measured surge tracking the 0.15 m/s command,
bounded turn transients, and repeatable 0.182-0.190 m coast after result.

The unchanged normalized X mixer is:

```text
FL = -x - y - r       FR = +x - y + r
RL = -x + y + r       RR = +x + y - r
```

It normalizes all four channels together when any magnitude exceeds one, preserving ratios. The
three allocation columns are independent and symmetric; isolated-axis measurements verified ROS
surge, sway, and yaw signs. Thrusters remain in shaft-velocity mode at +/-500 rad/s, with quadratic
submerged thrust applied by `AddForceAtPosition` at each articulated thruster.

No mass, center of mass, inertia, damping, buoyancy, water interaction, force law, scene geometry,
manual-controller source, or input binding changed during navigation tuning. The retained Unity
model remains the physically credible baseline reported by the human. There is currently no
quantitative evidence justifying a hydrodynamic change.

The remaining dynamics evidence gap is a dedicated multi-speed stopping-distance table. Docking
runs consistently measure about 0.19 m of post-result coast, which is sufficient for the accepted
goal-checker correction but is not a substitute for a full plant-identification campaign.
