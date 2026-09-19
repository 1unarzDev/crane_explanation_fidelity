# Experiment Log

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
