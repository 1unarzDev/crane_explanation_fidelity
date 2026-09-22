# Experiment Log

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
