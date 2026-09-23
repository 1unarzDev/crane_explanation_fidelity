# Environment Catalog and Submission Scope

This catalog separates platform infrastructure from inclusion in the TRUSTMORE 2026 empirical
study. `IMPLEMENTED / VALIDATED INFRASTRUCTURE` does not mean `INCLUDED IN TRUSTMORE EMPIRICAL
STUDY`.

## Submission-critical environments

| Environment | Existing infrastructure | Current validation | Explanation evaluation | Submission status |
|---|---|---|---|---|
| Controlled TurtleBot3 land/Nav2 corridor | Differential dynamics, ROS, LiDAR, odometry/TF, Nav2, evaluator-only interventions, BT/action capture | Repeated success, recovery-success, and terminal-abort development/frozen runs | Frozen F/G/H collection closed under the additive disposition amendment at 33 episodes; annotation/adjudication and analysis remain `NOT_RUN` | **LEGACY CONTROLLED EVIDENCE — immutable, under-target, awaiting annotation** |
| TurtleBot3 warehouse/industrial | Manifest-driven 20 × 26 m canonical geometry, separate presentation, semantic/route/scenario IDs, deterministic static/delayed/temporary obstacles and a temporary four-wall enclosure, differential robot and LiDAR | Structural/physics/sensor/headless gates; 13.61 m nominal detour; exact bounded-policy pair produced 53.38 s success versus 71.10 s BT-deadline abort under complete blockage; temporary enclosure passed 3/3 exact-condition recovery-success repetitions; direct keyboard inspection and collision-aware Follow view pass | A governed recovery-sequence R/P/T/N development comparison and blinded packet retain source-qualified invocations while withholding physical causation; human annotation remains `NOT_RUN` | **DEVELOPMENT QUALIFIED — no additional environment tuning; use retained evidence** |
| Configurable land proving ground | Manifest-driven eight-motif generator with separate canonical/presentation layers, seeded configuration hashes, semantic IDs, evaluator truth, dynamic schedules, dedicated Nav2 parameters, inspection overlays, and hash-checking behavioral/repetition QA; additive v3 supplies a bounded temporary enclosure without changing v1/v2 | Structural/physics/sensor/headless/explanation checks pass; all eight original motifs have one behaviorally qualified development revision across preserved v1 plus additive v2 slalom. Corrected S-turn and bounded blockage each have current qualified exports. Historical dynamic-gate success is preserved as calibration, but current source-qualified attempts did not reproduce the required result. The straight-through v1 slalom remains a negative calibration | Governed blockage and corrected-S-turn R/P/T/N development comparisons and blinded packets exist. `dynamic-gate-v1` is `HISTORICAL_CALIBRATION_ONLY`; U-trap is `NOT_READY_NO_QUALIFIED_EXPORT`. Human annotation remains `NOT_RUN` | **CLOSED FOR ENVIRONMENT DEVELOPMENT — use retained qualified evidence; do not tune dynamic-gate or add scenarios** |
| RoboBoat surface navigation/docking | Integrated CRANE aquatic platform, command-response fixtures, long-range Nav2/docking fixtures, and independent docking predicate | Command mapping and navigation/docking progression pass; five repeated far-dock actions and physical predicates succeeded, with 3/5 strict generic-valid due to an unrelated depth-camera startup issue | Governed terminal-margin R/P/T/N development outputs, an evidence mask, blinded packets, and a separate retained-grid diagnostic exist; prospective evaluation and human annotation remain `NOT_RUN` | **INTEGRATED / PROTECTED — focused surface diagnostic domain; do not redesign scene or physics** |

The ecological land target is obstacle-rich, longer, multi-route navigation that actually produces
avoidance, path changes/replanning, narrow-passage stress, recoveries, and blockage/no-path
outcomes. Visual complexity without behavioral complexity is insufficient.

### Closed ecological pilot set

The development-only information-parity pilot admits exactly three current qualified exports:

1. warehouse temporary-enclosure recovery (`eco-pilot-001`);
2. complete blockage (`eco-pilot-002`);
3. corrected S-turn (`eco-pilot-003`).

U-trap would be eligible only if a current qualified export already existed; none does, so it is
not in this pilot. `dynamic-gate-v1` remains a valid historical/calibration result but is not
currently pilot-qualified. The next work is explanation generation, parity auditing, and blinded
annotation—not additional environment development.

### Submission ecological domain matrix

| Domain | Submission scenario/question scope |
|---|---|
| Land | Recovery; terminal failure; obstacle avoidance; replanning/substantive path change; evidence insufficiency; physical-evidence questions |
| Surface / RoboBoat | Focused cross-domain diagnostic source; development navigation/docking is qualified, but prospective explanation evaluation remains to be frozen and run |
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
