# Experiment Log

## 2026-09-23 — time-resolved command-motion instrumentation qualification

- **IMPLEMENTED / TESTED:** the passive observer capture at umbrella revision `42a33d9` retained
  376 `/nav2/cmd_vel` records and 3,141 odometry records. The goal-bounded blind export retains
  376 commands and 1,598 odometry samples, exact event/runtime/BT/Nav2 hashes, and strips the
  intervention-coded acquisition identifier. No Nav2 or Unity physics path was changed.
- **DIAGNOSTIC SUPPORTED, DEVELOPMENT ONLY:** five initial one-second windows calibrate a median
  0.2597 m/s measured response to a 0.800 m/s command. The earliest qualifying 7–17 s interval
  retains a 0.800 m/s median command and 0.000 m/s median planar odometry. Two FollowPath failures
  and two source-qualified Wait invocations precede a third attempt and action abort.
- **INDEPENDENT RECOMPUTATION / QA PASS:** `analysis/reference_command_motion.py` imports neither
  the proposed core nor exporter and reproduces the interval, measurements, and counts. QA passes
  source hashes, exact final-text verification, reference parity, and intervention-token leakage.
  Core plus exporter/reference regressions pass 28/28; the complete core suite passes 71/71.
- **BOUNDARY:** this supports a sustained command-to-motion discrepancy, not actuator acceptance,
  Nav2 consumption of delivered odometry, or a unique motor, mobility, obstruction, collision, or
  slip cause. The rerun qualifies instrumentation and adds zero independent scenario clusters.
  Model comparison, blind annotation, and confirmatory use are `NOT_RUN`.

## 2026-09-22 — corrected proving-ground v3 recovery capture

- **INFRASTRUCTURE-INVALID / NOT AN EPISODE:**
  `/tmp/proving-v3-recovery-btcap-dev-20260922-02` failed before NavigateToPose goal submission
  because the fixture's ROS `nav_msgs.msg.Path` import shadowed `pathlib.Path`. Revision `d701cf0`
  fixes that namespace collision. The attempt contributes no navigation or explanation evidence.
- **TESTED / RETAINED NEGATIVE CALIBRATION:** the corrected fresh capture used isolated ROS domain
  99, TCP port 11299, build-manifest SHA-256
  `6eb7cdde539fa57fac6c2ee461e71d0537c745418953cc91c483bd19aa773d3e`, and result root
  `/tmp/proving-v3-recovery-btcap-dev-20260922-03`. The predeclared contract expected `succeeded`;
  NavigateToPose instead returned `aborted` after 91.661 wall seconds. Delivered odometry records
  17.404 m displacement and a 21.214 m sampled path. Evaluator truth retains the four wall
  activations at 18.040 simulated seconds and removals at 34.040 seconds.
- **RECOVERY CAPTURE PASS / OUTCOME GATE FAIL:** passive capture retained 2,672 unique transitions
  and eight completed, reset-delimited, source-qualified recovery invocations against the 16,384
  and 1,024 capacities, with zero dropped transitions/invocations, open invocations, overlaps, or
  restart-without-reset anomalies. The invocations were three `ClearLocalCostmap-Context`
  completions and one each of `ClearLocalCostmap-Subtree`, `ClearGlobalCostmap-Subtree`, `Spin`,
  `Wait`, and `BackUp`; `Spin` terminated `FAILURE` and the others `SUCCESS`. Feedback's separate
  maximum recovery count was 8.
- **QA BLOCKED / EXPORT NOT_RUN:** exact scenario/configuration identity and the minimum-feedback
  recovery gate passed, but the required terminal-success condition did not. The independent QA
  summary at `/tmp/proving-v3-recovery-btcap-dev-20260922-03/environment-qa-summary.json` reports
  `BLOCKED`, `routeReady=false`, `navigation=PARTIAL`, and `headless=PARTIAL`. No ecological export
  was created. Whole-history completeness is `not_proven` because `BehaviorTreeLog` has no
  publisher sequence number and the configured terminal root transition was absent. This supports
  the eight recorded software invocations, not an exact episode count, changed costmap contents,
  controller consumption, physical causation, or an explanation-performance result.
- **DECISION:** preserve both the historical successful `-01` calibration and this current corrected
  negative result. Do not rerun merely to obtain success or weaken admission criteria. Use the
  already export-qualified warehouse recovery, proving-ground blockage, and S-turn artifacts for
  the ecological explanation pilot before spending more time tuning v3. Frozen/DVC artifacts and
  RoboBoat-specific source, environment, vehicle, sensor, physics, Nav2, and documentation files
  were untouched.

## 2026-09-22 — additive proving-ground bounded-recovery calibration

- **IMPLEMENTED / TESTED:** additive catalog `crane-land-proving-ground-v3` preserves v1/v2 and
  adds only `temporary-enclosure-recovery-v3`, a four-wall enclosure centered on the observed
  nominal trajectory. Its walls are scheduled to activate at 18 s and be removed at 34 s.
- **BUILD / STRUCTURAL PASS:** Unity 6000.5.10f1 built
  `/tmp/crane-v3-recovery-build/CRANE.x86_64`; its build-manifest SHA-256 is
  `6eb7cdde539fa57fac6c2ee461e71d0537c745418953cc91c483bd19aa773d3e`. Headless reference
  validation reported seven canonical colliders, seven separate visual renderers, nine unique
  semantic identities, zero duplicate IDs, and `STRUCTURAL_PASS`, `PHYSICS_PASS`, `SENSOR_PASS`,
  `HEADLESS_PASS`, and `EXPLANATION_READY`.
- **NAVIGATION / FAILURE-RECOVERY PASS:** the first predeclared development calibration used ROS
  domain 96, TCP port 11296, the retained 90-second recovery policy, a 100-second action deadline,
  and result root `/tmp/proving-v3-recovery-btcap-dev-20260922-01`. Evaluator truth records all four
  walls activating at 18.040 simulated seconds and being removed at 34.040 seconds. NavigateToPose
  succeeded at 85.219 wall seconds, traversed 17.478 m, and feedback changed from recovery count 0
  to 1. The independent QA summary passed its predeclared minimum-recovery gate. CRANE revision is
  `d5a25e6`; manifest, navigation-gate, BT-policy, and QA-summary SHA-256 values are respectively
  `c7c6b7ad713b6a74e9542ec767ebc826f1034e0163993c8d2e3e02f23603e3ae`,
  `ab360a15efec17e0c3795ea9d798b344ca28faf6ff7718e228595f59e7be84ba`,
  `9fb490be79d16c482d9c1b1a8f2f946d142e0d21ed3d4f5901aa3065304329d1`, and
  `019f43174e553047b627da3a9dc9f2fc636f594b31b29584e95663d1d2b72584`.
- **CAPTURE LIMITATION / EXPORT NOT_RUN:** passive capture retained 756 unique BT transitions with
  zero dropped transitions or invocations against the 16,384-transition capacity. The delivered
  chain includes FollowPath failure, the successful controller-recovery guard, and
  `ClearLocalCostmap-Context IDLE -> SUCCESS`, but no configured recovery leaf exposed the strict
  `IDLE -> RUNNING` edge used to assign a stable recovery-invocation ID. The ecological export's
  minimum-invocation gate was therefore not weakened and no separated export was produced. This
  run supports the recorded software sequence and feedback count, not an exact attempt count or
  physical causation. It is calibration, not an independent statistical episode.
- **REGRESSION:** 90 component land/reference tests plus two unittest subtests passed. Frozen/DVC
  artifacts and RoboBoat-specific source, environment, vehicle, sensor, physics, Nav2, and
  documentation files were untouched.

## 2026-09-22 — current-build proving-ground S-turn evidence

- **STRUCTURAL / PHYSICS / SENSOR / HEADLESS PASS:** the current player re-ran the v2 reference
  validator for `slalom-s-turn-v2`; seven canonical colliders, seven collider-free renderers, nine
  unique semantic IDs, floor/collision support, differential motion/turn response, and semantic
  sensor resolution passed under the exact v2 manifest.
- **NAVIGATION / ROUTE-SHAPE PASS, DEVELOPMENT ONLY:** on isolated ROS domain 95 and TCP port
  11295, NavigateToPose succeeded at 87.410 wall seconds. The independent QA summary reports a
  21.467 m sampled path, signed lateral extrema +1.343/−1.342 m, and four direction changes,
  satisfying the predeclared +0.75/−0.75 m and three-change S-turn gate. Ordered capture retained
  763 unique BT transitions with zero drops and no recovery invocations. QA-summary SHA-256 is
  `a04c7f95d1b5c7dd44c51437cfc87fc1c6bc3ee60925b825991c54fcb4dd4e82`.
- **ROUTE-ADMISSION PASS:** ecological admission now checks signed lateral extrema and direction
  changes, rather than accepting any successful trajectory with enough samples. The revised
  development contract SHA-256 is
  `65b10d62259e741c296d3fe20de4653bd00cde7b6ccce46763c9a6be195124ac`.
  The current S-turn passes; a unit regression proves a straight/no-reversal trace is rejected.
- **SEPARATED EXPORT PASS:** two outputs were byte-identical and the independent robot-visible
  leakage scan passed. The robot-visible trajectory summary reports 21.548 m from the fixture's
  one-second samples, lateral extrema +1.248/−1.342 m, and four direction changes. This supports
  an S-shaped recorded trajectory, not optimality, physical causation, or controller consumption.
- **REGRESSION:** 88 land/reference tests (plus two subtests) pass. Raw artifacts remain ephemeral
  under `/tmp`; this is not an independent study episode or explanation-performance result.
  Frozen/DVC artifacts and RoboBoat-specific content were untouched.

## 2026-09-22 — current-build proving-ground blockage export

- **NAVIGATION / TERMINAL-POLICY PASS, DEVELOPMENT ONLY:** current player build-manifest SHA-256
  `5ef48bba5c30570d1f85afbff0c71e6347c52918328338452ac0f847b67c6624` ran
  `complete-blockage-v1` on isolated ROS domain 94 and TCP port 11294 with the repository-retained
  70-second task-policy tree. The action returned the predeclared `aborted` result at 71.809 wall
  seconds, before the 90-second client deadline; the aggregate fixture verdict was valid.
- **ORDERED EVIDENCE PASS:** 629 unique transitions were retained against the 16,384-record
  ecological capacity with zero drops. `Timeout IDLE -> RUNNING` was record
  `bt-transition-000001`; zero recovery-leaf invocations and feedback sequence `[0]` were observed.
  Seventy trajectory samples covered 17.978 m with 3.016 m maximum lateral excursion and 3.465 m
  endpoint displacement. Fixture SHA-256 is
  `bccf5d469bb9db605756a45843bd5e8ce065f60738ffe0642166cd0ec0f5226b`.
- **FAIL-CLOSED EXPORT PASS:** the run satisfied its declared `aborted`, `Timeout`, trajectory,
  and zero-drop admission gates. Two export roots were byte-identical. Robot-visible SHA-256 is
  `5c30b7f4dbc03b60479c695cc933fb10a51cbbfa8a3341a569789a9ee6cdbf96`, evaluator-only SHA-256
  is `d9f7898a6a5a634b4ed8d5f2a0ad4eb29495050c604bc04ec99e227d017ce168`, and export-manifest
  SHA-256 is `4832fd3b58402965265819c574c300cce3fe642bcd0a2861be5f6197b621dad6`.
  The independent robot-visible leakage scan passed.
- **BOUNDARY:** the terminal root transition remained absent and subscriber loss remains
  undetectable, so BT history is `not_proven`. The evidence supports a recorded task-policy abort;
  it does not establish that the physical blocker caused termination or that the planner found no
  path. This is an interface/mechanism qualification, not an independent study sample or
  explanation-performance result. Frozen/DVC artifacts and RoboBoat-specific content were
  untouched.

## 2026-09-22 — fail-closed ecological mechanism admission

- **IMPLEMENTED:** CRANE revision `86e7658` adds explicit runtime-admission criteria to every
  development ecological scenario contract. Scenario/configuration identity alone is no longer
  sufficient: terminal status, minimum recorded recovery invocations, minimum trajectory
  inventory, required BT node observations, and zero-drop requirements are checked before export.
  The revised contract SHA-256 is
  `ff2b2c45606a8f918fd4a4d70194dcfa9ceeac1a031245a94cc3bbbfa529209d`.
- **REAL NEGATIVE-ARTIFACT PASS:** the two retained current-build `dynamic-gate-v1` calibrations
  were both rejected before output creation: the first because `aborted` did not satisfy the
  declared `succeeded` terminal status, and the second because `timeout` did not satisfy it. Thus
  neither a matching layout hash nor a plausible question can silently convert a mechanism miss
  into an ecological benchmark input.
- **REAL POSITIVE-ARTIFACT PASS:** the current-build warehouse recovery-success artifact passed
  admission with terminal `succeeded`, four retained recovery-leaf invocations, 3,950 retained
  transitions against a 16,384 capacity, and zero drops. Its regenerated separated export retained
  physical truth only in the evaluator plane. This validates admission behavior, not explanation
  correctness or an additional independent sample.
- **REGRESSION:** 86 land/reference tests (plus two subtests) pass. Frozen study files, governed
  DVC data, and RoboBoat-specific content were untouched.

## 2026-09-22 — proving-ground ecological export calibration

- **PURPOSE:** exercise the separated ecological evidence exporter on a proving-ground mechanism
  using the same current Unity player and ordered BT capture already qualified for the warehouse.
  These are development calibrations, not independent study episodes.
- **NEGATIVE / RETAINED:** `dynamic-gate-v1` with the warehouse-specific 90 s recovery policy
  activated its gate at 20.040 simulated seconds and removed it at 45.040, but the policy aborted
  near the goal after 91.659 wall seconds. It recorded 800 unique BT transitions, zero dropped
  records, and zero recovery-leaf invocations. This does not satisfy the contract's
  recovery-followed-by-success mechanism and was not exported or relabeled.
- **NEGATIVE / RETAINED:** one bounded rerun used the stock Jazzy replanning/recovery tree from the
  exact pinned ROS image (tree SHA-256
  `5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`; image digest
  `sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`).
  The client deadline elapsed at 105.009 s after 925 retained transitions, with zero recovery-leaf
  invocations and zero dropped records. It likewise was not exported. No further outcome-driven
  reruns were made.
- **INTERPRETATION:** the historical three-run proving-ground qualification remains valid for its
  recorded component/policy state, but it is not sufficient to claim that the same mechanism is
  export-ready on the current build. Fail-closed terminal/mechanism admission was added in the
  subsequent checkpoint; qualifying one current-build proving-ground scenario that actually
  satisfies its contract remains open. Frozen/DVC artifacts and RoboBoat-specific content were
  untouched.

## 2026-09-22 — ecological BT capture-capacity qualification

- **IMPLEMENTED:** CRANE revision `ac10443` keeps the shared/frozen fixture defaults at 4,096
  transitions and 1,024 recovery invocations, but gives warehouse and proving-ground ecological
  launchers a bounded 16,384-transition default. The capture summary and separated exporter now
  expose configured capacities and retained counts so truncation risk is auditable rather than
  inferred from a near-limit record count.
- **TESTED / DEVELOPMENT ONLY:** a second current-build
  `warehouse-temporary-enclosure-recovery-v1` run on isolated ROS domain 91 and TCP port 11291
  succeeded. It retained all 3,950 unique transitions and four completed recovery-leaf
  invocations (`Spin`, `Wait`, `BackUp`, `Spin`) against capacities 16,384 and 1,024, with zero
  dropped transitions or invocations. The maximum Nav2 feedback recovery count was 16; this remains
  a different count stream and does not convert four recorded BT invocations into an exact
  whole-history count.
- **COMPLETENESS LIMIT RETAINED:** the configured root terminal transition was again absent and
  `BehaviorTreeLog` still provides no publisher sequence number. History therefore remains
  `not_proven`, exact-count eligibility remains false, and no physical-causation claim is licensed.
- **REGRESSION:** 83 land/reference tests (plus two subtests), 105 umbrella/core tests, and four
  frozen-study integrity tests pass. The runtime root remains ephemeral under
  `/tmp/warehouse-btcap-dev-20260922-02`; it is neither a sealed study episode nor an independent
  statistical sample. Frozen/DVC artifacts and RoboBoat-specific content were untouched.

## 2026-09-22 — current-build warehouse BT capture and separated ecological export

- **BUILD PASS:** Unity CLI 1.0.0-beta.5 used installed Unity 6000.5.10f1 and the repository's
  `CranePerformanceBuild.BuildLinuxWorker` entry point to produce an isolated player under `/tmp`.
  CRANE build-manifest SHA-256 is
  `5ef48bba5c30570d1f85afbff0c71e6347c52918328338452ac0f847b67c6624`; it includes
  `TurtleBot3 Warehouse Validation` and warehouse manifest SHA-256
  `c6db13e9c7190482f1eca723cb515cc7a38ce01a9caa60d6fbf9720810e68d69`. Unity's incidental
  settings serialization changes were removed, leaving the component clean before execution.
- **NAVIGATION / RECOVERY PASS, DEVELOPMENT ONLY:** isolated ROS domain 90 and TCP port 11290 ran
  `warehouse-temporary-enclosure-recovery-v1` with the current player. Evaluator truth confirms
  environment `crane-industrial-warehouse-v2`, seed 4105, the exact four-wall activation at
  18.040 simulated seconds, and removal at 34.040 seconds. Nav2 succeeded after 75.516 wall
  seconds, displaced 12.605 m, sampled a 15.748 m path with 2.112 m lateral excursion, and reported
  a maximum feedback recovery count of 15.
- **ROBOT-VISIBLE BT EVIDENCE PASS:** the passive fixture retained 3,994 unique transitions with no
  duplicate or dropped records and four completed recovery-leaf invocations: `Spin`, `Wait`,
  `BackUp`, and `Spin`. The root terminal transition remained unobserved and the topic has no
  publisher sequence number, so history is still `not_proven` and exact-count eligibility is
  false. This is evidence for four recorded leaf invocations, not proof that exactly four recovery
  attempts occurred or that the physical enclosure caused them. Fixture-summary SHA-256 is
  `07e402570b4563e257dea8074d6ea5570ba5bf46c698a399113f49401bcfbd50`.
- **SEPARATED EXPORT PASS:** `export_ecological_evidence.py` bound the exact environment,
  configuration, BT-policy, and ecological-contract hashes and produced physically separate
  `robot_visible/` and `evaluator_only/` files plus a content-free hash manifest. Two independent
  output roots were byte-identical. Robot-visible SHA-256 is
  `326631676944546678951dc2a1ca068d43b120157189aabc1b49783ed5c43b22`, evaluator-only SHA-256
  is `a1f2ec8c7886879a62aa189338187db7eba2e7d1ee1d13f077153f016107c845`, and export-manifest
  SHA-256 is `64f1d1076cb754b1a07644a6fd238e44d8ed04e817ebd5960424bbdeda4e4f84`.
  The independent robot-visible leakage scan passed.
- **REGRESSION / BOUNDARY:** 68 land/reference tests and four frozen-study integrity tests pass.
  Raw build/run/export artifacts remain ephemeral under `/tmp`; this is not an independent study
  episode or explanation-performance result. Frozen/DVC artifacts and RoboBoat-specific content
  were untouched.

## 2026-09-22 — bounded ordered BT evidence capture for ecological land

- **IMPLEMENTED / TESTED:** `crane_ml` commit `8cc1cbb` adds a ROS-independent bounded transition
  recorder to the existing passive Nav2 fixture. Each retained transition has a stable record ID,
  node name/UID, prior/current status, event/message timestamps, accepted-goal relation, and goal
  ID when available. Exact-name-classified recovery leaves receive a distinct invocation ID only
  on `IDLE -> RUNNING`; repeated messages, completion, halting, overlap, open invocations, and
  bounded-record loss are represented explicitly. Nav2 feedback `number_of_recoveries` remains a
  separate evidence stream.
- **TESTED / DEVELOPMENT ONLY:** isolated ROS domain 89 and port 11289 reproduced a mobility-hold
  recovery followed by success. The fixture retained 22 unique transitions with no duplicate or
  dropped records, including `FollowPath RUNNING -> FAILURE`, a successful recovery guard, and
  `Wait IDLE -> RUNNING -> SUCCESS`. That Wait received
  `bt-recovery-invocation-000001`; independent Nav2 feedback changed from 0 to 1. Fixture-summary
  SHA-256 was `ec1fc96c5dbeb63cbb8c32b42a3620617b6320087dd98af269f7bc5dd0c9b591`;
  raw output remains ephemeral under `/tmp` and is not a study episode.
- **NEGATIVE / PRESERVED:** neither a 431-transition nominal run nor a short 34-transition run
  delivered the configured final `NavigateRecovery` transition before capture shutdown, including
  after a bounded 0.5 s post-result drain. `BehaviorTreeLog` has no publisher sequence number, so
  subscriber-side message loss cannot be excluded. Whole-history completeness therefore remains
  `not_proven` and exact recovery-count eligibility remains false. The supported wording is “one
  Wait invocation is recorded,” not “exactly one recovery occurred.”
- **INVALID WAREHOUSE CALIBRATION:** the locally retained player used for the first wrapper check
  emitted `crane-land-corridor-truth-v1` rather than the requested warehouse scenario truth. That
  run validates the mounted Python capture path only; it is not counted as warehouse ecological
  validation and does not alter the previously retained warehouse qualification artifacts.
- **REGRESSION:** 61 land/reference Python tests and four frozen-study integrity tests pass. Frozen
  artifacts, governed DVC data, and RoboBoat-specific files were untouched.

## 2026-09-22 — ecological land scenario-to-question contract

- **IMPLEMENTED / DEVELOPMENT ONLY:** a non-frozen contract maps five qualified land mechanisms
  to ten prospective evidence-rich questions: warehouse recovery-success, dynamic-gate
  recovery-success, bounded blockage termination, corrected S-turn route shape, and U-trap route
  change. Five questions require partial answers because physical cause, controller consumption,
  no-path, optimality, exact counts without complete invocation identity, or counterfactual success
  are not established by the allowed runtime evidence.
- **VALIDATED:** every scenario resolves against its exact environment manifest, runtime seed,
  catalog entry, manifest SHA-256, and derived configuration SHA-256. Robot-visible and
  evaluator-only evidence vocabularies are disjoint; required evidence is restricted to the former;
  question IDs are unique; withholding boundaries are mandatory; and `REPETITION_PASS` requires at
  least three declared qualified runs. The contract validates as 5 scenarios, 10 questions,
  and 5 explicitly partial questions. Contract SHA-256 is
  `bfd344cb22ad307a7dd9be2fb885a555466aae3a5ca53e0e87f1fa2f62f7bd3c`.
- **BOUNDARY:** qualification hashes select mechanisms but do not supply model-visible obstacle
  identity, schedules, geometry, or expected outcomes. This is not a frozen-study amendment,
  independent episode collection, answer generation, annotation, or performance evidence. Frozen
  artifacts, DVC payloads, and RoboBoat-specific files were untouched.

## 2026-09-22 — warehouse direct keyboard inspection and Follow-view correction

- **INTERACTIVE_PASS:** a dedicated X11 display at `:96` and an explicitly focused player window
  delivered real Input System events. `1` selected Overview, `2` selected Oblique, `H`/`C`/`T`
  changed semantic/collider/trajectory state in the HUD and rendering, and `3` selected Follow.
  Final screenshot SHA-256 values are respectively
  `2c3faf7ff564b418529e4e5d527f320a4761f15949e4584440f38f7658bd4efe`,
  `0048802b8a66088ba72377a8da2707547d7281c86affbf03ab5c5ddebf6822ef`,
  `3ff56d9237fa891236ec7aa7bed0c0929055025a41746ae1969eb6d6db073420`, and
  `a242bc03496842466c3010061e9cd0acc04b59510ce68823d30cace2a521b7f7`.
- **NEGATIVE CALIBRATION AND FIX:** the first X11 Follow capture changed the HUD state but showed
  only an empty horizon because the original chase position fell outside the south boundary. The
  generic reference-inspection controller now checks the canonical sightline, prefers the ordinary
  chase position when clear, uses an unobstructed lateral position at a boundary, and retains an
  overhead last resort. The final Follow capture keeps the robot readable with nearby warehouse
  geometry visible. This changes only a spectator camera and no collider, robot, sensor, or task
  state. An earlier Wayland-inherited launch exited during surface setup and supports no gate.
- **HEADLESS PARITY_PASS:** the final build manifest SHA-256 is
  `e6d17e58b4ca431c9ca80f2deb023b7eac8339fbd3e5cc283fa59207512eac3c`. Its independent warehouse
  validator reproduced result SHA-256
  `cd3dde90795bfb1c76a60eba9d2de8f1246bb8b39ab2ab6cbdc4fa65a199eda6`, including the same 20
  canonical colliders, 20 collider-free renderers, 28 semantic identities, physics, sensor,
  highlighting, differential-motion, and headless gates.
- **PARALLEL SAFETY:** display `:97` and the parallel RoboBoat runtime were not touched. The edited
  controller is attached only to reference-environment spectator cameras; the full multi-scene
  player compiled successfully, and no RoboBoat source, scene, model, physics, sensor, or Nav2
  configuration changed. Screenshots, player builds, and logs remain ephemeral under `/tmp`.

## 2026-09-22 — warehouse recovery mechanism repeatability qualification

- **PROSPECTIVE DEVELOPMENT CONTRACT:** before the additional runs, a versioned contract fixed
  three distinct runtime/navigation artifacts, exact warehouse environment, scenario, route,
  obstacle, seed, and configuration identity, action success, route acceptance, at least one
  recorded recovery, and all required QA gates. Contract SHA-256 is
  `9cb872500cd19a638eb8f39446f125a93e3c63d2028d0dc22212c123ab0b295f` and configuration SHA-256
  is `e18a16cbf9524e1dec4df9fae352ea9255b9ec2d6343dfe2cb6cc8a4150fe242`.
- **TEMPORARY ENCLOSURE / REPETITION_PASS:** all three runs recorded recovery followed by action
  success. Endpoint displacement ranged 12.590--12.597 m, sampled paths 14.295--15.918 m, and
  wall time 70.522--82.931 s. Maximum recovery feedback varied from 16 to 20 and is retained rather
  than treated as a fixed property. Aggregate SHA-256 is
  `818fd1c4118c1579d76e50f9222f06ddf68868b17f11e8a8b89bfa977a062033`.
- **IDENTITY RESOLUTION IMPLEMENTED:** the generic environment QA summarizer now resolves a
  warehouse dynamic scenario through its manifest, verifies its route, robot, challenge, expected
  broad outcome, seed, and complete ordered obstacle-ID inventory, and emits a deterministic
  configuration hash. This closes the earlier gap in which only static warehouse routes and
  proving-ground layouts had aggregate identity support.
- **DERIVATION BOUNDARY:** the retained original run was not overwritten. A schema-compatible
  summary was derived from its unchanged inputs and combined with two new runs on isolated ROS
  domains 186--187 and ports 10626--10627. Raw artifacts remain outside Git under `/tmp`.
