# Decision Log

## 2026-09-23 — retain bounded delivered-plan geometry for path-decision explanations

- Decision: extend the shared Nav2 fixture's existing `planHistory` records with a content hash,
  planned length, and absolute/signed lateral deviation from the requested start--goal line. Retain
  only these bounded summaries, not every path pose. Hash the executed fixture observer itself in
  the additive diagnostic runtime manifest.
- Evidence: current-source development episode `diagnostic-land-dev-002` retained 70 delivered
  global plans but only their endpoints and pose counts. The costmap and odometry supported a
  restricted direct route plus 1.036 m trajectory deviation, yet the discarded path geometry
  prevented an evidence-backed statement that Nav2 actually published a changed route.
- Alternatives: infer a route decision from odometry alone; retain every pose from every plan; add
  a new perception stack; or leave the answer failure-oriented. Odometry cannot establish a
  planner output, full paths add avoidable volume, perception does not repair this provenance gap,
  and the existing answer under-expresses a supported navigation decision.
- Validity boundary: a delivered `/plan` summary establishes what reached the fixture, not that the
  controller consumed it or that a particular costmap snapshot or physical object caused its
  shape. Evaluator layout identity remains separate. Any explanation must preserve those limits.
- Expected RQ impact: enables a compact, parity-compatible physical path-comparison input for new
  Q1/Q2 without giving P privileged evaluator geometry. It may still yield no P-over-R advantage;
  that is an admissible result.
- Revisit condition: replace the summaries with fuller time-aligned path retention only if a
  concrete diagnostic question cannot be independently evaluated from the bounded measurements.
- Outcome/amendment after the first qualification run: `diagnostic-land-dev-003` produced useful
  summaries, but an independent evaluator could not recompute them because the underlying
  delivered poses were absent. That run is retained as partial instrumentation evidence. The
  revisit condition was therefore met immediately: future development captures also retain the
  delivered plan poses in DVC-only robot-visible data, while the compact summaries remain the
  method-facing default. This does not authorize rerunning or replacing `dev-003`.

## 2026-09-23 — qualify command-to-motion diagnosis without naming the hidden intervention

- Decision: retain a blind robot-visible export from the time-resolved instrumentation rerun and
  diagnose only a sustained delivered-command/measured-motion discrepancy. Do not expose the
  intervention-coded acquisition identifier or evaluator truth, and do not label the mechanism as
  motor failure, slip, collision, obstruction, or another unique cause.
- Evidence: five initial command-active windows calibrate a 0.2597 m/s median measured response.
  The earliest sustained low-response interval spans 7–17 s with a 0.800 m/s median command and
  0.000 m/s measured planar response. Two FollowPath failures, two hash/source-qualified Wait
  invocations, a third attempt, and the abort are retained. An independent implementation
  reproduces the diagnostic values and the leakage/source-hash QA passes.
- Alternatives: use command-derived NavigateToPose feedback as motion, reveal the evaluator hold,
  assign a unique physical cause, or treat the instrumentation rerun as a new episode. Each would
  confound signal semantics, leak truth, overclaim causality, or inflate effective sample size.
- Study effect: this qualifies the second planned mechanism and improves the final answer beyond
  abort/recovery narration. A matched time-resolved nominal rerun now passes `not_triggered` and
  false-premise handling. This does not establish P superiority; ambiguous evidence, fair R/P/T/N
  calls, blinded labels, and independent collection remain.

## 2026-09-22 — close environment/platform development at three ecological pilot inputs

- Decision: close the submission environment workstream with exactly three development-only,
  current-qualified inputs: warehouse temporary-enclosure recovery, complete blockage, and the
  corrected S-turn. Preserve their separated exports, evaluator truth, QA summaries, and source
  provenance in governed DVC storage. Begin information-parity explanation evaluation and blinded
  annotation rather than adding or tuning environments.
- Evidence: all three pass their declared route, headless, and explanation-readiness gates with
  exact scenario/configuration hashes. Current source-qualified `dynamic-gate-v1` attempts did not
  reproduce its historical recovery-success result, and no current qualified U-trap export exists.
  The exporter now retains bounded recovery-classifier provenance and marks scan/costmap summaries
  delivered but not proven consumed.
- Boundaries: `dynamic-gate-v1` is `HISTORICAL_CALIBRATION_ONLY`; its successful historical result
  and negative current calibrations remain intact. U-trap is excluded, not relabeled. No Unity
  builds are retained, no new perception stack is added, and explanations must withhold physical
  obstacle causation and internal controller consumption.
- RQ impact: these artifacts support a small ecological information-parity pilot, not an effect
  estimate or confirmatory expansion. Independent episode collection, blinded annotation,
  statistics, figures, and manuscript work now dominate submission value.
- Revisit: no environment expansion before submission unless a manuscript-critical validity gap
  cannot be addressed from the retained land artifacts or the separately owned RoboBoat workstream.

## 2026-09-21 — retain and stratify an operator-reported load-balancer source change

- Decision: retain all sealed calls, preserve the frozen paired F-versus-G primary analysis, and
  record the load-balancer source change as an operational batch boundary rather than silently
  treating the route as immutable. Do not rerun or exclude any response. If both temporal strata
  are sufficiently populated, report a pre/post-boundary sensitivity analysis; otherwise report
  the boundary descriptively. Amendment 6 fixes this treatment before `pn-0025`.
- Evidence: the operator reported changing the source used by the load balancer. The local Codex
  configuration modification time falls after every `pn-0021` call and before every `pn-0022`
  call; `pn-0022` through `pn-0024` therefore postdate the observable client boundary. The retained
  requests still report `gpt-5.6-luna`, low reasoning, `codex-cli 0.155.1`, and the same adapter.
- Limits: a client timestamp does not prove when server source was deployed or that the effective
  backend/model changed. The client does not expose a deployed source revision or resolved backend,
  so amendment 6 records the operator report, an SHA-256 fingerprint of non-secret route settings,
  and the uncertainty. It does not claim a causal load-balancer effect.
- Validity: F and G remain paired within every episode and use the same route, model alias, effort,
  and retry budget. A temporal implementation change could nevertheless interact with condition,
  so it is a reportable heterogeneity threat. The frozen primary estimand, inclusion rules, prompts,
  verifier, and minimum sample size are unchanged.

## 2026-09-21 — regenerate annotation pairs after an incomplete DVC publication

- Decision: retain the keyless `sealed-claude-v1` packet as unusable audit evidence and generate
  fresh v2 packet/key pairs from the unchanged result envelopes: 126 primary responses over 21
  episodes and 54 Claude responses over nine episodes. Move the surviving historical Luna key from
  `model_outputs` into evaluator-only storage. Never reconstruct a missing HMAC secret.
- Evidence: `annotation_keys.dvc` referenced a two-file directory object absent both locally and on
  R2. `scripts/dvc_r2_sync.sh` named only the original six pointers, so the new seventh pointer was
  refreshed and committed but never uploaded. A guarded pull failed with DVC's missing-files error.
- Correction: add the evaluator-only annotation-key pointer to every sync operation and test that
  refresh and network scripts name the same seven governed roots. Each new packet/key pair was
  created together and its packet hash and entry count were independently verified.
- Validity: packet regeneration changes only opaque HMAC response IDs and shuffle order. It does
  not change or inspect any response, condition, evidence, label, model call, or study hypothesis.
  Annotation and sealed effect estimation remain `NOT_RUN`.

## 2026-09-20 — retain failed model calls outside the answer cache

- Decision: a model call that produces no parsed answer is never written to the content-addressed
  answer cache. It is retained under `_retained_failed_calls/` in the same cache root, and the
  adapter raises. A cache hit is validated before it is returned, so a stored failure or a violated
  read-only workspace contract is stated rather than replayed. Recorded as arm amendment 3.
- Evidence: the sealed Claude batch stopped at `pn-0004 failure-cause`. Its condition-H call
  returned a Claude Code CLI envelope with `is_error`, `terminal_reason = api_error`,
  `api_error_status = 429`, and an account spend-limit notice in place of a response. The adapter
  cached that envelope and the resumed batch then failed while reading the absent answer, so the
  arm could never have reached 18 envelopes no matter how often it was resumed.
- Alternatives: delete the record, which destroys evidence that a paid provider call occurred;
  leave it cached, which reports a quota notice as a condition-H response and strands the arm at 17
  of 18 envelopes; or hand-write the missing envelope, which fabricates a result.
- Why this is not resampling: the frozen single-sample/no-retry rule protects against resampling an
  answer or repairing language. The 429 call produced no answer at all. No answer text was
  inspected, compared, or selected against, and a re-call cannot be conditioned on content that does
  not exist. Re-calling after a transport failure is the same act as making the call the first time.
  A successful call remains cached and is still never re-called.
- Validity: no prompt, model, effort, episode, condition, evidence hash, or schema delivery changed,
  and no frozen file was touched; `analysis/test_freeze_integrity.py` still verifies every frozen
  hash. The failed call's real provider cost and tokens are reported separately and are excluded
  from response counts, specificity, and every scored summary. Unlike amendments 1 and 2, this
  correction was made during sealed collection rather than before it.

## 2026-09-20 — define replication around a provider-neutral call contract

- Decision: treat model configuration, provider adapter, agent harness, and explanation condition
  as separate identities. New model families implement the normalized model-call contract and run
  in separately declared arms; evidence, reasoning, verification, and scoring remain provider
  neutral. Rename the living arm documentation from a Claude-specific page to
  `MODEL_FAMILY_REPLICATION.md`, with Claude retained as the first worked instance.
- Evidence: the Claude work already emits the same `crane-explain-model-call/v1` schema and reuses
  frozen F/G/H logic, while its different tool surface and read-only enforcement show why “same
  model task” does not mean “same harness.” A Claude-only architecture would obscure both reuse and
  the harness confound.
- Alternatives: embed Claude throughout the core study docs; generalize every frozen runner now;
  or keep a monolithic Claude narrative. The first makes the method vendor-specific, the second
  breaks hash-frozen artifacts for no scientific gain, and the third duplicates architecture,
  protocol, results, and operations in one file.
- RQ impact: supports honest RQ4 sensitivity analysis without claiming cross-family equivalence or
  inflating episode count. A future local, API, or CLI model can replicate the arm by adding an
  adapter and declaration rather than changing the trust boundary.
- Validity: provider adapters may have different system prompts, tools, sandboxes, telemetry, and
  schema facilities. Every arm must publish a capability profile and report combined
  model-family-plus-harness sensitivity unless those factors are experimentally controlled.

## 2026-09-20 — reject the lower Claude tier and select claude-sonnet-5

- Decision: use `claude-sonnet-5` at low effort for the secondary Claude arm; do not adopt
  `claude-haiku-4-5` despite its lower tier. Fixed before the first sealed Claude call and recorded
  as arm amendment 2.
