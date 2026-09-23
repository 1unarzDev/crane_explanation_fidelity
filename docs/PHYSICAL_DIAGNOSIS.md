# Physical-diagnosis contract

Status: **DEVELOPMENT PATH TESTED / PROSPECTIVE STUDY NOT YET RUN**. A retrospective RoboBoat
development run now exercises measurement extraction, a bounded terminal-margin computation,
checked deterministic rendering, and fail-closed final-text verification. This is an engineering
milestone, not confirmatory evidence or an independently annotated explanation result.

The new method reuses capture, provenance, checked planning, generation, and final verification.
It adds a narrow diagnostic layer before language:

```text
robot-visible observations + commands + execution/source evidence
→ validated diagnostic computations
→ candidate mechanisms, conflicts, and unresolved alternatives
→ checked diagnostic answer plan
→ language
→ final-text verification or deterministic rendering
```

## Diagnostic result

Every result must record:

- diagnostic/result ID, episode and temporal interval;
- input evidence IDs and immutable hashes;
- measured quantities with units, coordinate frames, timestamps, and sampling scope;
- computation name/version and parameters/thresholds;
- assumptions and applicability bounds;
- candidate mechanism and supported causal-language level;
- supporting and contradictory evidence;
- distinguishable and unresolved alternatives;
- sufficiency status independent of whether the implementation produced the desired diagnosis;
- one fixed-menu next check when evidence is insufficient.

Robot-visible diagnostics may use a sensor not consumed by Nav2 to establish a physical condition.
They may claim Nav2 acted *because of* that observation only when runtime dependency/consumption is
established. Evaluator geometry, intervention identity, simulator force decomposition, and hidden
scenario labels never enter ordinary method inputs.

## Initial mechanisms

### Geometric restriction

Compare observed free space to the footprint at orientation, configured safety envelope, and
requested path. Report physical clearance and configured-envelope clearance separately. A local
disconnection establishes only the audited local/model region; an unsuccessful search is not proof
of infeasibility. A controlled rerun may establish that changing geometry/configuration restores
modeled feasibility, but not that physical execution would succeed unless it is executed.

The v2 delivered-plan path records retain every pose plus a SHA-256 identity, length, and signed
deviation from the requested start--goal line. The method recomputes those summaries and fails
closed on missing poses or disagreement; a separately implemented evaluator repeats the same
calculation without importing the method. In the one-run development qualification
`diagnostic-land-dev-004`, both implementations agree that the first delivered plan was direct,
later delivered plans were non-direct on both sides of the requested line, delivered odometry also
deviated, and the action succeeded. This licenses a recorded plan-change explanation. It does not
establish controller consumption or which observation or physical condition triggered the change;
the retained rolling costmap did not cover enough of the complete route to close that causal gap.

### Command-to-motion discrepancy

Align desired command, accepted/applied command where available, actuator feedback, and independent
pose/velocity over a calibrated response window. Thresholds must come from development nominal
trials and include delay/inertia. A discrepancy supports an execution-response mechanism, not a
unique claim of slip, motor failure, collision, wind, current, or waves.

The first passive-capture qualification now exercises this mechanism end to end. It uses fixed
one-second receipt-time windows, five initial command-active windows for within-run calibration,
at least five command and 20 odometry samples per window, a 0.4 m/s minimum command, a response
ratio at or below 0.2, and at least three consecutive low-response windows. These thresholds are
development choices, not frozen confirmatory settings.

For blind episode `diagnostic-motion-dev-cm-001`, the calibrated median planar response was
0.2597 m/s. The earliest qualifying interval was 7–17 s after the first active command: median
delivered Nav2 command remained 0.800 m/s while delivered planar odometry was 0.000 m/s. Two
recorded FollowPath failures were followed by two source-qualified Wait invocations, and a third
FollowPath attempt was active before the action aborted. A separately implemented evaluator-side
window computation reproduces the values without importing the proposed core or exporter.

This establishes a sustained **command-to-motion discrepancy** and its execution sequence. It does
not prove actuator acceptance, Nav2 consumption of the odometry stream, or a unique actuator,
mobility, collision, obstruction, or slip cause. The acquisition rerun qualifies instrumentation;
it repeats a development condition and adds zero independent scenario clusters. Only its blind
robot-visible export may be supplied to explanation methods. Governed artifacts and source hashes
are inventoried by `manifests/data/diagnostic-motion-dev-cm-001.*.json`.

