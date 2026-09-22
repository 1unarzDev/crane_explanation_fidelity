# RoboBoat navigation baseline

Date: 2026-09-21; actuator isolation updated 2026-09-22. This is the verified reconnaissance
baseline for the dedicated
`/home/lunarz/worktrees/roboboat-docking` worktree. It is not a tuning proposal. No Nav2
parameter, manual controller, mixer, thruster, mass, inertia, buoyancy, drag, water, scene, or
environment value was changed.

## Provenance

- Superproject `roboboat-docking` at `3bd20a847e776690b6be6acbdbcb5c36e7d6f215`.
- Gitlinks: `astro_dock` `36202373ae186a8fd247a20b7b477312a744de99`; nested
  `src/ros_tcp_endpoint` `3c3d405db665a8c52c28e45f23b8c9782a9564ba`; current `crane_ml`
  diagnostic commit `e8b35ca` based on `c9d905f474a0e2d872644e35787fb2b013ad0f2a`.
- Active YAML SHA-256: `20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`.
- Current ROS adapter SHA-256: `366e8fa8a1d68a0bdc472317f151a8b2845f203283a58b959b0ddfbfbc969865`;
  navigation-state publisher: `db1bff46ecfca449405e0fe8f99e459cda70de9d2dff53382b2787164875518a`.
- Manual controller and input action are unchanged: SHA-256
  `b846a21a1ea163555c5489b5b0fc3dd29f46f4f93c1fd7e16c48b1c0333e4f83` and
  `54026e4af2d0b74b8ac23633887f10150a133c5ef298d1f685be3cb7d8f47cc0`.
- Thruster source is byte-identical to the pinned commit, SHA-256
  `1853f88946ae51f5e35423bdb467a287b01dde4dc60cefca1d301ad9b721ffde`.
- Unity `6000.5.10f1`; asset-set hash
  `FD3BAED2268824DB37BAD943C4D4004ABC71D4FFE6652817A1200FAC97D4BF47`; build-manifest
  SHA-256 `09dcda0b28a8b33130fb3a28ec8fe5d77398456a652275495d11be9dc79e0fb7`.
- Runtime image `lunarzdev/astro:cuda`, Nav2 `1.3.12`, digest
  `sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`.

## Current architecture

```text
/navigate_to_pose -> BT navigator -> Navfn A* -> /follow_path
                                          |
direct /follow_path -----------------------+
  -> controller_server / Regulated Pure Pursuit @ 10 Hz
  -> Twist /nav2/cmd_vel
  -> fixture stamps latest /crane/odom time -> TwistStamped /crane/cmd_vel_stamped
  -> ROS-TCP endpoint -> Unity ROSOmniXCommand queue @ FixedUpdate
  -> FLU-to-controller adapter + independent [-1,1] normalization
  -> OmniXController four-thruster X mixer
  -> torque-controlled Thrusters -> quadratic submerged AddForceAtPosition
  -> articulated catamaran + buoyancy + GeneralDynamics + Fossen dynamics
  -> CraneROSNavigationState @ 50 Hz: /crane/odom and /tf
  -> controller, costmaps, planner, and BT
```

The live launcher is
[`run_nav2_controller_fixture.sh`](../../packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh).
It directly starts controller, planner, behavior, BT-navigator, and lifecycle-manager processes.
There is no velocity smoother. The default scene is `Roboboat Course`. Aquatic runtime requires a
graphics-backed X display; `-batchmode`/`-nographics` is invalid because HDRP water queries do not
advance correctly.

## Active Nav2 stack

The active default is
[`nav2_controller_fixture.yaml`](../../packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml).
`CRANE_NAV2_PARAMS` can override it, but no override was used. Land/warehouse YAML files are unused
alternatives for RoboBoat.