- **LIMITS:** these are exact-condition development repetitions, not independent frozen-study
  episodes. Delivered BT, costmap, command, and odometry evidence does not prove controller
  consumption, and repeated temporal association does not establish physical causation.
  Scenario-to-question contracts, explanation generation, and blinded annotation remain
  `NOT_RUN`. Frozen/DVC artifacts and RoboBoat-specific files were untouched.

## 2026-09-22 — proving-ground mechanism repeatability qualification

- **PROSPECTIVE DEVELOPMENT CONTRACT:** before the new repeats, a versioned contract fixed three
  required distinct runtime/navigation artifacts, exact configuration identity, expected terminal
  status, route acceptance, required QA gates, and minimum recovery count per scenario. Contract
  SHA-256 is `bfdb6d521c5e5476304169ab5b5bc55a2f00e21c3745f5e93b7df219821d1d17`.
  Exact-condition repetitions measure operational reproducibility, not independent scenario
  diversity or statistical sample size.
- **CORRECTED S-TURN / REPETITION_PASS:** three runs succeeded and passed every v2 route-shape
  check. Sampled paths ranged 21.121–22.207 m, action time 82.961–89.875 s, endpoint displacement
  17.577–17.597 m, lateral direction changes were exactly four, and recovery feedback remained
  zero. Aggregate SHA-256 is
  `e5a10178e8104a3009e792af35b3e0f2bbb876617dd45c6b15266117e62bbc65`.
- **DYNAMIC GATE / REPETITION_PASS:** three runs recorded recovery followed by success. Sampled
  paths ranged 22.382–23.330 m and action time 91.383–98.323 s. Maximum recovery feedback varied
  materially from 1 to 8; this variability is retained and prevents treating a single recovery
  count as a scenario invariant. Aggregate SHA-256 is
  `21010265d272b2c4b6d738f2312ba31f40c8d824c0307c337a0259325033c112`.
- **COMPLETE BLOCKAGE / REPETITION_PASS:** three runs aborted under the explicit 70-second BT
  task-policy deadline before the 80-second client horizon. Action time ranged 70.331–71.131 s,
  sampled exploratory paths ranged 17.519–18.151 m, and recovery feedback remained zero. This is
  repeatable task-policy termination, not proof that the blocker physically caused the abort.
  Aggregate SHA-256 is
  `f7c6a43286c06a5fe3c11873e355d0b70dc084515c56cf09d8175c8ce6b081fe`.
- **DERIVATION BOUNDARY:** the historical first-run summaries for dynamic gate and blockage
  predated current artifact-hash and route-acceptance fields. They were not overwritten. New
  summaries were derived from their unchanged inputs solely for schema-compatible aggregation.
  All new runs used isolated ROS domains 180–185 and TCP ports 10620–10625; the parallel RoboBoat
  runtime was not stopped or modified.
- **LIMITS:** delivered BT, costmap, command, and odometry records do not prove controller
  consumption or physical causation. These development repeats are not frozen-study episodes.
  Scenario-to-question contracts, explanation generation, and blinded annotation remain
  `NOT_RUN`; raw outputs remain outside Git under `/tmp`.

## 2026-09-22 — corrected proving-ground slalom qualification

- **VERSIONED CORRECTION / HISTORY PRESERVED:** the v1 slalom manifest and its SHA-256 remain
  unchanged. Additive catalog `crane-land-proving-ground-v2` contains only
  `slalom-s-turn-v2`, using four alternating partial-width barrier banks. Catalog SHA-256 is
  `3f249258362fb47ceb135b7423e77ba5716bd1ebf4b3db7cf3650a8f8f0640f2`; its separately versioned
  navigation-gate SHA-256 is
  `67b10e775b2b7794e1e639dd69061156e2233651ef5cfe73db51c6e0934315c6`. Launchers default to v1
  and require explicit v2 selection, preventing historical artifact identity from changing.
- **PREDECLARED DEVELOPMENT RUN / PASS:** on isolated ROS domain 223 and port 10615, v2 succeeded
  in 82.96 s with 17.577 m endpoint displacement, a 21.122 m sampled path, lateral extrema of
  +1.349/-1.248 m, and four lateral direction changes. It delivered 727 BT transitions, 818
  returned commands, and 314 costmap observations with zero recoveries. The aggregate record
  passed identity, `NAVIGATION_PASS`, `HEADLESS_PASS`, `EXPLANATION_READY`, and every declared v2
  route-shape check; summary SHA-256 is
  `e4601110c15fdada259c26ae3027fb6bf381144b1aa0db40d036de29fd28f4b9`.
- **HEADLESS / COMPATIBILITY PASS:** the v2 validator reported seven canonical colliders, seven
  collider-free renderers, nine unique semantic IDs, and a semantic hit on
  `slalom-bank-west-near`; result SHA-256 is
  `e86eb8e45b800f8e393fbfc512620457088d09780c0dd1ce940ac11ff7718532`. The same player reproduced
  the exact historical v1 validator SHA-256
  `3d70047b66eed769fc061a5af2753a72ef0a593e870e42e58e59dabb2764f527`.
- **INTERACTIVE PASS FOR REPRESENTATIVE CONTROL:** isolated X11 overview and oblique captures
  showed the corrected topology, TurtleBot3, v2 environment/route HUD, semantic highlight, and
  collider overlays. A focused `2` keypress changed `View: Overview` to `View: Oblique`; before
  and after screenshot SHA-256 values are respectively
  `add950fbf078a38d11ae1c6f9c144a31de46740d966d70cd8a53b46c40776813` and
  `4bc3c6352b2efe1835b53d01d75ad447669f8524a2fffd3de7ebb39447354392`. An earlier Wayland attempt
  produced a black frame, and a later keyboard attempt omitted the named scene and opened the
  default aquatic scene; both are invalid calibration and contribute no environment evidence.
- **LIMITS:** this is one development calibration, not an independent explanation-study episode.
  Repeated qualification, scenario-to-question contracts, explanation generation, and blinded
  annotation remain `NOT_RUN`. Delivered transitions, commands, and observations do not prove
  controller consumption or physical causation. Frozen/DVC artifacts and RoboBoat-specific files
  were untouched.

## 2026-09-22 — proving-ground route-shape qualification

- **PREDECLARED DEVELOPMENT RUN / PASS:** `offset-gates-v1` ran on isolated ROS domain 222 and
  port 10614 with expected status `succeeded`. It finished in 76.86 s with 17.592 m endpoint
  displacement, a 19.571 m sampled path, lateral extrema of +1.597/-1.455 m, two sampled lateral
  direction changes, 682 delivered BT transitions, 768 returned commands, 287 costmap
  observations, and zero recoveries. This establishes traversal of the two offset route regions;
  it does not prove which delivered observation Nav2 consumed.
- **DEVELOPMENT RUN / PASS:** the valid `staggered-obstacles-v1` rerun on isolated ROS domain 220
  succeeded in 73.06 s with 17.546 m endpoint displacement, an 18.331 m sampled path, lateral
  extrema of +0.506/-0.347 m, three sampled lateral direction changes, 646 BT transitions, 721
  commands, 270 costmap observations, and zero recoveries. Its first attempt on domain 233 was
  infrastructure-invalid before the episode because the Fast DDS derived port exceeded the valid
  range; that startup attempt is retained as invalid calibration and contributes no evidence.
- **NEGATIVE CALIBRATION RETAINED:** `slalom-s-turn-v1` returned action success in 69.46 s, but its
  17.478 m sampled trajectory stayed exactly on the centerline with maximum angular command 0.0
  and zero lateral direction changes. The current bollards leave a straight route, so this run
  fails the declared S-turn navigation gate and is not counted as qualified.
- **AUTOMATED QA IMPLEMENTED:** the aggregate summarizer can apply a separately versioned
  behavioral-gate catalog after validating canonical manifest/configuration identity. Catalog
  SHA-256 is `86c98ca008778bd97401c165e00d2543bddeac1432c9b96d05077b484aec40e8`.
  This preserves the canonical v1 manifest and every earlier run identity while preventing mere
  action success from satisfying a route-shape claim. Staggered obstacles and offset gates return
  `NAVIGATION_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`; slalom returns navigation
  `PARTIAL`, headless `PARTIAL`, and overall `BLOCKED`. Their summary hashes are respectively
  `101381abef9faa7c57205694ac276db58a0d598d2011279e86673ef809342bee`,
  `8af41c8f573dd8b1d7cc3b0f91a287f5ea9618a519f271a35931178c1a6b9006`, and
  `55e756e282b0b1448e3043633441d9568e104d41cc8e515492280aea80cfaaca`.
- **LIMITS:** these are single development calibrations, not independent explanation-study
  episodes. The slalom geometry correction and rerun, repeated scenario qualification,
  explanation generation, and blinded annotation remain `NOT_RUN`. Raw artifacts remain under
  `/tmp`; frozen/DVC artifacts and RoboBoat-specific files were untouched.

## 2026-09-22 — proving-ground narrow passage, U-trap, and aggregate QA

- **PREDECLARED DEVELOPMENT RUN / PASS:** `narrow-doorway-v1` ran on isolated ROS domain 231 and
  port 10610 with expected status `succeeded`. It passed the centered 1.0 m opening in 69.06 s,
  displaced 17.467 m, followed a 17.542 m sampled path with 0.236 m lateral span, delivered 610 BT
  transitions and 264 costmap observations, and reported zero recoveries. This is evidence of
  narrow-passage traversal, not a replanning claim. Fixture SHA-256 is
  `62d034616e09fd187a16645e12325add184cda354f7271a1351ce9854ef007c1`.
- **PREDECLARED DEVELOPMENT RUN / PASS:** `u-trap-v1` ran on isolated ROS domain 232 and port 10611
  with expected status `succeeded`. It advanced into the trap region, reversed across 14 sampled
  intervals, moved 3.003 m laterally onto an exterior route, and returned to the goal. It succeeded
  in 98.16 s with 17.604 m endpoint displacement, 25.207 m sampled path, 871 delivered BT
  transitions, 375 costmap observations, and zero recoveries. This establishes a substantial route
  change around the canonical trap; delivered observations do not prove which input caused it.
  Fixture SHA-256 is
  `53915007050868879651f411cef83135c75ad9f6e0e10ecefcc283b1af545e6c`.
- **HEADLESS PARITY / PASS:** independent validators for the doorway and U-trap returned
  `STRUCTURAL_PASS`, `PHYSICS_PASS`, `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`, with
  zero duplicate semantic IDs and semantic ray hits on `doorway-east-jamb` and `u-trap-back`.
  Result SHA-256 values are
  `82a22fc9b37e86fe95e039dcef7c023e59b1062e3755444c787f431d33ccad75` and
  `011ec87998fdc3ad72ffaa72a03a933e7732c351230d0e492188bfc276318000`.
- **AUTOMATED QA IMPLEMENTED:** `summarize_environment_qa.py` now resolves both warehouse-route
  and proving-ground-layout schemas behind its existing command interface. It verifies exact
  manifest/configuration identity, contract parity, expected terminal status, and independent
  structural/navigation records; computes path, excursion, and sampled reversal metrics; and
  hashes every referenced artifact. Actual summaries for all five qualified proving-ground layouts
  report `identityValid=true`, `NAVIGATION_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`.
  Dynamic-gate recovery-success and expected complete-blockage abort additionally report
  `FAILURE_RECOVERY_PASS`. Overall verdicts remain `PARTIAL` because interactive evidence is not
  silently inferred. A retained warehouse nominal route was also re-summarized through the same
  interface and preserved `identityValid=true`, `NAVIGATION_PASS`, `HEADLESS_PASS`, and
  `EXPLANATION_READY`, confirming warehouse-output compatibility.
- **QA / LIMITS:** 50 land/reference tests pass. These are single development calibrations, not
  independent explanation-study episodes. `staggered-obstacles-v1`, `slalom-s-turn-v1`, and
  `offset-gates-v1`, repeated-run qualification, explanation generation, and blinded annotation
  remain `NOT_RUN`. Raw outputs remain ephemeral under `/tmp`; frozen study data, DVC artifacts,
  and RoboBoat-specific files were untouched.

## 2026-09-22 — configurable land proving-ground implementation and calibration

- **IMPLEMENTED:** CRANE's existing TurtleBot3 warehouse scene can now replace its authored world
  with manifest-driven `crane-land-proving-ground-v1`. The SHA-256
  `bea854292d7298e04f37ed9f6cc50f49d59d51fdec0e1b78a9d5f9247beee720` catalog defines eight
  deterministic layouts: staggered obstacles, S-turn slalom, offset gates, narrow doorway,
  U-trap, alternate corridors, complete blockage, and dynamic gate. Canonical collision,
  collider-free presentation, semantics, schedules, configuration hashes, and evaluator truth
  remain separate. The frozen corridor truth schema and study artifacts were not changed.
- **NEGATIVE CALIBRATION RETAINED:** the first 18 m alternate-corridor run used the warehouse's
  30 m rolling global costmap and aborted in 1.14 s. The planner explicitly reported the goal at
  `(18, 0)` outside its bounds. A dedicated proving-ground configuration widened only the
  ecological global window to 44 m; this is not counted as an environment failure or hidden.
- **TESTED ONCE / NAVIGATION CALIBRATIONS:** `alternate-corridors-v1` succeeded in 71.21 s with
  17.573 m endpoint displacement, 17.930 m sampled path, 1.10 m lateral excursion, 628 delivered
  BT transitions, 711 commands, 268 costmap observations, and zero recovery feedback.
  `dynamic-gate-v1` activated at simulation time 20.040 s, was removed at 45.040 s, and succeeded
  in 91.38 s with maximum recovery feedback 1, a delivered `FollowPath` failure and contextual
  local clear, 22.328 m sampled path, and 1.723 m lateral span. `complete-blockage-v1` aborted at
  70.33 s under the existing separate 70 s task-policy deadline, before its 80 s client deadline,
  after 17.973 m sampled exploratory motion and 4.54 m lateral span. These are development runs,
  not independent study episodes; no scan-consumption or obstacle-causation claim is made.
- **TESTED / HEADLESS QA:** Unity 6000.5.10f1 built Linux player SHA-256
  `a7ad5b156bd9a1232544ff6fc12e5f863d8f1f2348c5b141f5c3d4230e5be292`. The alternate-corridor
  validator returned `valid=true`, six canonical colliders, six collider-free renderers, eight
  unique semantic IDs, semantic LiDAR hit `alternate-route-divider`, evidence highlighting,
  collision/drop support, differential response, `STRUCTURAL_PASS`, `PHYSICS_PASS`,
  `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`; result SHA-256 is
  `3d70047b66eed769fc061a5af2753a72ef0a593e870e42e58e59dabb2764f527`.
- **TESTED / INTERACTIVE PARTIAL:** the proving-ground build reconfigures the existing
  presentation-only inspection controller with the selected layout and relevant obstacle IDs.
  Isolated 1280×720 overview and oblique captures showed the correct environment/layout HUD,
  semantic highlight, collider wireframes, and trajectory state. The host Wayland attempt exited
  during surface setup and yielded no usable audit; the accepted captures used a separately named
  X display and did not touch the parallel RoboBoat display. Manual keyboard polling remains
  `NOT_RUN`, so this is not a full interactive pass.
- **QA / LIMITS:** all 49 land/reference static tests passed; the build compiled cleanly and the
  headless validator passed after inspection wiring. Five layouts and repeated-run qualification
  remain `NOT_RUN`; explanation generation and blinded annotation remain `NOT_RUN`. Build,
  screenshots, and calibration outputs are ephemeral under `/tmp`; no DVC or sealed artifact was
  modified.

## 2026-09-22 — warehouse temporary-enclosure recovery calibration

- **IMPLEMENTED / RETAINED DEVELOPMENT INFRASTRUCTURE:** warehouse manifest v2.2.0 adds a
  four-wall temporary enclosure with stable semantic IDs. All walls activated at simulation time
  18.040 s and were removed at 34.040 s; scheduled and actual times remain evaluator-only. The
  recovery BT preserves the existing navigation/recovery structure and uses a 90 s steady-clock
  task-policy deadline (SHA-256
  `9fb490be79d16c482d9c1b1a8f2f946d142e0d21ed3d4f5901aa3065304329d1`).
- **NEGATIVE CALIBRATION RETAINED:** the first run under the earlier 70 s policy exercised 15
  recovery leaf invocations and resumed substantial motion after enclosure removal, but aborted
  about 1.4 m short of the goal. It is recovery followed by a task-policy deadline, not
  recovery-success. A first Unity build attempt hung after import and was terminated with exit 130;
  it is infrastructure-invalid and supports no validation claim. The clean retry built and passed.
- **TESTED ONCE / NOT A STUDY EPISODE:** the predeclared 90 s follow-up succeeded in 82.93 s with
  maximum recovery feedback 20, recovery sequence
  `[0,1,3,4,5,6,7,8,10,11,12,13,14,15,17,18,19,20]`, 4,499 delivered BT transitions, planner and
  controller failures, contextual and system-level costmap clears, spin/wait/backup transitions,
  658 returned controller commands, and 276 costmap observations. Its unobstructed control
  succeeded in 53.62 s with zero recoveries. Delivered odometry and costmap/BT messages are not
  proof of internal controller consumption or physical causation.
- **QA:** manifest v2.2.0 validation retained 20 canonical colliders, 20 presentation renderers,
  and 28 nominal semantic IDs. The land/reference contract suite passed (`41 passed`); all BT XML
  parsed, changed shell scripts passed syntax checks, and `git diff --check` passed. The headless
  validator result SHA-256 is
  `cd3dde90795bfb1c76a60eba9d2de8f1246bb8b39ab2ab6cbdc4fa65a199eda6`; the manifest SHA-256 is
  `c6db13e9c7190482f1eca723cb515cc7a38ce01a9caa60d6fbf9720810e68d69`. These runs are environment
  calibration only and do not contribute independent samples to the frozen F/G/H study.

## 2026-09-22 — sealed pn-0028 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0028`, seed 3028, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.123 m displacement, 308 returned controller commands, 65 costmap
  observations, maximum 9,055 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring or used to change the protocol.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both frozen questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 623,562 input tokens, 415,744 cached input tokens, 4,814
  output tokens, 892 reasoning tokens, and 237.627 s aggregate latency. G's failure-cause
  realization passed final-text verification and remained partial; its recovery-mechanism
  realization failed verification and used the full checked-template fallback. No repair call or
  resampling was made. A--E remain non-model smoke outputs and frozen model evaluation is
  `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0028-provenance-v1.json`.
- **VERIFIED:** all 24 robot-visible, 15 evaluator-only, and eight model/cache manifest artifacts
  match their retained byte counts and SHA-256 hashes; the robot-visible leakage scan passed. The
  first model-run attempt failed before caller construction because stale temporary Unity builds
  exhausted `/tmp`; it produced no output or cache artifact. Twenty-two stopped, rebuildable
  environment-build directories were removed, freeing roughly 12 GB, and the governed run then
  completed without changing any frozen file, runtime, prompt, or call policy.

## 2026-09-22 — sealed pn-0029 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-followed-by-success row `pn-0029`, seed 3029,
  passed every answer-blind inclusion gate and the exact expected-success contract. The action
  succeeded after one unique Wait invocation with 3.717 m displacement, 255 returned controller
  commands, 80 costmap observations, maximum 13,598 occupied cells, and accepted 10/7-unit parity
  audits. The capture used the exact frozen CRANE commit `c559932a5ebef00bfa7752511799fd904e5c9dbe`;
  the working gitlink was restored to `c46de4d7e83a18ebef3abc4c97eff1b706a79282` afterward.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both frozen questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 481,153 input tokens, 326,912 cached input tokens, 4,681
  output tokens, 801 reasoning tokens, and 138.454 s aggregate latency. G's failure-cause
  realization passed final-text verification; its recovery-mechanism realization failed exact
  verification and used the frozen deterministic checked-template fallback. No repair call or
  resampling was made. No output was scored or used to alter the protocol. A--E remain non-model
  smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0029-provenance-v1.json`.
- **VERIFIED:** the robot-visible leakage scan passed across all 24 retained files. Robot-visible,
  evaluator-only, output, and cache payloads are content-addressed by their retained manifests and
  DVC pointers. Frozen design, prompts, split, annotation guide, runtime, inclusion rules, and
  stopping rules were unchanged.

## 2026-09-22 — sealed pn-0030 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0030`, seed 3030, passed every
  answer-blind inclusion gate and the exact expected-abort contract. The action aborted after two
  unique Wait invocations with 0.233 m displacement, 315 returned controller commands, 65 costmap
  observations, maximum 8,907 occupied cells, and accepted 10/7-unit parity audits. Capture used
  exact frozen CRANE commit `c559932a5ebef00bfa7752511799fd904e5c9dbe`; the current gitlink was
  restored afterward.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both frozen questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 514,828 input tokens, 351,488 cached input tokens, 4,796
  output tokens, 822 reasoning tokens, and 149.181 s aggregate latency. G's failure-cause
  realization passed final-text verification; its recovery-mechanism realization used the frozen
  deterministic fallback after exact verification rejected the candidate. No repair call,
  resampling, scoring, or protocol change occurred. A--E remain non-model smoke outputs and frozen
  model evaluation is `NOT_RUN`. Retained hashes and usage are in
  `manifests/model_outputs/pn-0030-provenance-v1.json`.
- **VERIFIED:** all robot-visible, evaluator-only, output, and cache artifacts are governed by
  content-addressed manifests and DVC pointers; leakage, frozen integrity, scoped regression, and
  data-governance checks are required before checkpoint publication.

## 2026-09-22 — sealed pn-0031 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-followed-by-success row `pn-0031`, seed 3031,
  passed every answer-blind inclusion gate and expected-success contract. The action succeeded
  after one unique Wait invocation with 2.716 m displacement, 208 returned controller commands,
  61 costmap observations, maximum 13,044 occupied cells, and accepted 10/7-unit parity audits.
  Capture used exact frozen CRANE commit `c559932a5ebef00bfa7752511799fd904e5c9dbe` and restored
  the current gitlink afterward.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 489,399 input tokens, 372,224 cached input tokens, 4,754
  output tokens, 996 reasoning tokens, and 198.583 s aggregate latency. Both G realizations used
  the frozen deterministic checked-template fallback after exact final-text verification rejected
  their candidates. No repair call, resampling, scoring, or protocol change occurred. A--E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Retained hashes and usage are
  in `manifests/model_outputs/pn-0031-provenance-v1.json`.
- **VERIFIED:** robot-visible leakage scan passed across all 24 files. Robot-visible,
  evaluator-only, output, and cache payloads are content-addressed by retained manifests and DVC
  pointers. Frozen design, prompts, split, annotation guide, runtime, inclusion rules, and stopping
  rules remain unchanged.

## 2026-09-22 — sealed pn-0032 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0032`, seed 3032, passed every
  answer-blind inclusion gate and expected-abort contract. The action aborted after two unique
  Wait invocations with 0.000 m displacement, 303 returned controller commands, 63 costmap
  observations, maximum 9,217 occupied cells, and accepted 10/7-unit parity audits. The zero
  displacement is retained as observed and was not used to trigger a rerun. Capture used exact
  frozen CRANE commit `c559932a5ebef00bfa7752511799fd904e5c9dbe` and restored the current
  gitlink afterward.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 645,513 input tokens, 477,696 cached input tokens, 4,493
  output tokens, 882 reasoning tokens, and 154.082 s aggregate latency. Both G realizations used
  the frozen deterministic checked-template fallback after exact final-text verification rejected
  their candidates. No repair call, resampling, scoring, or protocol change occurred. A--E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Retained hashes and usage are
  in `manifests/model_outputs/pn-0032-provenance-v1.json`.
- **VERIFIED:** robot-visible leakage scan passed across all 24 files. Payloads are governed by
  retained content-addressed manifests and DVC pointers; frozen study artifacts remain unchanged.

## 2026-09-22 — sealed pn-0033 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-followed-by-success row `pn-0033`, seed 3033,
  passed every answer-blind inclusion gate and expected-success contract. The action succeeded
  after one unique Wait invocation with 2.981 m displacement, 222 returned controller commands,
  66 costmap observations, maximum 13,266 occupied cells, and accepted 10/7-unit parity audits.
  Capture used exact frozen CRANE commit `c559932a5ebef00bfa7752511799fd904e5c9dbe`; the current
  gitlink was restored afterward.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with
  Luna-low: six unique calls, no retries, 484,925 input tokens, 370,176 cached input tokens, 4,655
  output tokens, 954 reasoning tokens, and 135.548 s aggregate latency. Both G realizations used
  the frozen deterministic checked-template fallback after exact verification rejected their
  candidates. No repair call, resampling, scoring, or protocol change occurred. A--E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained
  in `manifests/model_outputs/pn-0033-provenance-v1.json`.
- **VERIFIED:** robot-visible leakage scan passed across all 24 files. Payloads are governed by
  retained content-addressed manifests and DVC pointers; frozen study artifacts remain unchanged.

## 2026-09-22 — research redirect, archive audit, and final legacy annotation packet

- **DECISION / COLLECTION CLOSED EARLY:** the legacy provenance cohort is frozen at 33 included
  episodes (17 recovery-success, 16 terminal-abort), below its prespecified minimum 40 and target
  50. The redirect was based on deadline/scientific scope before any sealed annotation; no sealed
  labels or adjudicated results exist. Frozen files, raw evidence, answers, and analysis remain
  unchanged. See `manifests/study/research-redirect-20260922.json`.
- **AUDIT PASS:** direct size/SHA-256 checks passed for 792 robot-visible files, 495 evaluator-only
  files, and 264 output/cache artifacts. All 33 checkpoints pin frozen CRANE commit `c559932...`,
  freeze integrity passed, and R2 reported cache/remote synchronization.
- **FRESH-CHECKOUT RESTORE PASS:** a clean `origin/main` clone initially had no R2 remote, as
  designed. After running the documented local `scripts/configure_dvc_r2.sh` step with private
  credentials, `dvc pull` restored all seven governed roots (3,967 files added), and all 1,551
  artifacts referenced by 99 episode/model manifests matched byte counts and SHA-256 hashes.
  Builds, staging data, and non-governed ignored files were not expected to restore.
- **TOOLING LIMITATION:** `analysis/audit_model_artifact_manifest.py` targets an older aggregate
  schema and fails before validation on current per-episode manifests because
  `accepted_output_roots` is absent. The direct current-schema audit passed; the utility should be
  adapted prospectively without modifying frozen study artifacts.
- **PACKAGED / NOT_ANNOTATED:** `sealed-primary-v3` contains 198 blind F/G/H responses covering all
  33 episodes. The evaluator-only key remains physically separate. Packet/key sizes and hashes are
  retained in `manifests/annotation/sealed-primary-v3.json`. Dual annotation, adjudication, key
  join, and sealed statistical analysis remain `NOT_RUN`.
- **FALLBACK AUDIT:** G used deterministic fallback on 46/66 responses (69.7%): all 33 recovery-
  mechanism answers and 13/33 physical-cause answers. This is an operational outcome, not a
  correctness label; final reporting must distinguish raw realization acceptance from final-answer
  performance and describe G as predominantly template-rendered if this pattern remains.