- Evidence: under the predeclared four-margin rule over 48 development calls, Haiku recorded 7
  material errors out of 8 in condition F against Sonnet's 1, with aggregate specificity 117/156
  versus 135/156. Substantive coverage was 1.0 for every condition in both settings. Haiku failed
  the per-condition margin outright and is ineligible; Sonnet met every margin.
- Validity: Haiku's errors were concentrated almost entirely in F, the strong repository-agent
  baseline, so adopting it would have inflated the F-versus-G contrast the arm exists to examine.
  That is the model-strength confound the control exists to prevent. Haiku was also the more
  expensive setting, at 8.75M input tokens against 2.08M, so no cost argument favours it either.
- Limitation: the control's sixteen G responses are byte-identical to the frozen arm's, so it
  discriminated only through F and H, and its single annotator was an unblinded automated session.

## 2026-09-20 — correct Claude-arm schema delivery to the out-of-band flag

- Decision: deliver the answer schema through the Claude Code CLI's `--json-schema` flag rather
  than through an adapter-appended prompt suffix; retire the 16 calls made under the suffix
  revision and re-run the whole development control under the corrected adapter.
- Evidence: the suffix revision failed on its own terms. Condition F of `e021 failure-cause`
  answered in prose and could not be parsed, and appending text altered a prompt the freeze pins by
  hash. `--json-schema` is the direct analogue of the Codex CLI's `--output-schema`, so the frozen
  prompt now reaches the model byte-unchanged in both arms.
- Validity: no sealed Claude call, annotation, or model selection existed when the defect was found,
  so no result could have influenced the correction. `schema_delivery` is part of the
  content-addressed request, so the change invalidates the old cache keys instead of silently
  reusing stale answers. Retired results and their cache records are retained, never deleted.
  Recorded as `manifests/study/provenance-claude-replication-arm-v1-amendment-1.json`.

## 2026-09-20 — add a secondary Claude replication arm rather than amend the frozen study

- Decision: re-run F/G/H over the nine retained sealed episodes with a Claude model as a separately
  reported secondary arm, in physically separate output, cache, manifest, and annotation
  namespaces. The frozen Luna study remains the primary record and is not amended.
- Evidence: the sealed calls were made from a sandboxed Codex CLI session that is unavailable on the
  current host, and new capture is impossible here (arm64 macOS, no Linux Unity player, no running
  Docker daemon). Every input the model arm needs is retained, so the arm re-runs over
  byte-identical evidence; the batch driver refuses to run unless each episode's
  runtime-presentation and parity-audit hashes match the frozen result exactly.
- Alternatives: amend the freeze to change its model, which would rewrite a study whose calls are
  already sealed; or skip the arm, which would leave the host unable to contribute anything.
- Validity: the arm adds no independent episodes. The same nine episodes under two model families
  are not eighteen clusters and must never be pooled. Model family and agent harness are
  confounded, so an arm difference cannot be attributed to model weights. No frozen file changed;
  `analysis/test_freeze_integrity.py` verifies all 32 frozen hashes in amendment order.
- RQ impact: provides descriptive sensitivity evidence for RQ4 — whether the F/G/H contrast
  survives a change of model family — and nothing more. It does not relieve the unmet 40-episode
  minimum.

## 2026-09-20 — run the arm's own model-strength control instead of inheriting the frozen one

- Decision: repeat the predeclared model-strength procedure within the Claude arm, comparing
  `claude-sonnet-5` against `claude-haiku-4-5` at low effort over the same four development
  episodes the frozen control used, and fix the selected setting before the first sealed Claude
  call.
- Evidence: the frozen design forbids giving G a stronger model than its baselines, and satisfied
  that by a predeclared four-episode rule rather than by assertion. Inheriting Luna's selection
  would carry no information about the Claude tiers.
- Validity: eligibility is evaluated strictly within the Claude arm, so no cross-family equivalence
  is claimed. Selection uses development episodes only. The single annotator is an unblinded
  automated assistant session, which is weaker than the blinded dual annotation the sealed analysis
  requires and is recorded as a limitation.

## 2026-09-19 — correct the exact pinned expected-status contract

- Decision: supersede amendment 4's incomplete variable-name correction with the exact pinned
  fixture contract `CRANE_EXPECTED_NAV_STATUS`; retain `pn-0002` and `pn-0004` without rerun.
- Evidence: direct source inspection shows `run_nav2_controller_fixture.sh` reads
  `${CRANE_EXPECTED_NAV_STATUS:-succeeded}`. Amendment 4 used `CRANE_EXPECT_NAV_STATUS`, so the
  terminal `pn-0004` capture again defaulted to expected success. `pn-0003` did not expose this
  because its predeclared outcome was success.
- Validity: only the evaluator-side outer summary expectation is affected. Capture dynamics,
  intervention, Nav2 result, prompts, and model behavior are unchanged. The regression test now
  cross-checks the wrapper string against the pinned fixture source. No `pn-0004` model calls or
  annotations existed when discovered.

## 2026-09-19 — retain pn-0002 after expected-status wrapper mismatch

- Decision: retain the single `pn-0002` capture without rerunning it, correct the frozen wrapper's
  environment-variable name for subsequent episodes, and apply the pre-existing inclusion validator
  to its retained artifacts.
- Evidence: the split predeclared `pn-0002` as `terminal_recovery_abort`, and the capture contains an
  `aborted` NavigateToPose result, two recoveries, populated costmaps, and the scheduled unreleased
  mobility hold. The outer summary alone expected `succeeded` because the wrapper exported
  `CRANE_EXPECT_NAVIGATION_STATUS`; the pinned fixture reads `CRANE_EXPECT_NAV_STATUS`.
- Validity: the mismatch did not change scene dynamics, intervention, ROS capture, Nav2 behavior, or
  terminal result. No `pn-0002` model calls or annotations existed when found. Preserve the
  incorrect outer flag as retained evaluator metadata and disclose amendment 4; never rerun the
  episode to obtain a cleaner flag.

## 2026-09-19 — distinguish sealed model calls from embedded smoke outputs

- Decision: model-artifact manifests report F/G/H as the model-evaluated conditions and label the
  inherited A–E envelope entries as deterministic smoke outputs. A–E remain `NOT_RUN` as frozen
  model conditions until their dedicated runner is executed.
- Evidence: each `pn-0001` question envelope contains eight condition entries but references only
  three physical model calls, one each for F/G/H. The initial manifest builder incorrectly promoted
  all envelope entries to evaluated conditions; its hash audit was valid but its semantic accounting
  was not.
- Validity: the correction changes only manifest construction and adds no calls, retries,
  annotations, evidence, prompt, output text, or verifier behavior. The invalid uncommitted manifest
  was replaced, and a regression test now requires six model outputs and ten smoke outputs for a
  two-question F/G/H batch.

## 2026-09-19 — label sealed result envelopes without rerunning calls

- Decision: add a `SEALED_TEST` result-envelope status option after pn-0001's first three calls;
  preserve the original mislabeled result and do not rerun it.
- Evidence: the runner's hardcoded development label affects metadata only. Cache keys, prompts,
  evidence, answer text, model, verifier, and call count are unchanged.
- Validity: three sealed calls and no annotations existed. Record the amendment before the remaining
  calls and treat the pn-0001 recovery result's legacy status as a documented metadata limitation.

## 2026-09-19 — correct leakage-gate false positive before model calls

- Decision: allow the exact audit field `evaluator_truth_available_to_methods=false`; continue to
  reject it when true and reject all evaluator payload keys/paths. Revalidate retained `pn-0001`
  without rerunning it.
- Evidence: the frozen gate rejected only two parity-audit negative attestations after every other
  inclusion check passed. They disclose absence, not evaluator truth.
- Validity: one sealed capture existed, but zero sealed model calls or annotations existed. Record a
  second amendment and do not inspect model output before resealing the gate.

## 2026-09-19 — pre-collection freeze amendment for sealed execution

- Decision: before collecting `pn-0001`, amend the operational freeze to select physically separate
  `data/*/final/` roots and state constant fixture/action timing. Execute split rows through one
  deterministic wrapper; do not alter the scientific hypothesis, questions, balance, or stopping
  rule.
- Evidence: the first dry execution audit after freeze found `run_land_capture.sh` still hardcoded
  `dev`, while the split specified varying scenario values but omitted common duration settings.
- Validity: zero sealed episodes or answers existed when found. Preserve the original freeze
  manifest, record changed-file hashes in an amendment, and require the amended commit in every
  runtime manifest.

## 2026-09-19 — seal known runtime configuration before final collection

- Decision: final captures must retain a hash-checked robot-visible runtime manifest with the actual
  Nav2 parameter file, BT XML, harness scripts, container image digest, installed package versions,
  checkout commits, player hashes, and effective scene/command/LiDAR launch settings. The parity
  presentation exposes this same identity to F/G/H.
- Evidence: every material F error in the four-episode pilot inferred that
  `nav2_land_fixture.yaml` governed the run. The harness actually knows and fixes that path; omitting
  it in final collection would manufacture an avoidable evidence gap.
- Alternatives: preserve the omission to keep a discriminative benchmark; add the YAML only to G;
  or treat repository proximity as sufficient. Those respectively bias the study, create privileged
  information, or violate the central provenance claim.
- RQ impact: strengthens RQ4 and may reduce the favorable F–G pilot effect. That is scientifically
  necessary. The remaining discriminative question is whether methods avoid promoting configured
  progress checking into the actual failure cause without a controller error payload.
- Risk/revisit: the current player build still lacks a proven embedded source commit, and package
  versions do not prove source-to-binary rebuilding. Keep those limits explicit rather than adding a
  native hook or claiming more provenance than retained.
- Validation: e041 was retained as an invalid pre-execution CLI-boundary failure. The separately
  predeclared e042 passed exact-hash, Git-object, launch-contract, leakage, and F/G/H parity checks.
  Freeze this manifest design for the main provenance study; changes require a documented amendment.

## 2026-09-19 — select gpt-5.6-luna low for matched F/G/H collection

- Decision: use `gpt-5.6-luna` at low reasoning for every F/G/H condition in the main provenance
  study; retain `gpt-5.6-sol` only as the stronger-model development control.
- Evidence: under the precommitted four-episode rule, Luna has F/G/H errors 3/0/1 versus Sol 4/0/0,
  equal aggregate specificity (140/156), and full coverage. It passes the one-response condition
  margin, 10-point specificity margin, overclaim margin, and coverage floor. Across 24 calls Luna
  used 2,253,937 versus 2,467,391 input tokens, 18,484 versus 23,252 output tokens, and 625.923 versus
  891.518 seconds aggregate latency.
