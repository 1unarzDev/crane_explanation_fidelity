# Physical-diagnosis contract

Status: **PROSPECTIVE / NOT YET VALIDATED END TO END**.

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
