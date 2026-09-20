# Decision Log

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
  checked method G the central novelty comparison. Integrate the temporary follow-up direction
  into canonical architecture, study, benchmark, research, environment, and decision documents.
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
