# RoboBoat navigation development

Status: Gates 1-8 pass for the current development configuration. The active controller remains
Regulated Pure Pursuit under
`packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml` (SHA-256
`047e0981aee88fb1e8833aabefe718a35ab2be49925dd95640139ac7b401385c`). Unity physics,
the thruster mixer, the scene, and the manual controller are unchanged.

The active stack is Navfn A* plus forward-only RPP at 10 Hz, 0.15 m/s desired speed, fixed 0.8 m
lookahead, 2 m approach scaling, and 0.02 m/s minimum approach speed. It uses
`StoppedGoalChecker` at 0.20 m XY, 0.35 rad yaw, 0.05 m/s translation, and 0.05 rad/s yaw rate;
`SimpleProgressChecker` requires 0.05 m in 20 s. The local/global maps are 20 x 20 m and
60 x 60 m. Both use `odom`, `base_link`, a 0.80 m robot radius, and 1.0 m inflation. There is no
velocity smoother. RPP emits `linear.x` and `angular.z`, never `linear.y` in these runs.

The ROS boundary interprets `TwistStamped` as desired FLU body surge, sway, and yaw rate. A
ROS-only PI/feedforward adapter converts those velocities to normalized effort before the
unchanged four-thruster X mixer. Manual W/S, A/D, Q/E input bypasses that adapter and has not been
modified.

## Validation progression

- Gate 1: positive/negative surge, sway, yaw, combined commands, and coast were characterized.
- Gate 2: three 10 m straights succeeded at 0.0025-0.0026 m RMS cross-track error.
- Gate 3: two 30 m straights succeeded at 0.0022-0.0023 m RMS cross-track error. The rejected
  velocity-scaled-lookahead alternative looped near the goal.
- Gate 4: two 15 m gentle turns succeeded at 0.0247-0.0248 m RMS cross-track error; two 15.63 m
  S-turns succeeded at 0.0340-0.0345 m. A prior positive-turn abort was an invalid route through
  course geometry, not a free-water control defect.
- Gates 5-6: the 34.62 m known dock path succeeded three consecutive times after the XY checker
  changed from 0.40 m to 0.20 m. RMS cross-track was 0.0316-0.0319 m; all three independently
  satisfied full-hull containment, stopped state, pose, five-second settle, and zero-contact
  requirements.
- Gates 7-8: the retained docking-development set contains ten independently evaluated attempts:
  nine physical successes overall and 8/8 after the checker correction. Five post-change full
  `NavigateToPose` trials from about 23 m away all docked. Three were strict-valid end to end; two
  were excluded from generic validity solely by a transient depth-camera GPU readback error. None
  had a navigation, command-transport, water, or contact failure.

The decisive matched result was terminal margin. With the former 0.40 m Nav2 XY tolerance, the
known path returned at 0.374 m while moving 0.0486 m/s, then coasted 0.188 m to 0.559 m and failed
the frozen 0.40 m independent predicate. At 0.20 m, three matched runs returned at 0.194-0.198 m,
coasted 0.182-0.185 m, and settled at 0.375-0.382 m. No speed, controller, adapter, mixer, or
physics parameter changed.

The corrected far target is `(0.8641434,-27.586906,+pi/2)`, on the open side of the rotated far
dock. `+pi/2` points the LiDAR/catamaran noses (the bow) toward ROS `+Y`; the Blastoise head is
aft. Full planning succeeded in all five post-change trials. Settled results spanned 0.205-0.224 m
XY, 0.264-0.345 rad yaw, 0.016-0.042 m/s, and 0.185-0.190 m post-result coast with zero contacts.

The active RPP controller has no critics. The reported aggressive circles therefore cannot be an
active critic defect. Circling was reproduced only in rejected MPPI or velocity-scaled-lookahead
experiments. Current RPP makes a strong terminal turn and sometimes finishes close to the 0.35 rad
yaw boundary, but the retained far-goal runs do not show sustained positional looping.

Plots retained under [`research/roboboat-navigation-plots`](research/roboboat-navigation-plots)
cover planned versus actual trajectory, tracking/heading error, commanded versus measured body
motion, distance to goal, and final approach. Full architecture, configuration identities,
commands, artifacts, limitations, and evidence gaps are in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md).