## 2026-09-21 — sealed pn-0027 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0027`, seed 3027, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 3.457 m displacement, 245 returned controller commands, 75 costmap
  observations, maximum 13,814 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six unique calls, no retries, 490,737 input tokens, 332,288 cached input tokens, 4,286 output
  tokens, 843 reasoning tokens, and 139.919 s aggregate latency. Both G realizations failed
  final-text verification and used checked-template fallback; the failure-cause answer is partial
  and the recovery-mechanism answer is full. No repair call or resampling was made. A–E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained
  in `manifests/model_outputs/pn-0027-provenance-v1.json`.
- **VERIFIED:** all 24 robot-visible, 15 evaluator-only, and eight model/cache manifest artifacts
  match their retained byte counts and SHA-256 hashes; the robot-visible leakage scan passed; the
  full suite passed with 105 tests.

## 2026-09-21 — sealed pn-0026 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0026`, seed 3026, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.000 m displacement, 305 returned controller commands, 63 costmap observations,
  maximum 9,217 occupied cells, and accepted 10/7-unit parity audits. The zero displacement is
  retained, not rerun or filtered. No answer was inspected for scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six unique calls, no retries, 615,887 input tokens, 444,160 cached input tokens, 4,610 output
  tokens, 772 reasoning tokens, and 142.399 s aggregate latency. G used checked-template fallback
  for recovery mechanism after its realization failed final-text verification; its partial
  failure-cause realization passed. No repair call or resampling was made. A–E remain non-model
  smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0026-provenance-v1.json`.
- **VERIFIED:** all 24 robot-visible, 15 evaluator-only, and eight model/cache manifest artifacts
  match their retained byte counts and SHA-256 hashes; the robot-visible leakage scan passed; the
  full suite passed with 105 tests.

## 2026-09-21 — sealed pn-0025 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0025`, seed 3025, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 3.224 m displacement, 236 returned controller commands, 69 costmap
  observations, maximum 13,784 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six unique calls, no retries, 497,247 input tokens, 335,104 cached input tokens, 4,353 output
  tokens, 661 reasoning tokens, and 140.299 s aggregate latency. Both G realizations failed
  final-text verification and used checked-template fallback; the failure-cause answer is partial
  and the recovery-mechanism answer is full. No repair call or resampling was made. A–E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained
  in `manifests/model_outputs/pn-0025-provenance-v1.json`.
- **VERIFIED:** all 24 robot-visible, 15 evaluator-only, and eight model/cache manifest artifacts
  match their retained byte counts and SHA-256 hashes; the robot-visible leakage scan passed; the
  full suite passed with 105 tests.

## 2026-09-21 — sealed pn-0024 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0024`, seed 3024, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.092 m displacement, 305 returned controller commands, 63 costmap observations,
  maximum 8,741 occupied cells, and accepted 10/7-unit parity audits. No answer was inspected for
  scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six unique calls, no retries, 476,899 input tokens, 360,960 cached input tokens, 4,577 output
  tokens, 742 reasoning tokens, and 139.303 s aggregate latency. Both G realizations failed
  final-text verification and used checked-template fallback; the failure-cause answer is partial
  and the recovery-mechanism answer is full. No repair call or resampling was made. A–E remain
  non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are retained
  in `manifests/model_outputs/pn-0024-provenance-v1.json`.
- **VERIFIED:** all 24 robot-visible, 15 evaluator-only, and eight model/cache manifest artifacts
  match their retained byte counts and SHA-256 hashes; the robot-visible leakage scan passed; the
  full suite passed with 105 tests.

## 2026-09-21 — load-balancer source-change boundary recorded

- **OPERATIONAL CHANGE / EFFECT UNKNOWN:** the operator reported changing the source used by the
  model load balancer. The observable client-configuration modification falls between the retained
  calls for `pn-0021` and `pn-0022`; the exact server deployment revision and resolved backend are
  not exposed by the client. Amendment 6 freezes retention of all episodes and a descriptive or
  sufficiently powered stratified sensitivity check without changing the paired F-versus-G primary
  analysis. No response was inspected, rerun, excluded, or reclassified.

## 2026-09-21 — sealed pn-0023 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0023`, seed 3023, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 2.975 m displacement, 222 returned controller commands, 68 costmap
  observations, maximum 13,044 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 577,930 input tokens, 369,408 cached input tokens, 4,566 output tokens,
  855 reasoning tokens, and 191.217 s aggregate latency. Both G realizations failed final-text
  verification and used checked-template fallback; no repair call or resampling was made. A–E
  remain non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are
  retained in `manifests/model_outputs/pn-0023-provenance-v1.json`.

## 2026-09-21 — sealed pn-0022 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0022`, seed 3022, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.000 m displacement, 295 returned controller commands, 60 costmap
  observations, maximum 8,732 occupied cells, and accepted 10/7-unit parity audits. The zero
  displacement is retained, not rerun or filtered. No answer was inspected for scoring.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 705,643 input tokens, 491,520 cached input tokens, 4,867 output tokens,
  754 reasoning tokens, and 171.134 s aggregate latency. G used checked-template fallback for the
  recovery-mechanism question after its single generated realization failed final-text
  verification; the failure-cause realization passed. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0022-provenance-v1.json`.

## 2026-09-21 — annotation-pair recovery and DVC sync correction

- **DIAGNOSED:** the committed `annotation_keys.dvc` object was absent locally and on R2. The DVC
  sync wrapper still listed six targets after pointer refresh had expanded to seven, so Claude's
  claimed key publication could not be restored. The original 54-row Claude packet is retained but
  unusable. A historical Luna key survived under the wrong `model_outputs` boundary.
- **IMPLEMENTED / VERIFIED LOCALLY:** the sync wrapper now includes evaluator-only annotation keys,
  a regression test requires both DVC scripts to name all seven roots, and the legacy Luna key was
  relocated to evaluator-only storage. Fresh pairs were generated without inspecting responses:
  `sealed-primary-v2` has 126 rows/entries over 21 episodes and `sealed-claude-v2` has 54 over nine.
  Both packet hashes match their newly generated evaluator-only keys. Annotation remains `NOT_RUN`.
- **TESTED / PUBLISHED:** all seven pointers were refreshed from a fully materialized workspace;
  the guarded upload pushed six new DVC objects and post-upload status reported `Cache and remote
  'r2' are in sync.` The v2 pairs are remotely reproducible. Git pointer checkpoint follows this
  ledger entry.

## 2026-09-20 — sealed Claude-family replication arm completed

- **SEALED SECONDARY-ARM CALLS RETAINED / NOT ANNOTATED:** the declared nine-episode Claude
  replication over `pn-0001`–`pn-0009` is complete. Eighteen result envelopes exist, two questions
  per episode, each containing exactly one physical call for F, G, and H: **54 physical calls, 54
  unique cache keys, no retry and no resampling**. Every envelope reports
  `status = CLAUDE_ARM_SECONDARY_REPLICATION`, `single_sample_no_retry = true`,
  `evaluator_truth_available_to_methods = false`, `read_only_workspace_verified = true`, accepted
  information parity, `claude-sonnet-5` at low effort, and pinned commit
  `c559932a5ebef00bfa7752511799fd904e5c9dbe`. No sealed answer text was opened or summarized.
- Resource totals across the 54 calls: 4,176,634 input tokens, 3,511,517 cached input tokens,
  74,953 output tokens, 1,783 reasoning output tokens, 944.116 s aggregate latency, and $4.1116
  provider-reported cost. Cost is reported for this arm only; the primary ChatGPT-login arm never
  reported it, so no cross-arm cost comparison is valid.
- Condition G used its deterministic checked-template fallback on 16 of 18 responses — 9/9
  recovery-mechanism and 7/9 failure-cause — after the single generated realization failed final-text
  verification. Two failure-cause realizations were accepted. No repair call was made and no
  verification failure was prompt-tuned away.
- Artifact hashes and usage are retained in
  `manifests/model_outputs/provenance-claude-replication-arm-v1.json`. All 72 manifest artifacts —
  18 envelopes plus 54 cache records — were independently re-hashed and matched on byte length and
  SHA-256.
- **Infrastructure failure retained, not scored:** one earlier condition-H call for `pn-0004
  failure-cause` returned a Claude Code CLI `is_error` envelope with `api_error_status = 429` and an
  account spend-limit notice in place of a response. It produced no parsed answer, cost $0.0472168,
  and is retained under
  `research/explanation_fidelity/model_cache/claude-replication-v1/_retained_failed_calls/`. It is
  excluded from the 54-call shape, the manifest, and every summary. The adapter previously wrote such
  a record into the answer cache, which made the call permanently unrepeatable; see arm amendment 3.
- The arm reuses retained episodes and therefore contributes **zero** new independent clusters. It
  does not relieve the unmet 40-episode primary minimum, which stands at 21 included episodes.
  Annotation is `NOT_RUN` and no cross-family effect estimate exists.

## 2026-09-20 — sealed pn-0021 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0021`, seed 3021, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 2.726 m displacement, 216 returned controller commands, 63 costmap
  observations, maximum 12,896 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 455,754 input tokens, 356,864 cached input tokens, 4,789 output tokens,
  1,068 reasoning tokens, and 157.513 s aggregate latency. G used checked-template fallback for
  the recovery-mechanism question after its single generated realization failed final-text
  verification; the failure-cause realization passed. No repair call or resampling was made. A–E
  remain non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are
  retained in `manifests/model_outputs/pn-0021-provenance-v1.json`.

## 2026-09-20 — sealed pn-0020 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0020`, seed 3020, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.290 m displacement, 313 returned controller commands, 66 costmap
  observations, maximum 9,708 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 503,482 input tokens, 361,216 cached input tokens, 4,805 output tokens,
  748 reasoning tokens, and 152.312 s aggregate latency. G used checked-template fallback for the
  recovery-mechanism question after its single generated realization failed final-text
  verification; the failure-cause realization passed. No repair call or resampling was made. A–E
  remain non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are
  retained in `manifests/model_outputs/pn-0020-provenance-v1.json`.

## 2026-09-20 — sealed pn-0019 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0019`, seed 3019, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 3.717 m displacement, 255 returned controller commands, 79 costmap
  observations, maximum 14,100 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 537,878 input tokens, 386,304 cached input tokens, 4,517 output tokens,
  703 reasoning tokens, and 150.839 s aggregate latency. G used checked-template fallback for the
  recovery-mechanism question after its single generated realization failed final-text
  verification; the failure-cause realization passed. No repair call or resampling was made. A–E
  remain non-model smoke outputs and frozen model evaluation is `NOT_RUN`. Hashes and usage are
  retained in `manifests/model_outputs/pn-0019-provenance-v1.json`.

## 2026-09-20 — sealed pn-0018 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0018`, seed 3018, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.170 m displacement, 308 returned controller commands, 64 costmap
  observations, maximum 8,829 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 409,079 input tokens, 306,176 cached input tokens, 4,166 output tokens,
  806 reasoning tokens, and 140.492 s aggregate latency. G used checked-template fallback for the
  recovery-mechanism question after its single generated realization failed final-text
  verification; no repair call or resampling was made. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0018-provenance-v1.json`.

## 2026-09-20 — sealed pn-0017 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0017`, seed 3017, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 3.457 m displacement, 246 returned controller commands, 78 costmap
  observations, maximum 13,514 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 466,210 input tokens, 348,928 cached input tokens, 4,476 output tokens,
  661 reasoning tokens, and 138.003 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0017-provenance-v1.json`.

## 2026-09-20 — sealed pn-0016 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0016`, seed 3016, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.030 m displacement, 303 returned controller commands, 63 costmap
  observations, maximum 8,852 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 567,740 input tokens, 392,704 cached input tokens, 4,998 output tokens,
  837 reasoning tokens, and 147.703 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0016-provenance-v1.json`.

## 2026-09-20 — sealed pn-0015 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0015`, seed 3015, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 3.224 m displacement, 237 returned controller commands, 71 costmap
  observations, maximum 13,488 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 496,155 input tokens, 387,328 cached input tokens, 4,486 output tokens,
  814 reasoning tokens, and 129.884 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0015-provenance-v1.json`.

## 2026-09-20 — sealed pn-0014 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0014`, seed 3014, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.000 m displacement, 304 returned controller commands, 62 costmap
  observations, maximum 9,217 occupied cells, and accepted 10/7-unit parity audits. The zero
  displacement is retained as observed, not rerun or filtered. No answer was inspected for scoring
  before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 570,985 input tokens, 449,536 cached input tokens, 4,525 output tokens,
  748 reasoning tokens, and 138.451 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0014-provenance-v1.json`.

## 2026-09-20 — sealed pn-0013 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0013`, seed 3013, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 2.955 m displacement, 222 returned controller commands, 68 costmap
  observations, maximum 13,488 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 442,855 input tokens, 296,448 cached input tokens, 4,369 output tokens,
  772 reasoning tokens, and 149.767 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0013-provenance-v1.json`.

## 2026-09-20 — sealed pn-0012 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0012`, seed 3012, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.000 m displacement, 303 returned controller commands, 61 costmap
  observations, maximum 8,515 occupied cells, and accepted 10/7-unit parity audits. The zero
  displacement is retained as observed, not rerun or filtered. No answer was inspected for scoring
  before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 623,670 input tokens, 459,264 cached input tokens, 4,774 output tokens,
  782 reasoning tokens, and 152.407 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0012-provenance-v1.json`.

## 2026-09-20 — sealed pn-0011 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0011`, seed 3011, passed every
  inclusion gate and the exact expected-success contract. The action succeeded after one unique
  Wait invocation with 2.700 m displacement, 215 returned controller commands, 63 costmap
  observations, maximum 12,600 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 475,480 input tokens, 308,736 cached input tokens, 4,570 output tokens,
  763 reasoning tokens, and 119.714 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0011-provenance-v1.json`.

## 2026-09-20 — sealed pn-0010 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0010`, seed 3010, passed every
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 0.087 m displacement, 303 returned controller commands, 63 costmap
  observations, maximum 8,955 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 556,288 input tokens, 344,064 cached input tokens, 4,768 output tokens,
  831 reasoning tokens, and 141.456 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0010-provenance-v1.json`.

## 2026-09-20 — provider-neutral model-family replication path

- **IMPLEMENTED / TESTED:** added a normalized `crane-explain-model-call/v1` adapter for the Claude
  Code CLI, a sibling F/G/H runner that imports the frozen method logic, an evidence-hash-gated
  batch driver, arm-aware model manifests, and deterministic adapter/freeze-integrity tests. The
  design preserves the frozen primary runner and makes model configuration, provider adapter,
  agent harness, and method condition explicit experimental identities.
- **RETAINED / EXCLUDED:** the first Claude adapter revision appended schema instructions to the
  frozen prompt. It produced 16 development calls, including one unparsable prose response. No
  sealed Claude call or selection existed. Amendment 1 moved schema delivery to the CLI's
  out-of-band `--json-schema` flag; the original calls remain retained but are excluded from every
  summary.
- **TESTED (DEVELOPMENT ONLY):** the predeclared control made 48 corrected calls over four retained
  development episodes (F/G/H × two questions × two settings). Haiku recorded F/G/H errors
  7/0/1 out of eight per condition and specificity 117/156; Sonnet recorded 1/0/0 and 135/156.
  Coverage was 1.0 throughout. Haiku failed the per-condition error margin and was also slower and
  costlier ($2.42, 8.75M input tokens, 1,070 s versus $1.77, 2.08M, 456 s). Amendment 2 fixed
  `claude-sonnet-5` at low effort before any sealed Claude call. Labels are unblinded,
  single-annotator, automated, and configuration-selection evidence only.
- All 16 G control answers were byte-identical to the primary arm because final verification chose
  the deterministic template. The control therefore discriminated settings through F and H, not
  G. Model family and the F/H agent harness are confounded across arms.
- **NOT_RUN:** the selected Claude-family sealed replication over `pn-0001`–`pn-0009`. It has zero
  sealed calls, zero sealed annotations, and contributes zero independent episodes. No
  cross-family effect or cost comparison has been calculated.
- **ANNOTATION ARTIFACT NOTE:** a 54-row historical primary packet is retained, but its separate
  evaluator-only HMAC/condition key is absent from this checkout. It cannot be joined or analyzed;
  regenerate a fresh packet and key as one pair before annotation. No labels exist.
- Retained declarations/results: `manifests/study/provenance-claude-replication-arm-v1*.json`,
  `manifests/model_outputs/claude-arm-model-strength-*-v1.json`, and
  `analysis/results/claude-arm-model-strength-20260920.json`.

## 2026-09-19 — sealed pn-0009 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0009`, seed 3009, passed every
  frozen inclusion gate and the exact expected-success contract. The action succeeded after one
  unique Wait invocation with 3.717 m displacement, 255 returned controller commands, 78 costmap
  observations, maximum 13,886 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected for scoring before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 468,846 input tokens, 346,112 cached input tokens, 4,308 output tokens,
  864 reasoning tokens, and 169.891 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0009-provenance-v1.json`.

## 2026-09-19 — sealed pn-0008 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0008`, seed 3008, passed every frozen
  inclusion gate and the exact expected-abort contract. The action aborted after two unique Wait
  invocations with 314 returned controller commands, 67 costmap observations, maximum 9,709 occupied
  cells, and accepted 10/7-unit parity audits. No answer was inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 480,079 input tokens, 328,960 cached input tokens, 4,044 output tokens,
  688 reasoning tokens, and 168.842 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0008-provenance-v1.json`.

## 2026-09-19 — sealed pn-0007 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0007`, seed 3007, passed every
  frozen inclusion gate. The action succeeded after one unique Wait invocation with 3.457 m
  displacement, 245 returned controller commands, 75 costmap observations, maximum 14,036 occupied
  cells, and accepted 10/7-unit parity audits. No answer was inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 548,088 input tokens, 367,104 cached input tokens, 4,931 output tokens,
  907 reasoning tokens, and 229.510 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0007-provenance-v1.json`.

## 2026-09-19 — sealed pn-0006 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0006`, seed 3006, is the first terminal
  row to pass the exact `CRANE_EXPECTED_NAV_STATUS=aborted` contract directly. The action aborted
  after two unique Wait invocations with 303 returned controller commands, 60 costmap observations,
  maximum 8,515 occupied cells, and accepted 10/7-unit parity audits. Every frozen gate passed and
  no answer was inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 503,436 input tokens, 350,976 cached input tokens, 5,181 output tokens,
  930 reasoning tokens, and 229.919 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0006-provenance-v1.json`.

## 2026-09-19 — sealed pn-0005 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0005`, seed 3005, passed the exact
  expected-status contract and every frozen inclusion gate. The action succeeded after one unique
  Wait invocation with 3.224 m displacement, 236 returned controller commands, 72 costmap
  observations, maximum 13,390 occupied cells, and accepted 10/7-unit parity audits. No answer was
  inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 546,847 input tokens, 412,928 cached input tokens, 5,074 output tokens,
  993 reasoning tokens, and 183.548 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0005-provenance-v1.json`.

## 2026-09-19 — sealed pn-0004 inclusion and exact contract correction

- **CAPTURED ONCE / INCLUDED:** frozen terminal-abort row `pn-0004`, seed 3004, ended
  `aborted` after 33.648 s with 0.222 m displacement, 313 returned controller commands, 65 costmap
  observations, and maximum 9,228 occupied cells.
- **REPEATED OUTER-SUMMARY DEFECT:** amendment 4 used `CRANE_EXPECT_NAV_STATUS`, but the pinned
  fixture reads `CRANE_EXPECTED_NAV_STATUS`. The capture therefore retained `valid=false` against a
  default success expectation even though its terminal result matches the frozen abort family.
- **VALIDITY ACTION:** amendment 5 uses the exact source-read contract and cross-checks it in a
  regression test. `pn-0004` was retained without rerun; zero episode-specific model calls or
  annotations existed. The frozen validator then accepted matching goal/result identity, exact
  runtime/source hashes, two unique Wait invocations and complete recovery history, the predeclared
  abort family, populated costmaps, 10-unit recovery parity, 7-unit cause parity, and leakage scan.
  No answer output was inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 594,977 input tokens, 429,312 cached input tokens, 4,821 output tokens,
  846 reasoning tokens, and 177.068 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0004-provenance-v1.json`.

## 2026-09-19 — sealed pn-0003 inclusion and model calls

- **CAPTURED ONCE / INCLUDED:** frozen recovery-success row `pn-0003`, seed 2003, passed the corrected
  expected-status contract. The action succeeded after exactly one recorded Wait invocation with
  2.965 m displacement, 225 returned controller commands, 67 costmap observations, and maximum
  13,192 occupied cells. Both frozen parity audits passed with 10 recovery and 7 cause units; the
  inclusion validator inspected no answers.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** both questions ran once for F/G/H with Luna-low:
  six calls, no retries, 564,864 input tokens, 416,512 cached input tokens, 4,910 output tokens,
  798 reasoning tokens, and 165.896 s aggregate latency. A–E remain non-model smoke outputs and
  frozen model evaluation is `NOT_RUN`. Hashes and usage are retained in
  `manifests/model_outputs/pn-0003-provenance-v1.json`.

## 2026-09-19 — sealed pn-0002 capture, inclusion, and wrapper-contract amendment

- **CAPTURED ONCE / INCLUDED:** frozen row `pn-0002`, seed 3002, ROS domain 101,
  TurtleBot3 warehouse corridor, 3.25 m goal, and an unreleased mobility hold scheduled after
  14.5 fixed simulation seconds. Nav2 returned `aborted` after 32.597 s with two reported
  recoveries; the fixture retained 303 controller commands, 62 costmap observations, maximum 9,378
  occupied cells, and 0.082 m displacement.
- **ORCHESTRATION DEFECT:** the sealed wrapper exported `CRANE_EXPECT_NAVIGATION_STATUS=aborted`,
  but `run_nav2_controller_fixture.sh` consumes `CRANE_EXPECT_NAV_STATUS`. The outer worker summary
  therefore defaulted to expected `succeeded` and set `valid=false`, even though the captured result
  matches the predeclared terminal-abort family.
- **VALIDITY ACTION:** retained the episode without rerun; zero `pn-0002` model calls or annotations
  existed. Amendment 4 corrects only the future wrapper contract. The frozen validator subsequently
  accepted matching goal/result identity, exact retained runtime/source hashes, two unique Wait
  invocations matching final feedback, complete recovery history, the predeclared abort family,
  populated costmap evidence, 10-unit recovery parity, 7-unit cause parity, and robot-visible
  leakage scanning. No answer output was inspected before inclusion.
- **SEALED MODEL CALLS RETAINED / NOT ANNOTATED:** after inclusion, both frozen questions ran once
  for F/G/H with `gpt-5.6-luna` at low reasoning: six physical calls, no retries, 441,057 input
  tokens, 304,640 cached input tokens, 4,538 output tokens, 741 reasoning tokens, and 154.163 s
  aggregate latency. A–E entries in the result envelopes remain deterministic smoke outputs and
  are explicitly `NOT_RUN` as frozen model conditions. The hash-checked model manifest is
  `manifests/model_outputs/pn-0002-provenance-v1.json`.

## 2026-09-19 — fair-configuration provenance re-pilot predeclaration

- **PREDECLARED/NOT_RUN:** e043 is one development-only recovery diagnostic using the calibrated
  runtime manifest. It exposes the exact Nav2 parameter identity equally to F/G/H while keeping the
  mobility intervention evaluator-only.
- Fixed before execution: seed/configuration, two questions, F/G/H, `gpt-5.6-luna` low, one call,
  no retry, existing material-error and 13-unit specificity rubric, and retention regardless of
  outcome. If recovery does not activate, e043 is retained and not rerun.
- Purpose: determine whether F/H still turn configured progress-checker semantics into an observed
  or physical cause once the parameter file is fairly available. This diagnostic cannot lower the
  15-point smallest practical effect or the 40/50/60 episode collection targets.
- **TESTED/DEVELOPMENT ONLY:** e043 activated one FollowPath failure → recovery guard success → Wait
  invocation, then the goal succeeded. Both ten-unit recovery and seven-unit physical-cause parity
  audits passed. Six Luna calls were made once with no retries.
- Unblinded annotation: F/G/H material errors were 1/0/0 over two questions; specificity was
  11/10/12 of 13 and coverage was full for all. F validly identified the now-sealed YAML but still
  promoted timing plus configured progress checking into a controller-progress diagnosis without a
  controller error payload. H matched G's error rate and remained more specific. This preserves a
  plausible F–G distinction but does not establish an effect size or G superiority over H.

## 2026-09-19 — runtime-configuration provenance integration

- **IMPLEMENTED:** `build_runtime_manifest.py` resolves the ROS image digest, installed Nav2 package
  versions, exact BT/parameter/harness hashes and Git objects, umbrella/astro/CRANE checkout
  identities, player/build/assembly hashes, and effective scene/command/LiDAR launch settings. It
  excludes intervention identity/timing, expected outcome, and evaluator truth.
- `run_land_capture.sh` builds the manifest before launch, mounts it read-only into the passive ROS
  capture, and requests byte-for-byte retention through the existing `--runtime-manifest` seam.
- The shared F/G/H presentation verifies the retained manifest hash/run identity, exposes it to G/H,
  copies it into F's raw workspace, and adds a question-level configuration-identity parity unit.
  Legacy captures without a runtime manifest remain valid development artifacts.
- Prototype against the actual local image resolved digest `sha256:9c286b78...50053`, Nav2 package
  versions 1.3.12, parameter SHA `3851544a...cf0c3`, and BT SHA `14939b78...f48520`; all four source
  artifacts are byte-identical to the pinned `crane_ml` Git object. The player source commit remains
  unproven, as recorded.
- **INVALID/PRE-EXECUTION:** predeclared e041 stopped before Docker capture or Unity launch because
  `argparse` rejected the dash-prefixed command-interface value when passed as a separate token.
  Only evaluator-only `build-provenance.json` was created; no navigation outcome exists. The run is
  retained and must not be rerun or counted.
- **TESTED/PASS:** the distinct predeclared e042 calibration ran once. Navigation succeeded (one
  goal, 1.469 m displacement, 59 controller commands, 343 odometry messages, 21 costmap
  observations, and 10,972 maximum occupied cells), but outcome was not a pass criterion. The
  deterministic calibration validator accepted the exact retained manifest SHA-256
  `375eddca...85bc`, matching run/episode identities, six byte-identical Git artifacts, populated
  image/ROS/player identities, absence of evaluator-only keys, and a seven-unit F/G/H parity audit.
- Status: **IMPLEMENTED/TESTED.** Runtime-configuration capture is eligible for study freeze; the
  player binary's source commit remains explicitly unproven.

## 2026-09-19 — predeclared provenance model-strength control

- Config committed before calls:
  `research/explanation_fidelity/experiment_configs/development/provenance-model-strength-20260919-v1.json`.
- Fixed inputs: e019/e021/e037/e038, recovery-mechanism and physical-cause questions, F/G/H,
  current prompts, one sample, no retry, low reasoning, and the same parity audits.
- Comparison: retained `gpt-5.6-sol` outputs versus new `gpt-5.6-luna` outputs. Eligibility allows at
  most one additional error per condition, at most a 10-point aggregate specificity loss, at most
  one additional source/causal overclaim, and at least 0.875 substantive coverage per condition.
