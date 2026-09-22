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
| Warehouse/industrial ecological world | **PASS:** 20 nominal canonical colliders, 20 separated renderers, 28 unique nominal semantic IDs; five manifest scenario contracts | **PASS:** drop/contact plus 0.150 m differential drive and 19.1° turn response; scenario collider/visual state changes share fixed-time boundaries | **PASS:** ROS/LiDAR/odometry, semantic hit on `rack-center-blocker`, populated costmaps | **PASS:** nominal detour; 53.38 s success versus 71.10 s bounded task-policy abort under complete blockage; temporary enclosure passes 3/3 exact-condition recovery-success repetitions with 16--20 maximum recovery feedback | **PASS:** direct X11 keyboard audit selected Overview, Oblique, and collision-aware Follow; H/C/T changed semantic, collider, and trajectory overlays; representative 1280×720 views are readable | **PASS:** final interactive build reproduced the exact manifest v2.2.0 headless result hash under null graphics | **PASS for ecological handoff:** exact scenario/configuration binding plus recovery-sequence and evidence-insufficiency questions declare required robot-visible fields and physical-cause/count/consumption withholding; frozen study is untouched | **PARTIAL overall:** environment and question-contract gates pass; explanation generation, parity audit, and annotation remain `NOT_RUN` |
| Configurable proving ground | **PASS:** preserved eight-layout v1 manifest plus additive one-layout v2 slalom revision; separate canonical/presentation roots; validators report 5–7 canonical colliders, matching collider-free renderers, 7–9 unique semantic IDs, zero duplicates | **PASS for qualified revisions:** collision/drop support, 0.150 m differential motion and 19.1° turn response; dynamic gate uses recorded fixed-simulation-time activation/removal; narrow doorway preserves its declared 1.0 m opening | **PASS:** ROS/LiDAR/odometry path, populated costmaps, and semantic hits on layout-relevant obstacles | **PASS:** all eight motifs pass versioned trajectory/recovery gates. Corrected S-turn, dynamic recovery-success, and bounded blockage each pass 3/3 exact-condition repetitions; recovery feedback varies 1–8 in the dynamic scenario. The v1 straight-through run remains a failed negative calibration | **PASS for representative control:** isolated HUD, semantic, trajectory, and collider views passed; a focused `2` keypress changed Overview to Oblique. The omitted-scene aquatic launch is excluded as invalid calibration | **PASS:** matching manifest geometry and qualified action runs under null graphics; v1 compatibility validator hash reproduced exactly | **PASS for ecological handoff:** exact layout/seed/configuration binding plus eight questions cover recovery, terminal policy, route shape/change, false premises, and causal/optimality withholding; exact-condition repeats remain non-independent | **PARTIAL overall:** environment and question-contract gates pass; explanation generation, parity audit, and annotation remain `NOT_RUN` |
| RoboBoat ecological demonstration | Parallel workstream | Parallel workstream | Parallel workstream | Parallel workstream | Parallel workstream | Aquatic runtime requires graphics | Parallel workstream | **PARALLEL / OWNED ELSEWHERE** |

Active land development should move warehouse/proving-ground rows toward `NAVIGATION_PASS` and
`EXPLANATION_READY`, with explicit per-route results and artifact references.

The shared land fixture now captures bounded ordered BT transitions and recovery-leaf invocation
IDs, and it passed a development-only recovery-success runtime check. This closes the prior
sequence/identity capture gap for recorded invocations. It does **not** close whole-history
completeness: current Jazzy `BehaviorTreeLog` delivery has no detectable publisher sequence gap,
and final root transitions were absent in three live checks. Ecological answers must therefore use
qualified observed-count language unless a later evidence source establishes completeness.

A current-source warehouse run now also passes the ordered-capture and evidence-separation gate:
3,994 transitions and four completed recovery-leaf invocations were retained without truncation,
the exact scenario/configuration identity was verified evaluator-side, and deterministic export
produced byte-identical physically separate evidence planes whose robot-visible leakage scan
passed. This establishes an ecological pipeline input, not explanation correctness; generation,
information-parity audit, blinded annotation, and statistical evaluation remain `NOT_RUN`.

Because 3,994 records approached the former shared 4,096 bound, ecological warehouse and
proving-ground launchers now use an explicit 16,384-transition capacity while the shared/frozen
default remains unchanged. A second current-build warehouse run retained all 3,950 unique
transitions and all four completed recovery-leaf invocations with zero drops, and reported both
configured capacities and retained counts. The repeated mechanism is a capacity qualification,
not an additional independent episode; whole-history completeness remains `not_proven`.

A current-build attempt to carry this export boundary into proving-ground `dynamic-gate-v1` did
not reproduce its historically qualified recovery-success mechanism: the warehouse-specific
90-second policy aborted near the goal, while one stock-policy rerun reached the client deadline;
both recorded zero recovery-leaf invocations. Both are retained negative calibrations and neither
was exported. Historical proving-ground passes remain scoped to their recorded revisions, but a
current-build recovery-success export is still `NOT_RUN`.

The export boundary now mechanically rejects this class of mismatch. Both negative artifacts fail
their declared `succeeded` terminal-status gate, while the current-build warehouse artifact passes
the new terminal/mechanism/inventory/zero-drop gates. This closes false admission; it does not
close the proving-ground runtime gap or create an explanation-evaluation result.

The proving-ground terminal-policy path now has a current-build mechanism-matching handoff.
`complete-blockage-v1` returned `aborted` at 71.809 seconds under the retained 70-second policy,
retained 629 unique transitions including `Timeout IDLE -> RUNNING` with zero drops, and passed
deterministic physically separated export plus an independent robot-visible leakage scan. Because
the terminal root transition is absent and topic loss is undetectable, this supports a recorded
task-policy abort—not physical obstacle causation, planner `no path`, or complete BT history.

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
