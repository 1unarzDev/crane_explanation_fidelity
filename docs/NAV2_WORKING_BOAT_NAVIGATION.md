# Working Nav2 boat navigation and demo

The same Unity worker and Nav2 fixture run headlessly or with a spectator window.
Both `--crane-ros-nav-state` and `--crane-ros-cmd-vel /crane/cmd_vel_stamped`
are required: the old handoff omitted the command adapter. The launcher installs both.

## Reproduce

From the repository root, after building the player:

```bash
packages/crane_ml/Tools/Performance/run_roboboat_evidence_capture.sh interactive
packages/crane_ml/Tools/Performance/run_roboboat_evidence_capture.sh headless
```

The default player is `Builds/CRANE-Evidence-ShoreFade/CRANE.x86_64` inside
`packages/crane_ml`; override with `CRANE_PLAYER`. Build using the installed Unity
Editor and `CranePerformanceBuild.BuildLinuxWorker`; the retained build manifest
records the editor, scene and profile. Interactive mode overrides the worker's
`train-gpu` profile with `interactive-high`, so one measured player renders the
real spectator window. Headless aquatic workers remain graphics-backed for HDRP
water; this is not a `-nographics` mode.

A longer recording run, with the current first-dock defaults:

```bash
env CRANE_RUN_ID=nav2-first-dock-demo \
  CRANE_DURATION=360 CRANE_NAV2_ACTION_DURATION=300 \
  packages/crane_ml/Tools/Performance/run_roboboat_evidence_capture.sh interactive
```

Each run copies its exact CRANE environment, YAML, behavior tree, launcher and
build manifest to its result directory, alongside logs and fixture/worker results.
Port 12082/domain 220 isolate these runs; overrides are supported. Simulation
defaults to half speed (`CRANE_TIME_SCALE=0.5`) to give ROS wall-time headroom
without relaxing the 10-tick lag limit; `CRANE_TIME_SCALE=1` is an explicit override. RGB/depth-image
readback is explicitly disabled because full-sensor runs accumulated stale
observations. Nav2 uses LiDAR `/points`. Full RGB/depth reliability remains unproven.

## Actual first dock and navigation evidence

Scene inspection locates `Marina/Dock0` at Unity center X=17.337, Z=2.864;
`Marina/Dock1` is farther away at X=24.837. The first clear slip spans
X=[16.337,18.837], Z=[0.114,1.614]. The goal is ROS
(0.8641434,-17.337,+pi/2), facing into its east opening. The local/global
footprint uses the measured 1.063 by 0.895 m hull plus 0.01 m padding;
the old 0.8 m radius circle cannot fit the 1.5 m gap. Navfn tolerance is
0.05 m and the global map resolution 0.1 m. Terminal XY checking remains
active during rotation, with 0.15 m controller tolerance and 4 m approach slowing.

Earlier target ROS (0.8641434,-27.586906,+pi/2) lies outside the visible
second slip. Historical passing runs and `recording-demo` prove only their
declared 3 by 2 m evaluator region. Their raw artifacts and recovered commands
remain local in `artifacts/nav2-historical-recovery`; they are not actual-slip proof.

Fresh evidence under `artifacts/nav2-docking-reproduction-20261002`:

- `first-dock-shore`: Nav2 succeeded but stopped 0.447 m from goal; zero qualified
  settling duration; strict timing failed with 21 stale/rejected actions.
- `first-dock-tight`: Nav2 succeeded, 13.52 m displacement, and independently
  verified five-second first-slip containment. First qualified success at
  simulation 82.04 s: XY 0.314 m, yaw error -0.0083 rad, speed 0.0311 m/s.
  The physical predicate qualified for up to 8 s. All three image audits pass.
  Strict timing fails with 54 stale/rejected actions; this is not a fully valid benchmark.

- `first-dock-headless`: Nav2 success and up to 14.9 s of first-slip qualification;
  strict timing fails with 38 stale/rejected actions at simulation speed 1.
- `first-dock-paced`: interactive at half speed; **all navigation audits pass**,
  including actual-slip containment and strict harness validity. 865 actions
  accepted, zero stale/rejected actions, zero stale/failed observations; maximum
  accepted source-to-application lag 4 ticks. The third scheduled image missed
  the earlier qualification; the launcher now starts monitoring at 30 s.

- `first-dock-final`: **all checks pass**, including all three PNG metadata audits,
  actual first-slip containment and strict timing. Default half-speed launcher
  plus earlier 30 s middle capture reproduced navigation and captured qualification.
  This is the current complete capture, not the earlier diagnostic run.

The docking predicate requires XY<=0.40 m, |yaw error|<=0.35 rad,
speed<=0.05 m/s, |yaw rate|<=0.05 rad/s, hull containment and zero recorded
prohibited contacts for five continuous seconds. `--first-dock` additionally
projects hull corners into the inspected real slip bounds. Contact callbacks
reported zero, while the user observed contact and Nav2 predicted collision ahead;
physical impact remains unconfirmed. See [the image/explanation pairing](NAV2_DOCK_CONTACT_EVIDENCE.md).

```bash
python analysis/verify_nav2_visualization_capture.py \
  artifacts/nav2-docking-reproduction-20261002/first-dock-tight --images --first-dock
```

The auditor preserves failed checks instead of equating Nav2 success with docking
or benchmark validity. A five-second interval does not establish indefinite
station keeping; later wave drift is retained.

## Presentation

The camera follows the real articulation controller, shifted left and closer,
with 50 degree FOV. A clean screen-space TMP legend replaces world text.
The batched costmap tiles display the received 2-D occupancy grid, not raw voxel
heights. Nine water probes set the display plane 0.45 m above the sampled maximum.
Visuals have no colliders and are excluded from sensor cameras. Dense inflated
cells still obscure parts of the dock and hull; screenshots alone cannot prove contact.

Primary `first-dock.png` waits for all evidence topics and a boat distance <=1.6 m
from Dock0 bounds, closer to Dock0 than Dock1. The final image is requested while
the evaluator qualifies. Each PNG has a sidecar retaining topic stamps, displayed
plan, occupancy bytes, water probes, camera pose, proximity and evaluator sample.
The separate visual shore terrain now fades underwater sand into deeper water;
its original physics terrain is unchanged. See [shore verification](ROBOBOAT_SHORE_FADE.md).

A bounded [review capsule](../artifacts/nav2-docking-reproduction-20261002/review-capsule/)
retains the primary/final images, sidecars, audit, configuration, log excerpt and
language explanation. Larger raw run directories remain local.


The committed final evidence is directly auditable, with gzip-compressed original
fixture and harness JSON accepted by the auditor:

```bash
python analysis/verify_nav2_visualization_capture.py \
  artifacts/nav2-docking-reproduction-20261002/review-capsule/final-capture \
  --images --first-dock
```

All final navigation/capture checks passed. Pixel inspection confirms the first-dock
approach, elevated tiles, clean legend, and sand fade. The final photograph shows
the hull in the first slip with some costmap occlusion. Contact interpretation
remains bounded by the separate user-report/telemetry discrepancy.