- Executed 24 Luna calls across the fixed four episodes, two questions, and F/G/H. All calls passed
  parity gates, used one sample with no retries, and have unique retained cache keys.
- Unblinded annotation: Luna F/G/H material errors 3/0/1 versus Sol 4/0/0; specificity Luna
  49/40/51 and Sol 48/40/52 out of 52 per condition; every condition has 8/8 substantive coverage.
  Luna's H error calls an unproven progress-checker diagnosis; its F baseline makes one fewer such
  error than Sol. Total source/causal overclaims are equal across settings.
- Resource evidence over 24 matched logical calls: Luna versus Sol input tokens 2,253,937 versus
  2,467,391; output tokens 18,484 versus 23,252; aggregate latency 625.923 versus 891.518 seconds.
  Monetary cost was not reported.
- Selection: **`gpt-5.6-luna`, low reasoning**. It meets every committed margin and is the lower
  model tier. This selects a configuration; it does not establish equivalence.
- Retained artifacts: `manifests/model_outputs/land-nav-provenance-model-strength-luna-v1.json`,
  annotation `land-nav-provenance-model-strength-luna-v1.json`, and reproducible result
  `analysis/results/provenance-model-strength-20260919.json`.

## 2026-09-19 — four-episode parity-controlled F/G/H development pilot

- Episodes: e019/e021 recovery followed by success (one recorded Wait invocation each), and
  e037/e038 repeated recovery followed by terminal abort (two recorded Wait invocations each).
  Captures were reused without simulator reruns. Every retained BT XML is byte-identical to the
  pinned `crane_ml` object at `c559932a...`.
- All eight question-specific pre-call parity audits passed: nine units for each recovery-mechanism
  question and six for each evidence-limited physical-cause question. The three new episodes add 18
  model calls (F/G/H × two questions × three episodes), each single-sample with no retry.
- New-call usage: 1,851,759 input, 1,461,376 cached-input, 17,045 output, and 2,496 reasoning tokens;
  aggregate latency 691.670 s; provider cost not reported. Concurrent execution changed wall time,
  not condition inputs or sample count.
- Development-only unblinded annotation across all four episodes: F 4/8 material errors, G 0/8,
  H 0/8. All F errors treat the repository parameter YAML as the running configuration or relate its
  10-second SimpleProgressChecker setting to the observed failure without a retained runtime link.
  G/H correctly withhold those attributions. Substantive coverage is 8/8 for every condition.
- Specificity: F 48/52, G 40/52, H 52/52. H therefore matches G's pilot error rate while exposing
  more answerable detail. This is negative evidence against claiming G dominates a strong structured
  repository agent; G's current advantage is deterministic auditability/fallback, not demonstrated
  H-relative response accuracy.
- F-versus-G response risk difference is −0.50. The 20,000-draw episode-cluster bootstrap percentile
  interval is [−0.875, −0.125], but it is highly discrete at four clusters; secondary response-level
  exact McNemar p=0.125 (four F-only discordances). H-versus-G error difference is 0.
- A provisional 15-point minimum practical F-to-G reduction gives simulated power 0.802/0.884/0.936
  at 40/50/60 episodes under two questions, ICC 0.15, and paired latent correlation 0.50. Use 50 as
  the planning target, 40 as the minimum, and do not use the observed 50-point difference to shrink
  collection.
- Existing A–E outputs embedded in the new result files are excluded from this summary because some
  predate the fix preserving intermediate failures after later task success. The pilot analysis is
  explicitly F/G/H only.
- Retained artifacts: per-episode data manifests for e019/e021/e038, model manifest
  `manifests/model_outputs/land-nav-provenance-multiepisode-v1.json`, annotation
  `research/explanation_fidelity/annotations/development/land-nav-provenance-multiepisode-v1.json`,
  and reproducible summary/power JSON under `analysis/results/`.
- Next validity task: run the predeclared model-strength control on this exact four-episode input,
  then freeze the F/G primary comparison, question-unit rubric, prompts, and collection target before
  scaling provenance calls.

## 2026-09-19 — information-parity-controlled provenance pilot v2

- Episode: retained `land-nav-20260919-e037-worker-0`; no simulator rerun and no evaluator-only
  artifact entered a method workspace.
- Implementation: added a deterministic runtime presentation with exact accepted goal/result,
  3,236-message feedback summary, all 39 BT transitions with stable/raw identities, two ordered
  recovery entries, exact BT XML hash, limitations, and separate whole-execution versus recovery
  count completeness. The checked-plan episode must validate as a projection of this presentation.
- Pre-call audits: recovery-mechanism accepted 9/9 required information units; physical-cause
  accepted 6/6. F receives raw capture files; G/H receive the same structured presentation. G-only
  provenance links, bounded spans, checked planning, and final verification are explicitly excluded
  from shared-runtime parity.
- Calls: `gpt-5.6-sol`, low reasoning, one sample, no repair/resampling. The unchanged F requests
  reused their exact v1 cache records. Four genuinely changed H/G requests produced new retained
  records: 349,042 input, 283,648 cached-input, 3,062 output, and 453 reasoning tokens; aggregate
  latency 113.832 s; provider cost not reported.
- Development-only unblinded annotation: recovery F retains one material error by treating an
  unsealed parameter YAML and its 10-second progress window as governing this run. G has no material
  error and now exposes both exact recovery sequences, attempt IDs/timestamps, BT path, commit, and
  artifact hash. H no longer claims an unobserved error code and is scored without a material error;
  its repository-YAML details are not credited as runtime-governing facts. All methods correctly
  withhold physical-obstacle causality on the evidence-limited question.
- Across the two questions: response-level material errors are F 1/2, G 0/2, H 0/2; specificity is
  F 12/13, G 10/13, H 13/13. A–E are unchanged controls. One episode is diagnostic only, not an
  effect estimate.
- Retained manifests:
  `manifests/data/land-nav-20260919-e037.provenance-parity-v2.robot-visible.json` and
  `manifests/model_outputs/land-nav-e037-provenance-pilot-v2.json`.
- Remaining validity threat: a single episode cannot estimate F/G/H discordance; the next step is a
  small, family-balanced multi-episode development pilot. Runtime manifests still do not seal the
  running parameter-file/image/package identity, so parameter-level mechanism claims remain
  intentionally unsupported.

## 2026-09-19 — first provenance-linked A–H development pilot

- Episode: retained `land-nav-20260919-e037-worker-0`; no simulator rerun. Robot-visible input is
  the original passive capture. Evaluator-only truth remained outside both agent workspaces.
- Provenance audit: captured `behavior_tree.xml`, capture-manifest hash, current file, and exact
  `crane_ml` Git object at `c559932a5ebef00bfa7752511799fd904e5c9dbe` are byte-identical
  (`14939b78...`). The bounded anchor is the smallest `NavigateRecovery` subtree containing the
  observed `FollowPath`, `WouldAControllerRecoveryHelp`, and `Wait` nodes.
- Implementation: added typed source artifacts/anchors/runtime links, bounded validation/resolution,
  claim classes, A–H routing, BT provenance construction, runtime-manifest retention for future ROS
  captures, and checked mechanism promotion only under full strong link coverage.
- Questions: one evidence-rich recovery-mechanism question and one evidence-limited physical-cause
  question. A–E reuse the retained single-sample e037 outputs; F/G/H use `gpt-5.6-sol`, low effort,
  one call per condition/question, no repair/resampling. F/H had isolated exact-repository
  workspaces with only allowed robot-visible evidence. G had the bounded source context and plan.
- New model calls: 6; input/cached/output/reasoning tokens 477,964 / 361,216 / 5,237 / 918;
  aggregate latency 160.147 s; provider did not report monetary cost.
- Development-only annotation: F and H each made one material error on the evidence-rich question;
  G made none and fell back after strict verification rejected both free paraphrases. F treated an
  unsealed parameter YAML as the running configuration. H additionally described the unobserved
  bound error-code semantics as established. All conditions correctly withheld physical-obstacle
  causality on the evidence-limited question.
- Evidence specificity across 13 question-specific units: A 10, B/C/D/E 8 each, F 12, G 10, H 11.
  This shows the intended risk–specificity tension but is not an effect estimate.
- Retained manifests:
  `manifests/data/land-nav-20260919-e037.provenance-pilot-v1.robot-visible.json` and
  `manifests/model_outputs/land-nav-e037-provenance-pilot-v1.json`.
- Provenance gaps: e037 did not seal the Nav2 image digest, installed package inventory, parameter
  file identity, launch argv/environment, or a rebuild-verified source-to-binary mapping. The
  whole-BT log remains incomplete under audited Jazzy/Nav2 logger semantics. Physical cause and
  precise consumed sensor inputs remain unproven.
- Validity threat: F raw logs contain more low-level observations than the current G/H structured
  record. Before a multi-episode pilot, freeze an information-unit audit for F/G/H and ensure G's
  structured view retains every answer-relevant robot-visible fact available to F.
- Next action: strengthen the structured pilot record and runtime manifest, then run a small
  parity-audited multi-episode F/G/H development set before resuming large episode collection.

## 2026-09-19 — predeclared balanced batch e028–e031

- Configuration was committed and pushed before execution as
  `research/explanation_fidelity/experiment_configs/development/land-nav-balanced-batch-20260919-v2.json`.
  Four isolated ROS domains/ports ran concurrently against the same pinned player artifact.
- **TESTED/PASS INCLUDED:** e028 TurtleBot3 succeeded in 10.130 s, displaced 2.222 m, recorded zero
  recoveries and 33 costmap observations, and ran at RTF 1.000027. E031 reached its 9.028 s client
  deadline, captured cancellation and terminal canceled status, recorded zero recoveries and 24
  costmap observations, and ran at RTF 1.000007.
- **TESTED/RETAINED EXCLUDED:** e029/e030 each had healthy transport, LiDAR, costmap, and timing
  metrics, but both reached the 35.03 s client deadline instead of the predeclared terminal abort.
  They are not rerun, relabeled, or replaced. This is negative evidence against static partial
  blockers as a reliable terminal-exhaustion generator.
- All 12 e028/e031 parity audits pass. Sixty new A/B/C/D/E outputs were generated with sequential
  within-episode cache use and no retries. E028-A repeats the unsupported obstacle-premise claim;
  e031-A repeats unsupported deadline causality. B/C/D/E add no new error.
- Thirteen-episode totals are 79 responses per condition (395 total): A 6/79 material errors, B
  0/79, C/D/E 1/79 each. A/B substantive coverage is 66/79 and information coverage 163/175;
  C/D/E are 65/79 and 155/175. These are unblinded development descriptors only.
- The cumulative artifact audit covers 171 unique request keys and 181 referenced physical cache
  artifacts. All four runs have separate robot-visible/evaluator-only checkpoints; raw data and
  model artifacts remain excluded from Git.

## 2026-09-19 — predeclared balanced batch e024–e027 and eleven-episode audit

- The four scenario instances were committed before execution in
  `research/explanation_fidelity/experiment_configs/development/land-nav-balanced-batch-20260919-v1.json`.
  E024/e027 are included; e025/e026 are retained and excluded without rerun, tuning, or relabeling.
- **TESTED/PASS INCLUDED:** e024 was a TurtleBot3 unblocked success in 7.883 s with 1.729 m
  displacement, zero recoveries, 25 costmap observations, and RTF 1.000023. E027 was an Ackermann
  client-deadline/cancellation instance: fixture timeout 8.033 s, captured terminal action status
  canceled, explicit deadline and cancel events, 0.450 m displacement, zero recoveries, 23 costmap
  observations, and RTF 1.000037.
- **TESTED/RETAINED EXCLUDED:** e025 reached its 35.029 s client deadline instead of the predeclared
  terminal recovery-exhaustion abort. E026 aborted after 0.412 s with the expected planning family,
  but zero costmap observations made its navigation-reset quality report invalid.
- All 12 parity audits pass. The 12 question instances produced 60 A/B/C/D/E responses with one
  sample per model-mediated request and no quality-based retries. E024-A repeats the unsupported
  obstacle-premise classification; e027-A repeats an unsupported deadline→cancellation causal
  relationship. B/C/D/E add no new error in this batch.
- Eleven-episode development totals are 67 responses per condition (335 total): A 4/67 material
  errors, B 0/67, C/D/E 1/67 each. A/B substantive coverage is 56/67 and information coverage
  141/151; C/D/E are 55/67 and 133/151. These remain unblinded descriptive results.
- The cumulative artifact audit passes with 159 unique request keys, 169 referenced physical cache
  artifacts, and exact usage retained in
  `manifests/model_outputs/land-nav-development-eleven-episode-gpt-5.6-sol.json`. Ten request keys
  have multiple referenced physical artifacts due to concurrent cache materialization; all are
  retained, including six keys whose sampled final text differs. No artifact was selected by quality.
- Robot-visible/evaluator-only manifests and run checkpoints were created for all four runs. Raw
  captures and model outputs remain outside Git. Current sample size is 11 included independent
  episodes versus the provisional 60 target and 50 minimum.

## 2026-09-19 — predeclared recovery-success batch e020–e023

- Configuration was recorded locally before execution in
  `research/explanation_fidelity/experiment_configs/development/land-nav-recovery-success-batch-20260919-v1.json`;
  it was not yet committed to Git, which is an audit limitation. CRANE revision `2581497`,
  explanation ROS revision `9ab4f32`, Unity 6000.5.10f1, ROS 2 Jazzy.
- **TESTED/RETAINED EXCLUDED:** e020 succeeded in 19.495 s with zero recovery attempts despite its
  evaluator-only hold from 14.040–26.040 s. It violates the predeclared minimum-recovery outcome,
  is not relabeled, and does not increase the explanation-evaluation sample.
- **TESTED/PASS INCLUDED:** e021, e022, and e023 used distinct seeds, corridor widths, goal
  distances, and hold/release times. Each captured exactly one accepted goal and matching successful
  result, one FollowPath failure, one successful recovery guard, one unique successful Wait, complete
  recovery-count history, and incomplete whole-BT transition history. Their action durations were
  25.342/22.694/25.502 s and measured RTFs were 1.000019/1.000018/1.000017. Evaluator-only hold and
  release events occurred as configured; their identity/timing never entered model-visible evidence.
- All 18 information-parity audits pass. The 18 question instances produced 90 A/B/C/D/E responses
  with one cached sample per model-mediated call and no retries. Internal annotation found no new
  material error: all conditions preserve terminal success, the intermediate FollowPath failure,
  exact one-attempt recovery count, and unknown physical/counterfactual cause.
- Development totals are nine independent configured episodes, 55 responses per condition and 275
  total responses. Material errors remain A 2/55, B 0/55, and C/D/E 1/55 each. Substantive coverage
  is A/B 46/55 and C/D/E 45/55; answerable-information coverage is A/B 119/127 and C/D/E 111/127.
  These are unblinded development descriptors, not inferential results.
- The cumulative artifact audit resolves 275 logical outputs to 127 unique request keys and 129
  physical cache artifacts. Two request keys were independently materialized in both cache roots;
  their final texts match but latency metadata differs. Manifest v2 retains both instead of silently
  selecting one. `analysis/audit_model_artifact_manifest.py` recomputes the inventory and passes.
- Raw capture/model artifacts remain outside Git. Separate robot-visible/evaluator-only manifests
  and run checkpoints were committed for e020–e023; the batch annotation and nine-episode aggregate
  are under `research/explanation_fidelity/annotations/development/`.
- **VALIDITY THREAT:** four of nine included episodes now exercise the same mobility-hold recovery
  mechanism. The next collection batch should prioritize mechanism/family balance—terminal recovery
  exhaustion, unblocked success, planning failure, and client cancellation—over more timing variants.

## 2026-09-19 — first capture-complete recovery followed by success

- CRANE revisions `9a24503` (mobility hold) and `2581497` (harness QoS); explanation ROS revision
  `9ab4f32`; core revision `576fb64`; Unity 6000.5.10f1; ROS 2 Jazzy.
- **IMPLEMENTED/TESTED:** a fixed-simulation-time mobility hold temporarily freezes only planar
  rigid-body translation and yaw, then restores the original constraints. Scheduled/actual hold and
  release times remain evaluator-only. The nine-scene Linux worker built successfully headlessly;
  13 land contracts and four ROS tests pass in their proper runtimes.
- **TESTED/EXCLUDED:** e018 succeeded after one Wait recovery, but the volatile harness channel
  lost its accepted-goal record during DDS discovery. It is an instrumentation failure and is not
  an independent episode.
- **TESTED/PASS INCLUDED:** predeclared e019 repeated e018's seed/configuration after reliable
  transient-local QoS was frozen. It captured exactly one accepted goal and matching successful
  result, complete bounds, final recovery count one, one unique successful Wait, two planning
  starts/successes, and the ordered FollowPath FAILURE → recovery guard SUCCESS → Wait sequence.
  Evaluator truth records hold at 15.040 s and release at 27.040 s. NavigateToPose succeeded in
  22.286 s with 2.472 m displacement, RTF 1.00001, 301 LiDAR scans, populated costmaps, and no
  rejected, stale, cross-episode, or failed observations.
- Six parity-controlled question families produced 30 A/B/C/D/E outputs (24 model-mediated), with
  19 new unique cached calls and no retries. All six A/B information-parity audits pass.
- **NEGATIVE DEVELOPMENT RESULT:** on physical-failure attribution, A/B preserved the intermediate
  FollowPath failure and withheld physical cause. C/D/E incorrectly claimed the failure premise was
  contradicted by later task success. Each receives one material scope/false-premise error; outputs
  are retained unchanged. The corrected core now preserves intermediate failures; 25 tests pass.
- Development totals are now six episode clusters and 37 responses per condition: A 2/37 material
  errors, B 0/37, C/D/E 1/37 each. Substantive coverage is A/B 31/37 and C/D/E 30/37; answerable-
  information coverage is A/B 77/82 and C/D/E 72/82. These unblinded descriptive results remain
  inadequate for empirical cluster-variance estimation or inference.
- **DEVELOPMENT POWER SENSITIVITY:** a reproducible paired episode-cluster simulation pre-specifies
  a practically meaningful A 8% → D 3% material-error reduction. Under six questions/episode,
  ICC 0.10, paired latent correlation 0.50, and 1,000 simulations, estimated planning power is
  0.771/0.863/0.922 at 40/50/60 independent episodes. The provisional target is 60, minimum 50;
  this normal-interval planning model does not replace the frozen clustered-bootstrap analysis.
  Sensitivity at the sparse unblinded 2/37 versus 1/37 rates remains only 0.772 at 100 episodes.

## 2026-09-19 — differential corridor qualification and Ackermann calibration stop

- CRANE revision `6a2d22c2bc55b582f60c362ec2d4310626152051`; Unity 6000.5.10f1; ROS 2
  Jazzy image `lunarzdev/astro:cuda`. Unity licensing recovered after removing more than 9 GB of
  explicitly identified, reproducible `/tmp` build products; governed workspace data was not
  removed. The nine-scene Linux worker then built successfully in batch mode.
- **TESTED/PASS:** predeclared calibration-only e015 ran the existing TurtleBot3 Waffle-class
  differential base in the controlled 4 m corridor, entirely with `-nographics`. It reached the
  2 m goal in 6.126 s with terminal `succeeded`, zero feedback recoveries, 59 controller commands,
  297 odometry messages, 176 LiDAR scans, and 22 costmap observations (maximum 11,467 occupied
  cells). Displacement was 1.469 m, consistent with the configured 0.55 m goal tolerance. RTF was
  1.00003; no stale, rejected, cross-episode, or failed observations were reported.
- **TESTED/PASS:** passive capture brackets one accepted goal and its successful result with the
  exact BT XML and a final monotonic recovery count of zero. Evaluator-only truth separately
  records platform `turtlebot3-waffle-differential`, no blocker, seed 1015, and canonical corridor
  geometry. e015 remains calibration-only and does not increase the five-episode primary sample.
- **TESTED/NEGATIVE, EXCLUDED:** predeclared e016 placed a partial blocker at 1.5 m and removed it
  at simulation time 29.040 s (29.020 s scheduled). The action timed out at 45.026 s with 1.053 m
  net displacement, 0 recoveries, and explicit client deadline/cancellation. Capture was bounded;
  ComputePathToPose returned SUCCESS and FollowPath started, but no terminal FollowPath transition,
  recovery guard, or Wait entry was recorded. The worker's `valid=false` is solely the frozen
  expected-success mismatch; transport, costmap, sensor, and action-lag gates passed. This run does
  not support recovery-success and will not be relabeled.
- **IMPLEMENTED/TESTED, NEGATIVE:** CRANE revision
  `1811b3ca5622eb9e6a642c8a3493077fef94ee69` adds a deterministic blocker window with separate
  scheduled/actual activation and removal times in evaluator-only truth. Predeclared e017 activated
  a full-width blocker at simulation time 15.040 s and removed it at 17.040 s. Both interventions
  occurred, but FollowPath remained active with zero recovery entries until the 45.025 s client
  deadline; net displacement was 1.258 m. The result is excluded expected-outcome mismatch, not
  recovery-success evidence. No further obstacle-timing tuning is justified without first changing
  or independently diagnosing the controller/plant behavior.
- **TESTED/NEGATIVE:** e011–e014 showed that the longer-goal Ackermann corridor repeatedly drifts
  or stalls: e011's timed blocker was removed but the run timed out after two successful Wait
  recoveries; e012/e013 timed out after 3.41/3.97 m displacement; e014 still timed out after raising
  minimum approach velocity and exhibited 1.08 m lateral drift. These retained runs do not support
  a simple low-speed actuation-floor explanation.
- Decision: stop tuning deadlines or approach speed to force Ackermann success. Use the validated
  differential platform for controlled recovery collection while retaining Ackermann/F1TENTH as
  an embodiment-specific deterministic benchmark. The five-episode figures at this checkpoint are
  superseded by the six-episode recovery-success results above.

## 2026-09-19 — timed land-blocker intervention implementation

- CRANE base commit `5b5073c615c2e10a85e99d81d41365b61b1d6cd5`; Unity target 6000.5.10f1.
- **IMPLEMENTED:** `--crane-land-blocker-remove-after SECONDS` deactivates the existing canonical
  blocker at a fixed-simulation-time boundary. Stable semantic IDs were added to both corridor
  walls and the blocker. Configured/scheduled/actual timing, geometry, removal state, and semantic
  ID remain in evaluator-only truth; no fault label was added to robot-visible capture.
- **TESTED/PASS:** 10 land-launch/bootstrap static contracts, five F1TENTH converter tests, the SDF
  converter suite, 24 core explanation tests, `git diff --check`, and a single-process C# build of
  `PhysicsAssembly.csproj` after including the new source in Unity's generated project file.
- **SUPERSEDED BLOCKER:** the authoritative Unity player build repeatedly lost the Unity Licensing Client,
  reported `com.unity.editor.headless` unavailable, and was stopped cleanly with exit 130 after no
  valid build verdict. No runtime/Nav2 recovery-success claim is made and no e011 episode was
  collected.
- The Clearpath offline-import documentation now uses `unity run ... -- -nographics`; `unity run`
  already owns batch/quit flags. This avoids the unnecessary visible window that had looked like
  an unmoving simulation. Offline scene construction is explicitly not a robot-motion test.
- At that checkpoint the next task was to restore licensing and run e011. Licensing later recovered,
  e011 was retained as a failed calibration, and e015 subsequently qualified the differential path
  as documented above.

## 2026-09-19 — Clearpath pipeline offline Unity import

- CRANE commit `2501359964716cecfc378428d6cc77da829ef373`; Unity 6000.5.10f1; Clearpath
  simulator 2.9.4 commit `ee098ad6f67b4e35d77841ed6f004b8f86cd77e4`.
- **TESTED/PASS:** converter resolved three SDF models and nine local `model://` assets/dependencies,
  hashed each source, retained collision/visual roles, preserved DAE hierarchy, and converted the
  unsupported base-station STL deterministically to OBJ. Generated assets (34 MB) remained ignored.
- **TESTED/PASS:** editor tooling generated and loaded `Clearpath Pipeline Validation` with a
  Jackal-dimension/class differential body and 2-D LiDAR configuration. Runtime validation found
  11 collision meshes, 13 visual renderers, no canonical renderers or visual colliders, and bounds
  `[-63.294,-3.719,-46.560]` to `[135.956,7.616,82.309]` m.
- **TESTED/PASS:** physics ray query hit semantic object `clearpath-pipeline`; an actual collision
  callback was observed for the rigid-body drop. The standard nine-scene worker rebuilt afterward
  with zero generated-asset dependencies, preserving the optimized normal build path.
- Negative iteration: the first drop verdict was **TESTED/INVALID** because it required final
  speed below 1 m/s and therefore mislabeled a real contact that continued rolling on sloped
  terrain. The final predeclared check uses an actual collision callback plus a fall-through bound;
  geometry/layer/raycast criteria were not weakened.
- **NOT_RUN:** Blender/FBX conversion (Blender unavailable), native Gazebo comparison, ROS sensor
  transport, Nav2 traversal, spawn/goal calibration, corridor-width checks, and high-fidelity
  material parity. Two expected ROS-TCP connection failures are not sensor verdicts.
- Explanation-evaluation sample remains 0; this is infrastructure evidence, not RQ1–RQ4 outcome
  evidence. Raw builds/results remain ephemeral under `/tmp`.

## 2026-09-19 — PX4 ArUco and windy reference environments

- CRANE commit `a0acabec5005da6ae9dbc286d740e3ea20982014`; Unity 6000.5.10f1; upstream
  `PX4/PX4-gazebo-models` commit `bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9`.
- **TESTED/PASS:** ArUco scene retained one 0.5 m semantic/render landmark with no collider. A
  downward query passed through the tag and hit canonical `ground-plane` at 2.0 m. Normal aerial
  dynamics and landing checks passed. Camera-based tag recognition is **NOT_RUN**.
- **TESTED/PASS:** windy scene applied source ENU `(5,2,0)` m/s as Unity `(5,0,2)` m/s through
  CRANE air-relative drag. Two headless runs were byte-identical and measured positive x/z
  displacement `(3.267,4.732)` m. The non-proportional component response is a retained model-
  calibration limitation; this is directional/determinism evidence, not Gazebo equivalence.
- **TESTED/PASS:** post-change regressions for base aerial, PX4 walls, and PX4 ArUco scenes.
- ROS-TCP was unavailable in these isolated runs; sensor transport/navigation remain **NOT_RUN**.
  Explanation-evaluation sample remains 0.

## 2026-09-19 — PX4 walls reference environment

- CRANE commit `97229e8b0300ce31e429c9ad9ac4599a8e79e488`; Unity 6000.5.10f1.
- Source: `PX4/PX4-gazebo-models` commit
  `bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9`, `worlds/walls.sdf`, SHA-256
  `aad581c1a9c78ef81354401d89285f2dbd27462f1054137f3e0572cecd9d38a9`.
- **TESTED/PASS:** Linux worker build completed headlessly. `PX4 Walls Validation` loaded with four
  exact source-derived box transforms and semantic IDs; a physics ray resolved `wall-box-01` at
  4.5 m; the x500-class CRANE rigid body was stopped/rebounded by its authoritative collider.
