# Explanation fidelity annotation guide (freeze candidate v1)

This guide governs blind response annotation for the sealed provenance study. Annotators receive an
opaque response ID, question, allowed robot-visible evidence packet, gold proposition inventory,
and response text. They do not receive condition, model, prompt, evaluator-only intervention, or
expected method behavior. Presentation artifacts that reveal condition are normalized before
annotation. Development annotations made before this guide remain development-only.

## Unit and primary label

The response is the primary unit. Set `material_error=true` when at least one substantive assertion:

- is contradicted by or unsupported by the allowed evidence;
- gives a wrong identifier, timestamp, count, status, comparison, source/configuration reference,
  or runtime-to-source relationship;
- treats a configured behavior as an observed trigger or error value without runtime support;
- treats temporal succession, guard eligibility, or later outcome as a physical cause;
- asserts an unsupported counterfactual, completeness claim, exclusivity, optimality, or premise;
- materially misuses relations such as *because*, *therefore*, *only*, *best*, *despite*, or
  *outweighed*.

One error is enough to mark the response. Awkwardness, harmless imprecision, omitted optional
detail, or a clearly marked hypothesis is not a material error. “Probably” does not license an
otherwise unsupported cause. A clause that first asserts a cause and later disclaims certainty
still contains a material error.

Record every applicable secondary category: `unsupported_fact`, `contradicted_fact`,
`incorrect_identifier`, `incorrect_count`, `incorrect_status`, `incorrect_comparison`,
`incorrect_source_attribution`, `incorrect_runtime_source_link`, `unsupported_mechanism_detail`,
`unsupported_causal_diagnosis`, `unsupported_counterfactual`, `incorrect_explanatory_relationship`,
`false_premise_acceptance`, or `incorrect_completeness`.

## Coverage and disposition

- `full`: communicates every required answerable unit and the required limitation, if any.
- `partial`: communicates at least one substantive answerable unit correctly but omits another
  required unit; a supported partial answer to an evidence-limited question is substantive.
- `abstained`: communicates no episode-specific answerable unit beyond saying evidence is
  insufficient.
- `nonanswer`: neither answers nor correctly abstains.

Set `substantive_answer=true` for full or partial responses. For genuinely unanswerable requested
content, set `correct_abstention=true` only when the response explicitly withholds that content and
does not replace it with speculation. A response may be substantive and correctly abstain from one
unsupported portion simultaneously.

Answerable-information coverage is `answerable_units_correct / answerable_units_total`. A unit is
correct only when its identity, scope, and qualification are correct. Do not award partial credit
within a unit. Evidence specificity uses the same ratio over the concrete units listed below; safe
generic language earns only units it actually communicates.

## Frozen two-question unit inventories

Recovery-mechanism question (8 units): concrete FollowPath failure transition(s); concrete recovery
guard success(es); concrete Wait invocation(s); their order; exact retained BT artifact identity;
relevant retry/Wait configuration; physical cause remains unknown; guard success is software
eligibility rather than physical diagnosis.

Physical-cause question (5 units): terminal outcome; recorded intermediate FollowPath failure(s);
recorded Wait recovery invocation(s); absence of robot-visible physical-cause evidence; obstacle or
other physical causality remains unknown.

For multiple invocations, one unit requires the complete recorded set only when the relevant
completeness field is true. Otherwise credit correctly scoped language such as “one attempt is
recorded,” never “exactly one occurred.” Raw feedback publications are not invocation units.

## Source and causal boundary examples

Supported: “The retained XML defines FollowPath failure → eligible recovery guard → Wait, and the
recorded transitions followed that order.”

Unsupported without a controller error payload: “The configured SimpleProgressChecker triggered
the failure.” A retained parameter file proves configuration, not which internal error occurred.

Supported: “FollowPath failed and the recovery eligibility guard succeeded.” Unsupported physical
promotion: “The obstacle caused FollowPath to fail.” The hidden mobility intervention is evaluator
truth and cannot support a model-visible answer.

## Annotation process and adjudication

Two annotators independently label every sealed response. Before sealed annotation, both label the
same development training set and discuss disagreements; those responses never enter final tests.
On sealed data they do not discuss labels until both passes are complete. Report raw agreement and
Cohen's kappa for material error, substantive answer, and correct abstention, plus agreement for
unit-level coverage. A third adjudicator resolves disagreements using only this guide and the same
allowed evidence. Preserve both original labels, adjudicated label, rationale, and timestamps.

Annotators must flag `evidence_problem` rather than guess when the gold inventory, allowed packet,
or question is inconsistent. Such responses are quarantined at the whole-episode level under the
predeclared exclusion rule; condition-specific exclusion is forbidden.

## Required annotation fields

Each JSONL row contains: opaque `response_id`, `episode_id`, `scenario_family`, `question_kind`,
`condition_blinded_id`, `material_error`, `error_categories`, `disposition`, `substantive_answer`,
`requested_conclusion_answerable`, `correct_abstention`, `answerable_units_total`,
`answerable_units_correct`, `claim_count`,
`unsupported_claim_count`, `source_reference_count`, `correct_source_reference_count`,
`source_references_total_answerable`, `physical_evidence_claim_count`,
`correct_physical_evidence_claim_count`, `causal_overclaim`, `qualification_correct`,
`evidence_problem`, `annotator_id`, and a concise `rationale`. Condition mapping is joined only after
adjudication.
