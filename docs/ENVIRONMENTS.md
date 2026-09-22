# Environment Catalog and Submission Scope

This catalog separates platform infrastructure from inclusion in the TRUSTMORE 2026 empirical
study. `IMPLEMENTED / VALIDATED INFRASTRUCTURE` does not mean `INCLUDED IN TRUSTMORE EMPIRICAL
STUDY`.

## Submission-critical environments

| Environment | Existing infrastructure | Current validation | Explanation evaluation | Submission status |
|---|---|---|---|---|
| Controlled TurtleBot3 land/Nav2 corridor | Differential dynamics, ROS, LiDAR, odometry/TF, Nav2, evaluator-only interventions, BT/action capture | Repeated success, recovery-success, and terminal-abort development/frozen runs | Frozen F/G/H provenance study in progress | **PRIMARY CONTROLLED STUDY — protocol frozen** |
| TurtleBot3 warehouse/industrial | Manifest-driven 20 × 26 m canonical geometry, separate presentation, semantic/route/scenario IDs, deterministic static/delayed/temporary obstacles and a temporary four-wall enclosure, differential robot and LiDAR | Structural/physics/sensor/headless gates; 13.61 m nominal detour; exact bounded-policy pair produced 53.38 s success versus 71.10 s BT-deadline abort under complete blockage; temporary enclosure passed 3/3 exact-condition recovery-success repetitions; direct keyboard inspection and collision-aware Follow view pass | Exact-hash questions cover recovery sequence and physical-cause insufficiency; current-build recovery-success runs retained ordered BT/invocation evidence with explicit 16,384-record ecological capacity and zero drops, and the first passed deterministic, physically separated export with no robot-visible truth leakage. Explanation generation/annotation remains `NOT_RUN`, recovery-count variability is retained, and no physical-cause claim is made | **REQUIRED — environment, question-contract, capture, and separated-export gates pass; explanation pilot next** |
| Configurable land proving ground | Manifest-driven eight-motif generator with separate canonical/presentation layers, seeded configuration hashes, semantic IDs, evaluator truth, dynamic schedules, dedicated Nav2 parameters, inspection overlays, and hash-checking behavioral/repetition QA | Structural/physics/sensor/headless/explanation checks pass; all eight motifs have one behaviorally qualified development revision across preserved v1 plus additive v2 slalom; corrected S-turn, dynamic recovery-success, and bounded blockage each pass three exact-condition runs; the straight-through v1 slalom remains a negative calibration; direct keyboard Overview-to-Oblique switching passes | Exact-hash ecological questions cover dynamic recovery-success, bounded terminal policy, S-turn path shape, U-trap route change, false premises, and causal/optimality withholding. A current-build bounded-blockage run passed ordered capture and fail-closed separated export; dynamic-gate recovery-success did not reproduce on the same build and remains unexported. Explanation generation/annotation remains `NOT_RUN` | **REQUIRED — terminal-policy evidence handoff passes; current-build recovery/path-shape handoffs and explanation pilot remain** |
| RoboBoat surface navigation/docking | Existing CRANE aquatic platform and parallel docking worktree | Owned and being qualified by the separate RoboBoat workstream | Candidate cross-domain demonstration only if reliable | **PARALLEL / OWNED ELSEWHERE** |

The ecological land target is obstacle-rich, longer, multi-route navigation that actually produces
avoidance, path changes/replanning, narrow-passage stress, recoveries, and blockage/no-path
outcomes. Visual complexity without behavioral complexity is insufficient.

### Submission ecological domain matrix

| Domain | Submission scenario/question scope |
|---|---|
| Land | Recovery; terminal failure; obstacle avoidance; replanning/substantive path change; evidence insufficiency; physical-evidence questions |
| Surface / RoboBoat | Ecological cross-domain navigation/docking demonstration only if the parallel workstream qualifies it |
| Underwater | `DEFERRED_POST_SUBMISSION` |
| Aerial | `DEFERRED_POST_SUBMISSION` |

This living matrix narrows submission planning without editing the hash-frozen long-term taxonomy in
`docs/BENCHMARK.md`. Potential underwater/aerial decision motifs remain valid future design notes.

## Retained land/reference infrastructure

| Environment | Current validation | Submission status |
|---|---|---|
| F1TENTH Spielberg importer | Deterministic PNG/YAML conversion and headless geometry/physics qualification; full-lap ROS control not run | Retained infrastructure; not a current ecological priority |
| Clearpath pipeline offline import | Geometry/layer/contact checks and a local 1 m ROS/Nav2 motion/sensor smoke; representative route and native-Gazebo comparison not run | **DEFERRED_POST_SUBMISSION** unless it directly unlocks a required land experiment |
| Outdoor/campus expansion | No submission-critical environment contract validated | **DEFERRED_POST_SUBMISSION** |

## Retained aerial infrastructure

`Aerial Vehicle Validation`, `PX4 Walls Validation`, `PX4 ArUco Validation`, and
`PX4 Windy Validation` remain part of CRANE. Existing checks cover multirotor dynamics,
source-pinned wall geometry, collision/raycast behavior, render-only ArUco separation, and
repeatable response to the pinned wind vector. PX4 SITL, ROS navigation, camera marker detection,
Gazebo dynamics equivalence, and evidence-checked explanation evaluation were not established.

**DEFERRED_POST_SUBMISSION — existing environment and validated infrastructure retained; not part
of the TRUSTMORE 2026 confirmatory or ecological evaluation.** Historical results in
`docs/EXPERIMENTS.md` remain authoritative and are not relabeled.

## Retained underwater infrastructure

`Robosub Pool` and the existing underwater robot/assets remain available as CRANE infrastructure.
This scope decision neither invalidates nor deletes them. A submission-quality underwater
explanation study would require additional autonomy, sensor/evidence integration, scenario
contracts, and navigation validation that are not currently on the critical path.

**DEFERRED_POST_SUBMISSION — existing environment retained; not part of the TRUSTMORE 2026
confirmatory or ecological evaluation.** No new RoboSub task integration, underwater scene work,
or underwater explanation experiment is scheduled before submission.

## Evidence boundary

All environments preserve three separate layers:

1. `CanonicalGeometry`: authoritative collision, traversability, semantic IDs, and evaluator truth;
2. `Robotics/Simulation`: robot physics, joints, sensors, ROS, and autonomy;
3. `VisualPresentation`: meshes, materials, lighting, props, and optional debug overlays.

World truth becomes explanation evidence only through an explicit robot-visible capture or
supported runtime-to-source link. A semantic object in Unity, a delivered scan, or a costmap
snapshot alone does not prove what Nav2 consumed or why a decision occurred.