- **TESTED/PASS:** hover, vertical acceleration, roll/pitch/yaw response, CRANE wind response,
  landing, and command saturation all retained valid verdicts. The final worker used
  `-batchmode -nographics`; no graphical window was launched.
- **NOT_RUN:** PX4 SITL, Gazebo-equivalent dynamics, ROS sensor transport, navigation, ArUco
  perception, and the pinned upstream `windy.sdf` scenario. A failed ROS-TCP connection in this
  isolated run is expected and is not counted as sensor validation.
- Raw result/build logs remain ephemeral under `/tmp`; no raw runtime output was committed.
  Explanation-evaluation sample remains 0, so this adds environment coverage but no RQ1–RQ4
  effect estimate.

## 2026-09-19 — recovery clock diagnosis and TurtleBot3 reference environment

- CRANE base `cc0818e606a5640c788afe84112a15049878718c` plus this checkpoint; Unity
  6000.5.10f1; ROS 2 Jazzy image `lunarzdev/astro:cuda`.
- **TESTED:** `Land Vehicle Validation` lacked `/clock` while Nav2 used simulated time. Adding a
  clock and selecting the retained `nav2_land_progress_recovery.xml` produced controller-progress
  exhaustion and a `NavigateToPose` `aborted` result in 9.50 s. This is software recovery evidence,
  not proof that the physical blocker caused failure.
- **TESTED:** generated a TurtleBot3 Waffle-class warehouse with CRANE primitive canonical
  colliders, separate non-colliding visuals, and stable semantic IDs. A graphics-free smoke ran at
  RTF 1.0003 without logged errors/exceptions.
- **TESTED:** the TurtleBot3 2 m Nav2 smoke succeeded in 6.08 s, displaced 1.469 m, captured 136
  LiDAR scans and 22 costmap observations with up to 7,198 occupied cells, at RTF 1.00007.
- Negative iterations were preserved: an underpowered chassis could not overcome static friction;
  an over-gained force controller was unstable. The validated bounded-impulse model has a
  zero-friction chassis contact and non-holonomic lateral correction. It is not a detailed wheel
  contact reproduction.
- **IMPLEMENTED/TESTED:** F1TENTH PNG/YAML converter and synthetic regression; no GPL map imported.
- Independent explanation-evaluation sample remains 0; no material-error effect estimate exists.

## 2026-09-19 — initial implementation checkpoint

- Git state: two new, initially empty target repositories; CRANE
  `3fefd98904abc83842593be79be8eae133b3bb65`; astro_dock
  `36202373ae186a8fd247a20b7b477312a744de99`.
- Runtime: host Python 3.14; local Docker image `lunarzdev/astro:cuda`, image ID prefix
  `sha256:9c286b78dc`; ROS packages `nav2_msgs`/`nav2_bt_navigator` 1.3.12.
- Command: `python -m pytest -q`.
- Result: 14 passed; Dock/Slalom missing-policy, explicit-policy, recovery de-duplication,
  completeness qualification, outcome isolation, alternative status, final-clause rejection.
- Benchmark harness tests cover A/B shared generator/question, information-parity rejection,
  C extraction into checked reasoning, D no-resampling fallback, and deterministic E.
- Interface probe: inspected installed message/action definitions and `ros_topic_logger.hpp` in the
  container. Passive fields confirmed. This was not a live publication test.
- Data collected: 0 independent robot episodes; 0 benchmark responses; 0 exclusions.
- Model/provider/prompt: none; CPU-only deterministic test.
- Observation: existing CRANE fixture correctly labels odometry as delivered rather than proven
  internally consumed, but its `goalAttempts` is action-server startup/goal submission—not recovery.
- ROS package: isolated Jazzy container `colcon build` **TESTED**; writer test 1 passed. Live Nav2
  publication/capture and CRANE pilot remain **NOT_RUN**.

## 2026-09-19 — CRANE/Nav2 baseline reproduction and cold-start diagnosis

- Build command: `unity build "$WORKSPACE_ROOT/packages/crane_ml" --editor-version 6000.5.10f1
  --target StandaloneLinux64 --execute-method CranePerformanceBuild.BuildLinuxWorker
  --allow-dirty-build`.
- Build result: **TESTED/PASS**; `CRANE_BUILD_COMPLETE`, Linux worker 551,473,945 bytes;
  build manifest asset-set SHA-256
  `B12ED54E542E2B34A9C4AE762FE4DB66041731830CB9F384FEDFDEC0BED4A228`.
- Default fixture command used `Tools/Performance/run_nav2_controller_fixture.sh` with outputs at
  `data/robot_visible/dev/baselines/nav2-baseline-20260919/` (ignored, retained locally).
- Default result: **TESTED/INVALID**. Navigation status `timeout`; displacement 0.51986 m;
  `goalAttempts=3`; 65 accepted actions; fresh observations; RTF 1.00012. Controller logs show two
  inactive-server goal rejections, accepted execution at 1789833415.34, and client cancellation at
  1789833423.49. `goalAttempts` is not interpreted as recovery.
- Falsifiable diagnosis: the fixture's 20 s wall deadline included lifecycle/TF startup, leaving
  only about 8.15 s after the accepted goal. Single-variable rerun set
  `CRANE_FIXTURE_DELAY=15`; no code/config/physics changes.
- Delay-15 result: **TESTED/PASS**, `valid=true`; action succeeded in 9.983 s; one goal submission;
  displacement 0.52074 m; 79 accepted, 0 rejected/stale/cross-episode actions; depth 450,
  detections 240, LiDAR 300, 0 failed/stale observations; RTF 1.00053. Artifacts retained at
  `data/robot_visible/dev/baselines/nav2-baseline-delay15-20260919/`.
- Interpretation: the local full Nav2 loop is reproducible after adequate cold-start margin. This
  is one baseline scenario instance, not an explanation benchmark response and not evidence for
  RQ1–RQ4. Current explanation-benchmark sample size remains 0.
- Remaining threat: live `crane_explain_ros` capture has not yet been co-run with the fixture, and
  the default delay can still create invalid cold-start runs. Freeze an explicit startup-readiness
  rule before final collection; do not silently exclude timeouts after inspecting answers.

## 2026-09-19 — umbrella workspace refactor

- Top-level component gitlinks: astro_dock
  `36202373ae186a8fd247a20b7b477312a744de99`; CRANE
  `3fefd98904abc83842593be79be8eae133b3bb65`.
- Nested setup pins: explanation core `e83fd3280f85539f2717ae5bcf9daf7939c770c8`;
  ROS capture `2896024a614f2e0c11daf823a09bbfb6badad5f0`; astro_dock ROS-TCP endpoint
  `3c3d405db665a8c52c28e45f23b8c9782a9564ba` through its own submodule.
- Commands: `scripts/setup_workspace.sh` twice (fresh nested initialization, then idempotence);
  `scripts/check_data_governance.sh`; `python -m pytest -q`; `python -m compileall -q src scripts`.
- Results: **TESTED/PASS**. Exact lock matches all four primary/nested checkouts; governance passes;
  14 core tests pass; shell/Python sources compile.
- Raw payloads: moved locally to ignored `data/robot_visible/dev/baselines/`; none added to Git.
  Separate evaluator-only tree created empty. Two committed robot-visible manifests each inventory
  12 files (917,647 and 908,544 bytes respectively) using SHA-256, paths, sizes, and provenance.
- Data collected: no new episode. Explanation-benchmark sample size remains 0. No effect size.

## 2026-09-19 — live capture pilots p01–p03

- Component revisions after fixes: CRANE `aced6cd75f317873770e79477de136c82c4eafa1`;
  `crane_explain_ros` `3eebaef1ffdbcc1985abe15d90cc2eaa0fd6ed2f`; core
  `e83fd3280f85539f2717ae5bcf9daf7939c770c8`; astro_dock
  `36202373ae186a8fd247a20b7b477312a744de99`.
- Fixed inputs: seed 1000; ROS 2 Jazzy/Nav2 1.3.12 image `lunarzdev/astro:cuda`; ROS domain/port
  isolated per run; fixture delay 15 s; 0.5 m NavigateToPose goal; train-gpu profile; Unity
  6000.5.10f1; config SHA-256 `20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`.
- Exact BT: `navigate_to_pose_w_replanning_and_recovery.xml`, SHA-256
  `5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`.
- p01: **TESTED/EXCLUDED**. Recorder emitted only start/stop because Jazzy `GoalStatusArray` has no
  `header`; callback crashed. Simulator also failed quality (`valid=false`, RTF 0.778) and the
  client deadline canceled navigation. This found the ROS schema defect; it is not a robot failure.
- p02: **TESTED/EXCLUDED**. Schema fix captured 871 records and complete goal/result evidence, and
  navigation succeeded, but per-record `fsync` perturbed throughput (`valid=false`, RTF 0.848).
- p03: **TESTED/INCLUDED DEVELOPMENT PILOT**. Batched durability captured 881 records: 79 BT
  transitions, 794 feedback records, two action-status records, exact BT XML, and four harness
  events (CRANE identity, observation identity, accepted goal, result). Navigation succeeded;
  RTF 1.00055; 79 accepted/0 rejected actions; zero stale or failed observations; zero recoveries.
- A/B/C/D/E smoke: one recovery-count question over p03, using identical fact IDs and a transparent
  rule-based direct generator. All conditions answered `Exactly 0 recovery attempts occurred.`;
  C/D/E final text verified. Status: **PIPELINE_SMOKE_NOT_LLM_EVALUATION**. This yields no effect
  estimate and shows that recovery-free factual questions are too easy for the main comparison.
- Data governance: raw payloads remain ignored. Robot-visible p03 contains capture/action/BT and
  parity-smoke artifacts (9 files, 275,057 bytes); evaluator-only p03 contains simulator validity,
  internal worker logs/results, and performance artifacts (9 files, 893,822 bytes). Both have
  committed SHA-256 manifests. Earlier retained runs were physically separated and remanifested.
- Independent sample size: 1 valid actual episode (surface/CRANE success family); 0 material-error
  evaluation episodes; 0 model-generated responses; 2 excluded live pilots.
- Development effect/power: **NOT_AVAILABLE**. No final-test elements are frozen; H1/metrics remain
  draft pending diverse failure/recovery pilots and actual model outputs.
- Highest-value next step: implement or integrate the required land corridor scenario, then collect
  recovery-success and terminal-failure pilots before power planning.

## 2026-09-19 — pilot-driven terminal explanation support

- Motivation: the first actual-episode smoke exposed that the core supported contrast and recovery
  count only, leaving captured action termination and client events unusable for checked answers.
- Change: core revision `6ad002c4dde67dedb4bd08e8794d0db9dda9259e` adds checked terminal
  status planning and A/B/C/D/E routing. Explicit client deadline and cancellation events remain
  distinct from BT timeout and physical failure; abort status alone cannot license a physical cause;
  success does not imply every intermediate branch succeeded.
- Tests: **TESTED/PASS**, 17 CPU-only tests. No new robot episode or model response was generated.

## 2026-09-19 — graphics-free land/Nav2 vertical slice

- Motivation: the aquatic fixture necessarily opened a Vulkan window to keep HDRP water queries
  valid, and its 0.5 m goal looked stationary. It is unsuitable for high-throughput headless data
  collection; this is not evidence that the aquatic simulation was frozen.
- Implementation: added a dedicated `train-cpu`/`-batchmode`/`-nographics` launcher, runtime
  deterministic corridor and 360-degree LaserScan bootstrap, fixed-step stamped Ackermann command
  adapter, land body support in authoritative odometry/TF, and a LaserScan Nav2 configuration.
- Unity build: **TESTED/PASS** with 6000.5.10f1; Linux worker 551,487,081 bytes; build manifest
  asset-set SHA-256 `81E9250CF6728C0DABC26F81CD56A6BCB47CDAF9A80CD2CC91E7DF3EECD86421`.
- Fixed smoke inputs: seed 1000; no blocker; 4 m corridor width; ROS domain 42; 30 s benchmark;
  3 s warmup; 8 s fixture delay; NavigateToPose; no visual rendering. These are development
  calibration runs, not independent study episodes.
- p01: **TESTED/INVALID**. The 8 m goal hit the explicit 20 s client deadline after moving 4.12 m;
  the harness canceled the action. RTF 1.00003; 301 LiDAR scans; no stale/failed observations.
  This is a client deadline, not a BT timeout or demonstrated navigation failure.
- p02: **TESTED/INVALID**. A 3 m goal ended 0.47 m from the target under the original 0.35 m
  position tolerance and hit the same client deadline. Final heading error was 17.6 degrees,
  within the configured yaw tolerance. No result was relabeled.
- p03: **TESTED/PASS DEVELOPMENT SMOKE** after predeclaring a single 0.55 m position tolerance,
  proportionate to the 1.35 m-wide rover and below its 0.75 m costmap radius. The action succeeded
  in 4.91 s; displacement 2.63 m; 38 accepted and zero rejected/stale actions; 301 LiDAR scans;
  zero failed/stale observations; RTF 1.00003; no Unity window opened.
- Gap observed at that checkpoint: the fixture subscriber saw zero costmap messages despite both
  obstacle layers subscribing to `/scan`; the following diagnosis resolved internal-map validation
  through stock introspection. Ackermann still cannot execute zero-linear-velocity spin commands,
  so recovery design must preserve the embodiment. That smoke itself produced no explanation
  capture or A/B/C/D/E response.

## 2026-09-19 — land costmap diagnosis and first blocker capture

- Validated component revisions: CRANE `cc0818e606a5640c788afe84112a15049878718c`;
  ROS capture `b44dd4c70e442ddcd98fd6ec1dfce9459afde2d9`.
- Diagnosis: **TESTED**. The retained red-capable land gate requires at least one costmap
  observation with occupied cells. Initial probes confirmed 221 LiDAR scans with 66,531 ray hits
  and a live `odom -> lidar_link` transform, while the Nav2 master map remained all zero.
- Root cause 1: Jazzy height filtering is per observation source; omitted
  `scan.max_obstacle_height` defaulted to `0.0` and discarded elevated scan points. Explicit 0--2 m
  limits populated the internal layers. A service probe observed 548 lethal local-obstacle cells
  and 389 lethal global-obstacle cells.
- Publication finding: **NEGATIVE**. Full-map topics delivered zero samples under transient-local
  and volatile fixture subscribers, including with periodic full-map publication enabled. The
  stock `GetCostmap` service remained populated. The fixture records topic and bounded service
  observations separately and states that snapshots do not prove controller consumption.
- Regression: **TESTED/PASS**. The standard 3 m headless run succeeded in 4.83 s, moved 2.62 m,
  captured eight service snapshots with up to 16,656 nonzero cells, produced 301 LiDAR scans, and
  had zero stale/failed observations at RTF 1.00003. The strengthened validity gate passed.
- Opaque pilot `land-nav-20260919-e001`: **TESTED/PASS AS EXPECTED CLIENT CANCELLATION**, not
  navigation failure. Evaluator-only truth records a fixed
  full-width blocker at 4 m, 8 m goal, seed 1000, 25 s harness deadline. The client deadline fired,
  cancellation was requested, and action status reached canceled. Simulator/transport/costmap
  quality passed; the rover displaced 1.30 m. Passive capture retained 223 BT transitions, 2,341
  feedback records, exact BT XML, five harness events, and zero recoveries. No physical obstacle
  cause or BT timeout is licensed by robot-visible evidence.
- A/B/C/D/E terminal-status smoke: **TESTED/PASS, NOT LLM EVALUATION**. All conditions reported the
  recorded cancellation and client events and explicitly withheld BT-timeout and physical-failure
  claims. This supplies no material-error effect estimate.
- Independent explanation-evaluation sample remains 0; development robot captures are two (one
  aquatic success and one land cancellation). Highest-value next step is a controlled land variant
  that reliably causes a software recovery or Nav2 terminal result before the harness deadline.

## 2026-09-19 — recovery-bearing land capture and first model pilot

- `land-nav-20260919-e003`: **TESTED/EXCLUDED CALIBRATION**. The predeclared outcome was
  `aborted`, but a 25 s client deadline canceled the goal while the BT was in `Wait`; this is not a
  Nav2 terminal failure. The independently launched capture container also failed before recording
  because this image lacks the `ros2 run` CLI extension. The installed executable exists and must
  be launched directly. Evaluator artifacts remain retained; no robot-visible capture was created.
- `land-nav-20260919-e004`: **TESTED/PASS DEVELOPMENT PILOT**. The passive capture executable was
  started before Nav2 on ROS domain 48. A full-width 4 m blocker, 8 m goal, exact bounded recovery
  XML, and 2 s progress allowance produced an action result `aborted`/error 105 in 21.30 s, before
  the 55 s client deadline. The capture contains 2,053 records: 39 BT transitions, 2,006 feedback
  records, four harness records, terminal action status/result, and both capture boundaries.
  The retained XML SHA-256 is
  `14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520`.
- Simulator/evaluator validity: **TESTED/PASS**. RTF 1.00001; 651 LiDAR scans; 59 costmap
  observations with up to 12,637 occupied cells; 181 accepted commands; zero rejected, stale, or
  cross-episode actions; zero failed/stale observations. The full evaluator window was allowed to
  complete after the action result.
- Recovery evidence: feedback progressed 0→1→2; the BT log records two distinct `Wait` entries and
  two `Wait` successes, plus two `FollowPath` FAILURE and two recovery-guard SUCCESS transitions.
  A third `FollowPath` start has no terminal transition in the BT topic stream even though the
  action result and controller log terminate. Checked answers therefore say “at least two are
  recorded,” not “exactly two occurred.” The robot-visible trace does not license the evaluator's
  physical blocker as failure causality.
- Seed finding: **NEGATIVE/OPEN**. The requested `--crane-seed 1003` was appended after the worker's
  own seed flag, but Unity's first-match parser retained seed 1000. Future independent runs must set
  `CRANE_SEED_BASE`, not append a duplicate seed flag. This pilot is not a new seeded layout family.
- Parity audit iteration: the first model attempt was **EXCLUDED** because prose summarized one
  generic guard transition while native structure exposed two and exact timestamps. The corrected
  B presentation omits exact timestamps and maps ten explicit fact IDs one-for-one to strong prose;
  both formats explicitly mark physical cause and hypothetical outcome as not established.
- Actual model pilot: **TESTED/DEVELOPMENT ONLY**. Six question families × five conditions yielded
  30 final responses (24 model-mediated, six deterministic); 21 unique `gpt-5.6-sol` low-reasoning
  calls were cached without retry through documented noninteractive `codex exec --json`. Raw events,
  prompts/hashes, requested model/effort, CLI version, latency, tokens, and final outputs are
  retained. The CLI did not report monetary cost, temperature, or a sampling seed, so those fields
  are explicitly null. Provider/prompts remain mutable and are not frozen.
- Single unblinded development annotation: A had 1/6 response-level material errors (an exact
  recovery-count implication despite incomplete history); B/C/D/E had 0/6. All conditions gave
  substantive answers on 5/6 questions and correctly abstained on the unsupported counterfactual.
  Answerable-information coverage was A 13/16, B 16/16, and C/D/E 14/16. C and D used verified
  template fallback on 2/6 questions; their false-premise response omitted the useful supported
  fact that both recorded `Wait` actions succeeded. These correlated rates have no confidence
  interval or inferential meaning because the independent episode count is one.
- Retained tracked analysis:
  `research/explanation_fidelity/annotations/development/land-nav-20260919-e004.json` and
  `research/explanation_fidelity/analysis/development-land-nav-20260919-e004.json`. Raw capture,
  evaluator truth, cache, and model output remain outside Git and will be referenced by manifests.
- Current highest-value action: collect several genuinely independent success/recovery/failure
  episodes using `CRANE_SEED_BASE`, then estimate paired discordance and episode clustering. More
  environment engineering currently has lower expected paper value.

## 2026-09-19 — land collection e005–e009 and identity hardening

- `e005`: **TESTED/EXCLUDED EXPECTED-OUTCOME MISMATCH**. In a 5 m × 24 m unblocked corridor,
  seed 1004, a 4 m goal hit the 35 s client deadline after 3.37 m displacement and one feedback
  recovery. This is cancellation, not success or Nav2 terminal failure. The run demonstrated that
  “no configured blocker” does not imply “no recovery.”
- `e006`: **TESTED/EXCLUDED MISSING REQUIRED PROVENANCE**. The narrowed 3 m goal succeeded in
  5.78 s with healthy simulator metrics, but volatile harness delivery missed both one-shot
  identity events. Goal/result and capture boundaries were present; exclusion avoids silently
  accepting incomplete episode/observation identity.
- Instrumentation fix: CRANE revision `a17087ef01126c9f7c1360f5e9182d2ff0fd4b7f` republishes
  `crane_identity` and `observation_identity` at accepted-goal time with an explicit publication
  reason. It preserves the qualifier that initial odometry was delivered to the fixture and is not
  proven consumed by Nav2. Eight static land-fixture tests passed.
- `e007`: **TESTED/PASS INCLUDED SUCCESS FAMILY**. Seed 1006, 5 m × 24 m unblocked corridor, 3 m
  goal: `succeeded`/error 0 in 4.08 s, 2.58 m displacement, zero recoveries, exact BT XML, both
  initial and accepted-goal identity pairs, 13 populated costmap observations, 451 LiDAR scans,
  38 accepted commands, no rejected/stale/cross-episode actions, RTF 1.00002.
- `e008`: **TESTED/EXCLUDED EXPECTED-OUTCOME MISMATCH**. A 2.5 m partial blocker at 4 m was
  predeclared recovery-success but returned `aborted`/105 after two successful `Wait` recoveries.
  Simulator and capture quality passed; the outcome class did not. Static partial blockage plus a
  2 s progress threshold is not currently a recovery-success generator.
- `e009`: **TESTED/PASS INCLUDED TERMINAL FAMILY**. A distinct 2 m partial blocker at 5 m, seed
  1008, was predeclared `aborted` and returned `aborted`/105 in 21.70 s before the client deadline.
  The capture records the accepted-goal identity pair, exact BT XML, two successful `Wait`
  recoveries, three `FollowPath` starts/two captured failures, terminal result, and both boundaries.
  Simulator validity passed with 65 populated costmap observations, 701 LiDAR scans, 185 accepted
  commands, no rejected/stale/cross-episode actions, and RTF 1.00002. Physical blocker causality is
  still evaluator-only and not licensed in explanations.
- Pilot-driven checked-plan revision: **IMPLEMENTED/TESTED, 21 tests**. Successful FollowPath now
  closes capture completeness; successful episodes reject a question's false failure premise;
  checked recovery-count plans retain recorded recovery SUCCESS status; and a complete software
  recovery-mechanism answer is classified full even while physical cause remains explicitly
  unestablished. These changes use development evidence and precede study freeze.
- Current included captured families: e004 full-blocker terminal recovery/exhaustion, e007
  unblocked success, e009 partial-blocker terminal recovery/exhaustion. Only e004 has model outputs
  and annotation so far. Recovery-followed-by-success remains **NOT_RUN/BLOCKED ON SCENARIO
  CAPABILITY**, not a reason to delay terminal/success data collection.

## 2026-09-19 — corrected three-episode A/B/C/D/E development pilot

- Completeness correction: **TESTED**. Whole-BT transition completeness and recovery-count
  completeness are now separate. E004/e009 have incomplete final node transitions but complete
  recovery-count evidence through capture bounds, one accepted goal/result, matching goal IDs,
  monotonic final feedback, exact XML, and matching unique `Wait` entries. E007 analogously
  establishes exactly zero recoveries. The earlier e004 annotation and summary are retained with
  explicit `SUPERSEDED` status rather than rewritten.
- Model data: **TESTED/DEVELOPMENT ONLY**. E004, e007, and e009 each have six A/B/C/D/E outputs:
  90 final responses total, 72 model-mediated. Forty-seven unique model calls are referenced after
  cache reuse. No call was resampled. The combined cache/output hashes and usage are in
  `manifests/model_outputs/land-nav-development-three-episode-gpt-5.6-sol.json`.
- Provisional single-annotator result: A had 1/18 material errors (5.6%); B/C/D/E had 0/18. The A
  error called the success counterfactual's premise false even though implied obstacle presence was
  only unestablished. D-vs-A therefore has one favorable and zero unfavorable error discordances,
  far too little for inference.
- Coverage result: **NEGATIVE/MIXED**. A/B substantive coverage was 15/18 (83.3%) and provisional
  information coverage 37/40 (92.5%). C/D/E substantive coverage was 14/18 (77.8%) and information
  coverage 36/40 (90%). On the e007 false-premise recovery question, C/D/E abstained because no
  recovery transitions existed even though complete recovery evidence established exactly zero;
  A/B correctly rejected the premise. C fallback was 9/18 and D fallback 11/18 under the strict
  exact-sentence verifier. The checked method has not yet demonstrated a favorable risk/coverage
  tradeoff over B.
- Statistical status: independent evaluated episodes = 3; outcome families = success and terminal
  recovery/exhaustion; recovery-success remains absent. No confidence interval, significance test,
  equivalence statement, ICC estimate, or defensible power target is reported. The next plan fix
  is predeclared from this development error: reject a recovery premise when complete evidence says
  zero, then collect additional mechanisms before blind/adjudicated pilot annotation.
- Follow-up plan fix: **IMPLEMENTED/TESTED AFTER RETAINING PILOT OUTPUTS**. Core revision
  `d5a7c019f7efe078f9080f356014f028abb1a045` uses complete zero-recovery evidence to state that
  exactly zero attempts occurred and reject the premise that the BT entered recovery. Twenty-three
  core tests pass. The 90-response pilot was not regenerated, so the observed false abstention
  remains auditable evidence of the pre-fix behavior.

## 2026-09-19 — fourth evaluated mechanism: client cancellation

- Reused `land-nav-20260919-e001` rather than running another geometry-only terminal instance.
  Recovery-count completeness is established through its accepted goal, terminal canceled action
  status, explicit client events, capture boundaries, final monotonic zero count, goal identity,
  and zero unique `Wait` entries. A/B parity now includes the deadline and cancellation as separate
  facts; it does not add a causal edge between them.
- Six A/B/C/D/E questions produced 30 additional responses without resampling. The post-pilot
  zero-recovery plan correctly rejects recovery premises in C/D/E. Artifact hashes and cumulative
  66 unique-call usage are in
  `manifests/model_outputs/land-nav-development-four-episode-gpt-5.6-sol.json`.
- New provisional error: A explained termination “because” the client deadline was reached. The
  parity evidence records deadline and cancellation request but not their causal relation. B and
  checked conditions kept them separate. Four-episode development totals are A 2/24 material
  errors (8.3%) and B/C/D/E 0/24.
- Coverage remains mixed: A/B substantive coverage 20/24 and provisional information coverage
  50/54; C/D/E 19/24 and 49/54 because the retained e007 outputs predate the zero-recovery premise
  fix. The corrected planner was not used to rewrite those outputs. D-vs-A has two favorable error
  discordances and zero unfavorable error discordances, but only four independent episode clusters.
