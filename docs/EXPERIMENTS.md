# Experiment Log

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