- Alternatives: retain Sol by default; choose Luna solely because it is a lower tier; route source
  questions to Sol. The first ignores a passed predeclared control, the second would lack a quality
  gate, and the third adds condition/model confounding unsupported by this pilot.
- RQ impact: controls model strength for RQ4 and reduces the cost of scaling independent episodes
  without giving G a stronger model than F/H.
- Risk/revisit: only four episodes and one unblinded annotator were used; monetary cost was not
  reported, and the result does not establish equivalence. Revisit only for a documented provider
  availability failure before freeze, not in response to unfavorable sealed outputs.

## 2026-09-19 — gate F/G/H calls on a shared runtime information audit

- Decision: derive one evaluator-truth-free runtime presentation from the raw passive capture,
  retain raw-record traceability for each field, give H and G the same structured runtime facts,
  and refuse calls unless every question-relevant unit is also derivable by F from raw evidence.
  Runtime-to-source links, bounded spans, checked plans, and verification remain G's treatment.
- Evidence: the first e037 pilot gave F full goal/result/feedback/capture files, H a reduced episode,
  and G a narrower checked plan. Its F/G/H differences therefore could not be interpreted solely as
  provenance/checking effects.
- Alternatives: downsample F's raw capture; give every condition a checked plan; or accept coarse
  episode-level parity. Those choices would weaken the repository-agent baseline, erase the tested
  treatment, or leave privileged-information ambiguity unresolved.
- RQ impact: directly strengthens RQ4 and makes later F/G/H comparisons auditable. It also exposes
  representation burden rather than hiding it: F remains a realistic raw-log agent, while H
  controls for structured runtime access.
- Risk/revisit: explicit structured limitations may help H more than an unaudited raw agent; that is
  intentional for the H control but must be reported. Freeze the question-unit registry only after
  a multi-episode development pilot shows it covers all planned families.

## 2026-09-19 — make runtime-to-source provenance the central novelty

- Decision: treat runtime/physical evidence and exact source/configuration evidence as separate
  linked planes. Add strong generic repository-agent baselines F/H and make provenance-linked
  checked method G the central novelty comparison. Maintain this direction in the canonical
  architecture, study, benchmark, research, environment, and decision documents.
- Evidence: the 18-episode development result has B at 0/109 material errors and D at 1/109, so the
  current evidence does not support D superiority. Structured logs plus checking alone are also too
  close to prior provenance/planning work. Exact runtime-to-source correspondence is both a sharper
  contribution and an auditable distinction from “let a coding agent inspect the repository.”
- Alternatives: continue collecting for A–E; deny source access to baselines; dump whole repositories
  into all prompts; build a universal provenance graph. These either fail to test the novelty,
  weaken the baseline, or consume deadline-critical collection time.
- RQ impact: introduces RQ4 and shifts practical robustness to RQ5 while retaining RQ1–RQ3. The
  first checkpoint is one complete A–H provenance-linked pilot, not hundreds of new episodes.
- Validity risk: provenance could merely add privileged information or extra model calls. F/G/H
  must use the same robot-visible episode, exact checkout, matched model/effort, no evaluator truth,
  no resampling, and explicit cost/latency accounting.
- Revisit: after the first pilot, inspect actual F/G/H disagreements before expanding schema or
  resuming broad collection.

## 2026-09-19 — stop tuning static blockers for terminal recovery exhaustion

- Decision: do not spend further instances tuning full/partial static blocker width or distance to
  obtain a terminal abort. Retain e029/e030 as deadline mismatches and specify a deterministic
  software-level terminal mechanism before collecting that family again.
- Evidence: both predeclared partial-blocker instances produced healthy 35 s navigation runs with
  84/85 costmap observations but reached the client deadline. E025 behaved the same with a full
  blocker, while earlier e004/e009 aborts have not reproduced reliably across geometry variants.
- Alternatives: keep searching geometry/timing after every outcome; relabel deadlines as terminal
  recovery exhaustion; omit invalid instances.
- RQ impact: improves internal validity and prevents outcome-driven scenario selection for RQ2–RQ4.
- Validity risk: deterministic injection can reduce ecological realism, so evaluator-only fault
  identity must remain hidden and the paper must distinguish software mechanism from physical cause.

## 2026-09-19 — stop reference-environment expansion and resume balanced collection

- Decision: treat the TurtleBot3, F1TENTH, PX4, and Clearpath reference-environment suite as
  sufficient for the paper's current claims. Use the root-relative graphics-free validator for
  regressions, but spend subsequent engineering time on independent episodes and annotation.
- Evidence: PX4 Walls and Clearpath Pipeline both passed current headless geometry/physics/semantic
  checks. In the predeclared e024–e027 batch, e024/e027 added valid success/cancellation clusters,
  while e025 missed its terminal-outcome family and e026 failed the costmap quality gate.
- Alternatives: add another Gazebo conversion, import AWSIM/Flightmare art, or tune/rerun the two
  excluded instances.
- RQ impact: the valid runs increase the development sample to 11 clusters; retaining both invalid
  runs protects the stopping rule and makes scenario-generation failure visible.
- Validity risk: the sample is still unblinded and underpowered, and added instances repeat existing
  mechanisms. The next collection must continue balancing families rather than counting variants as
  new mechanisms.

## 2026-09-19 — stop expanding the mobility-hold family and distinguish physical model calls

- Decision: after e021–e023, collect the next batch across existing terminal-exhaustion,
  unblocked-success, planning-failure, and client-cancellation families instead of adding more
  mobility-hold timing variants. Model manifests distinguish unique request keys from separately
  retained physical call artifacts.
- Evidence: e021–e023 all passed but reproduce the same FollowPath-failure → guard-success → Wait
  mechanism already present in e019. The cumulative audit also found two request keys independently
  materialized in both cache roots with identical final text but different latency metadata.
- Alternatives: treat every seed as mechanism diversity; continue recovery-success collection only;
  count one file per cache key and silently discard duplicate physical records.
- RQ impact: improves scenario-family balance for RQ1–RQ4 and makes model-call provenance auditable.
- Validity risk: nine development clusters remain unblinded and underpowered; the next batch must
  remain development data until prompts, rubric, verifier policy, and final split are frozen.

## 2026-09-19 — retain recovery-success through bounded mobility loss, not obstacle timing

- Decision: use a predeclared evaluator-only planar mobility hold as the controlled progress-failure
  mechanism for the recovery-success family. Do not expose the intervention identity or timing to
  explanation conditions.
- Evidence: obstacle removal/window runs e016/e017 stayed in FollowPath with zero recoveries. In
  e019, the 12 s hold produced a recorded FollowPath FAILURE, recovery-guard SUCCESS, one successful
  Wait, a second FollowPath start, and terminal task success after release.
- Alternatives: keep tuning blocker timing; weaken the progress checker; inject BT transitions;
  call the intervention the physical cause in model-visible evidence.
- RQ impact: adds the missing recovery-success software mechanism for RQ1–RQ4 while preserving the
  required distinction between captured execution and evaluator-only fault truth.
- Validity risk: this is synthetic fault injection, not evidence of a real hardware fault. Vary
  independent seeds/start-goal instances and report the mechanism narrowly.

## 2026-09-19 — make harness boundaries transient-local and reject incomplete e018

- Decision: publish and subscribe to explicit harness events with reliable transient-local QoS and
  depth 20. Exclude e018 because its accepted-goal event was lost; use only the predeclared e019
  replication with matching goal/result IDs.
- Evidence: the volatile fixture publisher emitted identity/goal immediately after startup, before
  DDS discovery completed, while the later result arrived. e019 retained two identities, one goal,
  and one matching result after the QoS repair.
- RQ impact: prevents capture startup races from masquerading as incomplete robot evidence or from
  changing recovery-count completeness across benchmark conditions.
- Validity risk: transient-local replay can retain prior publisher samples while that publisher is
  alive; opaque run/episode/goal IDs and one-publisher-per-fixture checks remain mandatory.

## 2026-09-19 — distinguish intermediate failure from terminal task failure

- Decision: a successful task outcome rejects a failure premise only when no relevant execution
  failure is recorded. If FollowPath failed before later success, report both scopes and continue
  withholding physical cause.
- Evidence: retained e019 C/D/E answers incorrectly treated eventual success as contradicting an
  explicit intermediate FollowPath FAILURE. The error is present in deterministic E, identifying a
  checked-planner defect rather than an LLM-only failure.
- RQ impact: preserves negative development evidence while correcting future selective answers.
- Validity risk: failure-event kinds must remain explicitly enumerated and tested; do not infer a
  failure merely from generic temporal anomalies.

## 2026-09-19 — use the differential base for controlled corridor collection

- Decision: run the controlled corridor's powered success/recovery study on CRANE's validated
  TurtleBot3 Waffle-class differential base. Retain the Ackermann rover and F1TENTH environment as
  explicit embodiment-specific benchmarks rather than continuing to tune the corridor around them.
- Evidence: three longer unblocked Ackermann goals and one timed-removal run stalled or timed out;
  increasing minimum approach velocity did not restore success and one run accumulated 1.08 m of
  lateral drift. Under the same capture/Nav2 architecture, predeclared e015 reached a 2 m goal with
  a successful terminal result, populated costmaps, complete capture boundaries, and zero recovery.
- Alternatives: keep extending deadlines; force minimum throttle; directly manipulate pose; modify
  the planner/controller until this one corridor succeeds; abandon recognizable platforms.
- RQ impact: provides a working path to independent recovery-success episodes while keeping actual
  execution evidence grounded in platform semantics. The representation and verification methods
  remain unchanged.
- Validity risk: switching embodiments after development calibration can confound comparisons if
  mixed indiscriminately. Freeze and split scenario families by platform, and never count e015 as
  final or retroactively relabel the failed Ackermann runs.
- Revisit: only if an Ackermann-valid controller/path pairing is itself a predeclared research
  condition and the work displaces no required differential data collection.

### Recovery-scenario follow-up

The differential base passed an unblocked short-goal smoke, but e016/e017 showed that removing a
partial blocker or presenting a two-second full blocker window did not cause the retained RPP path
to enter the progress-recovery branch. Both captures stayed in FollowPath until the client deadline
with zero recovery entries. Freeze these negative calibrations and stop timing searches. The next
recovery-success mechanism must have an independently testable software/physics contract (for
example, a bounded mobility interruption), and its evaluator-only intervention must not be exposed
as robot-visible cause evidence.

## 2026-09-19 — record binary provenance separately from checkout provenance

- Decision: every new land capture records SHA-256 and byte size for the exact player executable,
  embeds and hashes its build manifest, and records the checkout commit/dirty state separately.
- Evidence: the existing `crane-build-manifest-v1` contains Unity, package, scene, and asset hashes
  but no source commit. The current checkout may advance without rebuilding the local player.
