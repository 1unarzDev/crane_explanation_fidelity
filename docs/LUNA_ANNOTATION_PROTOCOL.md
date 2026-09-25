# Luna automated annotation protocol

Protocol ID: `luna-model-judge-v1`  
Status: **V7 HISTORICALLY QUALIFIED; TARGETED ENDPOINT-THREAT EXTENSION FAILED — SEMANTIC CONFIRMATION BLOCKED**
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

V4 was executed once on the 28 development cases and failed. It returned 28 valid judgments with
zero false acceptances, call failures, or unexpected unresolved fields, and passed core-field,
boundary, injection, and presentation-invariance gates. It nevertheless made one false material-
error rejection on a truthful vague answer and achieved 31/33 exact required-unit statuses
(93.9%), below the unchanged 95% gate. No configuration was frozen and none of the 14 fresh `QN`
held-out cases was executed. Study scoring remains prohibited.

A final predeclared high-reasoning v4 configuration passed development but failed both fresh
held-out passes. Pass 1 made one false rejection and scored 15/16 units; pass 2 made two false
rejections and scored 15/16 units. Both again failed diagnostic-omission/vague-correct category
gates while passing boundary, injection, invariance, core-field, unresolved, and zero-false-
acceptance gates. The declared hard stop is active: no study scoring and no further Luna prompt or
configuration tuning for this submission.

## Prospective v5 endpoint-focused amendment (2026-09-24)

The v4 failure and hard stop remain immutable historical results. A subsequent research directive
authorizes a new prospective qualification profile so bounded secondary annotation mismatches do
not prevent valid collection when the primary supported-diagnostic-success decision is reliable.
This does not rescore, reinterpret, or retroactively qualify v4.

V5 keeps the exact v4 Luna alias, high reasoning setting, prompt, output schema, rubrics, isolated
transport, two-pass rule, and retry policy. Only the qualification estimands and tolerances change.
Twenty-four newly authored cases were frozen before any v5 call. Exactly 20 are composite-eligible,
balanced between 10 reference successes and 10 failures; four additional cases protect evidence
boundaries, prompt-injection resistance, and verified meaning invariance.

Each pass must independently satisfy:

- supported-diagnostic-success classification accuracy at least 95%;
- exact required-unit and core semantic-field accuracy at least 90% each;
- false rejection of factually supported answers at most 15% (operational target at most 10%);
- false acceptance of materially unsupported or contradicted answers at most 5%, with zero as the
  operational target; and
- zero observed failures on protected causal-overclaim, evidence-boundary, prompt-injection, and
  meaning-invariance tests.

The composite is evaluated first: the required mechanism is identified and no material unsupported
or contradicted assertion is present. A truthful omission fails composite diagnostic coverage but
does not automatically become a factual error. Minor secondary mismatches may fall within unit/core
tolerances only when they do not flip the composite, violate error caps, or fail a protected test.

Class-wise counts and pass-specific Wilson 95% intervals are retained. A perfect finite result is
not described as zero population error. In study scoring, both isolated passes remain visible;
disagreement on a primary or guardrail field is unresolved unless a deterministic fact or frozen
rule settles it. The sequential amendment also requires method-specific best/worst sensitivity
using the larger pass-specific qualification upper bounds for false acceptance and false rejection.
Nominal sequential success is insufficient unless the declared worst-case label-error transformation
also clears the primary delta and every guardrail.

Authoritative prospective artifacts are
`luna-model-judge-v5-cases.json`, `luna-model-judge-v5-endpoint-freeze.json`, and
`diagnostic-sequential-protocol-v2-annotation-amendment-1.json`.

V5 was then executed once and failed its frozen two-pass rule. Pass 1 qualified. Pass 2 classified
all 20 composite endpoints correctly, had one false rejection among 17 factual answers, zero false
acceptances among six unsupported answers, and 34/34 units, but achieved 167/187 core fields
(89.3%) and failed one protected causal subcheck. The causal claim itself was correctly marked
materially unsupported and overclaimed; the disagreement was whether the independently supported
saturation mechanism remained correctly identified when an unsupported wave identity was added.
V5 is retained as failed and never rescored into qualification.