- RQ1 negative finding: B has zero observed errors at the same response coverage as A, so this
  development sample does not show structured B outperforming strong prose A. RQ2 is suggestive
  only; the risk reduction remains confounded with the checked method's lower observed coverage.

## 2026-09-19 — e010 planning failure

- `land-nav-20260919-e010`: **TESTED/PASS INCLUDED PLANNING-FAILURE FAMILY**. The 4 m goal was
  placed at a full-width blocker at 4 m, seed 1009, with predeclared `aborted`. The action returned
  `aborted`/error 208 in 1.26 s before any controller command or displacement. The simulator gate
  passed: one populated costmap snapshot (12,995 occupied cells), 501 LiDAR scans, no rejected,
  stale, cross-episode, or failed observations, and RTF 1.00003.
- Robot-visible evidence records `ComputePathToPose` active and terminal error 208. The installed
  Jazzy `nav2_msgs` 1.3.12 defines ComputePathToPose error 208 as `NO_VALID_PATH`. The controller
  log independently reports NavFn failed to create a plan, but model-visible derivation uses the
  action error mapping and BT activity. The BT topic omits the node's terminal transition, so the
  plan does not invent one. Evaluator geometry does not license physical blocker causality.
- Core revision `8314e0964dbaf21b9e52bed7d2f09c592b959868` adds a checked planning-failure
  answer and regression; 24 core tests pass. A/B parity includes the 208 mapping and active node in
  both formats. Model evaluation is pending at this checkpoint.
- The first e010 parity derivation is **SUPERSEDED/EXCLUDED**: it marked the whole BT transition
  history complete by checking only `FollowPath`. The corrected derivation separately compares
  starts and terminal transitions for both `ComputePathToPose` and `FollowPath`. Fresh `parity2-*`
  artifacts correctly record whole-BT history incomplete while retaining complete recovery-count
  history, zero recorded recoveries, and the supported `NO_VALID_PATH (208)` planning proposition.
  All seven information-parity audits pass; retained `parity-*` inputs were not rewritten.
- Seven A/B/C/D/E model cases completed with the unchanged `gpt-5.6-sol` low-reasoning adapter,
  content-addressed caching, and no retries: 35 new logical outputs, 28 model-mediated. Across all
  five included episodes there are now 155 outputs, 124 model-mediated, and 88 unique referenced
  calls. Artifact hashes and usage are retained in
  `manifests/model_outputs/land-nav-development-five-episode-gpt-5.6-sol.json`.
- Provisional unblinded annotation found no e010 material error. All methods answer six of seven
  questions substantively; the unsupported counterfactual is correctly withheld. A/B cover all 13
  answerable information units. C/D/E cover 12 because the generic terminal-status plan says the
  action aborted and withholds physical cause but omits the available `NO_VALID_PATH` mechanism.
  This negative coverage result is retained rather than prompt-tuned away. C and D used verified
  template fallback on three cases after one generated realization failed exact verification.
- Five-episode development totals: A 2/31 material errors; B/C/D/E 0/31. A/B substantive coverage
  is 26/31 and information coverage 63/67; C/D/E are 25/31 and 61/67. These are descriptive only;
  five clusters, one unblinded annotator, and absent recovery-success data do not support inference
  or power planning.

## 2026-09-19 — F1TENTH Spielberg reference-environment qualification

- **IMPLEMENTED/TESTED** in CRANE revision `5b5073c615c2e10a85e99d81d41365b61b1d6cd5`.
  The offline PNG/YAML converter now traces closed contours, simplifies them at an explicit metric
  tolerance, retains input hashes and optional centerline provenance, and generates stable semantic
  wall IDs. Unity editor tooling constructs separate primitive collision/presentation layers plus a
  planar F1TENTH-class Ackermann body and LiDAR; no runtime SDF/world loader was added.
- External input: `f1tenth/f1tenth_racetracks` Spielberg at
  `b95c4eff766f6367d66b310ea20cd2c9563712c0`. GPL-3.0 map data remains outside Git. The input,
  canonical-output, implementation, and result hashes are retained in
  `manifests/reference_environments/f1tenth-spielberg-b95c4eff-v1.json`.
- Offline tests: **5 passed**. A 0.10 m simplification tolerance reduced 29,200 raster boundary
  edges to 290 wall boxes across four contours. The headless Unity 6000.5.10f1 `train-cpu` run
  validated 291 canonical colliders, 291 collider-free renderers, a semantic wall ray hit, rigid
  contact, four grounded wheels, 0.295 m planar motion, 5.388 degrees of steering response, and no
  enabled camera/graphics path. Two result JSON files were byte-identical.
- Negative calibration evidence retained in the session record: the initial small-car suspension
  had zero grounded wheels and the first motion metric included vertical settling. The accepted
  fixture uses mass-scaled suspension and planar displacement; roll/pitch are frozen because the
  source benchmark is a 2-D occupancy-map simulator, not a rollover-dynamics benchmark.
- **NOT_RUN**: full-lap controller, ROS transport, centerline adherence, source-simulator geometric
  comparison, and F1TENTH Gym/hardware dynamics equivalence. A Clearpath regression rebuild was
  attempted after generalizing its validator to primitive colliders, but first exhausted `/tmp`
  quota and then stalled with an empty Unity log; its five offline converter tests still pass.

## 2026-09-19 — graphics-free reference-environment launcher regression

- **IMPLEMENTED/TESTED** in CRANE revision `ff8a6a095b158c5b3af1f3c93d989ca0a0877907`.
  `Tools/ReferenceEnvironments/run_reference_validation.sh` resolves the CRANE root dynamically,
  checks the requested scene against the exact player build manifest, selects it through the
  `train-cpu` profile, and always supplies `-batchmode -nographics`. This prevents an accidental
  interactive launch of the build's default RoboSub scene.
- The first launcher attempt exposed a real lifecycle issue: `--crane-disable-ros` alone did not
  install the shared runtime gate for a standalone validation invocation, so the otherwise valid
  fixture started an irrelevant ROS reconnect loop. The accepted invocation selects
  `--crane-profile train-cpu` and `--crane-scene` before validation; reruns contained no failed ROS
  connection attempt.
- **TESTED**: eight reference-tool tests passed. PX4 Walls returned `valid=true`, including exact
  geometry, semantic ray, collision, multirotor dynamics, wind, landing, and saturation checks.
  Clearpath Pipeline returned `valid=true`, including 11 canonical colliders, 13 visual renderers,
  semantic LiDAR/raycast resolution, rigid contact, and evidence highlighting without collider
  mutation. Both runs used Unity 6000.5.10f1 and exited without a window.
- These are regression validations, not new independent navigation episodes and not additions to
  the explanation-study sample size. F1TENTH still requires a player built with its generated
  scene via `--crane-extra-scene`; TurtleBot3 continues to use the ROS/Nav2 closed-loop fixture.

## 2026-09-19 — e032–e035 persistent-hold development batch

- E032/e033/e034: **TESTED/EXCLUDED EXPECTED-INTERVENTION MISMATCH**. Each action aborted and the
  robot-visible BT stream recorded two completed `Wait` recoveries, but evaluator truth recorded
  `mobilityHeld=false` and `mobilityReleased=false`. The runs therefore do not validate the
  predeclared persistent-hold mechanism. All attempts are retained, checkpointed separately, and
  were not rerun, tuned, or relabeled.
- E035: **TESTED/INCLUDED**. The matched no-hold TurtleBot3 instance succeeded, displaced 3.469 m,
  recorded exactly zero recoveries, and passed transport, costmap, observation, and action gates.
  Six fact-parity audits passed.
- The unchanged single-sample `gpt-5.6-sol` procedure produced 30 e035 outputs. No material error
  was annotated. C and D each used checked-template fallback on four questions after final-text
  verification rejected the free realization; no retry or resampling occurred.
- Cumulative development-only totals are 14 independent episodes, 85 responses per condition, and
  425 outputs. Material errors are A 6/85, B 0/85, and C/D/E 1/85. A/B information coverage is
  172/185 versus 164/185 for C/D/E. This remains a negative/mixed result for D superiority.
- Validity threat: the intended hold did not schedule or activate in three of three terminal
  instances. Diagnose that configuration path before predeclaring another terminal batch; the
  observed aborts cannot be described as intervention-caused.

## 2026-09-19 — e036 persistent-hold regression calibration

- Root cause: **DIAGNOSED/FIXED**. E032–e034 player logs each contained
  `ArgumentException: Mobility hold and release boundaries must be configured together.` The
  terminal design deliberately omitted release, but the runtime required a finite release after it
  had already written initial evaluator truth. This was a contract mismatch, not timing noise.
- CRANE `c559932a5ebef00bfa7752511799fd904e5c9dbe` makes a negative release boundary mean
  persistent hold until process exit; release without a hold remains invalid. Thirteen static land
  contract tests pass, and Unity 6000.5.10f1 rebuilt the Linux player successfully.
- E036: **TESTED/PASS CALIBRATION ONLY, NOT A COUNTABLE STUDY EPISODE**. The hold was scheduled at
  simulation time 15.020 s and applied at 15.040 s; `mobilityHeld=true`,
  `mobilityReleased=false`, and the former exception is absent. The action aborted after 0.123 m.
- The generic worker summary is `valid=false` only because its default expected action status was
  success; action outcome was explicitly outside the predeclared calibration pass rule. Raw
  robot-visible and evaluator-only artifacts are retained and checkpointed under e036.

## 2026-09-19 — e037–e040 corrected persistent-terminal batch

- **TESTED/INCLUDED:** all four independent configurations recorded scheduled and actual
  persistent holds, `mobilityHeld=true`, `mobilityReleased=false`, one accepted goal, one aborted
  result, exactly two distinct successful `Wait` attempts matching final feedback, complete
  recovery history, populated costmaps, and clean transport/observation gates.
- Execution-note defect: the launcher invocation used `CRANE_EXPECT_NAVIGATION_STATUS` instead of
  the actual post-processing variable `CRANE_EXPECTED_NAV_STATUS`. Consequently each generic
  summary compared the observed abort with default `succeeded` and set `valid=false`. This did not
  enter Unity/Nav2/capture configuration. Inclusion uses the predeclared abort plus separately
  audited underlying gates; no instance was rerun.
- Twenty-four A/B information-parity audits passed. The unchanged sequential, single-sample model
  procedure produced 120 outputs with no retry or resampling. Single-annotator development review
  found no new material error. C used template fallback 16/24 times and D 20/24 times.
- Cumulative development-only totals: 18 episodes, 109 responses per condition, and 545 outputs.
  Errors are A 6/109, B 0/109, and C/D/E 1/109. A/B cover 228/245 answerable information units;
  C/D/E cover 220/245. These replications improve sample size but still do not support D over B.

## 2026-09-21 — Clearpath pipeline ROS/Nav2 motion and sensor smoke

- CRANE revision `7ddd1aa` (the validated source diff was committed after the run); Unity
  6000.5.10f1; generated Clearpath asset-set SHA-256
  `A85855FDA80AA08BD7773602E9133862EA9824A03CE73F002D33999482A0722F`.
- **IMPLEMENTED/TESTED:** `run_clearpath_pipeline_nav2_fixture.sh` selects the generated Clearpath
  scene, differential command adapter, `base_scan`, and a default 1.0 m goal. The generic land
  bootstrap preserves imported geometry and the scene-authored spawn, rejects synthetic corridor
  blockers, and records the environment/platform identity in evaluator-only truth.
- **TESTED/PASS:** the graphics-free 1 m action succeeded in 2.978 s after 10 returned controller
  commands. Planar odometry displacement was 0.497 m, within the configured 0.55 m goal tolerance.
  Capture retained 451 LiDAR scans, four costmap observations with at most 11,668 occupied cells,
  zero stale/rejected commands, valid transport, and RTF 1.00002. Evaluator truth recorded
  `environmentId=clearpath-pipeline-2.9.4-v1`,
  `platform=clearpath-jackal-class-differential`, `referenceEnvironmentPreserved=true`, and the
  authored start `(0,5,0)`.
- **TESTED/PASS:** the reference-environment regression remained valid with 11 canonical colliders,
  13 visual renderers, one LiDAR, and passing layer, bounds, raycast, contact, semantic-sensor, and
  evidence-highlight checks. The TurtleBot3 closed-loop non-regression also succeeded: 0.456 m
  displacement, 20 commands, 226 scans, seven costmap observations, at most 9,869 occupied cells,
  zero stale/rejected commands, valid transport, and RTF 1.00002.
- **TESTED/PASS:** 22 static land/reference-environment tests and launcher shell syntax. Unity's
  player build is the authoritative C# compilation verdict. A direct
  `dotnet build --no-restore` attempt produced no valid verdict because Unity had not generated the
  required `project.assets.json`; it is not counted as a passing or failing source test.
- Limits: this is a local smoke, not representative pipeline-route validation. Topic/service
  delivery does not prove controller consumption. Native Gazebo comparison, calibrated route and
  spawn catalog, high-fidelity material parity, and Jackal hardware dynamics are **NOT_RUN**. It
  adds no independent explanation-study episode and no RQ1–RQ4 effect estimate. Raw outputs remain
  ephemeral under `/tmp/crane-clearpath-platform-build.xDO9d5`; no sealed data was changed.

## 2026-09-21 — industrial warehouse v2 cross-aisle calibration

- **IMPLEMENTED/TESTED STATIC:** CRANE revision `626d07e` adds the manifest-driven
  `crane-industrial-warehouse-v2`, its preserved-reference launcher, and evaluator-only
  environment/route identity. Twenty canonical boxes, eight regions, four route contracts, and
  build-manifest inclusion are covered by the 27-test land/reference suite. Unity 6000.5.10f1
  produced a fresh null-graphics player with asset-set SHA-256
  `E75545A2DD4372CA6F224A71BD70604E2E1F1B1ADF07E30327FEC9812E8CD5C4`.
- **TESTED/NEGATIVE CALIBRATION:** `warehouse-cross-aisle-detour-v1` used a 13 m relative goal,
  60 s client deadline, seed 1000, and ROS domain 227. Transport, odometry, LiDAR, commands, and
  populated costmaps were valid, but the action timed out after 2.770 m displacement. The robot
  turned near the center route divider and then oscillated/crept without completing a side-aisle
  detour. The deadline produced a client cancel; no recovery or mission-failure claim is made.
- The first attempted ROS domain, 248, exceeded Fast DDS's valid port calculation range and has no
  simulation/navigation verdict. It was rerun once on a valid domain for infrastructure validity,
  not because of an outcome. A separate 22.8 m north-route attempt aborted because its goal lay
  outside the frozen 30 m rolling global costmap; the frozen Nav2 file was not modified.
- **TESTED/NEGATIVE DIAGNOSTIC:** the canonical side gaps are 3.5 m, the physical base's
  circumscribed radius is 0.188 m, and the shared costmap radius was 0.75 m. A single rerun on ROS
  domain 226 used a separate ecological parameter file with radius 0.22 m and inflation 0.55 m.
  Maximum occupied cells fell from 8,750 to 4,996, but the action again timed out at essentially
  the same endpoint after 2.775 m displacement. Oversized inflation is therefore not the sole
  limiting cause.
- Trajectory evidence shows the plant accepted linear/angular commands and alternated large turns
  while moving near its 0.26 m/s physical limit. Nav2 requested up to 0.8 m/s linear and 1.25 rad/s
  angular velocity; CRANE clamps the former to 0.26 m/s but does not proportionally scale the
  latter. Realized-curvature mismatch is the next bounded diagnosis target. No second tuning change
  was run in this session.
- **NOT_RUN:** representative route success, v2-specific structural/physics validator,
  interactive inspection, recovery/blockage contracts, explanation evaluation, and repeated
  scenario qualification. Raw calibrations remain ephemeral under
  `/tmp/crane-warehouse-v2d-build.IDNwQU`; sealed study data and frozen artifacts were untouched.

## 2026-09-21 — industrial warehouse v2 nominal route qualification

- **ROOT CAUSE/FIX:** ROS FLU positive yaw was applied directly as Unity positive-Y torque even
  though the navigation pose maps Unity `(x,z)` to ROS `(-y,x)`. This reversed the physical turn
  relative to the published pose. CRANE revision `0ebfcee` negates yaw only at the land
  differential command boundary; no RoboBoat code or configuration changed. Unity 6000.5.10f1
  compiled the change, and the unchanged controlled 1 m corridor subsequently succeeded with
  0.456 m physical displacement, 20 returned commands, populated costmaps, and zero clock/stale
  errors.
- The ecological-only Nav2 file now matches the TurtleBot3-class 0.26 m/s physical maximum. Its
  endpoint is a manifest-defined goal region without terminal orientation, so the checker does not
  promote the harness's inherited start quaternion into an undeclared task requirement. The action
  deadline is 75 s because the declared 16.5 m detour has a 63.5 s no-stop lower bound at the
  physical speed limit. Frozen controlled-study parameters are unchanged.
- **TESTED/PASS:** after one infrastructure-invalid attempt with 2,780 clock-rewind warnings, the
  single allowed rerun on isolated ROS domain 220 succeeded in 54.627 s with zero rewinds and zero
  stale/rejected commands. It retained 527 returned controller commands, 204 costmap observations,
  8,531 maximum occupied cells, 12.581 m goal displacement, and RTF 1.00002. The 1 Hz retained
  trajectory sampled 13.607 m of travel and a 1.998 m westward lateral excursion around the center
  divider before returning toward the goal. The invalid attempt is retained and is not a failed
  navigation verdict.
- **TESTED/PASS:** the new native-warehouse reference target independently found 20 canonical
  colliders, 20 collider-free visual renderers, 28 unique semantic identities, floor contact,
  semantic LiDAR evidence on `rack-center-blocker`, evidence highlighting without collider
  mutation, 0.150 m forward differential motion, and 19.075° turn response. It reports
  `STRUCTURAL_PASS`, `PHYSICS_PASS`, `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`.
- **IMPLEMENTED/TESTED:** `summarize_environment_qa.py` hash-checks and merges the scenario
  manifest, evaluator identity, structural output, navigation summary, and runtime trajectory. Its
  warehouse record adds `NAVIGATION_PASS` while keeping `failureRecovery=NOT_RUN` and
  `interactive=NOT_RUN`; overall verdict therefore remains `PARTIAL`. Thirty-one static land and
  reference-tool tests pass.
- **NOT_RUN / remaining:** interactive visual inspection, dynamic blocker/no-path/recovery route
  qualification, repeated nominal-route determinism, and ecological explanation generation or
  annotation. Raw outputs remain ephemeral under `/tmp/crane-warehouse-yawfix-build.y1Pmyr` and
  `/tmp/crane-warehouse-qa-build.Bq8D4k`; no frozen or sealed artifact changed.

## 2026-09-22 — warehouse interactive inspection increment

- **TESTED/NEGATIVE BASELINE:** the existing fixed spectator camera was launched in an isolated X
  display against `/tmp/crane-warehouse-qa-build.Bq8D4k`. The scene loaded, but the view was too
  distant, perimeter walls obscured the layout, lighting was overexposed, the robot was not
  legible, and no inspection controls or overlays existed. This is retained as the reason for the
  bounded presentation-only change; it is not a navigation or explanation failure.
- **IMPLEMENTED:** `CraneReferenceInspectionController` adds overview, oblique, and robot-follow
  views; a route/environment HUD; trajectory rendering; semantic evidence highlighting; and
  canonical-box-collider wireframes. It changes only the spectator camera and render-only overlay
  objects. Deterministic launch flags mirror the `1`/`2`/`3`, `H`, `C`, and `T` keyboard controls.
- **TESTED/PASS:** Unity 6000.5.10f1 regenerated the warehouse scene and produced a fresh Linux
  development player. Isolated 1280×720 screenshots visually confirmed a readable full-layout
  overview and oblique view, correct `crane-industrial-warehouse-v2` and
  `warehouse-cross-aisle-detour-v1` HUD identity, semantic-overlay state, trajectory state, and
  visible wireframes around canonical geometry. Wayland was explicitly removed from the player
  environment so the audit remained on its own X display and did not open a host window.
- **TESTED/NON-REGRESSION:** all 31 land/reference static tests passed. The new build's headless
  warehouse validator returned `valid=true`, 20 canonical colliders, 20 collider-free renderers,
  28 unique semantic IDs, zero duplicates, and unchanged `STRUCTURAL_PASS`, `PHYSICS_PASS`,
  `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY` results. The build includes the existing
  RoboBoat scene and compiled shared assemblies, but no parallel-workstream RoboBoat runtime was
  touched or rerun.
- **PARTIAL / remaining:** direct manual keyboard polling was not exercised; attempted synthetic X
  key injection did not change the view, so only deterministic launch controls are counted as
  tested. Dynamic blockage/no-path/recovery scenarios and ecological explanation evaluation remain
  `NOT_RUN`. Screenshots and build outputs are ephemeral under `/tmp`; frozen study data and sealed
  artifacts were not modified.

## 2026-09-22 — manifest-driven warehouse blockage calibration

- CRANE revision `db39095`; Unity `6000.5.10f1`; warehouse manifest version `2.1.0`, SHA-256
  `7462c373be4cceecd88ecbe0f510ab36cddb33dd0d15b602beda22d0355d80cc`.
- **IMPLEMENTED/TESTED:** the warehouse manifest now defines static full-width, delayed,
  temporary, and occupied-goal scenario obstacles with stable semantic/scenario/route identities.
  Canonical colliders remain authoritative, presentation objects mirror their state, and scheduled
  and actual fixed-simulation-time boundaries are written only to evaluator truth. Reapplying a
  scenario destroys its prior timer callbacks together with its scenario-owned geometry.
- **TESTED/PASS:** 37 land/reference static tests and launcher shell syntax passed. A fresh Linux
  player build succeeded. Nominal headless validation remained `valid=true` with 20 canonical
  colliders, 20 collider-free renderers, 28 unique semantic identities, and unchanged
  `STRUCTURAL_PASS`, `PHYSICS_PASS`, `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY` gates.
- **TESTED/NEGATIVE CALIBRATION:** the full-width barrier run remained active until its 75.03 s
  client deadline. It displaced 4.302 m, returned 729 commands, retained 279 costmap observations,
  and reversed course substantially as the rolling costmap revealed geometry. This is real
  obstacle-driven path change, but not a Nav2 abort or recovery result.
- **TESTED/NEGATIVE CALIBRATION, REPLICATED:** the final occupied-goal run on isolated ROS domain
  223 and TCP port 10570 ended at its 45.03 s client deadline with 1.742 m displacement, 439
  commands, 165 costmap observations, and 6,850 maximum occupied cells. Evaluator truth identifies
  `warehouse-occupied-goal-no-path-v1`, route `warehouse-blocked-goal-v1`, seed 4104, and active
  obstacle `blocked-goal-pallet-stack`. The controller repeatedly logged replacement paths until
  the client canceled the still-active goal; no progress failure or recovery was observed.
- **DIAGNOSIS:** the warehouse launcher selected no repository BT, so the installed stock
  `navigate_to_pose_w_replanning_and_recovery.xml` was used (installed SHA-256
  `5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`). Continuous replanning,
  a rolling global costmap, and `track_unknown_space: false` permit ongoing exploratory motion.
  The scenario launchers now explicitly expect `timeout` and state that client timeout is not a
  Nav2 abort; the unexpected runs are retained rather than relabeled.
- **NEXT / NOT_RUN:** qualify a repository-retained, bounded ecological BT/configuration against a
  paired unobstructed case before claiming recovery or terminal failure. Frozen controlled-study
  parameters and artifacts were unchanged. Raw calibration/build outputs remain ephemeral under
  `/tmp/crane-warehouse-*`.

## 2026-09-22 — bounded ecological warehouse policy and BT QA

- CRANE revisions `ea2f86c` (warehouse policy) and `37809b9` (generic passive QA metrics); exact
  warehouse tree SHA-256
  `423c61f90a57c79a1bae0580eb24a3866eee5169f888ac58cdca40e7db7656f3`.
- **IMPLEMENTED:** `nav2_warehouse_replanning_deadline.xml` retains the installed stock tree's 1 Hz
  replanning, contextual clearing, and six-retry recovery structure, but wraps it in an explicit
  70 s BehaviorTree.CPP steady-clock `Timeout`. Its 80 s client deadline is a later failsafe. This
  ecological policy is separate from the hash-frozen controlled-study BT and parameters.
- **TESTED/NEGATIVE CALIBRATION:** the first root guard used Nav2 Jazzy `TimeExpired`. The paired
  nominal route succeeded, but the blocked route remained active until the 80.03 s client deadline.
  Source inspection showed why: `TimeExpired` returns `FAILURE` while waiting and reinitializes the
  next time it is ticked from inactive status, so this root-guard placement never accumulated the
  configured interval. The run remains retained and was not called an abort.
- **TESTED/PAIRED PASS:** under the exact final tree, the unobstructed route succeeded in 53.38 s,
  displaced 12.597 m, returned 524 commands, and retained 199 costmap observations. The complete
  barrier case aborted in 71.10 s—before client cancellation—after 4.568 m displacement, 699
  commands, and 268 costmap observations. Both had zero clock rewinds and zero stale/rejected
  commands. This establishes a task-policy terminal outcome, not obstacle physical causation.
- **GENERIC SHARED CHANGE / TESTED:** the action-owning fixture now passively summarizes delivered
  `BehaviorTreeLog` transitions and NavigateToPose recovery-count feedback. A controlled 3 m
  TurtleBot3 corridor non-regression succeeded with 97 delivered transitions, 974 feedback
  messages, and recovery sequence `[0]`. No RoboBoat source, environment, vehicle, or configuration
  changed; no RoboBoat runtime was started.
- **TESTED/INSTRUMENTED REPLICATION:** the complete-barrier run again aborted at 71.18 s. It
  retained 629 delivered BT transitions, including `Timeout: IDLE→RUNNING`, 7,001 feedback
  messages, and recovery sequence `[0]`. The terminal `Timeout` transition is absent, consistent
  with the audited Jazzy terminal-tick flush limitation; the action result remains authoritative.
  Therefore this is terminal failure without a recorded recovery attempt.
- **QA:** 39 land/reference static tests pass; XML and shell syntax pass. The generic summary labels
  BT topic delivery as potentially incomplete and does not claim topic delivery proves internal
  consumption. Raw outputs are ephemeral under `/tmp/crane-warehouse-*` and
  `/tmp/bt-metrics-turtlebot-nonreg-001`; frozen/sealed artifacts remain unchanged.
- **NEXT / NOT_RUN:** produce a physical warehouse or proving-ground case with a uniquely recorded
  recovery leaf followed by success or bounded exhaustion. Do not describe the deadline-only case
  as recovery and do not use its paired outcome alone as a physical-causation result.

## 2026-09-22 — retrospective RoboBoat terminal-margin diagnostic pilot

- **INPUT / DEVELOPMENT ONLY:** read-only audit of retained sibling-worktree artifact
  `roboboat-gate5-known-dock-1/fixture-summary.json` (SHA-256 `6bcc1c1f...2223a`) and the exact
  pre-change Nav2 configuration at CRANE commit `4ae5124c...ecd3` (SHA-256 `7ad4490b...93f`). No
  RoboBoat scene, controller, physics, configuration, or historical artifact was modified.
