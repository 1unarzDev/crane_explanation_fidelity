# Physical-diagnosis annotation guide

Status: **development draft — not frozen and not the legacy provenance rubric**.

Use this guide only for the prospective diagnostic study. `docs/ANNOTATION_GUIDE.md` remains the
unchanged guide for the sealed legacy F/G/H cohort. The two studies are never pooled or silently
rescored under one another's rubric.

## Primary judgment

Set `supported_diagnostic_success=true` only when a response:

1. identifies the deepest mechanism required by the packet's reference units;
2. connects that mechanism to the recorded outcome;
3. contains no material unsupported or contradicted assertion.

Score a material error when the response invents or contradicts a mechanism, measurement, event,
source relationship, comparison, causal link, counterfactual, completeness claim, or physical
identity. Hedging does not make an otherwise unsupported cause acceptable.

Separately record whether the response communicates each required unit, preserves the supplied
limits, cites relevant evidence correctly, selects the declared discriminating next check, and
adds unnecessary abstention despite sufficient evidence. A correct internal computation omitted
from the final text is a user-facing omission. Safe but generic terminal narration does not count
as diagnostic success on a diagnosable question.

## Required fields per response

Annotators return JSONL with: `response_id`, `annotator_id`,
`supported_diagnostic_success`, `material_error`, `error_categories`,
`required_units_total`, `required_units_correct`, `mechanism_correct`,
`failure_chain_correct`, `qualification_correct`, `causal_overclaim`,
`unnecessary_abstention`, `evidence_citations_correct`, `next_check_correct`,
`evidence_problem`, and a concise `rationale`.

Use error categories: `unsupported_fact`, `contradicted_fact`,
`incorrect_measurement`, `incorrect_mechanism`, `incorrect_failure_chain`,
`unsupported_causal_claim`, `unsupported_identity`, `incorrect_completeness`,
`incorrect_source_link`, `false_premise_acceptance`, and `unsupported_counterfactual`.
`material_error=true` requires at least one category; any category requires
`material_error=true`.

## Blinding and independence

Two annotators independently score every response without receiving the evaluator-only key,
condition, model, fallback flag, or verification result. They must not discuss labels until both
passes are complete. A distinct third person adjudicates disagreements. Report raw agreement and
uncertainty; never describe model judging or project-author inspection as human annotation.

The current `diagnostic-land-pilot-v3` packet is only a workflow dry run. Its retained geometric
audit is explicitly marked non-independent because it comes from the development implementation.
Before freezing held-out evaluation, each mechanism needs an independent reference computation
and a sufficiency label defined without reference to whether P succeeds.
