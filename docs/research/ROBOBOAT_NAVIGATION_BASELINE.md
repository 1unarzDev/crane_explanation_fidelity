# RoboBoat navigation baseline (static reconnaissance)

Date: 2026-09-21. This is a primary-source static and runtime audit of the current dedicated
RoboBoat worktree. It changes no navigation, scene, or physics behavior.

## Provenance and scope

- Checkout: `/home/lunarz/worktrees/roboboat-docking`, branch `roboboat-docking`, superproject
  `9a0caa68af31e1cbe6c19a65def3e9e6309d34db`; the worktree was clean before this document.
- Gitlinks: `packages/astro_dock` at `36202373ae186a8fd247a20b7b477312a744de99`, its nested
  `src/ros_tcp_endpoint` at `3c3d405db665a8c52c28e45f23b8c9782a9564ba`, and
  `packages/crane_ml` at `c559932a5ebef00bfa7752511799fd904e5c9dbe`.
- “Active” below means the path selected by the repository's RoboBoat Nav2 fixture. The launcher
  permits environment overrides for image, scene, parameter file, BT, topics, and command scales;
  therefore an arbitrary external invocation is not reproducible without its environment. The
  defaults select `Roboboat Course`, `nav2_controller_fixture.yaml`, and the command/state flags
  shown below [launcher lines 7-27, 90-111](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh#L7).
- Content identities (SHA-256): active YAML `20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`;
  launcher `92d5bb03d9750bbd9298cb6fd0690e8f6a1739e566f2e3f53d217145f545df03`;
  command adapter `56ec3572ffd6989b1e53823db3ad0348b211e1045f4cb3e3901dcc16943eaf0c`;
  mixer `b846a21a1ea163555c5489b5b0fc3dd29f46f4f93c1fd7e16c48b1c0333e4f83`;
  active scene `db1399a23ff791dcf49d389381cf6f745169b671b8fb87fdc8ddeebe2342ed84`;
  Blastoise prefab `83ca73e37197c0eb49949210d4cb73724ce11c16554cdbd2a7ba90e5be9824c1`.

## Current architecture

```text
/navigate_to_pose (default) or /follow_path
  -> bt_navigator -> planner_server / Navfn (NavigateToPose only)
  -> controller_server / Regulated Pure Pursuit
  -> Twist /nav2/cmd_vel
  -> fixture stamps newest /crane/odom time, publishes TwistStamped /crane/cmd_vel_stamped
  -> ROS-TCP endpoint -> Unity ROSOmniXCommand (fixed-step queue, normalize/clamp)
  -> OmniXController four-channel X mixer -> four torque-controlled Thruster components
  -> quadratic, submerged AddForceAtPosition -> articulated Blastoise + buoyancy/drag
  -> CraneROSNavigationState at 50 Hz: /crane/odom and /tf (odom -> base_link + sensor children)
  -> Nav2 controller/costmaps/BT
```

The shell starts exactly `controller_server`, `planner_server`, `behavior_server`, `bt_navigator`,
and a lifecycle manager; it remaps controller and behavior `cmd_vel` to `/nav2/cmd_vel`
[launcher lines 64-70](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh#L64).
The fixture subscribes to that unstamped Twist and republishes a TwistStamped command paired with
the latest delivered odometry [fixture lines 58-90](../../packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py#L58),
[lines 169-186](../../packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py#L169). This is
bounded transport provenance, not proof of Nav2's internal odometry sample selection.

## Active Nav2 stack

The default parameter identity is
[`Tools/Performance/nav2_controller_fixture.yaml`](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml),
selected at launcher lines 25-32. `CRANE_NAV2_PARAMS` can replace it; no other RoboBoat launch path
was found. `nav2_land_fixture.yaml` and its launcher are land-only alternatives, not blended into
this configuration.

| Area | Current default |
|---|---|
| Clock / frames / odometry | `use_sim_time: true`; global/local frame `odom`; robot frame `base_link`; `/crane/odom` [params 1-5, 38-50, 93-106, 163-176](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L1) |
| Controller | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`, ID `FollowPath`, 10 Hz; desired linear 0.15 m/s, lookahead 0.4 m (0.2-0.6, velocity-scaled, 1.5 s), rotate-to-heading on at 0.4 rad/s, reversing off, collision detection on [params 5-36](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L5) |
| Goal checker | Stateful `SimpleGoalChecker`, 0.40 m XY and 0.35 rad yaw [params 18-22](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L18) |
| Progress checker | `SimpleProgressChecker`, 0.05 m in 20 s [params 14-17](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L14) |
| Planner | `NavfnPlanner`, expected 5 Hz, A*, unknown allowed, 0.5 m tolerance [params 81-91](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L81) |
| Local costmap | 20 x 20 m, 0.10 m cells, 10 Hz update / 2 Hz publish, rolling `odom`, radius 0.80 m, `/points` voxel layer plus inflation radius 1.0 m / scale 3.0 [params 38-79](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L38) |
| Global costmap | 40 x 40 m, 0.20 m cells, 5 Hz update / 1 Hz publish, rolling `odom`, no unknown tracking, same radius/layers/inflation [params 93-135](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L93) |
| Behaviors | 10 Hz Spin, BackUp, DriveOnHeading, Wait; 0.1-0.5 rad/s, 0.5 rad/s² rotational limit [params 137-161](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L137) |
| BT | NavigateToPose navigator, 10 ms loop, 20 ms server timeout, 60 s result timeout. No XML is pinned in the repo default: Nav2's installed default is used unless `CRANE_NAV2_BT_XML` overrides it [params 163-176](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L163), [launcher 15, 33-41, 67-69](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh#L15) |
| Smoother / limits | No velocity smoother is launched. No controller acceleration limit is configured. Controller-server deadbands are 0.001 on x/y/yaw; `failure_tolerance` is zero [params 7-10](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml#L7). |

RPP is a path-curvature controller for a forward/reverse mobile base: rotate-to-heading is enabled,
reversing is disabled, and the configuration supplies one desired linear speed. Nothing configures
a holonomic lateral command. Thus `linear.y` is accepted by the downstream boat interface but is
not expected to be intentionally generated by this active controller. Path pose orientations are
constant in the fixture-supplied straight path [fixture lines 198-231](../../packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py#L198); the goal checker nevertheless enforces final yaw.
Runtime queries against `lunarzdev/astro:cuda` (digest
`sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`) identify Nav2
`1.3.12`. RPP does not populate `linear.y`; its unconfigured maximum angular acceleration is
3.2 rad/s2 and it has no general linear acceleration limiter. The installed controller libraries
include RPP, DWB, MPPI, Graceful, and Rotation Shim; installed planners include Navfn, Smac, and
Theta Star. Availability is not a controller recommendation.

The installed default NavigateToPose tree is
`/opt/ros/jazzy/share/nav2_bt_navigator/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml`
(SHA-256 `5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`). It replans at 1 Hz
and includes clear-costmap, Spin, Wait, and BackUp recoveries. Navfn's installed default
`use_final_approach_orientation` is false.

## Boat command contract

The boundary is **not a desired-velocity controller**. Defaults divide ROS FLU `linear.x` and
`linear.y` by 1 m/s and `angular.z` by 1 rad/s, clamp each independently to [-1, 1], then apply the
latest queued sample on Unity `FixedUpdate` [adapter lines 43-54, 69-105, 118-141](../../packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs#L43).
The launcher does not override these scales [launcher lines 90-97](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh#L90).

- `linear.x`: nominal ROS body-forward command, converted to normalized controller `linear.y`.
- `linear.y`: nominal ROS body-left command, converted to normalized controller `linear.x`.
- `angular.z`: nominal positive-yaw command, converted to normalized controller yaw.

These values are normalized mixer requests which ultimately become motor torque commands, not
direct force or tracked body velocity. There is no deadband beyond Nav2's 0.001 output thresholds.
Commands are applied only at the 50 Hz physics boundary. The default stale timeout is 25 ticks =
0.5 simulated seconds, after which all axes are zeroed; episode reset also zeros them
[adapter lines 57-67, 82-99, 124-126](../../packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs#L57),
with the fixed 0.02 s step recorded by the project runtime documentation
[SimulationPhysicsAndRuntimeModes lines 43-49](../../packages/crane_ml/Docs/SimulationPhysicsAndRuntimeModes.md#L43).
Manual input temporarily overrides and clears queued ROS commands [adapter lines 82-87](../../packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs#L82).

Unity/ROS conversion is Unity `(x right, y up, z forward)` to ROS FLU `(x=z, y=-x, z=y)` for pose,
linear velocity, positions, and TF; odometry twist is explicitly body-frame
[navigation state lines 103-155](../../packages/crane_ml/Assets/Scripts/Controllers/CraneROSNavigationState.cs#L103).

## Thruster allocation and actuation

Four horizontal T200-like thrusters are assigned FL/FR/RL/RR by the enabled `OmniXController`
[Blastoise prefab lines 1302-1323](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L1302).
For normalized controller requests `(lateral, forward, yaw) = (x,y,r)`, the mixer is

```text
FL = -x - y - r       FR = +x - y + r
RL = -x + y + r       RR = +x + y - r
```

All four are divided by `max(1, max(abs(channel)))`, then multiplied by the configured maximum
command [mixer lines 64-85](../../packages/crane_ml/Assets/Scripts/Controllers/OmniXController.cs#L64).
This preserves request ratios while saturating each motor at +/-1 torque unit. The pattern has
rank three and is algebraically symmetric, so its *nominal* mixer can independently command all
three horizontal axes without cross-coupling.

The URDF locates/angles the four units (metres/radians) at FR `(0.01287, 0.26636, -0.28432)`, RR
`(0.01282,-0.26630,-0.28432)`, FL `(-0.01287,0.26637,-0.28232)`, RL
`(-0.01277,-0.26625,-0.28232)` [URDF lines 12-35, 51-78](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/blastoise.urdf#L12).
The corresponding Unity transforms are serialized in the prefab, e.g. FL
[lines 2639-2655](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L2639),
RL [3836-3852](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L3836),
FR [6227-6243](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L6227),
and RR [2838-2855](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L2838).

The shared asset config is torque mode, +/-1 Nm, axis Y, 500 rad/s cap, responsiveness 0.98,
`thrustK=-0.014`, equal forward/reverse coefficient, and 0.03 m submersion height
[OmniThrusterConfig lines 13-22](../../packages/crane_ml/Assets/Config/OmniThrusterConfig.asset#L13).
Motor torque is clamped and smoothed, then applied each fixed step
[MotorBase lines 103-140](../../packages/crane_ml/Assets/Scripts/Actuators/Motors/MotorBase.cs#L103).
Thrust is `sign(shaft_speed) * shaft_speed^2 * thrustK`, multiplied by reverse coefficient and
submersion fraction, then applied at the thruster body position
[Thruster lines 30-49](../../packages/crane_ml/Assets/Scripts/Actuators/Motors/Thruster.cs#L30).

### Allocation defect demonstrated at runtime

The static implementation contains a serious force-direction ambiguity. `Thruster.Awake()` searches only
`transform.root` for a physics body; the `Blastoise` root has no physics body
[prefab lines 1925-1987](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L1925),
so it falls back to the thruster's own articulation body. `FixedUpdate()` then evaluates
`rootBody.transform.TransformDirection(transform.localRotation * localAxis)`
[Thruster lines 15-43](../../packages/crane_ml/Assets/Scripts/Actuators/Motors/Thruster.cs#L15), apparently
applying the same local rotation both inside and through the transform. The scene additionally
rotates `base_link` 90 degrees [scene lines 4125-4149](../../packages/crane_ml/Assets/Scenes/Roboboat%20Course.unity#L4125).
Static matrix multiplication under normal Unity transform semantics does **not** reproduce the
nominal mixer axes. The isolated runtime response test below confirms that the command axes do not
match the reported body frame: surge and sway are exchanged. The exact minimal code correction
(thruster force transform versus controller/`base_link` convention) is deliberately not applied in
this reconnaissance pass.

## Physical model

The active scene is the Blastoise prefab, not `OmniBoat.prefab`; the scene references the Blastoise
GUID and enables its `OmniXController` [scene lines 2509-2520, 4150-4154](../../packages/crane_ml/Assets/Scenes/Roboboat%20Course.unity#L2509).
The base uses an ArticulationBody. Scene overrides set base-link mass 3 kg, COM y = -0.23 m, linear
damping 4, angular damping 15, explicit inertia `(10,15,10)` with a non-identity inertia rotation
[scene lines 3100-3158](../../packages/crane_ml/Assets/Scenes/Roboboat%20Course.unity#L3100).
The articulated vehicle's total mass is the sum of this base and child links; it is not 3 kg overall.
For example, the scene separately sets a hull link to 8 kg [scene lines 2905-2929](../../packages/crane_ml/Assets/Scenes/Roboboat%20Course.unity#L2905).
The prefab has gravity enabled [prefab lines 1085-1150](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L1085).

Enabled physics are triangle-submersion buoyancy (`rho*g*displaced volume` at submerged centroid)
[Buoyancy lines 33-46](../../packages/crane_ml/Assets/Scripts/Physics/Water/Statics/Buoyancy.cs#L33),
and enabled viscous plus pressure/suction drag with coefficients 100 linear / 30 quadratic and
unit reference/falloffs [prefab lines 1169-1239](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L1169),
[GeneralDynamics lines 61-89, 93-154](../../packages/crane_ml/Assets/Scripts/Physics/Water/Dynamics/GeneralDynamics.cs#L61).
Fossen dynamics are disabled in the prefab but **enabled by the active scene**
[prefab lines 1240-1272](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L1240),
[scene lines 3610-3614](../../packages/crane_ml/Assets/Scenes/Roboboat%20Course.unity#L3610). Its serialized
added-mass values are `(6,8,2)` kg and `(0.15,0.25,0.35)` kg m2; linear damping is
`(30,40,150)`, rotational damping `(8,12,20)`, and quadratic terms `(25,35,40)` / `(3,6,30)`.
The checked-in sources do not label the masses, inertia, damping, or thrust coefficients as
measured/calibrated; their provenance is unknown. Preserve them pending quantitative evidence.

## Geometry and frames

`base_link` is the controlled ArticulationBody and odometry child frame. The runtime publishes
`odom -> base_link` plus requested child frames `lidar_link`, `front_camera_link`, `imu_link`, and
`gps_link` at 50 Hz [navigation bootstrap lines 168-227](../../packages/crane_ml/Assets/Scripts/Controllers/CraneROSNavigationState.cs#L168).
The LiDAR is 0.29035 m above and 0.01270 m along its mount chain; its point cloud is `points` in
`lidar_link` at 10 Hz [URDF lines 36-50](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/blastoise.urdf#L36),
[prefab lines 3379-3559](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/Blastoise.prefab#L3379).

The base collision boxes alone span roughly 0.44 m laterally and 0.64 m longitudinally, with a
forward/back appendage extending the union to about 1.05 m [URDF lines 95-113](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/blastoise.urdf#L95); the two hull centers are +/-0.3302 m from base center
[URDF lines 51-55, 85-89](../../packages/crane_ml/Assets/Robot%20Descriptions/blastoise/blastoise.urdf#L51).
Thus the 0.80 m circular Nav2 radius is conservative rather than unrealistically small, but it
also requires 1.60 m logical clearance before inflation. Dock dividers are spaced at 2 m centers
[Marina prefab lines 109-133, 198-232](../../packages/crane_ml/Assets/Prefabs/MarinaPrefab.prefab#L109),
so the boat likely fits physically and nominally fits the raw footprint with only about 0.40 m
diametral margin. Inflation (1.0 m) may make a centered docking goal/path inaccessible depending
on obstacle marking and exact divider mesh thickness. Exact collision-mesh envelope and target
dock-region membership remain unmeasured.

## Existing capabilities and evidence

The unchanged harness can generate either a straight `FollowPath` (20 points) or a
`NavigateToPose` goal at configurable distance, observe odometry, command count/magnitudes,
costmap occupancy, action result, final displacement, transport lag/rejections, errors, and RTF
[fixture lines 198-231, 297-342, 355-373](../../packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py#L198),
[summarizer lines 116-199](../../packages/crane_ml/Tools/Performance/summarize_nav2_reset.py#L116).
It does not compute cross-track error, body-axis velocity response, final yaw error, collision,
dock membership, recovery counts, saturation duration, or save a full trajectory/rosbag.

Checked-in evidence already shows:

- `NavigateToPose` terminal success for the default short goal: 0.576 m displacement, 80 commands,
  79 accepted Unity actions, no rejected/stale/cross-episode actions, occupied local costmap, and
  1.0006 RTF [navigation summary lines 1-35](../../packages/crane_ml/PerformanceResults/nav2-navigate-loop-v1/navigation-summary.json#L1).
- Two earlier short `FollowPath` successes displaced 0.535 m and 0.496 m respectively
  [costmap fixture lines 1-21](../../packages/crane_ml/PerformanceResults/nav2-costmap-loop-v4/fixture-summary.json#L1),
  [controller fixture lines 1-18](../../packages/crane_ml/PerformanceResults/nav2-controller-loop-v6/fixture-summary.json#L1).

These runs establish short straight mobility and an end-to-end planner/BT/controller case. They do
not establish long-range tracking, docking, holonomic sway, stopping distance, arbitrary heading,
or recovery behavior. No RoboBoat docking, mixer, thruster-axis, step-response, or collision test
was found. The land fixtures and generic ROS observation bridge are alternatives, not evidence for
this plant.

## Runtime baseline observations

The player was rebuilt from this worktree with Unity `6000.5.10f1`; its manifest has asset-set hash
`FD3BAED2268824DB37BAD943C4D4004ABC71D4FFE6652817A1200FAC97D4BF47` and file SHA-256
`5e9bac251b7a1786b036b1f69a9abae4d35e828f16ff912ff25625d2d673c48b`. The missing worktree-local
ROS endpoint was built from the pinned `astro_dock` sources without source changes.

Aquatic `-nographics` and Unity `-batchmode` execution are invalid because HDRP water queries do not
advance correctly. A graphics-backed X11 virtual display was therefore used to avoid opening a
desktop window while preserving the production `train-gpu` physics path. The valid runs recorded
zero invalid water searches. One attempted batch-mode run recorded 31 invalid water searches and
is excluded from physical evidence.

### Unchanged short `NavigateToPose`

Run `roboboat-recon-short-xvfb` used active YAML SHA-256
`20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`. The fixture result SHA-256
is `9bfc039c38799777cf01b8df044e04328a39a0d5670b6fc24988acf3bb3de73b`.

- Nav2 returned `succeeded` in 8.98 s and displaced the boat 0.582 m for the 0.5 m goal.
- All 88 observed controller commands had zero `linear.x` and zero `linear.y`; maximum absolute
  `angular.z` was 0.470 rad/s.
- The boat nevertheless translated almost entirely along odom Y and changed pose yaw by 0.276 rad.
- This is not evidence of correct path following. It demonstrates that a rotation-only Nav2 request
  can create substantial translation, and that the loose 0.40 m goal tolerance can declare success.

### Direct body-command characterization

The behavior-neutral fixture sent each low-amplitude command through the production
`/crane/cmd_vel_stamped` adapter. The valid 65 s worker run retained 2,467 odometry samples,
accepted 1,046 actions, rejected none, and recorded zero stale/cross-episode actions, logged errors,
logged exceptions, or invalid water searches. Result SHA-256 is
`61287040ee0efb6a52e3f80f0537a799d01d3fcec8a5ff0b4f2b6d929e17de90`; sample CSV SHA-256 is
`09558714c4010ff0b5cb156fe42cc079bf6ef34a3d2629bac340a0a608008886`.

| Request held for 3 s | Tail body surge | Tail body sway | Tail reported yaw rate | Observed implication |
|---|---:|---:|---:|---|
| surge `+0.2` | +0.072 m/s | **+1.085 m/s** | -0.004 rad/s | Requested surge realizes primarily as sway |
| surge `-0.2` | +0.076 m/s | **-1.042 m/s** | -0.014 rad/s | Reverse sign is symmetric in the swapped axis |
| sway `+0.2` | **+1.181 m/s** | -0.001 m/s | +0.012 rad/s | Requested sway realizes primarily as surge |
| sway `-0.2` | **-0.989 m/s** | +0.002 m/s | -0.020 rad/s | Reverse sign is symmetric in the swapped axis |
| yaw `+0.2` | -0.021 m/s | +0.074 m/s | **+0.783 rad/s** | Yaw is controllable but has translation coupling |
| yaw `-0.2` | +0.054 m/s | +0.016 m/s | **-0.783 rad/s** | Reported yaw-rate sign follows request |

The odometry pose heading moved opposite the reported body yaw-rate sign: during positive yaw the
pose changed continuously from about -1.573 rad to +2.478 rad across the wrap, equivalent to
-2.233 rad, while reported `angular.z` settled near +0.783 rad/s. The implementation converts an
angular pseudovector with the same reflection used for polar linear vectors, which is inconsistent
with the handedness change in the pose quaternion. This feedback-sign defect explains persistent
rotate-to-heading behavior independently of controller tuning.

The same run also shows long coast distances at this command level (for example 0.526 m in the
four seconds after positive requested surge, which actually generated sway). Formal stopping time
and distance at several speeds remain Gate 1 evidence gaps.

## Baseline assessment and ranked hypotheses

1. **Command interface / force-axis realization (confirmed defect).** Surge and sway are exchanged,
   pose-yaw evolution conflicts with reported yaw rate, and yaw has measurable translation coupling.
   Fix only the frame/sign realization, then rerun the identical axis fixture; falsification requires
   dominant same-axis responses with consistent pose/twist yaw sign and bounded cross-coupling.
2. **Controller configuration.** Active RPP is configured around forward curvature and rotate-first
   behavior, while the vessel can in principle sway and has inertia/coasting. Confirm with a 10 m
   straight path recording cross-track, heading, body velocities, command components and stopping;
   falsify if tracking and settling remain bounded without repeated rotate/translate cycles.
3. **Footprint/costmap clearance.** A 0.8 m radius is conservative and inflation is 1.0 m; a 2 m
   dock lane may be logically pinched despite physical fit. Confirm by saving the exact global/local
   costmap and planned path through the intended berth; falsify if a collision-free center corridor
   retains adequate non-lethal width.
4. **Goal/progress checking.** 0.40 m / 0.35 rad tolerances can report success without docking
   precision; the 0.05 m/20 s rule may interact with slow coasting. Confirm with final pose/yaw and
   dock-region metrics plus recovery/action events; falsify if successful endpoints consistently
   meet the actual berth specification.
5. **Planner/final path geometry.** Navfn plans a point path in a rolling odom costmap and does not
   encode vessel terminal approach geometry. Confirm by plotting final 5 m path curvature and
   orientation versus dock geometry; falsify if it supplies a feasible, clearance-respecting final
   approach.
6. **Boat physics.** Physics are complex and currently reported realistic, but parameter provenance
   is absent. Only elevate this hypothesis if axis-isolated step and coast responses show implausible
   acceleration, speed, yaw inertia, or stopping distance. Do not retune hydrodynamics first.

## Smallest next experiment

The axis-sign experiment is complete and fails Gate 1. The smallest next experiment is to apply the
minimal frame/sign correction, then rerun the exact same low-amplitude fixture. Do not attempt the
far-dock goal until corrected surge/sway and pose/twist yaw consistency are demonstrated; otherwise
a docking result cannot distinguish controller behavior from the proven actuation/feedback defect.
