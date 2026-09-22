# RoboBoat navigation baseline

Date: 2026-09-22. This document describes the implementation actually running in the dedicated
`/home/lunarz/worktrees/roboboat-docking` worktree after the validated command-interface and
long-path checkpoints. It supersedes the earlier torque-mode reconnaissance snapshot. The
RoboBoat scene, hydrodynamics, mixer, manual controller, and input bindings were not changed in
this pass.

## Provenance

- Behavior/config checkpoint before this documentation commit: branch `roboboat-docking`, commit
  `6cba6a8b072cfe02ae9af34fdbbe3b740ed0b2de`.
- Gitlinks: `crane_ml` `7195d917f8b838cb5f5606f09f2c1a24be0014a3`, `astro_dock`
  `36202373ae186a8fd247a20b7b477312a744de99`, nested ROS-TCP endpoint
  `3c3d405db665a8c52c28e45f23b8c9782a9564ba`.
- Active Nav2 YAML SHA-256: `d11517f175805cef29555e9c64ac4a5285d27600ca417d755719b13dc6314b4d`.
- ROS adapter SHA-256: `886c1b11c9ec106bc6ec1a19d89281ee7ee5cf61df3bc42f6adc4acbe519265b`.
- Thruster config SHA-256: `ee66af800d106dad50bbdef22e3da97c7102446f91b9b84753958351024bef59`.
- Manual/shared mixer source remains `b846a21a1ea163555c5489b5b0fc3dd29f46f4f93c1fd7e16c48b1c0333e4f83`.
- Unity `6000.5.10f1`; final diagnostic build GUID
  `d698a8a2076c41a2a2f57b0907a4e760`; asset-set SHA-256
  `DEDCDC3B0E7057DBD1C4F5A4CAEB3367DA2213918CC2A505591076FF7D154834`.
- Runtime image `lunarzdev/astro:cuda`, Nav2 `1.3.12`, image digest
  `sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`.

The measurement extension adds only `straight`, `gentle-turn`, and `s-turn` path generation and
records `pathShape`; it does not alter runtime behavior.

## Current architecture

```text
/navigate_to_pose action
  -> bt_navigator (installed default NavigateToPose replanning/recovery tree)
  -> planner_server / Navfn A*
  -> /follow_path action
direct /follow_path -----------------------------------------------+
                                                                    |
  controller_server / Regulated Pure Pursuit, 10 Hz                 |
  -> Twist /nav2/cmd_vel                                            |
  -> fixture stamps latest odometry time                            |
  -> TwistStamped /crane/cmd_vel_stamped                            |
  -> ROS-TCP endpoint (127.0.0.1, per-run port)                      |
  -> ROSOmniXCommand queue, applied at Unity FixedUpdate (50 Hz) <---+
  -> ROS FLU desired body velocity PI/feedforward adapter
  -> normalized surge/sway/yaw effort
  -> OmniXController four-thruster X mixer
  -> shaft-velocity-controlled propellers
  -> quadratic submerged thrust via AddForceAtPosition
  -> articulated catamaran, buoyancy, drag, and Fossen dynamics
  -> CraneROSNavigationState at 50 Hz: /crane/odom plus /tf
  -> controller/costmaps/planner/BT
```

The live launcher is
[`run_nav2_controller_fixture.sh`](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh).
It starts the Nav2 servers directly and remaps Nav2 output to `/nav2/cmd_vel`; the fixture relays
that Twist as stamped `/crane/cmd_vel_stamped`. There is no velocity smoother. Aquatic players use
the dedicated `crane-xvfb-roboboat-goal` Xvfb at `DISPLAY=127.0.0.1:97` with
`CRANE_NOGRAPHICS=0`; the aquatic player is never run with `-batchmode` or `-nographics`.

## Active Nav2 stack

The only default loaded by the launcher is
[`nav2_controller_fixture.yaml`](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml).
`CRANE_NAV2_PARAMS` can explicitly replace it. Land/warehouse and experimental MPPI YAMLs are not
active and are not blended into these values.