- Alternatives: treat the current gitlink as the binary source; stop all collection until Unity
  licensing recovers; rely on file modification time.
- RQ impact: prevents configuration/source provenance from being misstated and lets valid static
  scenarios continue while the binary remains content-addressed.
- Validity risk: the old binary's source commit remains unproven. Its artifact identity is exact,
  but it cannot support source-level reconstruction beyond the embedded manifest.
- Revisit: add a source commit and dirty-diff hash to the build manifest at build time; require that
  stronger provenance for final collection after Unity licensing is restored.

## 2026-09-19 — Clearpath pipeline uses an offline, generated import boundary

- Decision: resolve and hash Clearpath SDF resources offline; keep the 34 MB generated asset tree
  out of Git; construct canonical collision and visual presentation separately in Unity.
- Evidence: pipeline has 10 terrain geometry nodes, render-only water, and a separate base station.
  Unity imports DAE but not STL locally, so the collider STL is deterministically converted to OBJ.
- Alternatives: runtime SDF support; committing upstream binaries; approximating terrain with
  arbitrary primitives; treating the entire scene as one collider.
- RQ impact: adds recognizable outdoor failure geometry and semantic IDs without changing what is
  robot-visible to explanations.
- Risk: no native Gazebo cross-check, Nav2 traversal, spawn/goal calibration, or corridor-width
  acceptance yet; source asset provenance beyond the repository license still merits confirmation.
- Revisit: run ROS/Nav2 only if a calibrated spawn/route can be established without delaying the
  explanation study; use Blender/FBX only when installed and validated.

## 2026-09-19 — reconstruct PX4 primitives without importing simulator dynamics

- Decision: reproduce pinned `walls.sdf` box geometry and semantics in CRANE while retaining
  CRANE's validated multirotor physics and explicit ENU-to-Unity coordinate conversion.
- Evidence: the source world uses four matching primitive visual/collision boxes; no mesh or
  runtime SDF support is needed. The source ground collision is an infinite plane, represented by
  a documented 100 m benchmark envelope matching its visual extent.
- RQ impact: semantic walls can support auditable evidence references without implying that the
  robot observed them.
- Risk: x500-class shape/identity does not establish PX4 SITL or Gazebo dynamics equivalence.
- Revisit: add ArUco only for a concrete perception question and validate upstream wind through
  measured CRANE behavior rather than configuration presence.

### Follow-up validation

ArUco was added as a render-only invariant suitable for a future perception question; camera
detection remains unrun. Wind was accepted only after two byte-identical measured response runs.
Its component magnitudes are not treated as calibrated physical fidelity.

## 2026-09-19 — reference environments separate canonical collision from visuals

- Decision: add recognizable platforms incrementally, beginning with a CRANE-native TurtleBot3
  warehouse, while separating canonical collision, simulation semantics, and presentation.
- Evidence: Unity's Nav2/SLAM example is Apache-2.0, but its pinned Robotics Warehouse dependency
  has no inspected license file. CRANE primitives retain the reproducible layout pattern without
  importing unclear assets.
- RQ impact: stable semantic IDs make obstacle/corridor references auditable without treating
  evaluator truth as robot-visible evidence.
- Risk: the differential base matches Waffle dimensions and remains PhysX-driven, but does not
  establish hardware-dynamics equivalence.
- Revisit: import higher-fidelity assets only with explicit terms and invariant collision geometry.

## 2026-09-19 — strict template verification as initial trust boundary

- Decision: accept only final sentences exactly licensed by a checked plan; reject arbitrary extra
  clauses and fall back to deterministic realization.
- Evidence: no independently validated proposition extractor exists in the repository yet.
- Alternatives: regex fact checks alone; LLM self-check; permissive semantic similarity.
- RQ impact: provides a conservative D/E implementation and measurable coverage cost for RQ2/RQ4.
- Validity risk: exact matching understates achievable LLM coverage and favors templates.
- Revisit: after independent verifier evaluation on held-out external and CRANE propositions.

## 2026-09-19 — passive Nav2 observer, no native hook

- Decision: use Jazzy `BehaviorTreeLog`, `NavigateToPose`, exact BT XML, and harness events.
- Evidence: local package/interface/header inspection confirms required level-1/2 fields.
- Alternatives: BehaviorTree.CPP/C++ blackboard hook; parsing console logs.
- RQ impact: faster auditable capture with no simulator/navigation behavior changes.
- Validity risk: transient blackboard values and exact internal sensor consumption remain unknown.
- Revisit: only under the five evidence-gap criteria in `ARCHITECTURE.md` after pilot.

## 2026-09-19 — prioritize independent episodes over broad integrations

- Decision: external benchmarks are gated to roughly one day and only after CRANE capture health.
- Evidence: deadline is October 4; primary inference depends on independent scenario instances.
- RQ impact: maximizes power and reduces risk that many paraphrases masquerade as sample size.
- Validity risk: narrower external generalization evidence.

## 2026-09-19 — treat Nav2 lifecycle readiness as capture quality, not robot failure

- Decision: pilot/final runs must distinguish action-server startup rejection from a navigation
  failure and record the startup margin/readiness procedure. The locally validated temporary
  setting is `CRANE_FIXTURE_DELAY=15`; it is not yet a frozen collection rule.
- Evidence: default-delay run timed out after two inactive-server rejections and only ~8.15 s of
  accepted execution; changing only the pre-fixture delay produced terminal success.
- Alternatives: call the timeout a mission failure; increase the action deadline; patch Nav2.
- RQ impact: prevents infrastructure startup from contaminating failure labels and recovery counts.
- Validity risk: a fixed delay can conceal host-load variation; explicit lifecycle readiness is
  preferable before final collection.

## 2026-09-19 — unified umbrella with pinned component boundaries

- Decision: use this repository as the umbrella root; pin astro_dock and CRANE as Git submodules,
  and install the exact explanation-package revisions into astro_dock through one setup script.
- Evidence: prior sibling checkouts embedded developer-specific paths and could drift independently.
- Alternatives: monorepo import; sibling repositories plus prose setup instructions; raw-data LFS.
- RQ impact: strengthens reproducibility and makes representation/verification comparisons traceable
  to exact simulator, ROS, evidence-core, and capture revisions.
- Validity risk: the nested core pin intentionally targets the last pre-umbrella core commit; later
  core updates require an explicit lock change and must not recursively initialize umbrella
  submodules inside astro_dock.

## 2026-09-19 — component source exists only in the pinned nested checkout

- Decision: the umbrella does not track a second copy of `crane_explain` source, tests, or Python
  packaging metadata. Setup installs the locked component revision only at
  `packages/astro_dock/src/crane_explain`.
- Evidence: retaining the pre-refactor root `src/`, `tests/`, and `pyproject.toml` duplicated the
  component and allowed umbrella code to diverge from the recorded nested pin.
- Alternatives: keep an umbrella-local editable copy; add `crane_explain` as another top-level
  submodule; copy files during setup.
- RQ impact: removes ambiguous code provenance from every benchmark and experimental run.
- Validity risk: core changes must be committed to the component repository first, then deliberately
  advanced in `manifests/workspace.lock.json`.

## 2026-09-19 — batch recorder fsync without dropping evidence

- Decision: flush each JSONL record, call `fsync` every 100 records, and always `fsync` on close.
- Evidence: per-record `fsync` captured 871 records but reduced the CRANE pilot to RTF 0.848 and
  invalidated it; the bounded-sync rerun captured 881 records at RTF 1.00055 and passed all quality
  gates with zero stale/failed observations.
- Alternatives: drop/downsample feedback; accept invalid runs; keep per-record barriers.
- RQ impact: retains full action evidence without perturbing the robot run enough to fail its
  collection validity gate.
- Validity risk: a process/host crash can lose up to the current buffered interval even though each
  line is flushed to the OS; completeness checks remain mandatory.

## 2026-09-19 — land is the powered primary benchmark

- Decision: request a minimal deterministic non-aquatic land corridor generator for the powered
  study; keep aquatic CRANE as ecological validation.
- Evidence: Nav2 capture is working, while aquatic HDRP requires a real windowed Vulkan loop and is
  less suitable for high-throughput collection. The first success question was too trivial to
  distinguish methods.
- Alternatives: scale only the Roboboat scene; implement multiple competition domains immediately;
  force aquatic simulation into unsupported headless modes.
- RQ impact: prioritizes independent C/D/F navigation motifs and statistical power for RQ1–RQ4.
- Validity risk: primary claims may be land-specific; surface/other-domain results must be labeled
  ecological or exploratory unless independently powered.

## 2026-09-19 — do not make direct BARN integration the primary path

- Decision: reuse BARN's generated-world and held-out sampling methodology now; defer its separate
  Gazebo/Jackal runtime to an optional, isolated one-day smoke after local land capture is healthy.
- Evidence: the audited ROS 2 harness has action/proximity outcome ambiguity and batch/report
  inconsistencies; the BARN 2026 organizer report says only one of five ROS 2 submissions was
  evaluable by the standard pipeline. See `docs/research/BARN_FEASIBILITY.md`.
- Alternatives: rebuild and repair BARN immediately; import BARN worlds into Unity; ignore BARN.
- RQ impact: preserves collection time while retaining scenario diversity/split principles.
- Validity risk: the primary study lacks a standardized external land embodiment unless the later
  smoke passes its frozen stop gates; report this limitation rather than implying BARN validation.

## 2026-09-19 — terminal explanations preserve client/BT/physical distinctions

- Decision: checked terminal plans report recorded action status and explicit harness deadline or
  cancellation as separate propositions, followed by an explicit causal limitation.
- Evidence: p01 involved a client deadline while p03 succeeded; neither record licenses a physical
  failure cause, and a successful terminal result does not prove every intermediate BT branch
  succeeded.
- Alternatives: collapse all non-success into navigation failure; answer only recovery counts.
- RQ impact: directly expands terminal-failure and misleading-premise coverage for RQ2–RQ4.
- Validity risk: richer software-mechanism explanations still require parsing exact BT transitions;
  terminal status alone remains level-1 evidence.

## 2026-09-19 — preserve Ackermann constraints in the headless land fixture

- Decision: use the existing PhysX Ackermann rover with a stamped, fixed-step ROS adapter; do not
  emulate Nav2 spin commands by rotating the transform or by inventing lateral actuation.
- Evidence: the first land smoke moved under wheel physics but later stopped when the controller
  requested near-zero linear velocity; an Ackermann rover cannot physically turn in place.
- Alternatives: reuse the aquatic holonomic controller; force a minimum crawl; directly manipulate
  pose; replace the rover with differential drive.
- RQ impact: execution explanations remain grounded in the actual embodiment, and recovery
  failures caused by incompatible behaviors can be represented honestly.