A matched time-resolved nominal rerun provides the real negative control under the unchanged
thresholds. It succeeded after 9.480 m displacement with 366 accepted fixture commands, no
FollowPath failure, and no source-qualified Wait invocation. Its initial measured response was the
same 0.2597 m/s median, and no required consecutive low-response sequence occurred. The checked
answer therefore leads with the false failure premise and returns `not_triggered`; its independent
reference and QA also pass. This is still repeated development calibration, not another independent
cluster. Its manifests are `diagnostic-motion-dev-cm-nominal-001.*.json`.

A predeclared, independently configured development scenario tests the same mechanism with
successful compensation. The unchanged thresholds identify an 8--18 s discrepancy with median
0.800 m/s delivered command and 0.000 m/s measured response. A later command-active 20--21 s
window records 0.2597 m/s measured response (ratio 1.0), after which the action succeeds at
9.469 m displacement. The retained execution includes one FollowPath failure and one
source-qualified Wait invocation. This supports **transient command--motion discrepancy followed
by recovered measured response**, while continuing to withhold actuator acceptance, Nav2 odometry
consumption, intervention identity, and any unique motor/slip/collision/obstruction cause.

The initial checked response merely appended the successful terminal status and did not quantify
recovery. The v2 recovery-window computation and revised deterministic response were added only
after that deficiency was observed. They are therefore post-observation development and regression
evidence, not a prospective method-effect result.

A subsequently predeclared single-sample R/P/T/N comparison retains the same evidence, tool
parity, model, and no-retry rules as the earlier pair while asking explicitly about temporary loss
and later success. On project review, R changes the checked 8--18 s / 10 s discrepancy into
8--20 s / 12 s; raw P preserves the checked mechanism, values, recovery, outcome, and limits; N has
no aligned computation and calls Wait/retry the changed condition demonstrably associated with
success. The operating verifier rejects raw P for a missing controller-failure-sequence
proposition, so immutable final P again falls back to T. These are candidates for blinded scoring,
not labels. The scenario now has a four-response packet, but still no human labels.
Robot-visible and evaluator-only artifacts are governed separately by
`manifests/data/diagnostic-motion-development-cm-002.*.json`.

After retaining that output, a post-hoc v2 language-gate correction was regression-tested against
the exact archived raw P candidate. It accepts a `FollowPath` failure proposition in decisive
evidence while continuing to require the Wait/recovery temporal connection in the failure-chain
section. It rejects a candidate that omits `FollowPath` entirely and a candidate that says the
Wait invocation caused measured response to recover. This is disclosed tuning evidence only: the
archived v1 rejection, final fallback, packet, and 12/12 observed fallback frequency are unchanged.

### Perception/model inconsistency

Add only after the first two mechanisms work end to end. Compare sensor timestamps/transforms and
observations with map updates. Obstacle disappearance in evaluator truth is not robot-visible proof
that the navigation representation was stale.

## Language acceptance gate

Final answers use four short sections:

1. **Diagnosis:** deepest supported physical/execution mechanism in ordinary language.
2. **Decisive evidence:** only the measurements needed to support it, with units and evidence IDs.
3. **Failure chain:** connection to planner/controller/recovery/outcome plus exact relevant source
   semantics.
4. **Limits and next check:** unresolved alternatives and one discriminating measurement/test.

Withholding a supported diagnosis is an informative-content failure. Adding an unsupported unique
cause is a material error. Candidate language, verification outcome, final rendering, and fallback
frequency are all retained and reported. If deterministic rendering dominates, the method is
described as predominantly deterministic rather than as successful LLM reasoning.

The original development gate accepted only byte-identical deterministic renderings and therefore
fell back on 8/8 diagnostic questions. A separate bounded verifier is now implemented for future
prospective use. Its single interface parses the four required sections, applies at most one
evidence-ID-only repair, licenses numerical claims against the checked result, enforces
mechanism-specific required propositions, and rejects unsupported physical-cause wording. It does
not alter substantive language or call another model.

A post-hoc audit accepted 7/8 previously rejected fluent candidates after citation repair and
rejected all 24 simple adversarial mutations. It correctly retained rejection of the masked-speed
candidate, which introduced two derived values absent from its checked plan and misplaced the
missing-measurement limitation. Because the verifier and mutations were authored after inspecting
these candidates, this is a development regression result—not an independent estimate of verifier
accuracy and not a retroactive change to any archived final response or fallback decision.

