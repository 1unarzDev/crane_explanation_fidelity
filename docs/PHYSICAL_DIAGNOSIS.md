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

### Command-to-motion discrepancy

Align desired command, accepted/applied command where available, actuator feedback, and independent
pose/velocity over a calibrated response window. Thresholds must come from development nominal
trials and include delay/inertia. A discrepancy supports an execution-response mechanism, not a
unique claim of slip, motor failure, collision, wind, current, or waves.

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