- Validity risk: stock recovery trees containing Spin may be structurally incompatible. Before
  powered collection, either configure an Ackermann-valid recovery tree and record its exact XML,
  or treat incompatibility as a deliberately scoped mechanism—not a generic navigation failure.

## 2026-09-19 — require populated costmap evidence through stock introspection

- Decision: land runs must observe at least one populated costmap. Record full-map topic deliveries
  and bounded `/local_costmap/get_costmap` snapshots separately; use the service snapshots for the
  validity gate while the topic path remains silent.
- Evidence: the initial configuration omitted the LaserScan source height limit and returned an
  all-zero map. Adding the Jazzy per-source `max_obstacle_height` populated the internal local and
  global obstacle layers (548 and 389 lethal cells in the discriminating probe). Neither
  transient-local nor volatile subscribers received the advertised full-map topic, including with
  `always_send_full_costmap=true`; the stock service returned populated snapshots reliably.
- RQ impact: obstacle/recovery pilots can require observable navigation-state evidence without a
  C++ hook. Recorded provenance explicitly does not claim controller consumption.
- Validity risk: service polling observes current Nav2 state, not the controller's exact sampled
  map. Claims must remain at that scope.

## 2026-09-19 — compare A/B through parity-controlled presentations

- Decision: derive a structured B presentation and strong prose A presentation from the same
  explicit fact inventory; do not expose native timestamps or repeated event details only to B.
  D still consumes the native structured record because checked native capture is the method under
  test. Retain and exclude any model batch whose proposition-level parity audit fails.
- Evidence: the first e004 model attempt gave native structure two guard-success events and exact
  timestamps while prose described one generic sequence. The corrected ten-fact presentation made
  each fact explicit in both formats and omitted exact timestamps from both.
- Alternatives: serialize the entire native episode to B; discard event detail from D; weaken prose
  so representation differences appear larger.
- RQ impact: makes B-vs-A attributable to representation rather than privileged information, and
  makes D-vs-B interpretation auditable.
- Validity risk: deriving the B presentation is itself deterministic preprocessing; the freeze must
  specify its mapping and ensure it neither drops question-relevant facts nor adds derived claims.

## 2026-09-19 — use Codex CLI only for the development model pilot

- Decision: use pinned `gpt-5.6-sol` at low reasoning through noninteractive `codex exec --json`
  for the first pilot because no generic provider API key is installed. Cache every unique request
  and never resample. Keep provider, prompt, and model mutable until several pilots support freeze.
- Evidence: the adapter retained raw JSONL events and reported token usage/latency, but ChatGPT
  login did not expose temperature, sampling seed, or monetary cost. Official CLI documentation
  describes `codex exec`, JSONL output, output schemas, and final-message output at
  <https://developers.openai.com/codex/cli/reference>.
- Alternatives: continue with a rule-based pseudo-generator; wait for another API key; treat the
  coding-agent wrapper as the final experimental generator without a pilot.
- RQ impact: produces real language-model failure evidence now while preserving a transparent
  route to a frozen provider adapter.
- Validity risk: agent system framing and large fixed input-token overhead may differ from a normal
  text-generation API. Final-study claims must name the exact interface and rerun development
  comparisons if the frozen provider changes.

## 2026-09-19 — completeness is scoped to the claim family

- Decision: retain whole-BT transition completeness separately from recovery-count completeness.
  A recovery count is exact only when capture brackets one accepted goal and terminal result, all
  feedback belongs to that goal, the final monotonic feedback count equals its maximum, and unique
  `Wait` entries match that count. Missing final BT node transitions still make detailed transition
  history incomplete.
- Evidence: Nav2's topic logger omitted the final `FollowPath` transition on both e007 success and
  e004/e009 aborts. Treating one global flag as authoritative changed a supported zero-recovery
  success into “at least zero,” while declaring the whole trace complete would hide the missing
  terminal transition.
- Alternatives: use one global completeness flag; always qualify every count; infer terminal node
  status from the action result and rewrite the BT trace.
- RQ impact: makes selective answers useful without weakening the evidence boundary for chronology
  or causal mechanism.
- Validity risk: the recovery-completeness cross-check depends on the exact retained BT XML and
  Nav2 feedback semantics. Freeze and test it per tree/version rather than generalizing globally.

## 2026-09-19 — exclude terminal runs when the predeclared intervention did not activate

- Decision: retain but exclude e032–e034 even though their terminal status and recovery counts
  match the expected family, because evaluator truth records `mobilityHeld=false`.
- Evidence: all three actions aborted after two recorded `Wait` attempts, while every hold timing
  and activation field remained unset/false. Matching the desired outcome is not evidence that the
  intended mechanism occurred.
- Alternatives: relabel them as generic terminal failures; infer the hold from zero displacement;
  rerun with adjusted timing. All would violate the predeclared mechanism or mismatch rule.
- RQ impact: prevents mechanism leakage and post-outcome selection from inflating the terminal
  sample. E035 remains a valid success-family replication.
- Validity risk: terminal recovery/exhaustion collection remains unreliable until the intervention
  configuration path is diagnosed on fresh development runs.

## 2026-09-19 — encode an omitted mobility release as a persistent hold

- Decision: `--crane-land-mobility-hold-after N` with no release now holds planar mobility from
  the fixed-time boundary until process exit. A release without a configured hold remains invalid.
- Evidence: e032–e034 parsed the hold value but threw before scheduling because the implementation
  required paired boundaries. The predeclared e036 full-stack calibration scheduled and applied
  the corrected hold within one fixed tick and retained it through shutdown.
- Alternatives: provide an arbitrary release after the worker deadline; encode infinity as a large
  float; abandon persistent hold. Optional release states the intended semantics directly and
  avoids deadline-dependent configuration.
- RQ impact: enables repeatable terminal recovery/exhaustion instances without leaking the
  evaluator-owned intervention into robot-visible evidence.
- Validity risk: this is synthetic fault injection. Explanations may describe recorded BT
  mechanism but must not claim a physical cause or identify the hidden intervention.

## 2026-09-21 — preserve imported Clearpath geometry during Nav2 validation

- Decision: recognize the generated Clearpath pipeline scene in the existing land Nav2 bootstrap,
  but retain its scene-authored spawn and imported canonical geometry. Reject synthetic corridor
  blockers in this mode rather than silently changing the reference task.
- Evidence: a graphics-free 1 m smoke succeeded while evaluator truth recorded
  `referenceEnvironmentPreserved=true`; the separate reference validator still found all 11
  canonical colliders, 13 visual renderers, semantic sensor/raycast resolution, rigid contact, and
  unchanged highlight behavior.
- Alternatives: replace the imported world with the synthetic corridor; add Clearpath-specific
  motion/ROS infrastructure; or defer all navigation checks after completing only structural
  validation.
- RQ impact: provides a narrow recognizable-platform transport and motion check without granting
  the explanation system privileged world truth or changing canonical task feasibility.
- Validity risk: the 1 m local goal is not a representative pipeline route, and delivered scans or
  costmap observations do not prove controller consumption. Native Gazebo comparison, route/spawn
  calibration, material parity, and Jackal hardware dynamics remain **NOT_RUN**.

## 2026-09-21 — defer underwater and aerial explanation validation until after TRUSTMORE 2026

- Decision: keep CRANE's multi-domain architecture and all existing aerial/underwater code,
  environments, assets, and scoped validation results, but mark their remaining navigation and
  explanation validation `DEFERRED_POST_SUBMISSION`. Submission-critical environment work is the
  frozen controlled land/Nav2 study, obstacle-rich warehouse/industrial validation, and a
  configurable land proving ground. RoboBoat remains a parallel, separately owned surface-domain
  demonstration if it qualifies.
- Evidence: land/Nav2 already supplies the highest-throughput path for runtime/source provenance,
  recovery, termination, evidence insufficiency, and blinded paired evaluation. Existing aerial
  results qualify geometry/physics motifs but do not provide an explanation-study navigation
  sample; underwater would require substantial autonomy and evidence integration. Before the
  October 4 deadline, independent episodes, ecological land behavior, annotation, analysis,
  figures, and paper work have higher validity value than shallow domain breadth.
- Alternatives: continue aerial and underwater integration in parallel; require one example from
  every CRANE domain; or remove those environments entirely. The first two dilute the powered and
  ecological evidence path, while removal would discard useful post-submission infrastructure and
  misrepresent completed work.
- RQ impact: the frozen confirmatory hypothesis remains unchanged and land/navigation remains its
  declared primary domain. Cross-domain robustness is exploratory; RoboBoat may add a distinct
  surface demonstration, while aerial/underwater claims move to future work. This decision does
  not imply that missing aerial/underwater experiments invalidate the primary result.
- Governance: `docs/STUDY_DESIGN.md`, `docs/BENCHMARK.md`, and
  `docs/ANNOTATION_GUIDE.md` are hash-governed by the existing study freeze and were deliberately
  left unchanged. This planning decision adds no freeze amendment because it changes neither the
  frozen protocol nor its already-land-primary estimand.
- Revisit only after (1) frozen provenance collection and annotation are complete, (2) ecological
  land scenarios are validated, (3) primary statistics and figures regenerate reproducibly,
  (4) manuscript-critical work is on schedule, and (5) another domain is demonstrably more
  valuable than additional land evidence or paper work.

## 2026-09-22 — close legacy collection early and redirect to supported physical diagnosis

- Decision: preserve the frozen provenance study unchanged, close its collection prospectively at
  33 included episodes, finish its original blind annotation/analysis as an explicitly under-target
  cohort, and make a separate diagnosis-to-language study the forward-looking contribution.
- Evidence: collection has 33 complete paired F/G/H episodes but zero sealed annotations; its G
  output falls back deterministically on 46/66 responses and its physical-cause question is
  deliberately evidence-insufficient. Three ecological land exports and a qualified RoboBoat
  baseline contain richer motion/physical evidence, while no paper draft exists.
- Alternatives: collect seven or seventeen more legacy episodes; retroactively change the frozen
  rubric; abandon the legacy study; or broaden environments. Additional legacy rows would improve
  old-study power but not add physical diagnosis, while the other alternatives damage validity or
  deadline focus.
- Expected effect: legacy results remain auditable evidence about provenance, software mechanism,
  and restraint. New Q1--Q3 separately test supported diagnosis, language faithfulness, and
  appropriate specificity using matched R/P/T/N methods.
- Validity risk: stopping below the frozen minimum reduces inferential power and must be disclosed.
  The new study has no pilot-informed sample target yet and cannot borrow the old power analysis.
- Revisit: do not reopen legacy collection based on observed answers or labels. A later amendment
  may authorize only a resource-based bounded completion before labels are inspected, but the
  default is closed so diagnostic pilots, annotation, analysis, and manuscript receive time.

## 2026-09-22 — use terminal stopping margin as the first RoboBoat diagnostic mechanism