| Area | Verified active value |
|---|---|
| Clock/frames | `use_sim_time: true`; global/local `odom`; robot `base_link`; odometry `/crane/odom` |
| Planner | `nav2_navfn_planner::NavfnPlanner`, A*, expected 5 Hz, unknown allowed, 0.5 m tolerance |
| Controller | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`, 10 Hz, 0.15 m/s desired linear velocity, 0.4 m lookahead, velocity-scaled 0.2-0.6 m / 1.5 s |
| Heading | rotate-to-heading enabled at 0.4 rad/s; reversing disabled; collision detection enabled |
| Goal checker | stateful `SimpleGoalChecker`, 0.40 m XY and 0.35 rad yaw |
| Progress checker | `SimpleProgressChecker`, 0.05 m in 20 s |
| Local costmap | rolling 20 x 20 m, 0.10 m cells, update 10 Hz/publish 2 Hz, voxel `/points`, 0.80 m radius, 1.0 m inflation, scale 3.0 |
| Global costmap | rolling 40 x 40 m, 0.20 m cells, update 5 Hz/publish 1 Hz, same footprint/layers/inflation, no unknown tracking |
| Behaviors | Spin, BackUp, DriveOnHeading, Wait at 10 Hz; rotational 0.1-0.5 rad/s and 0.5 rad/s2 limit |
| BT | installed default `navigate_to_pose_w_replanning_and_recovery.xml`, SHA-256 `5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`; replans at 1 Hz |
| Limits | no velocity smoother/general controller acceleration limiter; deadbands 0.001; failure tolerance zero |

Installed controller libraries include RPP, DWB, MPPI, Graceful, and Rotation Shim. Installed
planners include Navfn, Smac, and Theta Star. This records availability, not a recommendation.

RPP assumes forward-curvature motion with optional rotate-first/reverse behavior. It does not
generate `linear.y` here. It has no model of a torque-command boundary or measured vessel coast.
Those assumptions do not fully match an omnidirectional inertial surface vessel, but reconnaissance
alone does not justify replacing it.

## Boat command contract

`cmd_vel` is **not closed-loop desired body velocity** at Unity. The adapter divides ROS FLU
`linear.x`, `linear.y`, and `angular.z` by 1 m/s, 1 m/s, and 1 rad/s, clamps each independently to
`[-1,1]`, and applies the latest queued sample at the 50 Hz physics boundary. The stale timeout is
25 ticks (0.5 simulated seconds); reset and timeout zero all axes.

| ROS field | Actual downstream contract |
|---|---|
| `linear.x` | normalized surge/mixer request -> controller X |
| `linear.y` | normalized sway/mixer request -> controller Y |
| `angular.z` | normalized positive FLU yaw request -> negative controller yaw |

This adaptation is isolated in `ROSOmniXCommand`; W/S, A/D, Q/E and the manual controller are
untouched. ROS angular feedback is `(-unity.z, unity.x, -unity.y)` because angular velocity is an
axial vector under the handedness-changing Unity-to-FLU reflection. Linear position/velocity are
`(unity.z,-unity.x,unity.y)`.

## Thruster allocation and actuation

Four horizontal thrusters are front-left, front-right, rear-left, rear-right. For controller
`(x,y,r)` the unchanged rank-three symmetric mixer is:

```text
FL = -x - y - r       FR = +x - y + r
RL = -x + y + r       RR = +x + y - r
```

Channels are divided by `max(1,max(abs(channel)))`, preserving ratios during saturation. URDF
origins `(x,y,z)` in metres are FR `(0.01287,0.26636,-0.28432)`, RR
`(0.01282,-0.26630,-0.28432)`, FL `(-0.01287,0.26637,-0.28232)`, RL
`(-0.01277,-0.26625,-0.28232)`. The shared configuration is torque mode, +/-1 Nm, local Y axis,
500 rad/s cap, responsiveness 0.98, `thrustK=-0.014`, equal reverse coefficient, and 0.03 m
submersion height. Force is quadratic in shaft speed, scaled by submersion, and applied at each
thruster articulation position.

An isolated transform test initially suggested a double-rotation defect. That correction would
alter the human-validated manual actuation path, so it was removed. Production thruster source is
identical to baseline; ROS corrections remain only at ROS command/feedback boundaries.

## Physical model

The Blastoise prefab uses an `ArticulationBody`. Scene overrides include base-link mass 3 kg, COM Y
-0.23 m, linear damping 4, angular damping 15, and inertia `(10,15,10)`; child links add mass (the
hull link is 8 kg). Gravity is enabled. Buoyancy integrates submerged mesh triangles.
GeneralDynamics pressure/suction/viscous drag uses linear coefficient 100 and quadratic 30.
Scene-enabled Fossen dynamics use added mass `(6,8,2)` kg and rotational
`(0.15,0.25,0.35)` kg m2; linear damping `(30,40,150)`, rotational `(8,12,20)`, and quadratic
terms `(25,35,40)` / `(3,6,30)`. Provenance is not documented as measured/calibrated. The 0.02 s
physics step is retained. No physical coefficient changed.

## Geometry and frames

Odometry publishes `odom -> base_link` and `lidar_link`, `front_camera_link`, `imu_link`, and
`gps_link` at 50 Hz. `/points` is in `lidar_link` at 10 Hz. Unity X-right/Y-up/Z-forward converts
to ROS FLU X=Unity Z, Y=-Unity X, Z=Unity Y.

The platform is a catamaran. The Blastoise head is aft, not the bow. In the URDF, the head collider
is at longitudinal Y=-0.369 m, while the sensor mount is at Y=+0.277 m; the LiDAR is therefore at
the physical front. Physical bow/heading is defined by the sensor/catamaran geometry and measured
positive-surge motion, not by the character's face.

The physical envelope is roughly 0.895 x 1.063 m. Nav2's 0.80 m circle is conservative. Dock
dividers are 2 m apart, leaving about 0.40 m diametral margin before inflation; 1.0 m inflation may
logically pinch a berth even though the catamaran fits physically.

The marina assemblies are centered near Unity X 16.086906 and 26.086906 at Z 2.8641434. The far
target was the far assembly's near berth at Unity `(24.586906,0.8641434)`, ROS odom
`(0.8641434,-24.586906)`, yaw `-pi/2`. This yaw was cross-checked against LiDAR-at-bow geometry:
positive surge moves the bow toward increasing Unity X, into that 180-degree dock's open side.

## Existing tests and evidence

The harness now records full trajectory, active/post-result path metrics, body/command history,
final pose, costmap occupancy, transport lag/rejections, water/runtime validity, and RTF. It does
not measure hull/dock contact, minimum clearance, dock-region membership, or an independent
stopped-settle predicate. No RoboBoat rosbag was found.

### Body response: original manual plant, ROS-only frame corrections

Artifact `PerformanceResults/roboboat-ros-adapter-manual-plant-green/body-response.json`, SHA-256
`2fa74fed29e991d14cdcf3ee3c347a7efebfd0760e2cd88a7b82d865b1def8ec`:

- surge +0.2 -> +1.107 m/s surge, negligible sway;
- sway +0.2 -> +0.959 m/s sway, residual surge +0.084 m/s;
- yaw +0.2 -> +0.788 rad/s yaw;
- no rejected/stale/cross-episode commands or water errors.

Axes/signs pass, but 0.2 normalized effort produces about 1 m/s, proving the semantic mismatch.

### Supplied 10 m straight path

Artifact `PerformanceResults/roboboat-followpath-10m-manual-plant-1/fixture-summary.json`, SHA-256
`8e01f6ecec5e7840c13380af18dc35f6a52ca076caf5e21367d692f07f7c1f0e`:

- FollowPath succeeded; active RMS/max cross-track 0.048/0.072 m;
- active RMS/max heading error 0.0097/0.0184 rad;
- success at 0.285 m endpoint error and 1.183 m/s body speed;
- 3.05 s coast: 0.202 m, final speed 0.0078 m/s, final XY error 0.096 m;
- post-result yaw transient 0.716 rad/s, final yaw error 0.215 rad;
- clean transport/water, RTF 1.0001.

Straight active tracking works; action success does not mean stopped arrival.

### Far-dock NavigateToPose negative baseline

Artifact `PerformanceResults/roboboat-far-dock-baseline-1/fixture-summary.json`, SHA-256
`6b34cf1e3de6a5bf60b5b3e9b03fe3abb1ff839c8e3317e84d1fa93d24564a41`:

- action timed out at 90 s;
- 898 controller commands had maximum linear X/Y exactly zero and max angular 0.481 rad/s;
- rotate-only actuation drifted 6.166 m; terminal yaw rate 0.784 rad/s;
- logs show 1 Hz replanning, repeated Navfn failures, an RPP predicted-collision abort/recovery,
  and cancellation;
- command transport: 893 accepted, zero rejected/stale/cross-episode, max source lag five ticks,
  zero water errors;
- strict worker `valid:false` is due to four unrelated stale perception observations. Retain as
  negative navigation evidence, not a clean benchmark pass.

This reproduces aggressive circling. RPP has no critic framework, so no MPPI/DWB critic is active.
The immediate behavior is persistent rotate-to-heading plus yaw-induced translation drift and
changing replans before forward path following begins.

### Fixed-heading and shaft-speed isolation

The planner and berth geometry are not required to reproduce the circling. A supplied 5 m
`FollowPath` whose initial heading was offset by +pi/2 produced no translation command, accumulated
24.410 rad (3.89 revolutions) of rotate-only yaw and drifted 2.160 m before timeout. Artifact
`PerformanceResults/roboboat-rpp-rotate-90-baseline-1/fixture-summary.json`, SHA-256
`a45d90d11d60718e8803f95819773c9ecbdafd59cb563fb3b421a7de8d8f556d`.

An unchanged-plant yaw sweep then requested 0.025, 0.05, 0.1, 0.2 and 0.4 for two seconds each.
Every nonzero request produced essentially the same steady body yaw rate, 0.782-0.790 rad/s. An
opt-in observer confirmed that the mixer preserved each requested magnitude, but every nonzero
value drove the four propeller shafts to approximately +/-100 rad/s. For example, command 0.025
produced mean absolute shaft speed 100.011 rad/s; command 0.4 produced 100.012 rad/s. Artifact
`PerformanceResults/roboboat-yaw-shaft-diagnostic-1/body-response.json`, SHA-256
`d2aa446cf0c9132ced3f3f774a2af3a910f3c0fd2b1f8b55818474d748175cdc`; shaft log SHA-256
`a34249a2f5b1002af4d22cedf7e9b0f45a09c6c3fe19759011d1420209fecfc5`.

This behavior follows from the current torque contract: the propeller driven-axis inertia is
`1e-6 kg m2`, so even 0.025 Nm implies 500 rad/s of ideal one-step velocity change at the 0.02 s
physics step, well beyond the observed approximately 100 rad/s saturation. The mixer is not
quantizing commands; torque-driven shaft saturation is. No controller, mixer, manual input,
thruster configuration or physics value was changed in obtaining this evidence.

## Baseline assessment

### Existing capabilities

- End-to-end ROS/Unity transport, simulated time, odometry/TF, costmaps, and both Nav2 actions run.
- ROS surge/sway/yaw axes and signs agree with authoritative odometry.
- Manual controller/bindings, mixer, thruster, and physical parameters remain at baseline.
- RPP accurately follows a supplied 10 m straight path while active.
- The hull physically fits a nominal berth; logical geometry is conservative.

### Observed limitations

- Nav2 numerical velocity is normalized effort downstream, not desired body velocity.
- The goal checker reports success while moving; there is no stopped-state goal checker.
- Far-goal rotate-to-heading remains rotate-only while yaw creates translation drift.
- Any tested nonzero yaw magnitude saturates shaft speed, so reducing RPP's requested angular
  velocity alone cannot reduce actual turn rate.
- Navfn repeatedly failed during the far run; footprint plus inflation may pinch the berth.
- No independent collision/clearance/dock/stopped-settle evaluator exists.

### Evidence gaps

- Proportional shaft/body response under a non-saturating command contract, including stopping
  distance/time and manual-input regression.
- Repeated 10 m runs on the final build, then 30-50 m straight and turns.
- NavigateToPose planned-path capture and exact berth costmap clearance.
- Collision/contact, clearance, dock membership, stopped-settle, and repeated docking.
- An automated manual-input regression remains desirable, although every manual/shared-actuation
  source is currently identical to the pinned baseline.

## Ranked hypotheses and falsifiers

1. **Torque-mode command interface.** Confirmed: all tested nonzero yaw requests preserve their
   mixer magnitude but saturate every shaft near 100 rad/s, producing the same body yaw rate. A
   non-saturating shaft-speed request should restore monotonic command response; falsify if measured
   shaft speeds or body yaw remain quantized after that isolated contract change.
2. **Footprint/costmap clearance.** Radius 0.8 m plus 1.0 m inflation blocks the 2 m berth. Confirm
   from exact target costmap/path clearance; falsify with a non-lethal corridor wider than footprint.
3. **Goal/checker and command semantics.** Effort interpretation plus loose tolerance causes moving
   success. Confirm via speed/coast at result; falsify if endpoints repeatedly stop in tolerance.
4. **Planner/final geometry.** Rolling Navfn replans do not supply a stable dock-aligned approach.
   Confirm by capturing every plan/final 5 m geometry; falsify with repeated feasible approaches.
5. **Boat physics.** Elevate only if isolated tests remain implausible after interface/controller
   behavior is accounted for. The human reports realistic feel; no hydrodynamic tuning is justified.

## Smallest next experiment

Run one controlled A/B of the existing torque contract against the already-supported velocity-mode
thruster contract, using the unchanged yaw sweep and shaft observer. The acceptance signal is
monotonic shaft speed and body yaw rate across 0.025-0.4, with full-scale/manual top-end behavior
retained. This is smaller and more discriminating than Nav2 tuning: it tests the confirmed
command/actuator bottleneck without changing hydrodynamics, mixer signs, scene geometry or manual
bindings. Per the reconnaissance guardrail, report and review this behavior-changing configuration
experiment before applying it.
