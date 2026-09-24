# Luna automated annotation protocol

Protocol ID: `luna-model-judge-v1`  
Status: **PREDECLARED — NO STUDY LABELS GENERATED**  
Declared: 2026-09-23

This document defines a separately named automated evaluation arm. It does not amend or replace
the frozen human rubric in `docs/ANNOTATION_GUIDE.md`, does not turn automated judgments into human
annotations, and does not satisfy the original two-human-plus-adjudicator requirement documented in
`docs/ANNOTATION_WORKFLOW.md`. Human packets remain exportable for a later audit.

## Why this arm exists

The submission will use Luna as the operational semantic evidence auditor so that a full human
campaign is not a prerequisite for analysis. Results from this arm must be described as
**Luna-assessed semantic fidelity**. Independently recomputed quantities remain deterministic
measurements. Repeated Luna passes measure repeatability, not inter-human agreement or accuracy.

The physical-diagnosis redirect remains in force: diagnostic answers are evaluated for the deepest
supported physical or execution mechanism, its connection to the outcome, decisive evidence, and
appropriate limits. Legacy F/G/H answers remain governed by their original substantive rubric and
are not retrospectively required to perform physical diagnosis.

## Declared artifact inventory and prior exposure

Counts below were verified from tracked manifests and packets on 2026-09-23 rather than copied from
a briefing:

| Cohort | Responses | Independent statistical clusters | Status |
|---|---:|---:|---|
| Legacy F/G/H (`sealed-primary-v3`) | 198 | 33 | Collection closed early; unannotated |
| Legacy calibration (`legacy-calibration-e043-v1`) | 6 | 1 development episode | Workflow smoke test only |
| Diagnostic development inventory | 52 | 9 | Development only; 13 packets |
| Diagnostic primary power-planning subset | included above | 6 | Predeclared endpoints only |

The legacy cohort remains 33 clusters. Question variants, conditions, evidence masks, repeated judge
passes, and model-family replications do not create independent robot episodes. The diagnostic
inventory's nine clusters must not be conflated with its six predeclared power-planning clusters.

Before this protocol, project agents/operators had inspected some sealed response text and
verification/fallback metadata during collection and packaging. No sealed material-error labels,
adjudications, condition-key joins, or comparative effect estimates existed. Diagnostic-development
answers and deterministic references had been inspected during method development. The exact legacy
disposition remains recorded in `manifests/study/research-redirect-20260922.json`.

## Model and interface pin

- Requested model alias: `gpt-6-luna`; no substitution is allowed.
- Official model page: <https://developers.openai.com/api/docs/models/gpt-6-luna>.
- Officially documented interface: Responses API with structured outputs; documented reasoning
  efforts are `none`, `low`, `medium`, `high`, `xhigh`, and `max`.
- Operational provider: the configured `codex-lb` Responses endpoint authenticated by the local
  environment, accessed without model tools.
- Provider inventory check on 2026-09-23: `gpt-6-luna` was listed and required Codex CLI version
  `0.155.0` or newer; installed CLI was `0.155.1`.
- Snapshot limitation: the provider exposes the alias and capability metadata, not a resolved
  backend revision. Every call therefore records the requested alias, provider-facing response ID,
  returned model string if present, reasoning effort, request hash, prompt/schema/rubric hashes,
  timestamps, usage, and transport metadata. No stronger version claim is permitted.
- Sampling: temperature and seed are omitted because the reasoning-model/provider path does not
  expose a validated reproducible setting. Actual returned settings are retained where available.

Reasoning effort is selected only on the judge-development split from the bounded candidates
`low`, `medium`, and `high`, in that order for tie-breaking toward lower cost. The chosen effort is
then written to an additive freeze record before the held-out qualification split is run. Study
responses cannot be judged until held-out qualification passes.

## Input boundary and isolation

Every response is judged in a new API request with no conversation history and no model tools. The
runner sends an in-memory, condition-blind envelope containing only:

1. the versioned automated-auditor prompt;
2. the applicable rubric (frozen legacy guide or declared diagnostic guide);
3. the question and evidence-completeness statement;
4. allowed robot-visible evidence and relevant source/configuration excerpts;
5. a separately constructed answerable/required-unit inventory;
6. the candidate's unmodified final answer; and
7. results from approved deterministic calculations, when declared.

The call has no filesystem, shell, web, search, or repository tools. Input artifacts are read by the
coordinator and serialized into the request; evaluator keys and source files are never mounted or
made available to the model. The coordinator keeps condition keys outside the request and output
cache. Candidate text, evidence, and source comments are delimited as untrusted data and cannot
change the rubric or authorize tools.

