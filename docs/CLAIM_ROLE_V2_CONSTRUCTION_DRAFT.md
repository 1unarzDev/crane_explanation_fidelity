# Assertion-role successor: construction draft

Date: 2026-09-30. Status: **uncalled development candidate; not frozen or qualified**.

This is a measurement repair after the retained failed v1 role qualification. It changes no
claim contract, method output, evidence mask, evaluator reference, or primary endpoint. The
post-output v1 diagnosis is `docs/CLAIM_ROLE_V1_SEMANTIC_REVIEW.md`. The v1 gold and returns
remain immutable failed development evidence.

## Input and task

Give the isolated classifier only the exact answer text and a **reviewed**, method-blind atomic
inventory. It receives no evidence packet, evaluator truth, support label, method identity, or
prior role decision. For each atom, classify three separate properties:

1. **Stance**: asserted about this episode, offered as a hedged episode candidate, an inference
   limit/non-entailment, an unendorsed hypothetical or quotation, or unresolved.
2. **Claim kind**: what the atom is about, using the explicit categories below. Kind does not
   establish evidential support and is not itself an endpoint failure.
3. **Polarity**: positive occurrence, explicit nonoccurrence, or not applicable. “Cannot establish
   a motor fault” is an inference limit, not a negative motor-fault finding.

The output must quote an exact substring of that atom's response span as its rationale. A
structural validator should require exact atom IDs and ordering and reject extra or missing
claims. It must report `endpoint_scoring_authorized=false` until a fresh qualification and a
prospectively bound kind/stance/polarity-to-endpoint mapping pass.

## Claim-kind codebook candidate

| Kind | Includes | Boundary |
| --- | --- | --- |
| `TASK_OUTCOME` | Recorded goal success, abort, or explicit episode nonoccurrence | An outcome is not automatically a physical mechanism. |
| `SOFTWARE_ACTION_EVENT` | Reported `FollowPath` failure, action status, or error code | A controller code does not prove physical response loss. |
| `RECOVERY_TRACE_EVENT` | Source-qualified recovery invocation or `Wait` completion | `Wait` completion does not prove measured recovery or its cause. |
| `MEASURED_RESPONSE_RECOVERY` | Explicit later measured-motion recovery | “Motion returned” without a measurement source is ambiguous. |
| `MOTION_OBSERVATION` | Stationarity, measured speed, or response loss without command comparison | No command-motion discrepancy or unique cause follows. |
| `COMMAND_OBSERVATION` | Delivered command values or stream presence | Delivery does not prove actuator acceptance. |
| `COMMAND_MOTION_RELATION` | An explicit delivered-command versus synchronized measured-motion comparison | A command alone or stationary robot alone is insufficient. |
| `GEOMETRY_PLANNING_RELATION` | Direct-route restriction, connected detour, or governed plan relation | Geometry stays a non-pooled secondary arm. |
| `SPECIFIC_PHYSICAL_CAUSE` | Motor failure, wheel slip, collision, obstruction, or a causal relation naming such a cause | Hedged and negative findings keep their stance and polarity; neither is silently exempted. |
| `RECOVERY_CAUSAL_RELATION` | Claim that recovery activity caused motion or task outcome | Mere temporal ordering is not causation. |
| `SOURCE_OR_CONFIG_FACT` | Source quote, configuration value, trace contents or absence, citation, or a statement that a quote is not a diagnosis | Absence from a trace is not physical nonoccurrence. |
| `EVIDENCE_AVAILABILITY` | Missing odometry, missing code, or packet field availability | Missingness licenses a limit, not the hidden diagnosis. |
| `OTHER` | A reviewed atom that fits none of the above | Requires separate inspection before endpoint use. |

The v1 linear level labels must not be copied onto all kinds. Geometry has its own ontology
branch. A mapping from asserted/hedged kinds and polarity to mechanistic flags and diagnostic
abstraction is an explicit later development/P11 decision. `OTHER` and unresolved returns must
have prospectively fixed handling. Numeric values, source IDs, hashes, evidence thresholds, and
maximum justified levels remain deterministic/reference-scored, never inferred from this task.

## Pre-call reference and qualification gates

Construct new synthetic text with separate development and fresh held-out cases. Exposed v1
held-out sentences cannot be reused as held-out qualification. Include, in new wording, paired
contrasts for recorded versus physical nonoccurrence, `Wait` completion versus measured motion
recovery, raw stationarity versus command-motion relation, physical-cause hedges, geometry
relations, source quotation versus endorsed diagnosis, limitation versus negative finding, and
temporal recovery order versus causal attribution. Split every independent fact and relation
into an atom before freezing.

Before any model call: review each atom and gold field against the exact text, validate the
schema and prompt, bind raw hashes and the no-retry runner, and freeze explicit held-out gates.
Then use a non-study schema canary and two isolated no-tool passes with the exact chosen model
configuration. A structurally valid return is not semantic qualification. Any reference defect
invalidates the successor qualification; no post-output regrading or pilot-label rescue is
permitted.

The pending 113 pilot inventories still require response-by-response semantic completeness
review. This draft cannot be applied to them or used to score B2/B4. Confirmation and replication
independent N remain zero; P11 remains closed.