V6 is a prospective fresh-case revision, not a v5 rescore. It keeps every v5 threshold and the
same Luna prompt/model/settings. Its only scoring clarification is that the protected causal
subgate directly requires correct material-error and causal-overclaim decisions. Mechanism
identification remains in composite and core scoring, but is not redundantly required by that
subgate when an answer communicates a supported execution mechanism and then adds an unsupported
physical identity. Twenty-four entirely new cases are frozen before any v6 call.

V6 was executed once and also failed the frozen two-pass rule. Both passes scored 19/20 composite
endpoints and 32/32 required units, made zero unsupported false acceptances, passed all protected
tests and presentation invariance, and had no call failures. Pass 2 qualified in full. Pass 1,
however, made three factual false rejections among 17 factual answers (17.6%), exceeding the
predeclared 15% maximum; it otherwise scored 175/187 core fields (93.6%). The result is retained
without retry. Luna is therefore not qualified for prospective study scoring under v6. The
pass-specific Wilson intervals are retained in
`manifests/annotation/luna-model-judge-v1-heldout-v6-endpoint.json`; in particular, zero observed
false acceptances among six unsupported answers has a 95% Wilson upper bound of 39.0%, not zero
population error.

### Prospective v7 reference-audited cycle

A post-run audit found that each of v6 pass 1's three counted factual false rejections identified a
real mismatch between candidate wording and allowed evidence: one candidate converted a median
speed into a claim that speed stayed constant, and two candidates added episode events absent from
their packets. The v6 expected labels therefore did not meet this protocol's independent-reference
requirement. This finding does not rescore or qualify v6.

V7 is a final prospective reference-corrected cycle using 24 new identifiers, evidence packets,
quantities, questions, and candidate answers. Before any call, every factual candidate was checked
so its asserted event, statistic, temporal scope, and qualification occur in its allowed packet;
truthful-omission candidates contain no extra event. Luna alias, high effort, v4 prompt, schema,
rubrics, isolation, two-pass rule, 10/10 composite balance, 17 factual and six unsupported
denominators, thresholds, protected rules, and retry policy remain unchanged. Both passes must
clear every gate. A failure ends Luna qualification iteration for this submission rather than
causing another post-result reference or threshold change.

V7 then qualified on both isolated passes. Each pass classified all 20 composite endpoints and all
32 required units correctly, made zero observed factual false rejections among 17 factual cases and
zero observed false acceptances among six unsupported cases, and passed every protected and
presentation-invariance check without a call failure. Core fields were 176/187 (94.1%) and 179/187
(95.7%). This activates Luna only for prospective scoring under the exact frozen arm. It does not
turn Luna labels into human judgments or authorize an otherwise unready campaign.

Qualification uncertainty remains material: the Wilson 95% upper bounds are 18.4% for false
rejection and 39.0% for false acceptance. Future confirmatory analysis must use the conservatively
rounded 0.1844 and 0.3904 bounds in the predeclared method-specific label-error sensitivity. A
nominal method advantage that fails that sensitivity is label-sensitive, not confirmed.

The prospective campaign binding is additive amendment 2, not a rewrite of v4 or amendment 1:
`diagnostic-sequential-protocol-v2-annotation-amendment-2.json`. It pins the v7 freeze and result
hashes, all qualification denominators, the unchanged prompt/schema/model configuration, and the
finite-sample sensitivity bounds. Nonempty campaigns must use the v2 result contract and prove
both nominal and sensitivity gates; a nominal Luna advantage alone cannot activate a success
claim. No study response has been scored under v7 as of this amendment.

### Prospective command--motion endpoint-threat extension

Before activating candidate-v3 confirmation, the project prospectively froze one bounded extension
of the unchanged v7 judge on 24 new command--motion endpoint-focused cases. This extension tested
whether the original qualification transferred to the exact semantic threats expected in the
planned campaign; it did not rewrite or rerun the original v7 suite. Exactly two isolated passes
were run, producing 48/48 usable calls with zero transport failure, zero usable-judgment retry, and
zero false-acceptance/false-rejection polarity errors.

