# Environment Validation

Validation status is split between submission-critical work and retained infrastructure. Historical
results remain in `docs/EXPERIMENTS.md`; this file is the living gate summary.

## Gate definitions

- `STRUCTURAL_PASS`: no missing scripts/assets, invalid roots/transforms, or duplicate semantic IDs.
- `PHYSICS_PASS`: floor support, collision, openings, and intended blockage behave correctly.
- `SENSOR_PASS`: spawn, TF, odometry, ROS, and configured sensors/frames pass their contract.
- `NAVIGATION_PASS`: predefined routes produce the required nontrivial path/obstacle interaction.
- `INTERACTIVE_PASS`: representative views and controls are visually inspected and usable.
- `HEADLESS_PASS`: canonical geometry, semantics, physics, sensors, and navigation retain their
  contract without presentation/UI.
- `EXPLANATION_READY`: scenario, route, objects, actions, and physical events have stable identities
  and separated robot-visible/evaluator-only evidence.
- `PARTIAL`: some gates pass, but the environment is not ready for the declared use.
- `BLOCKED`: a recorded external or technical blocker prevents the gate from running.

A successful short goal does not establish a representative route. Topic/service delivery does not
establish controller consumption. An unexpected outcome is retained as observed and is never
relabeled to satisfy a gate.

## Submission-critical validation

| Environment | Structural | Physics | Sensor | Navigation | Interactive | Headless | Explanation | Current verdict |
|---|---|---|---|---|---|---|---|---|
| Frozen controlled TurtleBot3 corridor | Passed in retained runs | Passed for controlled layouts/interventions | Passed for ROS, LiDAR, odometry/TF, costmap observation | Passed for frozen recovery-success and terminal-abort families | Not required by frozen protocol | Passed | Passed for frozen F/G/H capture contract | Active frozen collection; do not change protocol |
| Warehouse/industrial ecological world | **PASS:** 20 nominal canonical colliders, 20 separated renderers, 28 unique nominal semantic IDs; five manifest scenario contracts | **PASS:** drop/contact plus 0.150 m differential drive and 19.1° turn response; scenario collider/visual state changes share fixed-time boundaries | **PASS:** ROS/LiDAR/odometry, semantic hit on `rack-center-blocker`, populated costmaps | **PASS:** nominal detour; 53.38 s success versus 71.10 s bounded task-policy abort under complete blockage; one temporary-enclosure recovery-success calibration in 82.93 s after planner/controller failures and recovery transitions. Repeated recovery qualification remains `NOT_RUN` | **PARTIAL:** isolated 1280×720 overview/oblique, HUD, semantic highlight, trajectory, and collider wireframes visually passed; manual keyboard polling not directly exercised | **PASS:** matching manifest v2.2.0 geometry and navigation under null graphics | **PASS for development contracts:** exact BT hashes, action results, delivered BT/recovery/trajectory evidence, evaluator-only obstacle IDs and timing; terminal ticks may be omitted and physical cause or controller consumption is not inferred | **PARTIAL overall:** behavior gates pass once; repeated scenario qualification, explanation evaluation, and full interactive check remain |
| Configurable proving ground | **PASS:** preserved eight-layout v1 manifest plus additive one-layout v2 slalom revision; separate canonical/presentation roots; validators report 5–7 canonical colliders, matching collider-free renderers, 7–9 unique semantic IDs, zero duplicates | **PASS for qualified revisions:** collision/drop support, 0.150 m differential motion and 19.1° turn response; dynamic gate uses recorded fixed-simulation-time activation/removal; narrow doorway preserves its declared 1.0 m opening | **PASS:** ROS/LiDAR/odometry path, populated costmaps, and semantic hits on layout-relevant obstacles | **PASS:** all eight motifs pass versioned trajectory/recovery gates. Corrected S-turn, dynamic recovery-success, and bounded blockage each pass 3/3 exact-condition repetitions; recovery feedback varies 1–8 in the dynamic scenario. The v1 straight-through run remains a failed negative calibration | **PASS for representative control:** isolated HUD, semantic, trajectory, and collider views passed; a focused `2` keypress changed Overview to Oblique. The omitted-scene aquatic launch is excluded as invalid calibration | **PASS:** matching manifest geometry and qualified action runs under null graphics; v1 compatibility validator hash reproduced exactly | **PASS for eight development contracts:** stable layout/obstacle IDs, exact manifest/configuration/artifact hashes, versioned behavior/repetition gates, evaluator-only schedule truth, and delivered BT/recovery/trajectory evidence; exact-condition repeats are not independent episodes, and physical cause/controller consumption are not inferred | **PARTIAL overall:** priority mechanisms repeatably qualified; broader route repetition, scenario-to-question contracts, and explanation evaluation remain `NOT_RUN` |
| RoboBoat ecological demonstration | Parallel workstream | Parallel workstream | Parallel workstream | Parallel workstream | Parallel workstream | Aquatic runtime requires graphics | Parallel workstream | **PARALLEL / OWNED ELSEWHERE** |

Active land development should move warehouse/proving-ground rows toward `NAVIGATION_PASS` and
`EXPLANATION_READY`, with explicit per-route results and artifact references.

## Retained infrastructure validation

| Environment | Retained result | Missing full validation | Submission status |
|---|---|---|---|
| F1TENTH Spielberg | Deterministic conversion plus structural/physics/headless qualification | Full-lap ROS navigation and source-simulator comparison | Retained; not active priority |
| Clearpath pipeline | Offline source/geometry/layer/contact validation plus local 1 m ROS/Nav2 sensor/motion smoke | Representative route, calibrated route catalog, native Gazebo comparison, controller-consumption evidence | `DEFERRED_POST_SUBMISSION` unless immediately required by land study |
| PX4 walls/ArUco/windy | Structural/physics/raycast/directional-response infrastructure checks | SITL/ROS navigation, camera detection, explanation evaluation, calibrated equivalence | `DEFERRED_POST_SUBMISSION` |
| RoboSub pool/underwater assets | Existing simulation infrastructure retained | Submission-quality autonomy, sensors/evidence, navigation routes, and explanation evaluation | `DEFERRED_POST_SUBMISSION` |

Existing aerial/underwater accomplishments remain valid within their recorded scopes. Deferral means
their missing navigation/explanation gates will not consume pre-submission time; it does not convert
past passes into failures.

## Batch result target

The environment validator should eventually emit one record per world/route containing environment
and asset hashes, scenario manifest hash, semantic/collider inventory, robot compatibility, sensor
checks, route outcome/path metrics, contacts, interactive screenshot references, headless result,
and explicit gate values. Until that aggregate schema exists, each gate must cite its retained
command/result in `docs/EXPERIMENTS.md` and must not infer unexecuted gates from adjacent tests.