- Decision: exercise the new diagnosis-to-language path first on the retained goal-checker margin
  mismatch, using only the goal, exact Nav2 thresholds, declared task tolerance, and independently
  measured odometry-derived motion. Keep matched 0.20 m rerun outcomes outside the ordinary
  robot-visible export and reserve them as retrospective development context.
- Evidence: the pre-change action returned at 0.3738 m error and 0.04861 m/s under 0.400 m and
  0.050 m/s thresholds, leaving 0.0262 m of task margin; it subsequently moved 0.1876 m and ended
  at 0.5614 m error. This directly supports an inadequate terminal-margin mechanism.
- Alternatives: begin with wave/current attribution, rebuild boat control, or use only a terminal
  status narrative. No retained evidence distinguishes wave/current/wind uniquely, controller
  rebuilding risks the validated baseline, and status narration omits the measured mechanism.
- RQ impact: establishes a concrete development example for Q2/Q3 and a candidate mechanism family
  for prospective Q1 comparison. It is not evidence that P outperforms R/N/T.
- Validity risk: this is a retrospectively selected development case from another workstream. The
  prospective study must freeze cases, evidence masks, methods, and stopping rules before held-out
  collection and must independently score both diagnosis and final language.

## 2026-09-22 — diagnose the land pilot as direct-route restriction, not complete no-path

- Decision: retain `land-blockage-global-002` as a valid development diagnostic pilot, but classify
  fault induction as partial. The ordinary answer may state that the retained navigation model
  restricted the direct route and that the abort aligned with the configured deadline. It may not
  state that no route existed, name the evaluator-only wall, or claim recovery exhaustion.
- Evidence: evaluator truth confirms the requested wall was active, but the robot-visible global
  costmap independently remains connected below cost 253. The centerline crosses lethal cells,
  delivered odometry deviates 2.705 m laterally, 69 planner updates succeed, recovery feedback
  remains zero, and action failure occurs 0.860 s from the exact 70 s BT deadline.
- Alternatives: use the scenario label as proof of complete blockage; discard the conflicting run;
  or tune geometry until disconnection appears. The first leaks evaluator truth, the second hides a
  valid unfavorable result, and the third risks outcome-directed scenario manipulation.
- RQ impact: provides an honest Q2/Q3 development case with a useful physical/model diagnosis and
  explicit alternative evidence. It is not a Q1 method-comparison result.
- Validity risk: the final BT transition is missing and the retained snapshot is not the exact grid
  consumed by every planner tick. A future prospective case should retain time-aligned global grids
  and full paths, but that instrumentation is lower priority than protocol freeze and annotation.

## 2026-09-22 — preserve positional diagnosis when RoboBoat return speed is missing

- Decision: treat the speed-masked case as partially diagnosable, not wholly unanswerable. State
  that observed post-return motion exceeded the remaining positional margin and led outside the
  task tolerance, while withholding whether the physical platform met Nav2's stopped-speed
  threshold and what caused the motion.
- Evidence: the mask retains action success at 0.3738 m error, a 0.400 m task limit, 0.1876 m of
  post-return displacement, and 0.5614 m settled error. R/N expressed this chain; the original P/T
  plan discarded it solely because measured return speed was absent.
- Alternatives: call the whole case unanswerable; infer the missing speed from action success; or
  attribute residual motion to waves/current. The first is unnecessary abstention, while the other
  two exceed the robot-visible evidence.
- Expected effect: Q3 can distinguish useful partial diagnosis from both speculation and blanket
  abstention. `terminal-stopping-margin-v2` implements the distinction; the v1 model outputs remain
  immutable and are annotated as generated.
- Validity risk: this correction is post-hoc on the exposing episode and its reference inventory is
  not independent gold. A separate prospective case must validate the rule before any Q3 claim.

## 2026-09-22 — keep legacy grouping metadata blinded until adjudication

- Decision: human annotation forms use an explicit `BLINDED_PENDING_KEY_JOIN` sentinel for
  `episode_id` and `scenario_family`, and the opaque response ID for `condition_blinded_id`. The
  evaluator-only key and frozen split restore true grouping only after complete adjudication.
- Evidence: the frozen guide requires these fields, but the sealed packet intentionally exposes no
  episode, scenario, or condition mapping. Requiring annotators to populate real values would be
  impossible without defeating the declared blinding boundary.
- Alternatives: give annotators the key; let them guess metadata; silently drop required fields;
  or rebuild the sealed packet. Those options respectively unblind conditions, create false data,
  violate the row schema, or mutate a governed artifact after collection.
- Scope: this is a pre-annotation operational clarification, not a rubric or analysis change. It
  leaves all questions, units, labels, packet bytes, key bytes, hypotheses, and comparisons
  unchanged. The dated hashes are in
  `manifests/annotation/sealed-primary-v3-operational-clarification.json`.
- Validity protection: the join verifies the packet/key hash and full response inventory and
  applies the predeclared whole-episode quarantine before producing analysis input.

## 2026-09-22 — retain the historical RoboBoat grid-disconnection case as development-only

- Decision: preserve the wrong-side-goal failure as a compact, robot-visible development case for
  retained navigation-model disconnection, but exclude it from confirmatory sampling and do not
  treat the later corrected docking run as a matched counterfactual.
- Evidence: independent decoding verifies the embedded costmap hash, result-cell cost 0, goal-cell
  cost 253, and no eight-connected route below 253. The controller log contains 23 exact Navfn
  planning-failure messages for that goal before action abort. Local reflog timing bounds the run
  between committed revisions, but the costmap-payload capture code was uncommitted and its exact
  dirty diff was not retained.
- Alternatives: discard the evidence; call the case physical berth infeasibility; treat corrected-
  goal success as a one-factor intervention; or rerun/tune RoboBoat before protocol freeze. The
  first loses a useful bounded mechanism, the middle choices overclaim, and the last has lower
  immediate paper value than annotation, prospective land collection, and study freeze.
- Expected effect: the development benchmark gains a surface-vehicle geometric/planning mechanism
  that answers more than “the action aborted,” while demonstrating explicit source-provenance and
  causal limits. It adds no R/P/T/N comparison, confirmatory cluster, or effectiveness evidence.
- Revisit: a prospective boat case is eligible only if exact source/build/configuration identity,
  synchronized planner inputs, a predeclared question, and a matched run protocol are retained
  before outcome inspection.

## 2026-09-22 — develop a bounded semantic gate without rewriting exact-verifier history

- Decision: retain all 8/8 exact-verifier fallbacks as generated, while implementing a separate
  development verifier for future prospective outputs. Its only repair appends the complete checked
  evidence-ID list; substantive wording is never rewritten.
- Evidence: project review found that most rejected candidates preserved the checked mechanism and
  limits but differed stylistically from the deterministic template. A post-hoc audit accepts 7/8
  after citation repair and rejects all 24 simple numeric, section-removal, and physical-cause
  mutations. The masked-speed candidate remains rejected for claims absent from its checked plan.
- Alternatives: keep exact equality permanently; allow all fluent candidates; use LLM self-check as
  the trust boundary; or retroactively replace archived final outputs. Exact equality collapses P
  into T, unconditional acceptance is unsafe, self-check is not independent, and retroactive edits
  would invalidate the retained experiment.
- RQ impact: the verifier creates a testable seam between diagnostic correctness and language
  faithfulness for prospective Q2. It does not establish P-over-R benefit or LLM usefulness.
- Validity risk and revisit: the policy was tuned after candidate inspection. Freeze its module,
  prompt, one-repair rule, adversarial/held-out evaluation, and threshold before new evaluation;
  report pre- and post-verification text and fall back deterministically on any rejection.

## 2026-09-23 — do not count seed-only proving-ground reruns as independent scenarios

- Decision: define the diagnostic study's primary sample unit as one genuinely distinct scenario
  instance with one predeclared binary endpoint. Different run seeds of the current proving-ground
  layout do not qualify because the seed enters identity hashes but does not alter its geometry.
- Evidence: source inspection shows the proving-ground builder selects fixed manifest boxes and
  uses the requested seed only in the recorded configuration hash/truth record. Exact paired power
  sensitivity requires 92 independent primary clusters for 80% power under the declared +15-point
  planning pattern (20% P-only versus 5% R-only success); 40 clusters provide only 36.4%.
- Alternatives: treat seeds or question paraphrases as independent; reuse the legacy 40-episode
  calculation; lower the effect threshold after seeing outcomes; or claim a powered study from a
  convenience cohort. Each would overstate effective sample size or introduce outcome-dependent
  design.
- Expected effect: protocol freeze is blocked on a genuinely varied, versioned geometry source and
  demonstrated collection throughput. If the target is infeasible by the predeclared cutoff, the
  paper becomes an honestly underpowered short/WIP result rather than an invalid full-paper claim.

## 2026-09-23 — retire the v4 planner-grid-disconnection induction after three failed calibrations

- Decision: preserve the eight generated blockage identities as development-calibration history,
  remove the 48 unrun confirmatory blockage identities, and prohibit counting either set as
  planner-grid-disconnection cases. Stop geometry tuning for this mechanism.
- Evidence: open 8 m, closed 8 m, and closed 5 m variants all reached the 100 s client deadline
  while retaining 96–97 successful planning records. The narrowest run remained laterally bounded
  but oscillated/reversed and reached feedback recovery count 2. In contrast, a connected-detour
  run and nominal control both succeeded and retained their expected path behavior. The offline
  canonical raster's disconnected label therefore does not establish the actual Nav2-grid state or
  runtime mechanism.
- Alternatives: tune more geometry until an abort occurs; label the deadline as disconnection;
  discard the unfavorable runs; or retain all 96 planned cases based on offline geometry alone.
  These choices would respectively consume collection time, confuse an outcome with a mechanism,
  hide failed induction, or make the prospective population scientifically false.
- RQ impact: the candidate primary inventory falls from 96 to 48 connected-detour instances. This
  does not alter the exact power sensitivity; it shows that the current catalog alone cannot meet
  it. A second independently testable mechanism is required before protocol freeze if the powered
  target remains feasible.
- Revisit: do not reopen this geometric induction before submission. Prefer one bounded
  command-to-motion family using already supported instrumentation, but admit it only after a
  matched healthy control, independent diagnostic computation, useful final answer, parity audit,
  and annotation dry run pass.

## 2026-09-23 — retain the command-motion pair as one blinded development cluster

- Decision: retain the held-condition and matched nominal command-motion comparisons as two
  blinded annotation packets but one statistical cluster. Preserve both original no-retry model
  outputs and their 2/2 deterministic fallback decisions unchanged.
- Evidence: the same predeclared intervention/control family and thresholds produced one supported
  7–17 s command-to-motion discrepancy and one successful `not_triggered` control. Tool-enabled R
  received the same blind samples, exact source, and executable computation as P. Project review
  finds R and raw P identify the supported mechanism and all model conditions reject the nominal
  false premise; independent human labels remain `NOT_RUN`.