- **IMPLEMENTED/TESTED:** the prospective core now represents measurements with units, frame,
  timestamps/intervals and evidence IDs; records assumptions, support/conflict, unresolved
  alternatives, source anchors, causal-language level, and a next check; computes terminal return
  margin; renders the four required answer sections; and rejects any final text unequal to the
  deterministic checked rendering. Core package: 47 tests pass. Exporter regression: 1 test passes.
- **MEASURED RESULT:** action success occurred at 0.3738 m goal error and independently measured
  0.04861 m/s, inside exact 0.400 m and 0.050 m/s Nav2 thresholds. The declared 0.400 m task
  tolerance left 0.0262 m margin. Delivered odometry recorded 0.1876 m post-result displacement
  and final 0.5614 m error. The supported conclusion is that the return criterion did not reserve
  enough margin for observed post-result motion.
- **EVIDENCE BOUNDARY:** the governed robot-visible export excludes the docking-success label,
  matched 0.20 m intervention outcomes, hidden simulator state, and force decomposition. It does
  not identify residual motion as wave/current/wind, plant failure, collision, or any unique
  physical source. Delivered odometry is not presented as proof of every value Nav2 consumed.
- **SELECTIVE-SPECIFICITY CHECK:** a paired declared evidence mask removes measured speed at action
  return. The diagnostic fails closed to `insufficient`, names the missing measurement, and retains
  the other observations. This is a synthetic development mask, not an independent episode; the
  unmasked pair must be inaccessible during any evaluated presentation.
- **NOT_RUN:** independent blinded scoring, R/P/T/N comparison, prospective rerun, land analogue,
  power planning, and held-out collection. This result validates the development path only.

## 2026-09-22 — current model-manifest audit compatibility

- **ROOT CAUSE/FIX:** `audit_model_artifact_manifest.py` assumed the older aggregate v2 schema and
  indexed `accepted_output_roots` unconditionally. Current sealed per-episode v1 manifests instead
  carry an explicit artifact list. The auditor now dispatches by schema shape, validates every
  listed path, byte count, and SHA-256, rejects duplicate/escaping paths, and retains the aggregate
  audit behavior.
- **TESTED/PASS:** all 33 `pn-*` per-episode manifests validate; the 18-episode aggregate
  development manifest still reproduces 545 logical outputs and 231 physical cache artifacts; the
  combined CPU-only suite passes 114 tests. No frozen manifest or retained artifact changed.

## 2026-09-22 — land diagnostic-capture development run, unexpected nominal outcome

- **PREDECLARED INTENT:** one current-build, headless `complete-blockage-v1` run using the retained
  70 s ecological policy, isolated ROS domain 218/TCP port 11618, CRANE `c46de4d`, and player
  SHA-256 `a7ad5b15...e292`. This was a development evidence check, not held-out evaluation.
- **VALID RECORDING / FAILED INDUCTION:** transport and runtime validity passed, but evaluator truth
  records the default clear corridor (`blocker=none`), not the requested proving-ground layout. The
  robot therefore succeeded after 69.964 s and 17.478 m displacement. This run is not a blockage,
  failure, or geometric-diagnosis example and no tuning rerun was made.
- **CAPTURE RESULT:** the robot-visible fixture retained 675 controller commands, 257 costmap
  observations, 66 successive plan summaries, 3,402 motion samples, 602 unique BT transitions with
  zero drops, and a compressed 240x240 latest costmap with content SHA-256 `3fa225de...bee`.
  Leakage scan passed. This validates the current capture path on an unexpected nominal control.
- **GOVERNANCE:** the robot-visible fixture and physically separate runtime/truth artifacts are in
  DVC development storage with committed manifests. Fault-induction success is explicitly false;
  recording validity is true. Frozen study runtime and artifacts were untouched.
- **ROOT CAUSE:** the executed player has build GUID `9fe01e68b8764d0f87d9823200f59aa4`.
  Its retained build manifest (SHA-256 `e0d9db58...e1a7`) lists the warehouse generator but not the
  later proving-ground generator asset. The source checkout was current, but the player binary/data
  was stale; therefore its command-line parser could not instantiate the requested layout. The
  executable-file hash alone was insufficient build provenance.
- **NEXT:** make one current-source player build and verify its manifest contains the exact
  proving-ground source/catalog hashes before scheduling a new geometric pilot. Do not rerun the
  stale build, modify geometry, or count this nominal as a fault-induction success.

## 2026-09-22 — current-source global-costmap geometric diagnostic pilot

- **BUILD/INPUT:** Unity `6000.5.10f1` built CRANE `c46de4d` from current source with build GUID
  `2e501629ce3544a783506153da3c0268` and build-manifest SHA-256 `1805281a...fcae`.
  The proving-ground generator and catalog hashes are `a6eb6bd2...c8b` and `bea85429...720`.
  No build directory was retained in DVC; the compact build manifest, source identities, and
  reproduction command are retained instead.
- **PRECURSOR / VALID BUT DIAGNOSTICALLY INSUFFICIENT:** the first current-source run used the
  fixture's default rolling local costmap. After applying the scenario's already-declared
  `aborted` expectation, runtime validity passed: action abort at 72.011 s, 3,528 trajectory
  samples, 272 costmap observations, no stale/rejected/cross-episode commands, and evaluator
  confirmation of the intended layout. The final 12 m local window followed the robot back past
  the start and no longer covered the relevant route restriction or 18 m goal, so it could not
  support a start-to-goal connectivity diagnosis. It remains an ephemeral development capture and
  was not presented as physical evidence; the one bounded global-costmap repeat below was chosen
  prospectively to retain the missing decisive observation, not in response to a favorable label.
- **VALID RECORDING / PARTIAL INDUCTION:** one development repeat requested
  `complete-blockage-v1`, the 70 s ecological BT, an expected `aborted` result, and the global
  costmap service/topic on isolated ROS domain 220/TCP port 11620. Evaluator truth confirms the
  intended layout and active wall. The action aborted in 70.860 s with zero stale/rejected/cross-
  episode commands, zero clock rewinds, 451 LiDAR scans, and a valid runtime record.
- **ROBOT-VISIBLE RESULT:** the retained 0.10 m global grid has 1,070 cells at cost >=253. The
  requested centerline first meets such a cell near x=8.45 m and has zero minimum lethal-cell
  clearance. However, an independent 8-connected audit finds the action-result pose and goal are
  still connected below cost 253. Delivered odometry records 2.705 m maximum lateral deviation,
  6.949 m maximum forward progress, and return away from the goal; 69 planning updates completed.
- **SUPPORTED DIAGNOSIS:** the direct route was restricted in the retained navigation model and
  the robot made a substantial detour before a deadline-aligned abort. This does **not** support
  global no-path, unique obstacle identity, or recovery-exhaustion claims. The final BT terminal
  transition was not delivered, so exact source plus 0.860 s deadline timing reconstructs—but
  does not directly observe—the terminal decorator tick.
- **ANSWER/VERIFICATION:** `geometric-route-restriction-v1` produces the four-section checked
  deterministic answer from robot-visible evidence only. Its decisive evidence is limited to
  direct-route clearance, lateral deviation, action time, and configured deadline; final-text
  exact verification passes. A missing connectivity value fails closed to `insufficient` in the
  regression suite.
- **GOVERNANCE:** fixture, QA summary, diagnostic export, compact build manifest, runtime result,
  and evaluator truth are physically separated under `diagnostic-pilot-v1`, with committed SHA-256
  manifests and DVC pointers. This is development evidence, not a frozen R/P/T/N result.

## 2026-09-22 — first information-parity diagnostic explanation pilot

- **DEVELOPMENT ONLY / SINGLE QUESTION:** one governed land episode and one mechanism/outcome
  question were run once with `gpt-5.6-sol`, low reasoning, through Codex CLI `0.155.1`. Conditions
  were R (repository-aware agent), P (checked diagnosis plus model realization and verification), T
  (deterministic rendering), and N (runtime/source ablation without the physical computation).
  No human label, effect estimate, or confirmatory conclusion exists.
- **RETAINED FAIRNESS FAILURE:** pilot v1 gave R the lower-level costmap audit but not P's exact
  diagnostic wrapper. R audited only the default final 5 m, missed the earlier route restriction,
  and incorrectly said `allow_reversing: false` although the exact configuration records `true`.
  The output is retained as a development failure and is excluded from any fair method comparison.
- **CORRECTED TOOL PARITY:** v3 gave R the governed raw fixture, exact CRANE `c46de4d`, exact core
  `910a097`, and the same `export_geometric_route_diagnostic.py` computation available to P. P and
  N reused their content-addressed v1 calls; only the corrected R request was newly sampled. All
  workspaces were read-only and no evaluator truth was available.
- **QUALITATIVE RESULT / NO INDEPENDENT LABEL:** parity-corrected R, P's raw candidate, and T all
  communicated the direct-route cost restriction, retained-grid connectivity, lateral detour,
  deadline alignment, and major causal limits. N explained the deadline accurately but explicitly
  lacked a route computation and did not identify the supported geometric restriction. R did not
  show an obvious material factual error in this corrected output and is at least as readable as
  T. This development case therefore provides no evidence that P beats tool-enabled R.
- **VERIFICATION/FALLBACK:** P's candidate preserved the supported mechanism and limits in more
  natural prose, but the exact-text verifier rejected it; final P equals T. Development fallback is
  therefore 1/1. This is evidence that current final verification is conservative and potentially
  usefulness-reducing, not permission to weaken it without an independently tested semantic check.
- **RESOURCE OBSERVATION:** retained model-call latency was 70.636 s for R, 19.837 s for P
  realization, and 16.980 s for N. The deterministic diagnostic recomputed byte-identically in
  0.111 s locally. Model monetary cost was unavailable. R used 159,005 input tokens (125,952
  cached) versus 17,806 for P and 16,889 for N; this resource difference must be reported rather
  than attributed solely to explanation quality.
- **NEXT:** obtain a nominal-control episode and an evidence-masked ambiguous case, then dry-run
  blinded diagnostic annotation. Do not freeze or power the study from this single selected case.

## 2026-09-22 — retained S-turn nominal-control attempt with unexpected abort

- **INTENT/OUTCOME:** one current-source development run requested catalog `v2`, layout
  `slalom-s-turn-v2`, and a nominal `succeeded` result. The action instead aborted at 70.918 s.
  The simulator was not rerun to obtain the intended outcome. The QA summarizer alone was rerun
  with `aborted` as the observed status, and the runtime recording then passed its transport,
  sensor, command-integrity, and occupied-costmap gates.
- **VALID RECORDING:** all 701 returned commands were accepted; zero commands were stale,
  rejected, or cross-episode; there were zero clock rewinds, 202 global-costmap observations,
  3,530 delivered-odometry samples, and 69 successful planning updates. The final BT transition
  was not delivered, so exact recovery counting remains ineligible.
- **BEHAVIOR/DIAGNOSIS:** the robot progressed 13.543 m toward the 18 m goal while following the
  alternating S route, with 1.699 m maximum lateral deviation. The retained costmap marks the
  requested direct line non-traversable near x=3.55 m but remains connected below cost 253. The
  action abort is 0.918 s from the exact 70 s source deadline. This supports a direct-route
  restriction, substantial detour, and deadline-aligned abort; it does not establish global
  infeasibility, a unique obstacle identity, recovery exhaustion, or the cause of failing to
  finish the remaining route within the deadline.
- **DISPOSITION/GOVERNANCE:** retain as `DEVELOPMENT_VALID_UNEXPECTED_OUTCOME`, not as a nominal
  control. Robot-visible fixture, QA, checked diagnostic, and build manifest are separated from
  evaluator-only runtime truth under `diagnostic-pilot-v1`; committed manifests contain exact
  hashes and DVC pointers. This run may inform benchmark design and induction-rate accounting but
  is not a confirmatory result.
- **NEXT:** use an already-qualified retained success with decisive physical evidence if one
  exists; otherwise collect a prospectively declared nominal control without tuning this S-turn
  layout to manufacture success.

## 2026-09-22 — diagnostic annotation workflow dry-run packet

- **IMPLEMENTED/TESTED:** a separate diagnostic-study packet builder packages the four final R/P/T/N
  responses from the parity-corrected land pilot under opaque HMAC response IDs. The packet omits
  condition, model, provider, fallback, raw-candidate, and verifier fields; its evaluator-only key
  retains those mappings. P and T's byte-identical final answers remain separate opaque rows and
  must receive identical labels.
- **REFERENCE LIMIT:** the seven-unit inventory is based on robot-visible measurements and the
  retained geometric audit, but that audit is the development implementation rather than an
  independent reference computation. The packet and rubric therefore identify themselves as a
  development workflow dry run, not a sealed effectiveness evaluation.
- **STATUS:** packet generated with four responses; human annotation and adjudication are
  `NOT_RUN`. Two independent annotators plus a distinct adjudicator for disagreements are required.
  No project-author inspection or model judgment will be reported as human annotation.

## 2026-09-22 — deterministic missing-cell evidence mask

- **PURPOSE:** create one matched ambiguity case from `land-blockage-global-002` without another
  simulation or evaluator-truth leakage. The transform removes only
  `/latestCostmapSnapshot/data`; it retains the declared hash as unverified metadata plus action,
  trajectory, source, and costmap metadata. The mask is grouped with its source episode for every
  split and statistical analysis.
- **FAIL-CLOSED RESULT:** the geometric computation is not run without cell values. The checked
  result is `insufficient` because direct-route classification and retained-grid connectivity are
  missing; deterministic final text verification passes. The result still reports the recorded
  terminal sequence and specifies a hash-checked costmap as the next required observation, but it
  may not claim geometric restriction or global infeasibility.
- **GOVERNANCE:** the masked fixture, transformation manifest, and checked diagnostic are retained
  in robot-visible development DVC storage with committed hashes. No evaluator-only field was
  added. This is one evidence variant of an existing development episode, not another independent
  sample or a confirmatory result.

## 2026-09-22 — missing-cell R/P/T/N development pilot

- **ONE SHOT / NO RETRY:** the matched evidence mask was run once through R/P/T/N with
  `gpt-5.6-sol`, low reasoning, Codex CLI `0.155.1`. R received the exact v2 wrapper and source;
  all methods lacked costmap cell values and evaluator truth. Three model calls were issued and
  retained; T was deterministic.
- **QUALITATIVE RESULT / NO INDEPENDENT LABEL:** every condition withheld a specific physical
  restriction. R gave the most useful partial answer: it identified a deadline-aligned abort while
  explicitly saying the missing cells prevent route obstruction/connectivity diagnosis and the
  missing terminal tick prevents conclusive timeout proof. P's raw candidate and final P/T safely
  withheld geometry, but they also called the whole terminal mechanism unresolved despite the
  retained source/timing evidence. This is an informative-content omission in the checked plan,
  not evidence that a more fluent model should speculate.
- **OVERCLAIM RISK:** N states timeout propagation as fact before later acknowledging the missing
  terminal transition. R uses qualified language. Whether either is a material error requires the
  independent draft-rubric annotation; no project-author observation is a label.
- **VERIFICATION/RESOURCES:** P again failed exact final-text verification and fell back to T
  (development fallback 1/1). Aggregate model latency was 93.032 s; input tokens 182,797
  (118,912 cached), output tokens 2,158, reasoning tokens 284; monetary cost was unavailable.
- **NEXT:** preserve this v1 failure, then change the checked plan so missing physical evidence
  produces a useful partial deadline-aligned diagnosis plus explicit geometric abstention. Do not
  resample this episode to replace the retained result.

## 2026-09-22 — checked partial-diagnosis correction after retained mask failure

- **TARGETED CHANGE:** core commit `38ae31c` changes only the insufficient-geometry branch. When
  exact source and action timing support deadline alignment, the plan now reports that bounded
  execution mechanism while explicitly withholding the missing physical/geometric reason. It
  still cannot classify the direct route, connectivity, obstacle identity, or the unobserved
  terminal BT tick.
- **REGRESSION/ACTUAL ARTIFACT:** 50 core tests pass. Re-exporting the retained masked fixture
  yields `deadline_aligned_abort_with_unresolved_geometry`, retains `insufficient` disposition,
  states the 0.86 s deadline alignment, names both missing geometric computations, and passes
  exact deterministic final-text verification. The original v1 output and model pilot remain
  immutable alongside the post-fix deterministic artifact.
- **INFERENCE LIMIT:** this is a post-hoc development correction on the episode that exposed the
  defect. It is not a prospective effectiveness result and the same model outputs were not
  resampled. The next independent/masked case must test whether the correction generalizes.
- **ANNOTATION HANDOFF:** a second four-response blinded development packet now covers the retained
  pre-correction missing-cell R/P/T/N outputs. Together with the unmasked packet, the dry run has
  eight responses but only one episode cluster. Annotation remains `NOT_RUN`; packet generation
  does not create a human label or an independent sample.

## 2026-09-22 — RoboBoat terminal-margin R/P/T/N development pilots

- **BOUNDARY / NO PLATFORM CHANGE:** no RoboBoat scene, physics, vehicle, controller, or Nav2
  configuration was changed or launched. Both comparisons consume the governed compact
  robot-visible export from the retained `roboboat-gate5-known-dock-1` run. R received exact CRANE
  commit `4ae5124`, diagnostic core `38ae31c`, exact configuration, raw observations, and the same
  hash-checking executable terminal-margin computation as P. Evaluator labels, matched
  intervention outcomes, hidden forces, and simulator truth were unavailable.
- **UNMASKED / ONE SHOT:** R, P, and N were each called once with `gpt-5.6-sol`, low reasoning,
  Codex CLI `0.155.1`; T is deterministic. R and N both expressed the central result: success was
  returned with only 0.0262 m positional margin before 0.1876 m of post-result motion led to
  0.5614 m settled error. R retained the physical-cause limits. P's candidate was useful but failed
  exact verification, so final P equals T. This is another null/negative development result for a
  P-over-tool-enabled-R claim.
- **SPEED MASK / ONE SHOT:** the paired mask removes independently measured speed at return and is
  the same episode/statistical cluster. R and N preserved the supported positional chain while
  withholding whether the physical platform met the 0.050 m/s stopped-speed threshold and why it
  moved. P/T instead said the entire stopping margin could not be assessed, an informative-content
  omission. P again fell back to T. No model output was retried or replaced.
- **POST-HOC CORRECTION:** `terminal-stopping-margin-v2` retains `insufficient` disposition for the
  complete stopped-criterion claim but reports the observed positional-margin mechanism. The
  deterministic corrected answer verifies exactly. It is post-hoc development evidence and does
  not replace the original output or establish Q3 prospectively.
- **RESOURCES:** unmasked aggregate model latency was 86.944 s with 125,663 input tokens (66,304
  cached), 2,102 output tokens, and 307 reasoning tokens. The mask used 99.135 s, 159,728 input
  tokens (116,096 cached), 2,432 output tokens, and 502 reasoning tokens. Monetary cost was not
  reported. The operator reported a changed load-balancer source; the resolved backend revision is
  unavailable, so equivalence to earlier calls is not claimed.
- **ANNOTATION/GOVERNANCE:** two new blinded four-response packets and physically separate keys are
  retained. Together with land, diagnostic dry runs now contain 16 responses but only two episode
  clusters. Two independent annotators and a distinct disagreement adjudicator remain `NOT_RUN`.
  Development references are not independent gold computations.

## 2026-09-22 — separate RoboBoat terminal-margin reference calculation

- **IMPLEMENTED / DEVELOPMENT ONLY:** `reference_terminal_margin.py` is an evaluator-side code
  path that imports neither the proposed diagnostic core nor its adapter. It independently checks
  the exact configuration hash and computes positional margin, radial error growth, settled task
  failure, and measured stopped-speed status from the permitted observation fields.
- **RESULT:** the unmasked case supports both the positional chain and an independently measured
  speed within the configured threshold. The speed mask still supports the positional chain but
  leaves stopped-speed satisfaction unresolved. Both variants require withholding the physical
  source of residual motion. This independently reproduces the reason the original masked P/T
  answer over-withheld.
- **LIMIT:** the implementation was authored within the project after development output
  inspection. It is not a human label, controlled intervention, or confirmatory gold result.
  Independent reviewer validation remains required before study freeze. Artifacts are confined to
  evaluator-only development DVC storage and are never supplied to R/P/T/N.

## 2026-09-22 — separate land geometric reference calculation

- **IMPLEMENTED / DEVELOPMENT ONLY:** `reference_land_geometric.py` imports neither CRANE's
  costmap-audit helper nor the proposed diagnostic core. It independently verifies/decompresses the
  retained grid, rasterizes the requested route with integer Bresenham cells, checks retained-grid
  connectivity with an eight-neighbor A* implementation, computes route-relative trajectory
  deviation, and parses the literal BT deadline.
- **RESULT:** the independent path finds the first cost-253 route cell centered at x=8.4500005 m,
  a retained-grid connection from action-result pose to goal, 2.7046 m maximum lateral deviation,
  69 successful planning updates, and 0.8602 s deadline alignment. With cell payload masked it
  withholds route restriction/connectivity while preserving deviation and deadline alignment.
- **NOMINAL QA / CORRECTION:** applying the reference to retained successful run
  `land-unexpected-nominal-001` exposed an implementation error: the first version conflated a
  route cell outside the final rolling-grid bounds with a blocked cell. The corrected reference
  tracks full-route coverage separately and never treats out-of-bounds as occupied. On the nominal
  run, the rolling grid does not cover the route start, contains no observed blocked cell on the
  covered route segment, connects action-result pose to goal, and the action succeeded; success
  0.036 s from the deadline is not called a deadline-aligned abort.
- **NOMINAL CHECKED PLAN:** the proposed geometric computation independently returns
  `not_triggered` with exact deterministic verification on this run. This is a valid unexpected
  nominal development control, not prospectively collected confirmatory evidence; R/P/T/N and
  human annotation remain `NOT_RUN` for it.
- **LIMIT:** this reproduces the development inventory but was authored after output inspection.
  It is not a human label or confirmatory gold, cannot prove global physical no-path or exact
  planner consumption, and needs independent reviewer validation before freeze. Both reference
  artifacts remain evaluator-only.

## 2026-09-22 — sealed legacy annotation-form and key-join wiring check

- **STATUS:** `IMPLEMENTED / TESTED`; human annotation remains `NOT_RUN`.
- **DISCOVERED GAP:** the frozen guide's 25-field output schema names episode/scenario/condition
  metadata that the sealed packet correctly withholds. An annotator could not construct a truthful
  validator-shaped row without evaluator-only access.
- **RESOLUTION:** `build_legacy_annotation_form.py` emits all 198 rows with opaque IDs, exact unit
  totals, unset judgments, and explicit pre-join sentinels. `join_legacy_annotation_key.py` is the
  only stage that reads the key; it runs only after complete adjudication, verifies hashes and ID
  inventories, restores frozen grouping, and enforces whole-episode quarantine.
- **TEST:** 29 focused tests passed. A synthetic-label wiring check over the actual sealed packet,
  key, and split restored 198 responses, 33 episode clusters, and F/G/H mappings. The synthetic
  values existed only in process memory, were not retained, and are not annotations or results.
- **FROZEN INTEGRITY:** guide, packet, key, split, raw evidence, responses, questions, and rubric
  were unchanged. Their pre-annotation hashes are recorded in the operational clarification
  manifest. No label or condition effect was inspected.

## 2026-09-22 — legacy annotator calibration packet

- **STATUS:** `IMPLEMENTED / NOT_RUN_BY_HUMAN_ANNOTATORS`.
- **SOURCE:** six retained F/G/H responses from development-only episode
  `land-nav-20260919-e043-worker-0`, spanning the frozen recovery-mechanism and failure-cause
  questions. No sealed response, final-split episode, or evaluator intervention was included.
- **BOUNDARY:** the packet uses opaque shuffled IDs and omits condition/model/fallback fields. Its
  key is physically evaluator-only and is revealed only after both independent calibration passes.
  Existing single-project-author development judgments are discussion context, not gold labels.
- **PURPOSE:** satisfy the frozen guide's pre-sealed calibration requirement and expose rubric
  disagreements before annotators touch `sealed-primary-v3`. The six responses are never pooled
  into final estimates and add zero independent study episodes.

## 2026-09-22 — diagnostic development annotation join inventory

- **STATUS:** `IMPLEMENTED / HUMAN LABELS NOT_RUN`.
- **INVENTORY:** four blinded R/P/T/N packets, 16 responses, and exactly two statistical clusters.
  The land costmap mask remains in `land-blockage-global-002`; the RoboBoat return-speed mask
  remains in `roboboat-gate5-known-dock-1`.
- **JOIN BOUNDARY:** method identity, model/provider, verifier outcome, and fallback status remain
  evaluator-only until every packet is completely adjudicated. The join checks packet/key hashes
  and exact response inventories before exposing them.
- **EXCLUSION:** an evidence problem in any packet quarantines the complete source cluster across
  all conditions and evidence variants. A mask or question variant is never counted as another
  episode.
- **INFERENCE LIMIT:** this only makes the retained development workflow executable. Two clusters
  cannot establish an effect or supply a stable clustered variance estimate; power planning and
  protocol freeze still wait for real human development labels and additional independent pilots.

## 2026-09-22 — first rendered manuscript QA

- **STATUS:** `COMPILED / VISUALLY_INSPECTED / NOT_SUBMISSION_READY`.
- **TOOLCHAIN:** pinned Tectonic 0.17.0 Linux archive, SHA-256
  `1a715688baf591e650c8aeb160ae934e181685eecbb38b317de30b269ac5d606`; IEEEtran conference
  class; BibTeX; Poppler page rendering. `scripts/build_paper.sh` reproduces the build from the
  umbrella root and refuses an archive whose hash differs.
- **RESULT:** four letter-size pages compiled, including six readable references. All four pages
  were rendered at 130 DPI and visually inspected. The first render exposed a pipeline equation
  crossing the column gutter and a results table overlapping the second column; both were fixed.
  The final checked render has no overfull boxes, clipping, or column overlap.
- **REMAINING GATE:** red `PENDING` text correctly exposes missing human annotation, prospective
  diagnostic results, clustered uncertainty, and final sample accounting. The paper is currently
  a short-paper-length draft, not an 8--9 page full paper and not ready for submission.

## 2026-09-22 — diagnosis-to-language positioning and second rendered manuscript QA

- **STATUS:** `COMPILED / VISUALLY_INSPECTED / NOT_SUBMISSION_READY`.
- **CHANGE:** primary-source positioning now credits explicit plan-before-realization, atomic
  factual-precision evaluation, bidirectional NLI checking, selective prediction, and
  provenance-to-plan-to-language as prior art. The paper claims only a scoped robot-navigation
  synthesis/evaluation centered on a validated bounded diagnostic record; it does not claim
  novelty for those component ideas.
- **BUILD:** `scripts/build_paper.sh /tmp/crane-paper-positioning` produced a five-page letter-size
  PDF with 11 references. All five pages were rendered as a contact sheet and visually inspected;
  no clipping, column overlap, or identifying author/affiliation/private-repository text was found.
  The corrected `Brand{\~a}o` BibTeX encoding renders as “Brandão.” Fontconfig and underfull-box
  warnings remain non-fatal layout diagnostics.
