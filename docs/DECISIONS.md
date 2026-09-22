# Decision Log

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