- Alternatives: count the two runs as independent scenarios; rerun P after correcting verifier
  false positives; replace final P with the newly accepted raw candidates; or omit the pair. The
  first inflates sample size, the middle choices rewrite an observed operating point, and omission
  discards a useful instrumentation and response-quality calibration.
- RQ impact: the pair completes a fair development dry run for the second mechanism and exposes
  language-gate failure separately from diagnostic failure. It supplies no confirmatory effect
  estimate and does not show P outperforming tool-enabled R.
- Validity protection: references state that physical computations predated model calls while
  annotation units were formalized afterward. Packet keys remain evaluator-only; the post-hoc
  bounded-verifier audit is manifested separately and cannot relabel the immutable outputs.

## 2026-09-23 — treat missing measured motion as partial answerability, not generic abstention

- Decision: when independent odometry samples are absent, withhold the command-motion mechanism but
  retain the recorded action and source-qualified execution sequence. Group the deterministic mask
  with its source episode and add zero independent scenarios.
- Evidence: the predeclared mask retains 376 command samples, zero odometry samples, action abort,
  two FollowPath failures, and two source-qualified Wait invocations. An independent evaluator
  labels the command-motion comparison insufficient while the sequence remains answerable. The
  first checked plan exposed an empty evidence section, which was corrected before any model call.
- Alternatives: call the whole question unanswerable; infer stopped motion from the abort; reuse
  the paired unmasked diagnosis; or count the mask as independent. These respectively discard
  useful facts, invent physical evidence, leak paired information, or inflate sample size.
- RQ impact: this gives Q3 a declared ambiguous development case and forces analysis to separate
  diagnosable supported success from ambiguous-case qualification. It does not establish a method
  effect: R, raw P, and N all withheld the missing mechanism on project review.
- Validity protection: the one-shot outputs and P fallback remain immutable. The post-hoc verifier
  acceptance is regression evidence only; blind human annotation and held-out evaluation remain
  required.

## 2026-09-23 — treat the merged RoboBoat baseline as integrated but protected

- Decision: remove living-document references to a still-active parallel RoboBoat owner. The
  completed docking/navigation work is merged into `main`; its validated scene, vehicle, physics,
  sensors, Nav2 configuration, and docking baseline remain protected inputs to the diagnostic
  study rather than targets for redesign.
- Evidence: the integrated reports retain calibrated command response, known-path docking, and
  five repeated far-dock Nav2/action and independent physical-predicate successes. Governed
  terminal-margin outputs and a retained-grid diagnosis already exist, while prospective surface
  explanation evaluation and human annotation remain `NOT_RUN`.
- Alternatives: continue waiting on a nonexistent parallel workstream; reopen platform tuning; or
  omit RoboBoat despite retained measured evidence. The first misstates ownership, the second risks
  manufacturing favorable behavior, and the third discards a qualified cross-domain substrate.
- RQ impact: RoboBoat is a focused surface diagnostic source, not a claim of cross-domain
  validation. Only prospectively governed cases may enter the new study.
- Validity protection: no RoboBoat source, scene, physics, vehicle, sensor, or Nav2 file changed.
  Any later narrow shared/capture change requires a measured non-regression and separate commit.

## 2026-09-23 — retain successful compensation as post-observation development evidence

- Decision: retain the prospectively declared compensated command--motion run as one new
  development scenario, govern its blind export and separate evaluator truth, and do not treat its
  revised recovery explanation as a prospective effectiveness result.
- Evidence: unchanged development thresholds independently reproduce an 8--18 s sustained
  delivered-command/measured-motion discrepancy, a later 20--21 s recovered-response window, one
  FollowPath failure, one source-qualified Wait invocation, and eventual action success. The first
  checked answer omitted a measured recovery comparison; v2 was implemented only after that
  deficiency was observed.
- Alternatives: retain only terminal success; silently present the v2 answer as prospective;
  expose the evaluator hold/release identity; infer a unique execution cause; or immediately spend
  model calls before governing the physical evidence. These would respectively under-explain the
  outcome, misstate chronology, leak truth, overclaim causality, or weaken reproducibility.
- RQ impact: the case shows that the diagnostic representation can distinguish the same supported
  discrepancy from its later recovery and different outcome. It does not show P over tool-enabled
  R, estimate verifier accuracy, or add an annotated cluster.
- Next gate: obtain independent human annotation on the already prepared blinded inventory before
  deciding whether another development packet has higher paper value than annotation, analysis,
  figures, or manuscript completion.

## 2026-09-23 — retain compensated comparison as one distinct blinded development cluster

- Decision: retain the no-retry R/P/T/N compensation comparison and add its blinded packet as one
  independent development cluster; do not score it by project review or alter the historical P
  fallback after observing outputs.
- Evidence: the physical scenario, independent computation, question, allowed/prohibited claims,
  model, prompts, and call cap were fixed before generation. R reports an incorrect interval and
  duration; raw P preserves the checked values but the operating verifier rejects it; N lacks the
  aligned computation and makes a stronger Wait/retry association. These are plausible
  differentiation signals, not independent labels.
- Alternatives: omit the unexpected R error; repair and rerun R; modify the verifier and replace
  final P; count the case with the earlier held/nominal family; or announce P superiority. Those
  choices would respectively discard a valid result, resample, rewrite an observed operating
  point, undercount independent physical configuration, or substitute author judgment for scoring.
- RQ impact: the packet directly tests the same diagnosed mechanism with a different outcome and
  may inform the prospective freeze after annotation. It does not establish significance, verifier
  accuracy, learned-language benefit, or a confirmatory effect.

## 2026-09-23 — correct the future verifier without rewriting compensated-motion output

- Decision: version the bounded diagnostic-language policy as v2 and allow a required
  `FollowPath` failure proposition anywhere in the complete checked response. Continue requiring
  the source-qualified Wait/recovery sequence, terminal outcome, and recovered-response relation
  in the failure-chain section, and reject language claiming that Wait/retry caused measured
  response recovery.
- Evidence: the exact archived raw P candidate states `FollowPath recorded 1 failure` under
  decisive evidence and gives the Wait/recovery ordering under failure chain. The operating v1
  gate rejected only because it looked for `FollowPath` in the latter section. A public-interface
  regression reproduces that candidate; adversarial regressions remove `FollowPath` entirely and
  substitute an unsupported recovery-causation claim.
- Alternatives: retain the known false negative for future runs; accept any controller statement;
  move or edit the archived candidate; or rerun P. These would respectively force avoidable
  fallback, weaken the proposition gate, rewrite observed output, or violate the no-retry design.
- Validity protection: this correction was designed after output inspection and is post-hoc
  development tuning, not an independent verifier-accuracy result. The archived v1 rejection,
  deterministic fallback, annotation packet, and aggregate 12/12 development fallback frequency
  remain immutable.

## 2026-09-23 — retain delivered-plan comparison as a negative differentiation case

- Decision: retain the predeclared no-retry R/P/T/N plan-change comparison as one distinct
  development cluster, build its blinded packet, and do not rerun or replace any condition after
  project review.
- Evidence: independent pre-model recomputation verifies 70 unique delivered plans and their
  geometry. Tool-enabled R closely matches the checked mechanism and limits; N adds stronger
  plan-following and distance-trigger language; raw P is substantively aligned but the operating
  lexical gate rejects it and final P falls back to T. None of these observations is a human label.
- Alternatives: omit the case because R performs well; rerun P after relaxing the verifier; deny R
  the executable tool; or score the outputs by author judgment. Those choices would selectively
  discard a negative result, resample, create an unfair baseline, or bypass blinded evaluation.
- RQ impact: the case validates useful recorded route-change communication and causal restraint,
  but supplies no evidence that P exceeds a fair tool-enabled R. It raises the development inventory
  to 52 responses over nine clusters; annotation, adjudication, and inferential analysis remain
  required before any comparative claim.

## 2026-09-23 — correct future route-change matching without rewriting the pilot

- Decision: version the bounded language policy as v3 and accept `route change` as a valid
  delivered-route-change proposition. Preserve the pilot's v2 rejection, deterministic final P,
  packet, and aggregate 13/13 fallback frequency.
- Evidence: the archived raw P diagnosis says `route change from an initially direct plan to later
  non-direct plans` and preserves all required measurements and limits. V2 rejects only because it
  matches `successful route change` or `plan change`. An exact-candidate regression now passes,
  while a mutation deleting the controller-consumption qualification fails.
- Alternatives: keep the known false negative; accept any mention of a route anywhere; edit the
  archived candidate; or rerun P. The chosen diagnosis-section phrase expansion is the narrowest
  change that removes the false negative without weakening the other mechanism gates.
- Validity protection: this is post-hoc development tuning, not independent verifier-accuracy or
  method-effect evidence. No archived answer, packet, key, annotation unit, or model call changed.

## 2026-09-23 — predeclare six diagnostic pilot endpoints before human labels

- Decision: use exactly one fully observed, diagnosable endpoint from each of six eligible
  development clusters for pilot-informed P-versus-R power feasibility. Keep masks, matched
  controls, retrospective cases, and non-independent-reference cases as secondary outcomes; never
  count them as additional independent planning observations.
- Evidence: the 13 packets represent nine clusters, but only six have an independently implemented
  or pre-model-audited primary variant suitable for the intended prospective population. No
  independent annotator form, adjudication, or joined condition label existed when this selection
  was committed.
- Alternatives: choose the most favorable variant after labels; count all 13 packets; use all nine
  clusters despite reference chronology; or ignore pilot labels entirely. The first three inflate
  or select the effect, while the last discards the requested pilot-informed feasibility check.
- Statistical rule: report raw paired discordance and a Jeffreys-smoothed four-cell sensitivity.
  The six clusters can increase the fixed 92-cluster smallest-practical-effect target or show that
  superiority is not credible, but cannot lower the target. Missing/quarantined endpoints are
  reported and never replaced post-label.
- RQ impact: this protects Q1's fair P-versus-tool-enabled-R comparison and keeps Q2/Q3 masks and
  controls available as secondary evidence without pretending they increase primary power.
## 2026-09-23 — use a qualified Luna model-judge as a separate automated arm

- Decision: create `luna-model-judge-v1` for operational semantic evaluation, with two isolated
  Luna passes, independently constructed answerable-unit references, fail-closed qualification,
  immutable caching, and unresolved-label sensitivity analysis.
- Original requirement preserved: `docs/ANNOTATION_GUIDE.md` and the dual-human/adjudication
  workflow remain unchanged and incomplete. Luna outputs are never stored as human annotations.