| Area | Active value |
|---|---|
| Time/frames | `use_sim_time: true`; global and local frame `odom`; robot frame `base_link`; odometry `/crane/odom` |
| Planner | `nav2_navfn_planner::NavfnPlanner`; A*; unknown allowed; 0.5 m tolerance; expected 5 Hz |
| Controller | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`; 10 Hz; desired linear 0.15 m/s |
| Lookahead | fixed 0.8 m; velocity scaling disabled; collision detection enabled; pose search 10 m |
| Heading/motion | rotate-to-heading disabled; reversing disabled; RPP outputs no `linear.y` in observed runs |
| Approach | scaling distance 2.0 m; minimum approach speed 0.02 m/s |
| Goal checker | stateful `StoppedGoalChecker`; XY 0.40 m; yaw 0.35 rad; stopped translation/yaw 0.05 m/s and 0.05 rad/s |
| Progress checker | `SimpleProgressChecker`; 0.05 m required in 20 s |
| Local costmap | rolling 20 x 20 m; 0.10 m; update 10 Hz/publish 2 Hz; Voxel `/points`; radius 0.80 m; inflation 1.0 m, scale 3.0 |
| Global costmap | rolling 40 x 40 m; 0.20 m; update 5 Hz/publish 1 Hz; no unknown tracking; same radius/layers/inflation |
| Behaviors | Spin, BackUp, DriveOnHeading, Wait at 10 Hz; 0.1-0.5 rad/s rotation, 0.5 rad/s2 acceleration |
| BT | installed default `navigate_to_pose_w_replanning_and_recovery.xml`; replanning at 1 Hz |
| Command limits | no velocity smoother; RPP 0.15 m/s linear; behavior max yaw 0.5 rad/s; adapter input scales 1 m/s and 1 rad/s |

Installed Jazzy controller libraries include RPP, DWB, MPPI, Graceful, and Rotation Shim. RPP is
the active controller and has no critic framework. MPPI tests were alternatives only: its default
PathAngle behavior spun, and removing PathAngle did not recover a matched route. Therefore a
critic is not the cause of the current RPP failure, although it was relevant to the rejected MPPI
candidate.

RPP assumes forward curvature-constrained motion. It consumes path orientation, generates
`linear.x` and `angular.z`, and does not use the vessel's available holonomic sway. Near the goal it
slows through approach scaling and requires both pose tolerance and stopped velocity. Acceleration
is not limited by a velocity smoother. These assumptions only partially match an omnidirectional,
inertial surface vessel; existing straight-path evidence does not by itself justify replacing it.

## Boat command contract

At the Unity boundary, Nav2 values are desired ROS FLU body velocities, not direct force or
normalized thrust:

| ROS field | Current meaning |
|---|---|
| `linear.x` | desired body-forward surge, m/s |
| `linear.y` | desired body-left sway, m/s |
| `angular.z` | desired counter-clockwise yaw rate, rad/s |

`ROSOmniXCommand` clamps translation to +/-1 m/s and yaw to +/-1 rad/s, samples measured local body
velocity from the physics body, and applies a ROS-only controller at 50 Hz. Translation uses linear
feedforward 0.21, Kp 0.1, Ki 0.1, and integral-effort limit 0.2. Yaw uses square-root feedforward
0.24 and Kp 0.05. Resulting normalized effort is clipped to `[-1,1]`. Latest commands time out
after 25 physics ticks (0.5 simulated seconds), then all axes are zeroed. Queue/reset/timeout
application occurs only on `FixedUpdate`.

ROS FLU to Unity/controller signs were verified against odometry: controller X realizes positive
ROS surge, controller Y realizes positive ROS sway, and controller yaw is negated so positive ROS
yaw feedback remains counter-clockwise. Linear position/velocity convert Unity to ROS as
`(z,-x,y)`; angular velocity, an axial vector under the reflection, converts as `(-z,x,-y)`.

Manual W/S, A/D, Q/E control does not pass through this velocity adapter. Manual input and the
shared mixer were not modified.

## Thruster model

Four horizontal thrusters are front-left, front-right, rear-left, and rear-right. For normalized
controller request `(x,y,r)` the unchanged rank-three mixer is:

```text
FL = -x - y - r       FR = +x - y + r
RL = -x + y + r       RR = +x + y - r
```

All four channels are divided by `max(1,max(abs(channel)))`, preserving ratios at saturation. The
matrix has independent surge, sway, and yaw columns; symmetric pure-axis requests cancel the other
two net axes in the algebra. No sign inconsistency was observed in isolated body-response tests.

URDF origins `(x,y,z)` in metres are FR `(0.01287,0.26636,-0.28432)`, RR
`(0.01282,-0.26630,-0.28432)`, FL `(-0.01287,0.26637,-0.28232)`, and RL
`(-0.01277,-0.26625,-0.28232)`. The active config is shaft-velocity mode with command range
`[-1,1]` mapped to +/-500 rad/s; reverse uses the same coefficient. The unchanged propeller model
uses local Y as its force axis, `thrustK=-0.014`, 0.03 m full-submersion height, quadratic shaft
speed, and `AddForceAtPosition` at each thruster articulation. Shaft-velocity mode restored
monotonic partial-command response while retaining the configured full-stick top end.

## Physical model

The boat remains an articulated catamaran. Scene overrides include base-link mass 3 kg, COM
Y=-0.23 m, linear damping 4, angular damping 15, and inertia `(10,15,10)`; child links add mass and
the hull link is 8 kg. Gravity is enabled. Buoyancy integrates submerged mesh triangles.
GeneralDynamics pressure/suction/viscous drag uses linear coefficient 100 and quadratic 30.
Scene-enabled Fossen dynamics use added mass `(6,8,2)` kg and rotational
`(0.15,0.25,0.35)` kg m2; linear damping `(30,40,150)`, rotational `(8,12,20)`, and quadratic
terms `(25,35,40)` / `(3,6,30)`. The physics step is 0.02 s.

The repository does not identify these coefficients as measured or calibrated; treat them as
estimated/arbitrary unless provenance is added. The human reports that motion looks and feels
realistic, and no hydrodynamic, mass, inertia, buoyancy, drag, water, or force-law value changed.

## Geometry and frames

Odometry publishes `odom -> base_link`; sensor transforms include `lidar_link`,
`front_camera_link`, `imu_link`, and `gps_link` at 50 Hz. `/points` is `lidar_link` data at 10 Hz.
Unity X-right/Y-up/Z-forward maps to ROS FLU X=Unity Z, Y=-Unity X, Z=Unity Y.

The LiDAR/sensor mount and catamaran noses are the physical bow. The Blastoise head is aft. The
physical envelope is approximately 0.895 x 1.063 m. Nav2's 0.80 m circular radius is conservative:
its 1.60 m diameter exceeds the physical beam by about 0.54 m. Berth dividers are about 2 m apart,
leaving about 0.40 m logical diametral clearance before inflation. The additional 1.0 m inflation
can make an otherwise physically traversable berth very costly or infeasible.

The tested far target is ROS odom `(0.8641434,-24.586906)`, yaw `-pi/2`, corresponding to the far
assembly's near berth. That yaw uses the LiDAR/catamaran bow as forward, not the character head.

## Existing capabilities and evidence

The current harness measures full odometry trajectory, cross-track and heading error for supplied
paths, body velocity, action/final pose, command extrema, transport timing, costmap occupancy,
recovery logs, navigation status, water validity, and real-time factor. It does not yet provide an
independent hull-contact, minimum-clearance, berth-region-membership, or stopped-settle predicate.
No RoboBoat rosbag was found.

- Body-command characterization at +/-0.2 produced tail surge +0.170/-0.139 m/s, sway
  +0.165/-0.164 m/s, and yaw approximately +/-0.208 rad/s. High Kp 0.5 was unstable and rejected.
- Three 10 m straight FollowPath runs succeeded: RMS cross-track 0.0025-0.0026 m, max
  0.0083-0.0093 m, settled speed 0.0196-0.0214 m/s, settled XY error 0.236-0.253 m.
- Two 30 m straight runs with fixed 0.8 m lookahead succeeded: RMS 0.0022-0.0023 m, max
  0.0086-0.0119 m, max yaw 0.029-0.032 rad/s, settled error 0.245-0.248 m. The matched
  velocity-scaled-lookahead run looped near the goal and timed out.
- A 15 m / +45 degree supplied path tracked at RMS/max 0.036/0.054 m until RPP predicted collision
  with course geometry; this was an invalid route rather than free-water instability.
- The mirrored 15 m / -45 degree path reached 0.224 m but timed out in terminal yaw oscillation.
  A ROS-only 0.1 rad/s yaw cap was tested as a single-variable diagnostic and rejected: it enlarged
  final error to 0.856 m and heading error to 1.985 rad. The cap was removed before the final build.

### Far-dock NavigateToPose baseline

Artifact
`packages/crane_ml/PerformanceResults/roboboat-far-dock-nav2-baseline-1/fixture-summary.json`,
SHA-256 `e52fc9d3333cc9578d332f6176b0bf45405dd3831ab91eeb9f6f474f7694a015`:

- requested pose `(0.8641434,-24.586906,-pi/2)`; occupied costmap evidence required;
- action accepted once and traveled 16.17 m from `(-2.271,-5.027)`;
- action aborted after 133.08 s at `(-0.788,-20.938)`, about 4.0 m from the requested pose;
- result yaw was `+1.283 rad`, nearly opposite the requested dock yaw;
- maximum Nav2 angular command was 0.5 rad/s; body yaw rate at result was 0.111 rad/s;
- after 8.05 s, coast was 0.191 m and final body speed was 0.0191 m/s;
- costmap was populated (maximum 8,643 occupied cells), transport had no rejected/stale/cross-
  episode commands, and water observations had no failures.

Controller logs identify the terminal cause. Beginning near `(-1.84,-18.83)`, Navfn repeatedly
reported `Failed to create plan with tolerance of: 0.500000`. The default BT cleared global and
local costmaps and ran Spin, Wait, and BackUp recoveries; no replan became feasible, so
`navigate_to_pose` aborted and canceled FollowPath. This test definitively shows that current
far-dock navigation is not fixed. It does not prove whether the infeasibility is caused by the
0.80 m logical radius, 1.0 m inflation, exact goal placement, sensed dock geometry, or a
combination.

## Baseline assessment

### What works

- The full ROS/Unity command and odometry/TF loop is stable and time-consistent.
- Surge, sway, and yaw signs are verified; the ROS boundary now represents desired body velocity.
- Manual control remains on its previous direct path and full-stick capability is preserved.
- RPP repeatedly tracks 10 m and 30 m straight supplied paths with centimetre-scale error and
  stopped arrivals.
- The physical catamaran fits a nominal 2 m berth by mesh dimensions.

### Observed limitations

- RPP does not exploit holonomic sway and can enter terminal yaw/path-pruning oscillation on a
  curved supplied path.
- The far-dock global plan becomes infeasible roughly 4 m before the goal. Recovery behaviors do
  not make it feasible.
- The logical 0.80 m circle plus 1.0 m inflation is much more conservative than the physical hull
  and is a leading explanation for the dock-entry failure.
- No independent docking-success predicate checks contact, clearance, berth membership, and
  stopped settling.

### Evidence gaps

- Distance-transform clearance at the exact target and along the last 5 m of the captured global
  costmap.
- A recorded sequence of global plans/costmaps showing the first infeasible replan.
- Independent dock-region/contact/clearance/stopped-settle measurement.
- Repeated feasible turns/S-turns and repeated dock approaches after, not before, geometry is
  shown feasible.

## Ranked hypotheses and falsifiers

1. **Footprint/costmap/goal clearance.** The radius/inflation or target cell makes the final berth
   unreachable. Confirm if a distance transform shows less than 0.80 m obstacle clearance at the
   goal or no connected collision-free corridor; falsify if the current captured grid contains a
   valid corridor and goal neighborhood for the active radius.
2. **Planner/final path geometry.** Rolling Navfn replanning loses a dock-aligned route as the boat
   approaches. Confirm by retaining successive plans and locating the first geometric
   discontinuity/failure; falsify if a stable collision-free final plan exists throughout.
3. **Controller/path orientation.** RPP's forward-only curvature and terminal orientation handling
   causes the mirrored-turn limit cycle. Confirm with a supplied feasible final curve that repeats
   the oscillation while planner feasibility remains true; falsify with repeated stopped success.
4. **Goal/progress checking.** Current stopped thresholds could delay success, but they cannot
   explain Navfn's explicit no-plan abort. Confirm only if feasible paths reach tolerance while the
   checker remains false; falsify when pose and speed predicates agree with action success.
5. **Command interface.** Current PI mapping could limit aggressive curvature. The rejected yaw
   cap shows simply reducing yaw authority is harmful. Confirm with requested-vs-measured tracking
   error on a feasible curve; falsify if body response follows command while path error grows.
6. **Boat physics.** Least likely given realistic human assessment and excellent straight-path
   evidence. Elevate only if feasible-path tests show implausible measured response after the
   above causes are falsified.

## Smallest next experiment

Perform a read-only footprint/dock-clearance audit on the retained far-run global costmap: map the
exact goal and final 5 m approach into grid cells, compute obstacle distance/connected free space,
and evaluate separately against the physical hull envelope, active 0.80 m radius, and 1.0 m
inflation. This single measurement distinguishes an invalid goal/corridor from planner or
controller failure without tuning Nav2, changing the environment, or touching boat physics.
