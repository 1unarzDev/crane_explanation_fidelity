# Luna automated annotation protocol

Protocol ID: `luna-model-judge-v1`  
Status: **HELD-OUT QUALIFICATION FAILED — NO STUDY LABELS GENERATED**
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

For any new sequential diagnostic campaign, this protocol is subordinate to the additional gate
in `docs/SEQUENTIAL_STUDY_PROTOCOL.md`: a newly versioned Luna arm must pass development and
untouched held-out qualification before the first confirmatory label. Its complete rubric,
references, model/settings, two-pass rule, and qualification-manifest hash are frozen with the
campaign. The current v1/v2 failures cannot be repaired by accumulating more study responses, and
any unresolved primary or guardrail field prevents a success declaration while remaining in the
reported sensitivity analysis.

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
- Operational provider: the configured `codex-lb` Responses endpoint through an ephemeral Codex CLI
  process inside a bubblewrap namespace. The namespace contains only the system runtime, an empty
  temporary work directory, the output schema, and non-secret minimal provider configuration. Shell,
  browser, app, plugin, computer, and unified-exec features are disabled; any observed non-language
  tool event invalidates the call without retry.
- Provider inventory check on 2026-09-23: `gpt-6-luna` was listed and required Codex CLI version
  `0.155.0` or newer; installed CLI was `0.155.1`.
- In the isolated custom-provider profile, CLI 0.155.1 emits a recorded fallback-model-metadata
  warning even when its copied provider inventory contains `gpt-6-luna`. The requested model and
  effort remain explicit, but this client-side limitation is reported and the warning is retained.
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

Prompt/suite v1 failed every reasoning configuration on development and is retained in
`manifests/annotation/luna-model-judge-v1-development-v1.json`. Before any held-out call, v2 made
one bounded clarification of rubric-derived output semantics and corrected ambiguous/incorrect
fixture expectations through a hashed additive amendment. V1 is not overwritten or presented as a
successful validation. V2 also failed: medium and high made no false material-error decisions and
exceeded 94% core-field accuracy, but achieved only 93.75% and 87.5% required-unit accuracy against
the fixed 95% gate. No effort was frozen, and neither held-out nor study scoring ran. No further
prompt iteration is authorized by this protocol without another prospective decision entry.

That decision was recorded on 2026-09-23 for one bounded v3 development attempt. V3 does not
change the suite, expected labels, thresholds, output schema, evidence, or held-out split. It adds
literal definitions for `covered`, `omitted`, `incorrect`, and `unresolved` required-unit statuses.
Based on v2 development only, medium is the sole predeclared reasoning configuration; low/high are
not rerun. If medium fails any existing gate, judge development stops again. If it passes, its
prompt/model/settings are frozen before the still-untouched two-pass held-out qualification.

V3 was executed once on 2026-09-24 and failed the same exact-status gate: 15/16 required-unit
statuses (93.75%), with zero false acceptances, false rejections, call failures, or unexpected
unresolved judgments. It corrected QD003 to `omitted` under the new literal rule, but the unchanged
development suite expected the analogous uncommunicated unique-cause limitation in QD011 to be
`incorrect`. Held-out remained unrun. This exposes a development taxonomy/reference inconsistency
that must be independently resolved before another judge version; it does not authorize lowering
the 95% threshold or scoring study answers.

The independent proposition-slot audit in `docs/LUNA_REQUIRED_UNIT_TAXONOMY.md` concluded that both
QD003 and QD011 explicitly attempt and contradict the required unresolved-cause proposition, so
both are `incorrect`; the prior QD003 `omitted` expectation was inconsistent. An additive amendment
changes only that development expectation. Offline rescoring of the already retained v2-medium
calls then passes every unchanged gate with 16/16 required-unit statuses, zero new model calls, and
94.4% core-field accuracy. V2 medium and the audited suite are frozen in
`luna-model-judge-v2-medium-freeze.json` before any held-out execution. This development selection
does not itself qualify the judge or authorize study scoring.

The frozen two-pass held-out qualification was executed once on 2026-09-24 and failed. All 28
calls were valid, with no retry, tool event, false acceptance, or unexpected unresolved judgment.
Pass 1 achieved 15/17 exact required-unit statuses (88.2%) and 97/107 core fields (90.7%), but
made three false rejections and changed the material-error label across the verified presentation
pair. Pass 2 achieved 17/17 required units and 98/107 core fields (91.6%), but made two false
rejections. In both passes the diagnostic-omission category failed closed because Luna treated
supported-but-incomplete answers as material errors; pass 1 additionally rejected a correct
paraphrase. Both passes passed the answerability-boundary and prompt-injection checks. The retained
report is governed under `model_outputs.dvc` and indexed by
`manifests/annotation/luna-model-judge-v1-heldout-v1.json`.

This is a judge-validity failure, not a comparison of explanation methods. The usable unfavorable
judgments will not be retried, thresholds will not be relaxed, and this configuration must not
score study responses. Any later automated judge requires a separately versioned prospective
development cycle and fresh held-out qualification; confirmatory collection remains blocked until
such a judge and the candidate/baseline/resource contract are frozen.

V4 is that bounded prospective cycle. Its only prompt change makes the existing rubric boundary
literal: truthful but incomplete narration is a coverage/mechanism omission, whereas an explicit
false statement about evidence sufficiency is a separately assessed material completeness error.
All 28 cases exposed in earlier development or held-out runs are development-only for v4. The
suite reserves 14 newly authored, independently checkable `QN` cases as a fresh held-out split;
none may be executed until the one-shot medium-effort development run passes every unchanged gate
and the exact configuration is hash-frozen. Two exposed reference inconsistencies are corrected
only in the v4 development view: an attempted unsupported cause is `incorrect`, and an explicit
false evidence-insufficiency claim is a material error. Prior reports and labels remain immutable.
The predeclaration is `manifests/annotation/luna-model-judge-v1-v4-predeclaration.json`.

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