- Evidence motivating it: a full human campaign is not a prerequisite the remaining submission
  schedule can safely assume. Automated scoring is useful only if its limitations and category-level
  qualification are explicit.
- Alternatives considered: block all analysis on two humans plus a third adjudicator; use one
  unqualified judge pass; treat two model passes as two annotators; or use the project's verifier as
  gold. The first was removed as a current prerequisite; the latter three are rejected as invalid.
- Expected impact: enables auditable “Luna-assessed semantic fidelity” analyses while preserving
  deterministic measurements and the physical-diagnosis redirect. It does not establish human
  trust, human agreement, or unrestricted semantic accuracy.
- Revisit condition: add an independently recruited human audit if feasible; restrict or label a
  category exploratory if held-out Luna qualification misses its predeclared gate.
- Protocol: `docs/LUNA_ANNOTATION_PROTOCOL.md`.
- Outcome: prompt/suite v1 and the single authorized v2 clarification both failed development
  qualification. V2 medium/high eliminated false material-error decisions but missed the 95%
  required-unit gate. No effort was frozen; held-out and study scoring remain `NOT_RUN`. Thresholds
  were not relaxed and prompt iteration stops.

## 2026-09-23 — prepare an honest short/WIP submission after judge qualification failure

- Decision: make the current paper a 4--6-page short/WIP submission rather than leave an incomplete
  seven-page full-paper scaffold. Remove empty confirmatory tables and result placeholders; report
  the deterministic development measurements, fair-baseline parity, 13/13 fallback, and failed
  Luna qualification without a semantic method-effect estimate.
- Evidence: the legacy cohort has 33 clusters and no completed semantic labels; the diagnostic
  inventory has nine development clusters and no qualified judge; both bounded Luna development
  qualifications failed; and tool-enabled R frequently matched P/T on project review. These facts
  cannot support the requested statistically significant superiority claim or an 8--9-page full
  paper, but they do support a reproducible WIP with explicit negative results.
- Alternatives: retain red placeholders until unavailable results appear; relax the judge gate;
  report author review as annotation; or add unscored prose to reach eight pages. Each would weaken
  auditability or overstate the evidence.
- Revisit condition: restore a full-paper claim only after a prospectively frozen, qualified
  semantic evaluation over enough independent clusters supports it. Git history preserves the
  earlier scaffold; frozen studies and original annotation workflows remain unchanged.

## 2026-09-23 — require sequential meaningful-advantage confirmation and fresh replication

- Decision: register an additive framework for future diagnostic campaigns with one primary
  comparison, P versus tool-enabled R; a +0.15 minimum worthwhile supported-diagnostic-success
  improvement; simultaneous nondegradation guardrails; anytime-valid paired-cluster monitoring;
  a closed program error ledger; and separately reserved fresh-configuration replication.
- Evidence: inspected development cases often show parity between P/T and a fair tool-enabled R,
  the existing 92-cluster calculation tests against zero rather than a +0.15 lower-bound target,
  and both Luna development qualifications failed. Repeated fixed-look testing or accumulating
  easy variants would therefore not establish the intended scientific advantage.
- Alternatives: treat the strongest observed ablation as optional; stop whenever an uncorrected
  p-value crosses .05; reuse inspected clusters; lower the worthwhile threshold; or spend all alpha
  on candidate revisions. These were rejected because they weaken fairness, independence,
  practical relevance, or replication.
- Validity protection: only fresh prospectively sampled configurations enter; related runs/masks/
  paraphrases remain clustered; all four corrected bounds must pass; failed/futile candidates
  consume their allocation; judge uncertainty blocks success; and legacy F/G/H remains untouched.
- Current consequence: no campaign is active. A candidate, parity-audited R contract, target
  samplers, newly qualified Luna arm, and replication reserve must be hash-frozen first.
- Revisit condition: a future protocol version may use a prospectively declared land-only target
  if surface strata remain unavailable, but never by redistributing weight after outcomes.

## 2026-09-23 — retire unused sequential v1 and register feasible v2 monitoring

- Decision: preserve `diagnostic-sequential-protocol-v1` as unused design history and make v2 the
  canonical framework before any confirmatory response or alpha consumption. V2 uses a fixed-
  fraction admissible betting mixture, an intersection--union decision rule, and a 1,600-cluster
  outer planning ceiling; the +0.15 improvement and all three guardrail margins are unchanged.
- Evidence: analytic zero-difference bounds and an initial pre-outcome simulation showed v1's
  global lambda cap, equal Bonferroni split, 20% ambiguity allocation, and 400-cluster maximum made
  the ambiguity guardrail practically unattainable. This was a design defect, not a negative method
  result. No v1 campaign existed and its cumulative ledger consumed 0.000 alpha.
- Mathematical basis: for null mean `m`, `lambda=c/(1+m)` keeps every bounded-mean factor positive
  and expectation at most one. Overall success is a conjunction, so testing each component at the
  campaign alpha is a valid intersection--union test; program alpha spending still controls
  candidate and replication multiplicity.
- QA evidence: 20,000 seeded boundary-null replicates per endpoint produced crossing estimates
  0.0079--0.0116 at component alpha 0.02. In 10,000-run budgeting sensitivities, a true +0.30
  primary effect reached joint success by 1,600 with probability 0.9946 under low and 0.9366 under
  moderate guardrail discordance. A true +0.15 boundary reached only 0.0027, as expected.
- Limits: simulations are not validity proofs or observed power. The large ceiling is not a sample
  target; a qualified-judge pilot must estimate discordance, invalid-run, and unresolved rates and
  set a campaign-specific ceiling prospectively.

## 2026-09-23 — authorize one bounded Luna v3 development clarification

- Decision: run exactly one new development qualification at medium reasoning with prompt v3,
  using the unchanged v2-amended suite, expected labels, thresholds, schema, and 14 development
  cases. Do not inspect or run held-out cases unless this configuration passes every development
  gate and is frozen first.
- Evidence: v2 medium had zero false acceptances, zero false rejections, 94.4% core-field accuracy,
  and 93.75% required-unit accuracy—one status miss. The miss classified an uncommunicated required
  limitation as `incorrect` because the answer contained a separate unsupported causal claim.
  Material-error fields already capture that claim; the unit inventory needs a literal distinction
  between omitted communication and an attempted-but-wrong unit.
- Change boundary: v3 only defines required-unit statuses. A limitation is `omitted` when absent,
  even if separate speculation is materially wrong; `incorrect` is reserved for an attempted unit
  with a wrong value, identity, comparison, sequence, scope, or qualification.
- Multiplicity and cost: this is judge development, not method confirmation and consumes no study
  alpha. Medium is fixed from v2 development evidence and is run once; low/high are not resampled.
  A valid but inconvenient judgment is never retried.
- Failure rule: any missed existing gate retains v3 as another negative result and blocks held-out
  and study scoring. Thresholds will not be relaxed.

## 2026-09-24 — audit required-unit references and freeze v2 medium for held-out

- Decision: adopt the proposition-slot taxonomy in `docs/LUNA_REQUIRED_UNIT_TAXONOMY.md`, correct
  QD003's development-only limitation status from `omitted` to `incorrect`, and select the retained
  v2-medium configuration by offline rescoring. Freeze it before any held-out execution.
- Evidence: QD003 says a scan return caused recovery while its required proposition says physical
  cause remains unresolved; QD011 analogously asserts a failed motor where unique cause remains
  unresolved. Both answers explicitly attempt and contradict the same cause-identity/qualification
  slot. Labeling one omitted and one incorrect was not a coherent reference rule.
- Alternatives: change QD011 to omitted so v3 passes; lower the 95% exact-status threshold; collapse
  exact statuses after seeing failures; or keep prompting. These were rejected. The proposition-
  slot rule supports the QD003 correction independently, preserves QD011, and leaves thresholds,
  held-out expectations, evidence, and outputs unchanged.
- Result: zero-call offline rescoring of the immutable v2-medium judgments passes every development
  gate: 16/16 unit statuses, 94.4% core fields, zero false acceptances/rejections, and all boundary,
  prompt-injection, category, and presentation-invariance gates.
- Validity boundary: development selection is not judge qualification. V2 prompt, medium effort,
  suite, schema, rubrics, caller, retry rule, and two-pass policy are hash-frozen before held-out.
  Study scoring remains prohibited unless both untouched held-out passes independently qualify.

## 2026-09-24 — retain failed Luna held-out qualification and prohibit study scoring

- Decision: retain both frozen held-out passes as executed, do not retry any usable judgment, and
  do not use this Luna configuration to score legacy or diagnostic-study responses.
- Evidence: pass 1 failed required-unit accuracy, category false-rejection, and material-error
  presentation-invariance gates; pass 2 passed unit/core/invariance checks but still made two false
  rejections and failed the diagnostic-omission category. Both passes were operationally valid,
  with no call failure, tool event, false acceptance, or unexpected unresolved label.
- Interpretation: Luna was conservative about incomplete supported answers in a way that conflated
  diagnostic coverage failure with material factual error. This threatens the primary endpoint's
  no-material-error conjunct and cannot be repaired by collecting more study responses.
- Alternatives rejected: rerun until agreement, lower the category gate, silently use pass 2,
  remove the failed categories after inspection, or score study responses provisionally. Each
  would violate the frozen qualification protocol or create outcome-dependent evaluator selection.
- Effect: no confirmatory campaign is active, no study labels or method effect exist, and program
  alpha consumption remains 0.000/0.050. A successor judge requires a separately versioned,
  prospective development decision and fresh held-out cases; an independently checkable or
  explicitly narrower endpoint should be considered against its deadline cost.

## 2026-09-24 — authorize one bounded Luna v4 evaluator cycle

- Decision: prospectively run one medium-effort v4 development qualification over all 28 exposed
  cases, with 14 newly authored independently checkable cases reserved for fresh held-out testing.
- Evidence: the prior held-out failure was concentrated at the semantic boundary between truthful
  diagnostic omission and material factual error. Without a qualified semantic judge, the primary
  endpoint cannot be evaluated; more robot episodes would not remove this blocker.
- Change boundary: clarify that omissions affect coverage/mechanism fields unless actual wording
  asserts something false, and that an explicit false evidence-insufficiency statement is a
  material completeness error. Reconcile QH003/QH006 only in the now-development view under rules
  already motivated independently of any explanation-method comparison.
- Alternatives: use pass 2, rescore the failed holdout, narrow categories after inspection, switch
  judges, or abandon semantic evaluation. The first three violate the freeze; switching models
  broadens scope; immediate abandonment would forfeit the registered endpoint before testing the
  isolated repair.
- Guardrails: same Luna alias, medium effort, schema, rubrics, thresholds, isolation, and retry
  policy. V4 must pass every development gate, then be hash-frozen before exactly two fresh held-out
  passes. Any miss is retained and study scoring remains prohibited.
