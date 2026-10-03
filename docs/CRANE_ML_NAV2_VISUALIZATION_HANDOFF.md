# CRANE ML / Nav2 visualization handoff

Historical starting state. For the current launcher, actual first-slip geometry,
verified captures, and timing limitations, see [NAV2_WORKING_BOAT_NAVIGATION.md](NAV2_WORKING_BOAT_NAVIGATION.md).
The original visible command below omitted `--crane-ros-cmd-vel`; the current launcher installs it.

## Current objective

Produce a trustworthy RoboBoat player capture in which the visible Unity simulation is controlled by Nav2, the planned path and odometry are visible, the local costmap voxels are visible without obscuring the water, and the boat reaches a real docking slot. Treat the image as an evidence-bound visualization. Do not call a run successful from a screenshot alone: retain the fixture summary, player log, topic names, timestamps, and final pose/evaluator output.

The most useful next step is to locate and reproduce the earlier configuration that observers saw navigate all the way to a dock. The recent experiments are diagnostic and should not be treated as proof that the architecture cannot complete the task.

## Workspace and main paths

- Repository root: `/home/lunarz/crane_explain`
- Unity project: `packages/crane_ml`
- Player build: `packages/crane_ml/Builds/CRANE-Worker/CRANE.x86_64`
- Active Nav2 parameter file: `packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml`
- Fixture launcher: `packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh`
- Nav2 fixture implementation: `packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py`
- ROS command adapter: `packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs`
- ROS pose/TF publisher: `packages/crane_ml/Assets/Scripts/Controllers/CraneROSNavigationState.cs`
- Evidence overlay: `packages/crane_ml/Assets/Scripts/Utils/Visualization/Nav2EvidenceOverlay.cs`
- Visible-player capture bootstrap: `packages/crane_ml/Assets/Scripts/Performance/CraneEvidenceCaptureBootstrap.cs`
- Docking evaluator: `packages/crane_ml/Assets/Scripts/Controllers/RoboBoatDockingEvaluator.cs`
- Docking notes and historical successful configurations: `docs/ROBOBOAT_DOCKING.md`
- Known supplied far-dock path: `packages/crane_ml/Tools/Performance/roboboat_far_dock_known_path.json`

## What is verified

The player can be launched in `interactive-high` with a detached elevated spectator camera. The capture bootstrap is opt-in and uses:

```text
--crane-profile interactive-high
--crane-scene "Roboboat Course"
--crane-ros-ip 127.0.0.1 --crane-ros-port 10000
--crane-ros-nav-state /crane/cmd_vel_stamped
--crane-evidence-overlay
```

It can write a screenshot with `--crane-evidence-capture <absolute-path>` and can write two later captures with `--crane-evidence-capture-2` and `--crane-evidence-capture-3`. The player image is real Unity rendering; it is not an SVG reconstruction.

The ROS TCP endpoint is normally supplied by the Astro Dock container on host port `10000`. A visible player and a benchmark worker are different processes. The benchmark worker launched by `run_worker.sh` is not the player window to use for presentation captures.

The external-player mode added to `run_nav2_controller_fixture.sh` is enabled with `CRANE_EXTERNAL_PLAYER=1`. In that mode the fixture starts Nav2 and uses an already-running player. If the endpoint is started twice, the second endpoint fails with “address already in use” and the resulting run is invalid.

The run in `artifacts/reproduce-run4-result/fixture-summary.json` proves that the visible-player sequence can receive a plan, commands, odometry, and costmap messages. It recorded 339 controller commands, 1,496 odometry messages, 7 costmap messages, and one plan. Its maximum linear command was zero because the controller remained in its rotate-to-heading branch.

After setting `use_rotate_to_heading: false` in the active Nav2 YAML, `artifacts/twist-forward-result/fixture-summary.json` recorded a maximum linear command of `0.8 m/s` and maximum angular command of `0.783 rad/s`. This proves that Nav2 can emit forward twists through the current setup. It did not yet prove full docking; displacement was only 0.364 m in the 35-second diagnostic window.