- **REMAINING GATE:** the red result markers remain visible. Human annotation, prospective
  protocol freeze, independent held-out episodes, statistics, and final empirical claims are still
  `NOT_RUN`; the extra page contains related-work positioning and references, not new evidence.

## 2026-09-22 — second independent land diagnostic development cluster

- **STATUS:** `IMPLEMENTED / TESTED / DEVELOPMENT_ONLY / HUMAN_LABELS_NOT_RUN`.
- **EPISODE:** retained unexpected S-turn abort `land-s-turn-unexpected-abort-001`; it remains one
  statistical cluster and is not relabeled as the nominal success originally requested.
- **REFERENCE FIRST:** before model comparison,
  `analysis/reference_land_geometric.py` independently decoded and hash-checked the retained grid,
  used integer Bresenham cells and a separate eight-neighbor A* implementation, and reproduced a
  direct-route cost-253 intersection near x=3.55 m, a retained-grid connection, 1.6995 m maximum
  lateral deviation, 69 successful planning updates, and a 0.9179 s deadline alignment. It rejects
  global physical no-path, unique obstacle identity, proven planner consumption, and direct
  observation of the missing terminal timeout tick. This is an independent implementation, not a
  human gold label or confirmatory reference.
- **METHOD RUN:** one single-sample, no-retry R/P/T/N comparison used `gpt-5.6-sol`, low effort,
  exact CRANE commit `c46de4d`, core commit `4d9ecb4`, current diagnostic wrapper SHA-256
  `656363a9...b532`, and prompt `diagnostic_repository_agent_dev_v2.txt`. R and P shared the raw
  fixture and exact executable diagnostic; evaluator truth was unavailable. Three new model calls
  consumed 180,464 input, 100,352 cached-input, 2,351 output, and 308 reasoning-output tokens over
  95,688 ms aggregate latency. The client reported no monetary cost. The configured load balancer
  does not expose a resolved backend/source revision, so none is inferred.
- **QUALITATIVE RESULT:** tool-enabled R, P's candidate, and T all communicate the central route
  restriction, retained-grid connectivity, detour, deadline alignment, and major limits. N reports
  the deadline mechanism but correctly lacks the geometric computation. R is again at least as
  diagnostically complete as P/T on project review; this remains a negative development result for
  P-over-R differentiation pending blind human labels.
- **VERIFICATION:** P's fluent candidate is substantively aligned but fails the conservative exact
  final-text gate; final P is byte-identical to T. Development fallback is now 5/5 questions across
  three clusters. This is further evidence that the current final method is deterministic at its
  native operating point.
- **GOVERNANCE:** the four-response blinded packet and evaluator-only key are retained separately.
  The development annotation inventory now contains 20 responses in five packets over exactly
  three clusters. Raw result, cache records, packet, key, current diagnostic export, and independent
  reference are hash-manifested; DVC artifacts were pushed to R2. Annotation, adjudication, power
  planning, protocol freeze, and held-out evaluation remain `NOT_RUN`.

## 2026-09-22 — false-premise nominal development control and route-coverage defect

- **STATUS:** `IMPLEMENTED / TESTED / DEVELOPMENT_ONLY / HUMAN_LABELS_NOT_RUN`.
- **SOURCE EPISODE:** `land-unexpected-nominal-001` is a retained stale-player fault-induction
  failure whose NavigateToPose action succeeded. Evaluator truth shows no requested blocker was
  instantiated. It remains a valid retrospective nominal/capture control, not a prospectively
  declared held-out nominal episode.
- **DEFICIENT PLAN:** the previous `not_triggered` result merely said that the failure mechanism was
  not established. It did not explicitly reject the question's false premise. Core commit
  `25b8b64` adds the recorded `action_status`, mechanism `no_failure_observed`, recorded-sequence
  causal level, an explicit “action succeeded” diagnosis, and a no-failure chain. The checked text
  uses only terminal status as decisive evidence and withholds universal obstacle-freedom claims.
- **MODEL RUN:** one no-retry R/P/T/N comparison used the same model/settings and information/tool
  parity as the other land pilots. All methods rejected the failure premise. P's candidate again
  failed the exact-text check, so final P equals T and development fallback becomes 6/6.
- **RETAINED TOOL FAILURE:** R additionally claimed that the complete direct route was clear. The
  independent evaluator-side reference shows that the rolling grid did not cover the whole route.
  The shared wrapper had conflated “no lethal sampled cell” with “fully covered and clear.” The
  immutable R response and pre-fix diagnostic remain retained. The wrapper now records route
  coverage and fails closed to an unknown route classification when any samples lie outside the
  grid; the episode was not resampled.
- **TESTS:** focused core/export tests cover successful false-premise handling with and without
  costmap cells and incomplete rolling-grid coverage. The current deterministic export reports
  `action_status=succeeded`, `direct_route.fully_covered=false`, and
  `direct_route.has_lethal_cell=null` while still rejecting the failure premise.
- **GOVERNANCE:** the four-response blinded packet, evaluator-only key, pre-model independent
  reference, raw output/cache, and pre-/post-fix diagnostic artifacts are retained. The inventory
  is 24 responses in six packets over exactly four clusters. Human annotation and adjudication
  remain `NOT_RUN`; no apparent P-over-R difference is claimed from project-author inspection.

## 2026-09-22 — blinded human-annotation handoff readiness

- **STATUS:** `PREPARED / STRUCTURALLY_VALIDATED / HUMAN_ANNOTATION_NOT_RUN`.
- **HANDOFF:** two separate local, ignored archives were generated under
  `artifacts/annotation-handoff-20260922/`. Each contains the appropriate legacy and diagnostic
  guides, the six-response legacy calibration packet, the 198-response sealed legacy packet, all
  six four-response diagnostic packets, and separately identified blank forms for one annotator.
  No evaluator-only key, condition/model identity, verifier result, or fallback field is present.
- **VALIDATION:** each archive contains eight packets and 228 form rows. Every form row retains its
  opaque response ID, prefilled unit total, and one non-identifying annotator ID. The packet-key
  hashes remain governed by their committed manifests; the archives themselves are convenience
  copies and are not study data or labels.
- **BOUNDARY:** no label was synthesized or inferred. Two independent humans must finish the
  calibration before opening the sealed legacy packet, label the sealed and diagnostic packets
  independently, and return forms for a distinct disagreement adjudicator. Until then, all legacy
  and diagnostic outcome cells remain `PENDING`.

## 2026-09-22 — isolated current-source Unity rebuild attempt

- **STATUS:** `NOT_RUN_TO_COMPLETION / INFRASTRUCTURE_FAILURE / NO_EPISODE_COLLECTED`.
- **PURPOSE:** prepare a fresh, prospectively declared nominal land control without modifying the
  stale default player or any frozen runtime. Unity CLI 1.0.0-beta.5 invoked editor 6000.5.10f1
  against pinned CRANE `c46de4d` with an isolated output below `/tmp`.
- **RESULT:** the editor completed initial asset refresh but then made no log or output-directory
  progress for eight minutes. The process was stopped once; no player, manifest, capture, model
  call, or episode resulted. Unity changed two editor-preference files during startup; both known
  side effects were restored byte-for-byte, leaving the CRANE checkout clean.
- **EXISTING BUILD CHECK:** the already documented isolated player at
  `/tmp/crane-current-source-build-20260922` remains available. Its manifest hashes exactly to
  `1805281a0910eae84b775a2f5e43efa2b99735c4c4f662cb3c751f6b85f0fcae`, build GUID is
  `2e501629ce3544a783506153da3c0268`, and warehouse source/manifest assets match the retained
  development record. This identity check does not itself create a prospective nominal episode.
- **DECISION:** do not retry the stationary build blindly and do not substitute the stale default
  player. Human annotation and manuscript/analysis work have higher immediate paper value; a new
  land capture should resume only with a predeclared, versioned diagnostic capture contract.

## 2026-09-22 — prospectively declared nominal land diagnostic control

- **STATUS:** `COLLECTED / VALIDATED / GOVERNED / DEVELOPMENT_ONLY`; one no-retry R/P/T/N
  comparison is retained and human annotation is `NOT_RUN`.
- **DECLARATION:** `diagnostic-land-nominal-20260922-001` was declared before execution with layout
  `narrow-doorway-v1`, seed 5201, expected action success, exact player/build/source/configuration
  identities, and a one-run no-retry rule. The single declared run was retained; no outcome-driven
  rerun or scenario tuning occurred.
- **RUNTIME RESULT:** fixture QA passed and NavigateToPose succeeded in 69.619 s with 17.477 m
  displacement, 679 accepted commands, zero rejected/stale/cross-episode commands, 193 retained
  costmap observations, 66 retained plan-history records, 611 retained BT transitions, and zero
  observed recovery invocations. Real-time factor was 1.000014. The terminal BT transition was not
  observed, so whole-history completeness and an exact lifetime recovery count are not claimed.
- **INDEPENDENT REFERENCE:** the separate evaluator-side implementation reports complete requested-
  route grid coverage, no cost-253 route intersection, retained-grid connectivity from the action-
  result pose to the goal, 0.084 m maximum lateral deviation, and 17.477 m maximum forward
  progress. It does not support global no-path, a unique physical obstacle, exact planner
  consumption, or a deadline-aligned abort.
- **RESPONSE-QUALITY ITERATION:** the first post-capture checked plan rejected the false failure
  premise but omitted useful route measurements. Core commit `509544a` added bounded nominal-route
  evidence. Inspection then found duplicated uncertainty wording in the deterministic final text;
  core commit `293fdd0` removes exact duplicate alternatives. The current verified answer leads
  with action success, reports the fully covered clear route audit, 0.379 m minimum lethal-cell
  clearance, 0.084 m lateral deviation, and 17.477 m progress, while withholding universal
  obstacle-freedom and planner-consumption claims.
- **GOVERNANCE:** robot-visible capture, QA summary, checked diagnostic, and compact Unity build
  manifest are physically separate from runtime truth and the independent reference. Both trees
  are hash-manifested under `manifests/data/diagnostic-land-nominal-20260922-001.*.json`; their DVC
  objects were pushed to R2. The Unity player/build payload was not retained.
- **MODEL COMPARISON:** one fixed `gpt-5.6-sol`, low-effort, single-sample comparison used exact
  CRANE commit `c46de4d`, core commit `293fdd0`, prompt
  `diagnostic_repository_agent_dev_v2.txt`, and equal diagnostic-tool access for R/P. Three model
  calls consumed 141,607 input, 57,600 cached-input, 2,120 output, and 156 reasoning-output tokens
  over 89.195 s aggregate latency; the client reported no monetary cost or resolved backend source
  revision. P's candidate failed the conservative exact-text check, so final P equals T and
  development fallback is 7/7 questions over five clusters.
- **QUALITATIVE REVIEW, NOT A LABEL:** all methods reject the false failure premise. R reports the
  useful route evidence but incorrectly discusses a 70 s deadline; the executed XML is hash-pinned
  to 90 s. N introduces a hypothetical stricter external evaluator absent from the evidence. P/T
  retain the supported nominal measurements and correct source deadline, although P does so through
  fallback. The immutable outputs are retained for blinded review; this project-author observation
  is not a material-error judgment, effect estimate, or confirmatory result.
- **ANNOTATION BOUNDARY:** the four responses are in a blinded packet with a physically separate
  condition key. The pre-model physical reference is preserved, while the explicit annotation units
  are honestly marked as formalized after output inspection. The development inventory is now 28
  responses in seven packets over five clusters. Two-human annotation and adjudication remain
  `NOT_RUN`.

## 2026-09-22 — annotation handoff refreshed for prospective nominal packet

- **STATUS:** `PREPARED / STRUCTURALLY_VALIDATED / HUMAN_ANNOTATION_NOT_RUN`.
- **CHANGE:** both local ignored handoff bundles now include the new prospective nominal diagnostic
  packet and a separately generated blank form. Each bundle contains nine packets and 232 rows:
  six legacy calibration rows, 198 sealed legacy rows, and 28 diagnostic rows across seven packets.
- **BOUNDARY:** archive scans found no evaluator-only key, condition/model identity, raw candidate,
  verifier outcome, or fallback metadata. Forms contain only opaque response IDs, prefilled unit
  totals, blank judgments, and the recipient's non-identifying annotator ID.
- **LOCAL ARCHIVE HASHES:** annotator A
  `7ae13fed15f9c1edc289d6850d80eff647aa29ed89c84be51d86aa120399648a`; annotator B
  `883f86c39d8ef1d511d82772fd4a61e7b651d25a8ed4bad48587b7f107cbe1b3`.
  The archives remain convenience handoffs rather than governed labels; completed human forms have
  not been received.

## 2026-09-22 — ecological warehouse recovery-mechanism derivation

- **STATUS:** `IMPLEMENTED / TESTED / GOVERNED / DEVELOPMENT_ONLY`; model comparison and human
  annotation are `NOT_RUN`.
- **SOURCE EPISODE:** retained ecological warehouse episode `eco-pilot-001`; no simulator rerun,
  scene change, or outcome-driven resampling occurred. The NavigateToPose action succeeded after
  14.261 m sampled path length, 2.002 m maximum lateral excursion, and four retained complete
  recovery-leaf invocations.
- **CHECKED MECHANISM:** core commit `af25ee5` validates unique invocation IDs, exact bounded
  classifier provenance and policy hash, matching leaf start/end transitions, and the ordered
  `ComputePathToPose` failure → `NavigateWithReplanning` failure →
  `WouldAPlannerRecoveryHelp` success → system-recovery entry preceding each retained invocation.
  The checked sequence is `Spin→SUCCESS`, `Wait→SUCCESS`, `BackUp→SUCCESS`, and `Spin→SUCCESS`;
  the action eventually succeeded.
- **RESTRAINT:** the result says **at least four retained invocations** because whole-history
  completeness is not proven. It does not convert the maximum Nav2 feedback count of 16 into an
  invocation count. It withholds the physical cause of the planner failures and explicitly notes
  that delivered costmap observations do not prove the exact planner-consumed state.
- **REGRESSION:** 59 core tests pass. Focused adapter tests reproduce the four-invocation result
  from the actual governed export, reject duplicate invocation IDs, fail to `insufficient` when a
  required recovery-eligibility transition is removed, and verify feedback-count separation.
- **GOVERNANCE:** the 10,102-byte checked export hashes to
  `482c4ce2c930b52bf6b6db02b5add9c01344d414baab95cfbcae42b927888501`; source/core/adapter hashes
  are recorded in `manifests/data/ecological-warehouse-recovery-development-v1.robot-visible.json`,
  and the updated development DVC object was pushed to R2. This is an execution-mechanism and
  ambiguity case for prospective Q2/Q3 development, not physical-cause diagnosis or an
  effectiveness result.

## 2026-09-22 — predeclared warehouse recovery R/P/T/N development comparison

- **STATUS:** `RUN / RETAINED / BLINDED_PACKET_BUILT / DEVELOPMENT_ONLY`; human annotation and
  adjudication are `NOT_RUN`.
- **PREDECLARATION:** commit `357b1d8` fixed the question, one-sample/no-retry rule,
  `gpt-5.6-sol` low-effort model setting, evidence/tool parity, prompt hashes, and pre-model
  annotation units before any model output was created.
- **FAIRNESS:** R received the same robot-visible ecological export, executable recovery diagnostic,
  exact CRANE commit `c46de4d`, and core commit `af25ee5` used by P. N received captured action,
  invocation, completeness, feedback, trajectory, costmap-delivery, and source-hash facts without
  the computed transition linkage. Evaluator truth was unavailable to all methods.
- **MODEL USE:** three new calls consumed 108,119 input, 51,584 cached-input, 1,713 output, and 264
  reasoning-output tokens over 70.621 s aggregate latency. The client reported no monetary cost or
  resolved backend/source revision. No call was retried or resampled.
- **PROJECT REVIEW, NOT LABELS:** tool-enabled R independently reproduced the same lower-bound
  four-invocation sequence, planner-failure/eligibility mechanism, eventual action success, and
  physical-cause limits as P/T. N correctly retained the lower-bound count and action success but
  stated that the upstream planner/eligibility mechanism was unproven because that computation was
  ablated. This is a negative development differentiation result for P versus R, pending blinded
  human review.
- **LANGUAGE GATE:** P's fluent candidate contained the central supported mechanism and limits but
  was not byte-identical to the checked rendering. The fixed exact verifier rejected it, so final P
  equals T and development fallback is now 8/8 questions over six clusters. No repair or second
  generation was attempted.
- **GOVERNANCE:** raw result, all three call caches, a four-response blinded packet, evaluator-only
  key, reference, and predeclaration are hash-manifested. DVC objects were pushed to R2. The
  diagnostic inventory is 32 responses in eight packets over six clusters and remains too small
  and entirely unannotated for an effectiveness estimate, power estimate, or significance claim.
- **MANUSCRIPT QA:** the recovery case and current 8/8 fallback rate were added to the five-page
  short-paper draft. The rebuilt letter-size PDF was rendered page by page; no clipping, overlap,
  broken table, or unreadable reference was observed. Pending-result markers remain intentionally
  visible because human labels, protocol freeze, held-out evaluation, and statistics are `NOT_RUN`.

## 2026-09-22 — annotation handoff refreshed for recovery-sequence packet

- **STATUS:** `PREPARED / STRUCTURALLY_VALIDATED / HUMAN_ANNOTATION_NOT_RUN`.
- **CHANGE:** both local ignored annotator bundles now include the blinded warehouse
  recovery-sequence packet and separately generated blank form. Each bundle contains ten packets
  and 236 form rows: six legacy calibration rows, 198 sealed legacy rows, and 32 diagnostic rows
  across eight packets.
- **BOUNDARY:** no evaluator-only key, condition/model identity, raw candidate, verifier outcome,
  or fallback field is present. The warehouse packet was built from the pre-model reference and
  contains only opaque response IDs and allowed annotation content.
- **LOCAL ARCHIVE HASHES:** annotator A
  `d2c63b00326f8891af827da167ed6a325213946a5021717db4ceab4e57c04c79`; annotator B
  `c4fe1fd2f1bbf9e92700c5785ea5d19850aae66e4c5f548ab605dc88e81fd14a`.
  These convenience archives are not labels or governed result data; completed independent human
  forms have not been received.

## 2026-09-22 — retrospective RoboBoat retained-grid disconnection diagnosis

- **STATUS:** `IMPLEMENTED / TESTED / GOVERNED / DEVELOPMENT_ONLY / CONFIRMATORY_INELIGIBLE`;
  model comparison and human annotation are `NOT_RUN`.
- **SOURCE AUDIT:** the historical `roboboat-far-dock-global-costmap-1` fixture hashes to
  `774c3c15111a0cdc3c05130d19755459b78d2906aabe4135b215ed652f8e9a85`; its controller log
  hashes to `02ba9df100357ab7327841c723f6201db25ae0a9c2065f2c7a92f5709896c40d`.
  Reflog timestamps place the run after committed parent `7195d917` and before `7d8b77e`, but the
  then-uncommitted costmap-payload capture diff was not retained. This source gap is explicit and
  disqualifies the case from held-out/confirmatory use.
- **INDEPENDENT CHECK:** decoding the 200 by 200 grid reproduces SHA-256
  `c3d7ef6bcc1c9d40c610efc8e1c95c4e3355c80fca4551df0c84f446d175d636`. The action-result
  cell is cost 0, the requested goal cell is cost 253, and an eight-connected search reaches 37,691
  cells without finding the goal below threshold 253. Threshold checks at 254 and 255 do connect,
  confirming the boundary rather than a decoding failure. The retained log contains 23 exact
  matching Navfn failure messages before action abort.
- **CHECKED ANSWER:** the new computation reports a retained navigation-model disconnection linked
  to recorded planning failures. It withholds physical berth infeasibility, obstacle identity,
  exact planner consumption of the snapshot, wave/current causation, and global no-route claims.
  The later corrected docking success changed both goal and planning-window configuration and is
  not treated as a matched intervention.
- **REPRODUCIBILITY:** a 22,534-byte compact robot-visible export contains the hash-checked grid and
  exact parsed planner messages; a fresh-checkout recomputation reproduces the supported diagnostic
  and byte-identical checked answer without the original 2.8 MB fixture. Evaluator interpretation
  remains physically separate. Manifests are
  `manifests/data/roboboat-grid-disconnection-development-v1.*.json`.
- **VALIDATION:** 22 focused core/adapter tests pass, including corrupt-grid rejection, fail-closed
  missing-connectivity behavior, and compact round-trip equality. Both changed DVC roots were
  pushed to R2 and `dvc status --remote r2` reports synchronization. No RoboBoat scene, physics,
  controller, Nav2 configuration, or historical raw result was modified.

## 2026-09-22 — post-hoc bounded diagnostic-language verifier audit

- **STATUS:** `IMPLEMENTED / TESTED / POST_HOC_DEVELOPMENT_ONLY`; independent verifier evaluation,
  prospective use, and human scoring are `NOT_RUN`.
- **MOTIVATION:** the original exact-text gate rejected all eight P realizations, making final P
  byte-identical to T even when project review found the fluent candidate substantively aligned.
  Archived candidates, final outputs, and fallback decisions remain immutable.
- **METHOD:** core commit `2645294` adds one deep verifier module with a single interface. It parses
  exactly four sections, checks numerical claims against the typed result, applies narrow mechanism-
  specific proposition gates, rejects unsupported physical-cause wording, and permits at most one
  deterministic repair: append the complete checked evidence-ID list when citations are wholly
  absent. Partial citations and substantive repairs fail closed; no model self-check is used.
- **RESULT:** 7/8 historical fluent candidates pass after citation-only repair. The speed-masked
  candidate remains rejected because it states derived 0.026192 m and 0.187573 m quantities absent
  from its then-current checked plan and does not preserve the missing-measurement limit in the
  required section. All 24 authored adversarial mutations—unlicensed wave cause, unlicensed
  999.999 m value, and missing limits section for each case—are rejected.
- **LIMITATION:** both the verifier and mutation suite were authored after inspecting these
  development candidates. The 7/8 and 24/24 rates are regression findings, not false-positive or
  false-negative estimates and not evidence of user-facing improvement. A held-out evaluator set
  and independent human review must be declared before prospective use.
- **GOVERNANCE:** configuration, candidate/result hashes, decisions, rejection reasons, and
  mutation outcomes are retained in evaluator-only DVC storage and manifested by
  `manifests/data/diagnostic-language-verifier-development-v1.evaluator-only.json`.

## 2026-09-23 — diagnostic-study power sensitivity and independence audit

- **STATUS:** `IMPLEMENTED / TESTED / DESIGN_ONLY`; prospective protocol and held-out collection
  remain `NOT_FROZEN` / `NOT_RUN`.
- **METHOD:** `analysis/plan_diagnostic_power.py` exactly enumerates the unconditional power of a
  two-sided paired sign/McNemar test at alpha 0.05, with one primary binary endpoint per independent
  scenario instance. Four regression tests cover exact-tail symmetry, monotonicity at the design
  points, reproducible minimum counts, and the non-observed-effect status.
- **SENSITIVITY:** under the declared smallest practically meaningful planning pattern—20% P-only
  success, 5% R-only success, net +15 points—92 independent clusters reach 80% power and 119 reach
  90%. A 96-cluster target gives 81.97%; 40 gives only 36.37%. These are assumptions, not estimates
  from unblinded pilot review. Large, smaller, and symmetric-discordance scenarios are also retained.
- **INDEPENDENCE FINDING:** source inspection confirms the current proving-ground requested seed is
  recorded in the configuration hash but does not alter fixed manifest geometry. Seed-only reruns
  cannot count as independent scenarios. Protocol freeze therefore requires a genuinely varied
  geometry source and a throughput check; no collection target is represented as currently met.

## 2026-09-23 — v4 land-catalog runtime qualification and failed disconnection induction

- **STATUS:** `DEVELOPMENT_ONLY / TWO VALID CONTROLS / FAILED_MECHANISM_INDUCTION / NOT_GOVERNED`.
  These five runs are not confirmatory episodes and are not part of the frozen F/G/H cohort.
- **RUNTIME:** Unity `6000.5.10f1`, CRANE parent `c46de4d` plus the then-uncommitted v4 catalog
  implementation, and catalog SHA-256
  `4916851c02448a12b1279b74a376f94a07635b64851144a5fcd123a165afff92`. The isolated player is
  retained only under `/tmp/crane-land-v4-player`; it is deliberately not added to Git or DVC.
- **STRUCTURAL QUALIFICATION:** representative grid, detour, and nominal layouts passed
  `STRUCTURAL_PASS`, `PHYSICS_PASS`, `SENSOR_PASS`, `HEADLESS_PASS`, and `EXPLANATION_READY`.
  Seven Unity EditMode tests and the contemporaneous Python manifest/contract suite passed.
- **FAILED INDUCTION 1 — OPEN 8 M ARENA:** the expected-abort run instead reached the client
  deadline at 100.028 s after 24.990 m sampled path length. Its lateral range was
  -0.815–+5.004 m and 97 planning records were retained; the robot routed outside the open rear
  boundary. This motivated closing both longitudinal ends, not an episode exclusion.
- **FAILED INDUCTION 2 — CLOSED 8 M ARENA:** the action again reached the client deadline at
  100.011 s after 25.413 m sampled path length, lateral range -0.791–+3.014 m, 97 planning records,
  and maximum feedback recovery count 1. Successful replanning continued.
- **FAILED INDUCTION 3 — CLOSED 5 M ARENA:** jointly observing the side boundaries and cross-wall
  still did not establish planner-grid disconnection. The action reached the client deadline at
  100.017 s after 23.749 m sampled path length, lateral range -0.614–+0.676 m, 96 planning records,
  and maximum feedback recovery count 2. The run oscillated/reversed while planners continued to
  return paths. Offline canonical-raster disconnection is therefore not a valid label for the
  actual Nav2 mechanism.
- **POSITIVE BEHAVIORAL CHECKS:** `diagnostic-development-connected-detour-001` succeeded in
  76.110 s with 17.569 m endpoint displacement, 19.045 m sampled path length, lateral range
  -1.401–+1.288 m, 72 planning records, 655 BT transitions, 285 delivered costmap observations,
  and zero feedback recoveries. `diagnostic-development-nominal-clear-route-001` succeeded in
  69.111 s with 17.477 m endpoint displacement and sampled path length, zero lateral deviation,
  67 planning records, 610 BT transitions, 255 costmap observations, and zero recoveries.
- **DISPOSITION:** stop geometry tuning. The eight stable development blockage identities are
  retained as `development-calibration / failed-induction-calibration`; the 48 unrun confirmatory
  blockage identities were removed. The regenerated candidate catalog contains 48 prospective
  connected-detour instances and 24 nominal controls, not 96 qualified diagnosable instances.
  Its current SHA-256 is
  `c2603491c16b99ba007085237097fc0cd66ee2453d1b9e4e1fc7f490bd1a0f8a`. Because the runtime
  summaries remain under `/tmp`, governance and fresh-checkout reproduction are still `NOT_RUN`.