The current future-execution policy is `bounded-diagnostic-language-v3`. Version v2 records the
post-hoc section-scope correction exposed by the compensated-motion output. V3 adds `route change`
to the delivered-plan proposition matcher after the plan-change pilot exposed a narrower lexical
false negative; the exact archived candidate passes after citation-only repair while a mutation
that removes the controller-consumption limit still fails. Historical v1/v2 outputs remain
identified by their retained core commit and verification policy, and their fallback decisions are
unchanged.

## Signal semantics

- Nav2 Jazzy `FollowPath.feedback.speed` is command-derived in the audited source revision, not an
  independent motion measurement.
- Commands, accepted/applied actuation, actuator feedback, odometry, IMU, simulator truth, and
  environment settings are distinct evidence types.
- For RoboBoat, a lumped lateral residual does not distinguish current, wind, waves, actuator
  imbalance, or model error. Say “uncompensated lateral disturbance” unless a validated
  robot-visible diagnostic distinguishes more.
- A directly applied force is a synthetic disturbance experiment, not validated wave physics.

## First measured development diagnosis

The retained `roboboat-gate5-known-dock-1` run supports a narrow configuration/execution
diagnosis. The action returned success at 0.374 m error and independently measured 0.0486 m/s,
inside its exact 0.400 m XY and 0.050 m/s stopped thresholds. The declared task required at most
0.400 m error, leaving 0.026 m of margin. Delivered odometry then recorded 0.188 m of post-result
motion and a final 0.561 m error. Thus the terminal criterion did not reserve enough margin for
the observed post-result motion.

This does **not** identify the physical origin of the residual motion. The robot-visible
development export deliberately excludes the docking-success label, matched-intervention result,
hidden simulator state, and force decomposition. It is governed at
`data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json` via
`data/robot_visible/dev.dvc`; its source hashes and reproduction entry point are recorded in
`manifests/data/roboboat-terminal-margin-development-v1.robot-visible.json`.

A paired development evidence mask omits measured speed at action return. The same computation
then returns `insufficient` and names that missing measurement instead of asserting the mechanism.
The mask is a selective-specificity regression, not a naturally missing held-out episode; evaluated
methods must not be able to retrieve its paired unmasked artifact.

### Retained RoboBoat navigation-model disconnection

A second retrospective RoboBoat artifact exercises a distinct geometric/planning mechanism. The
embedded global-costmap payload hashes to
`c3d7ef6bcc1c9d40c610efc8e1c95c4e3355c80fca4551df0c84f446d175d636`.
Independent decoding places the action-result pose in cost 0 and the requested goal in cost 253;
an eight-connected search finds no connection through cells below 253. The retained controller log
contains 23 exact Navfn `Failed to create plan with tolerance of: 0.500000` messages for that goal
before the action aborted. The deepest supported explanation is therefore a **retained navigation-
model disconnection corresponding with recorded planner failures**, not generic recovery
exhaustion.

The evidence does not prove that a particular physical dock object caused the grid restriction,
that every planner invocation consumed this exact snapshot, or that no physical route existed
outside the retained grid or under another configuration. Evaluator-only history identifies the
goal as the obsolete wrong-side target, but that label is unavailable to the ordinary explanation
method. A later corrected-goal success also changed the planning-window configuration and is not a
matched one-factor intervention.

The compact robot-visible artifact and evaluator-only interpretation are physically separated and
governed by `manifests/data/roboboat-grid-disconnection-development-v1.*.json`. The historical run
occurred with uncommitted costmap-capture code whose exact dirty diff was not retained, so this case
is explicitly ineligible for confirmatory evaluation. It remains useful development evidence and
can be recomputed from a fresh checkout without the original multi-megabyte fixture.

## First measured land diagnosis

The governed `land-blockage-global-002` development run exercises the geometric path without using
evaluator geometry. Its retained global costmap marks the requested centerline non-traversable
beginning near x=8.45 m and gives zero minimum lethal-cell clearance under the configured 0.22 m
robot radius and 0.55 m inflation. Delivered odometry records a 2.705 m lateral detour. The action
aborted in 70.860 s under the exact 70 s BT deadline.