## Voxel and LiDAR issue

The overlay originally created costmap cells with `GameObject.CreatePrimitive(PrimitiveType.Cube)`. Unity adds a `BoxCollider` to such cubes. Those colliders made the visualization geometry part of the physics/LiDAR scene, allowing the boat to sense its own rendered costmap and potentially expand the costmap recursively. The overlay now removes the collider immediately after creating each costmap cube and collision marker. This source change requires a fresh player build before it affects a run.

The overlay also limits rendering to a local radius and flattens cells so water remains visible. This is a presentation choice, not a modification of Nav2’s costmap. Do not infer that a sparse image means the costmap topic is empty; inspect the fixture’s `costmapMessages`, service snapshots, dimensions, origin, resolution, and cell counts. Conversely, do not claim the overlay is fixed until a fresh build log and a pixel-inspected screenshot show the intended voxels without LiDAR feedback from the overlay.

## Current Nav2 behavior and open questions

The active controller is Regulated Pure Pursuit. The previous `use_rotate_to_heading: true` setting produced angular-only commands for the RoboBoat’s slow yaw response. It is currently set to `false` so pursuit can emit a forward component. This change is diagnostic and still needs validation on the full far-dock route.

The corrected far-dock target documented in `docs/ROBOBOAT_DOCKING.md` is approximately:

```text
x = 0.8641434
y = -27.586906
yaw = +pi/2
```

The independent evaluator requires the hull to remain inside a 3 m by 2 m berth, XY error below 0.40 m, yaw error below 0.35 rad, low translational and yaw rates, zero prohibited contacts, and five seconds of continuous satisfaction. Historical notes report successful long-range runs, but their complete raw run directories are not all present in this worktree. Locate the manifests and exact parameter overrides before asserting reproduction.

Do not assume a nonzero `controllerCommands` count means the boat is moving. Check `maximumLinearCommand`, `maximumAngularCommand`, `outputTopic`, odometry displacement, thruster diagnostics, and the docking evaluator. Do not assume a screenshot path is the path used at decision time unless the source and timestamp are retained.

## Recommended clean-run procedure

1. Confirm no old player, fixture, or endpoint is using port 10000. Remove only the transient endpoint container; preserve artifacts.
2. Build the current Unity project and require `CRANE_BUILD_COMPLETE` with no C# errors.
3. Start one ROS TCP endpoint with ROS domain 42.
4. Start the visible player with `interactive-high`, ROS nav state, and the evidence overlay. Use absolute screenshot paths.
5. Wait roughly 10–15 seconds for the player’s ROS registration to complete.
6. Run the fixture with `CRANE_EXTERNAL_PLAYER=1`, the active YAML, and the documented far-dock target. Add `CRANE_DOCKING_EVALUATOR=1` for the independent berth predicate.
7. Inspect the fixture summary before inspecting images. Require nonzero linear commands, plan count, costmap messages, odometry displacement, and evaluator messages.
8. Inspect start/mid/final PNGs. Verify that the boat, dock, path, odometry trail, twist arrow, and local voxels are all visible and that water remains legible.
9. If linear commands remain zero, inspect controller logs and path heading before changing physics. If costmap cells expand after overlay activation, verify collider removal and rebuild provenance.
10. Record the exact command lines, build manifest, endpoint log, player log, fixture summary, and image paths in `docs/PAPER_REVIEW_STATUS.md`.

## Evidence boundaries

The overlay is read-only visualization. It must not change the experiment, add obstacles, or silently replace an original plan with a newly generated one. A rendered voxel is a depiction of a received costmap cell; it is not a physical obstacle. A published twist is a command, not measured motion. Thruster input is not measured thrust unless the retained diagnostic channel supports that claim. A final Nav2 action result is not by itself proof of sustained physical docking.

Past successful runs are valuable leads. Find their exact manifests, parameter files, goal tolerances, controller settings, and raw logs. Preserve them and reproduce them before concluding that the current setup is incapable of reaching the dock.