The judge never receives condition/generator identity, proposed-method labels, developer
impressions, verifier/fallback state, checked answer plans, prior annotations, other methods'
answers, evaluator-only interventions/ground truth, hypotheses, or current comparison results.
Transport-only metadata that would reveal a condition is stripped. Actual wording, formatting,
qualifiers, citations, and numbers are preserved, leaving unavoidable residual stylistic cues that
will be reported as a limitation.

## References and answerability

Checked plans and verifier verdicts are not gold. Reference facts and required units must cite
retained allowed evidence, declared diagnostic contracts, or separately tested calculations.
Deterministic checks may verify identifiers, hashes, attempts, timestamps, elapsed times, numeric
comparisons, units, path geometry, and thresholds, but do not automatically establish sentence
meaning.

Reference inventories are incomplete aids, not closed-world truth: a supported statement is not an
error solely because it is absent. The judge distinguishes:

- `answer_insufficient`: a complete packet cannot establish the requested conclusion;
- `evidence_problem`: the annotation packet is incomplete or inconsistent; and
- `unresolved`: the evidence may be sufficient but the judge cannot reliably interpret the claim.

Judge uncertainty is never converted into candidate error.

## Output and two-pass rule

Outputs must validate against
`research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json`. Each final study
item receives exactly two separately invoked, context-isolated passes under the same frozen
configuration. Passes do not see one another. Presentation order may be independently randomized
only where it does not alter meaning; pass ID and actual settings are retained.

Both valid judgments are immutable and cached by the byte-level question/evidence/rubric/answer,
prompt, schema, model, and effort identity. Byte-identical inputs reuse one audited label mapping
and are not new qualification examples. A failed transport with no usable judgment may be retried
at most twice with exponential backoff. Invalid or inconvenient labels are never retried.

Disagreement is resolved only by an independently checkable deterministic fact or an explicit
predeclared rule. Otherwise the affected field is `unresolved`; both passes remain available. A
third Luna vote is not adjudication. Explanation uncertainty and judge-assessment uncertainty are
reported separately, with worst/best-case sensitivity bounds that retain unresolved responses in
the denominator.

## Qualification before study evaluation

The six legacy calibration responses are a smoke test only. Qualification uses a versioned synthetic
and composition-based suite with a judge-development split and an untouched held-out split. Expected
labels are independently checkable from compact supplied evidence and explicit rubric rules. Cases
cover numeric/count/timestamp/comparison/source errors, unsupported causal links, configured versus
triggered behavior, diagnostic omission, justified and unnecessary abstention, false premises,
correct paraphrase, qualified hypotheses, one-error otherwise-good answers, embedded instruction
attacks, and multi-item evidence composition. Meaning-preserving presentation pairs are explicitly
linked and manually verified before execution.

Development selection ranks `low`, `medium`, and `high` by: (1) all hard gates passed, (2) fewest
category errors, (3) lowest unresolved rate, and (4) lower effort. The following thresholds are
predeclared before any qualification labels:

- zero false acceptances on material-error and prompt-injection cases;
- category-specific false-acceptance rate at most 10%, and zero when a category has fewer than ten
  held-out cases;
- category-specific false-rejection rate at most 10%, and zero when a category has fewer than ten
  held-out cases;
- unresolved rate at most 5% overall and no more than one unresolved case in any category;
- required-unit status accuracy at least 95% overall;
- accuracy at least 90% across the predeclared core semantic fields (judgment status,
  answerability, material error, disposition, mechanism identification, abstention correctness,
  causal overclaim, and evidence-problem status);
- 100% material-error and disposition invariance within verified meaning-preserving pairs; and
- 100% preservation of the distinction among answer insufficiency, packet evidence problems, and
  judge uncertainty.

Rates are reported by category with denominators. Aggregate agreement alone cannot qualify the
judge. If no development configuration passes, the prompt may change only on development data and
receives a new version. If held-out qualification fails, the failure is retained; affected study
categories remain exploratory or are excluded from confirmatory semantic claims under a prospective
amendment. The prompt is never chosen because it favors a study method.

## Analysis and allowed claims

The arm reports Luna pass agreement, unresolved rates, qualification false acceptance/rejection,
unit coverage, causal overclaim, and sensitivity bounds alongside scenario-clustered paired method
comparisons. Confidence intervals conditional on Luna labels do not include systematic judge bias.
Same-family bias is a limitation wherever Luna also generated candidate answers.

Allowed terms include “Luna-assessed semantic fidelity” and “deterministically verified diagnostic
measurements.” Disallowed claims include human agreement, human trust, completed human annotation,
or independent human adjudication. Automated legacy analysis is an additive analysis of frozen
responses, not completion of the original human endpoint. Diagnostic-development cases remain
development evidence regardless of how often they are judged.