The same retained grid still has a below-cost-253 connection from the action-result pose to the
goal. The supported diagnosis is therefore **direct-route model restriction plus a deadline-aligned
abort**, not global no-path or physical impossibility. Sixty-nine planning updates succeeded, no
recovery invocation is exact-count eligible, and the terminal BT transition was not observed. The
answer explicitly retains these conflicts and observation limits.

Robot-visible fixture/QA/diagnostic/build-provenance artifacts are governed through
`manifests/data/land-blockage-global-002.robot-visible.json`; scenario identity and Unity runtime
truth remain separate under the corresponding evaluator-only manifest. This is a development
response-quality milestone, not evidence that the proposed method beats R, N, or T.

## Bounded warehouse recovery mechanism

The retained ecological warehouse episode `eco-pilot-001` supplies a deliberately ambiguous
execution-mechanism case. A checked computation matches four unique capture-side invocation IDs
to the hash-pinned exact-name recovery classifier, their `IDLE→RUNNING` and terminal transitions,
and the ordered `ComputePathToPose` failure, `NavigateWithReplanning` failure,
`WouldAPlannerRecoveryHelp` success, and system-recovery entry preceding each leaf. The retained
sequence is `Spin→SUCCESS`, `Wait→SUCCESS`, `BackUp→SUCCESS`, and `Spin→SUCCESS`; the navigation
action eventually succeeded.

This establishes **at least four retained source-qualified recovery invocations**, not exactly
four over the goal lifetime. Whole-history completeness is not proven, and the maximum Nav2
feedback recovery count of 16 is not an invocation identity. The computation also does not infer
why planning failed: delivered costmaps are not proof of the exact planner-consumed state, and no
physical obstacle cause is established. The checked result is therefore useful for recovery
mechanism and causal-restraint evaluation, not a physical-cause diagnosis.

The source export and derived checked answer are governed through
`manifests/data/ecological-warehouse-recovery-development-v1.robot-visible.json`. Reproduce the
derivation with:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/export_recovery_execution_diagnostic.py \
  data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json \
  --source-reference data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json \
  --output data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/recovery-execution-diagnostic.json
```

## Command-motion language and parity dry run

The command-motion pair now has a no-retry R/P/T/N development comparison. For the primary fair
comparison, R received the same blind method input and executable window computation as P, plus the
exact pinned CRANE and diagnostic-core repositories. N received the same compact runtime/source
facts without the aligned computation and is therefore an explicit computation ablation, not an
information-parity baseline.

On project review, tool-enabled R and raw P both identify the supported sustained discrepancy; N
only calls it suggested. R, raw P, and N reject the matched nominal failure premise. The original P
candidate in each case was rejected by the then-current bounded gate—once because a requested next
measurement contained “actuation,” and once because `wind` matched inside `fixed-window`. Final P
therefore fell back to T in both immutable outputs. Whole-word and next-check-aware matching was
subsequently regression-tested; a post-hoc audit accepts both archived raw candidates after only
the allowed evidence-ID repair and rejects six authored unsupported-number, unsupported-wave, and
missing-limits mutations. This audit is tuning evidence, not an independent verifier evaluation.

The two four-response annotation packets are blinded and share one statistical cluster. Human
annotation and adjudication remain `NOT_RUN`; no effectiveness conclusion follows from project
review. The governed output, packet, key, reference, and verifier-audit hashes are recorded in
`manifests/model_outputs/diagnostic-command-motion-pilot-v1.json`, the two
`manifests/annotation/diagnostic-command-motion-*-pilot-v1.json` files, and
`manifests/data/diagnostic-command-motion-language-verifier-development-v1.evaluator-only.json`.

A predeclared third variant removes only the independently measured odometry samples. It retains
376 delivered command samples, action abort, two FollowPath failures, two source-qualified Wait
invocations, and all source hashes. The checked plan correctly returns `insufficient`: those
sequence facts remain useful, but without measured motion they cannot establish that commands
failed to produce motion. A pre-model independent evaluator reproduces this answerability boundary
without importing the proposed diagnostic result.

Tool-enabled R, raw P, and N all preserve the central withholding on project review, so this is
another negative differentiation result pending blind scoring. N additionally says “exhausted
recovery behavior”; whether that is a material completeness/causal overclaim is deliberately left
to annotators. The original P candidate was useful but rejected by a section-local verifier rule,
making overall development fallback 11/11 at that checkpoint. A post-hoc correction accepts it
after citation-only repair and rejects three authored mutations; the original fallback and packet
remain immutable.