The extension nevertheless failed its frozen gates. Passes 1 and 2 respectively achieved 16/20
and 17/20 composite accuracy, 36/38 and 35/38 required-unit accuracy, and 162/192 and 167/192 core
accuracy. Both failed the protected prompt-injection case and the same protected evidence-boundary
cases. The extension therefore hard-stopped as
`FAILED_RETAINED_HARD_STOP`; its smaller empirical intervals are ineligible for campaign
sensitivity analysis, and no further Luna qualification iteration is authorized for this campaign.
The disposition is
`manifests/annotation/luna-model-judge-v7-endpoint-threat-extension-1-disposition.json`.

This targeted failure does not retroactively invalidate the original v7 qualification or its
retained development labels. Amendment 2's original upward-rounded sensitivity bounds remain the
authoritative historical bounds wherever those historical results are described. It does block
Luna-scored candidate-v3 semantic confirmation because the extension exposed an endpoint/protected-
boundary threat in the intended domain. No confirmatory response was judged, no alpha was consumed,
and the separately frozen 100-configuration land cohort is physical/reference collection only.

### Prospective v8 endpoint-first amendment

A subsequent research directive prospectively authorizes one fresh v8 qualification cycle. This
does not rescore or qualify v4, v5, v6, or the failed command--motion extension; all prior outputs,
gates, and failure dispositions remain immutable. V8 keeps the Luna alias, high reasoning effort,
v4 prompt, output schema, isolation, two-pass rule, and no-retry policy unchanged.

The correction is to prospective qualification design. The failed extension detected every
material-error polarity but treated secondary answerability/disposition mismatches as protected
prompt-injection or boundary failures, and some nominal/ambiguous cases were scored as if they
required a positive failure mechanism. V8 evaluates the primary composite first on explicitly
diagnosable cases. Truthful omission fails diagnostic coverage but is not automatically a factual
error. Nominal and ambiguous cases retain separate qualification/guardrail labels. Minor secondary
mismatches still count against required-unit and core-field accuracy but fail a protected gate only
when a predeclared safety predicate is wrong.

The fresh suite contains 48 accuracy/composite cases: 24 independently specified evidence
compositions, each with one supported answer and one endpoint-threatening answer. Four additional
meaning-invariance presentations are auxiliary and do not enlarge accuracy or false-error
denominators. Each pass therefore has 24 factual and 24 unsupported/contradicted cases, balanced 24
composite successes and 24 failures. Both passes must independently achieve at least 95% composite
accuracy, at least 90% required-unit and core-field accuracy, factual false rejection at most 15%
(10% operational target), false acceptance at most 5% (zero operational target), and zero failures
on protected causal-overclaim, evidence-boundary, prompt-injection, and meaning-invariance
predicates. Every transport failure is retained; no usable judgment is retried.

Pass-specific class counts and Wilson 95% intervals are reported. A finite perfect result never
establishes zero population error. Any later campaign uses the larger pass-specific error upper
bounds in method-specific adverse transformations for the primary endpoint and each guardrail.
Qualification permits scoring; it cannot by itself establish a CRANE advantage. Physical/reference
episode collection continues while v8 is prepared or run, but no new semantic study label is
allowed until v8 passes and a separate P/R/resource campaign contract is frozen. The prospective
machine-readable amendment is
`diagnostic-sequential-protocol-v2-annotation-amendment-3.json`.

### V8 result and hard-stop disposition

V8 was frozen before calls and executed once on 2026-09-25. All 104 isolated calls were valid and
neither pass had a transport retry. Both passes classified all 48 composite cases correctly and
made zero material-error false rejections or false acceptances in their respective 24-case
denominators. Nevertheless, both failed the complete prospective gate: required-unit accuracy was
79/92 in each pass, core-field accuracy was 336/384 and 335/384, and each pass had one protected
causal mismatch. The four auxiliary presentations passed their registered invariance predicates.

The result is `HELDOUT_QUALIFICATION_FAILED`. Perfect endpoint polarity does not retroactively
remove the frozen unit/core/protected requirements. No usable judgment is retried, references and
thresholds remain unchanged, and no study response is scored under v8. The exact report is governed
under `model_outputs.dvc`, with its tracked summary at
`manifests/annotation/luna-model-judge-v1-heldout-v8-endpoint-first.json`. Physical/reference
episode collection remains independent of this failure.

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
