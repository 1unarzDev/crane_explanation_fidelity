# Sequential evaluation protocol for new diagnostic campaigns

> **SUPERSEDED UNUSED:** This v1 design was retired before any confirmatory response was inspected
> and before any alpha was consumed. The canonical prospective protocol is
> `docs/SEQUENTIAL_STUDY_PROTOCOL.md` (`diagnostic-sequential-protocol-v2`). This file is retained
> as design history and must not activate a campaign.

Protocol: `diagnostic-sequential-protocol-v1`

Declared: 2026-09-23
Status: **REGISTERED FRAMEWORK / NO CAMPAIGN ACTIVE**

This protocol applies only to future diagnostic-study campaigns whose configurations, method,
baseline, evidence contract, Luna judge, prompts, thresholds, target distribution, and analysis
are frozen before any confirmatory response is inspected. It is not an amendment to the frozen
F/G/H provenance study and cannot be applied to the nine diagnostic-development clusters or any
other outcome already reviewed.

The machine-readable declaration is
`research/explanation_fidelity/experiment_configs/prospective/diagnostic-sequential-protocol-v1.json`.
The monitor is `analysis/sequential_diagnostic_monitor.py`; its input contract is
`research/explanation_fidelity/schemas/diagnostic-sequential-results-v1.schema.json`.
The cumulative allocation state is
`manifests/study/diagnostic-sequential-error-ledger-v1.json`; unlike the immutable allocation plan,
this ledger is updated atomically to bind an allocation to a campaign before its first response is
inspected. A nonempty monitor input is rejected until that binding exists, and consumed alpha is
never returned to `AVAILABLE`.
`configs/fixtures/diagnostic-sequential-empty-dry-run.json` is a synthetic zero-outcome transport
check only: its all-zero component hashes are conspicuous placeholders and cannot activate a real
campaign.

## Primary comparison

The sole confirmatory comparison is **P versus tool-enabled R**.

- **P:** the selected frozen physical-diagnosis computation, runtime/source provenance, checked
  answer plan, natural-language realization, and final verification/fallback.
- **R:** the strongest repository-aware agent selected from development evidence. R receives the
  same robot-visible evidence, exact relevant source/configuration, executable diagnostic tools,
  and tool descriptions as P.

The model family/version, reasoning and sampling settings, maximum model calls, tool calls, input
tokens, wall-clock allowance, and permitted external resources are matched. Condition identity,
evaluator truth, P's checked plan, verifier/fallback state, prior labels, and other methods' answers
remain hidden. If P consumes extra deterministic or model resources, those resources are either
made available to R or disclosed as part of the treatment; they are never described as a prompting
advantage.

R is selected because inspected development evidence showed it was stronger than the provenance
ablation N and often matched P/T when given the same executable diagnostic. T and N remain useful
descriptive ablations but receive no confirmatory claim under this protocol unless alpha is
allocated prospectively.

## Outcomes and estimand

One primary question is selected before output generation for each independent scenario cluster.
Related interventions, exact-condition reruns, evidence masks, question variants, and paraphrases
retain the same cluster ID and cannot add a primary observation.

The primary binary outcome is **supported diagnostic success** on a diagnosable question:

> The final response identifies the independently required supported physical or execution
> mechanism and contains no material unsupported or contradicted assertion.

The primary estimand is the diagnosable portion of the target-distribution mean paired difference
`Pr(success_P) - Pr(success_R)`. Semantic success is explicitly **Luna-assessed**, conditional on a
held-out-qualified frozen judge. Independently recomputed path, clearance, timing, command, motion,
source-hash, and count measurements are reported separately and are not relabeled as semantic
judgments.

Three paired guardrails must also pass:

| Guardrail | Paired estimand | Unacceptable degradation |
|---|---|---:|
| Response-level material-error risk | `risk_P - risk_R` | greater than +0.02 |
| Useful answerable-information coverage | `coverage_P - coverage_R` | less than -0.05 |
| Correct handling of genuinely ambiguous cases | `correct_P - correct_R` | less than -0.05 |

Coverage is the frozen required-unit fraction communicated by the final answer, not response
length or citation count. Ambiguity handling is binary under independently declared sufficiency:
the response must retain supported information and withhold the unresolved mechanism. A missing or
inconsistent evaluation packet is `evidence_problem`, not an incorrect answer.

The minimum worthwhile primary improvement is **+0.15**. This retains the already declared
development planning threshold rather than lowering it after observing baseline parity. The added
diagnostic/checking complexity is not worthwhile for a smaller target-distribution improvement.
Success requires the corrected lower bound to be strictly above +0.15, not merely above zero.

## Target distribution and independent sampling

The target is 80% land and 20% RoboBoat surface navigation, split equally between geometric and
command--motion mechanisms, with 20% ambiguous-evidence cases. Exact stratum probabilities are in
the machine-readable declaration. They include adverse diagnosable behavior, nominal/false-premise
controls, successful compensation, and missing-decisive-evidence cases.

For each new cluster, the stratum and configuration-generation seed are drawn prospectively from
the frozen categorical mixture before the robot outcome or any method response is observed. The
configuration generator must make its declared seed materially alter geometry or physical
conditions; relabeled copies do not qualify. Sampling probabilities are retained per row. Invalid
recordings remain in the run ledger and are excluded only by predeclared recording-validity rules.
Unexpected valid outcomes remain included.

No family may be oversampled after seeing method differences. A shortage in one stratum pauses the
campaign; it does not transfer weight to a favorable stratum. The 20% surface allocation means the
mixed-domain campaign cannot start until surface geometric and command--motion strata pass
development admission. If surface is not ready, a land-only target requires a new prospective
protocol version—not an amendment after outcomes.

The sequential guarantee assumes independent clusters and that target-randomized cluster
differences have a stable conditional target mean. Shared layouts, paired interventions, evidence
masks, and paraphrases violate that unit assumption and remain one cluster. Departures from the
sampling mixture or conditional-mean assumption invalidate the confirmatory bound and must be
reported rather than repaired through post-hoc weights.

The primary sequence contains only prospectively labeled diagnosable strata; because ambiguity is
allocated proportionally within every domain/mechanism cell, conditioning on diagnosability
preserves the declared 80/20 domain and 50/50 mechanism mix. Material-error and coverage
guardrails use every cluster. The ambiguity guardrail uses the declared ambiguous strata. These
are distinct estimands and are never pooled into one favorable composite.

## Anytime-valid analysis

For each endpoint let `X_t` be the P-minus-R paired cluster difference, bounded in `[-1, 1]`. For a
candidate null mean `mu`, and a fixed bet `lambda` in `(0, 1/2]`, define

```text
M_t(mu, lambda) = product_i [1 + lambda (X_i - mu)].
```

Under `E[X_t | F_(t-1)] <= mu`, each factor is nonnegative and has conditional expectation at most
one. Therefore `M_t` is a nonnegative supermartingale. A fixed uniform mixture over the declared
lambda grid is also a nonnegative supermartingale. Ville's inequality bounds the probability that
it ever crosses `1/alpha` by alpha. Because the mixture decreases monotonically with `mu`, numerical
inversion gives an anytime-valid one-sided lower confidence sequence. Applying the same construction
to `-X_t` gives an upper sequence.

This is a proof-based guarantee under the declared boundedness, independence/conditional-mean,
fixed-mixture, and no-retrofit assumptions. Simulation is used for budget and precision planning,
not as proof. The implementation tests nonnegative factors, the one-step supermartingale identity,
monotone bounds, and fail-closed campaign rules.

The monitor and campaign input schema also fail closed on reused configuration IDs,
nonchronological arrivals, answerability/stratum disagreement, an incorrect protocol hash, missing
freeze hashes, or an unaudited P/R information/tool/resource-parity declaration. These checks do
not prove real-world independence; configuration provenance and family grouping remain auditable
campaign-admission evidence.

Each campaign allocation is Bonferroni-divided over the primary bound and three guardrail bounds.
A campaign succeeds only when all four simultaneously pass, the minimum diversity counts pass, and
the frozen Luna qualification remains valid. This correction covers repeated monitoring and the
four required claims; it does not authorize unregistered secondary comparisons.

## Program error ledger and candidate evolution

The research-program one-sided error budget is 0.05:

| Allocation | Role | Alpha | Initial status |
|---|---|---:|---|
| `candidate-v1-confirmation` | selected frozen candidate | 0.020 | available |
| `candidate-revision-reserve` | one later frozen revision | 0.010 | available |
| `selected-method-replication` | fresh-config replication | 0.020 | available |

An allocation is consumed when its first confirmatory response is inspected. Failure, futility,
abandonment, invalid scientific assumptions, or an unresolved result does not refund alpha. More
candidate versions require an unused prospectively registered program allocation; anytime-valid
monitoring is not a license for unlimited model, prompt, verifier, or endpoint searches.

The protocol JSON records the immutable initial allocation plan. The tracked cumulative ledger
records operational consumption without changing the protocol hash. The monitor cross-checks its
IDs, roles, amounts, cumulative total, campaign binding, and consumption timestamp against the
plan; status changes remain reviewable Git history.

The four required one-sided bounds each receive one quarter of the campaign allocation. Secondary
T/N comparisons, mechanism-specific slices, model-family replications, and preference judgments
are descriptive unless separately registered and charged before collection.

## Sample planning, stopping, and futility

Pilot information is used to simulate resource requirements and attainable precision under the
frozen target distribution. It is not evidence that eventual success is inevitable. Planning must
vary paired discordance, mechanism mix, invalid-run rate, judge unresolved rate, and systematic
judge-error sensitivity. The earlier 92-cluster fixed-look calculation is not reused as sequential
power.

The general framework sets conservative diversity floors of 100 total, 70 diagnosable, and 15
ambiguous independent clusters before success may be declared. Campaign-specific planning may
raise these floors before freeze but may not lower the +0.15 threshold or guardrails. Reviews occur
at 100, 150, 200, and 300 total clusters; the hard maximum is 400.

At a scheduled review, a nonbinding 95% anytime upper bound at or below +0.15 triggers a futility
review. Stopping for futility cannot create a false positive, but the negative/unresolved result and
all resource use remain reportable. At 400 clusters the campaign stops whether or not a favorable
p-value exists. A frozen method that fails returns to a separately versioned development cycle;
its confirmatory data are never used to tune and then re-evaluate that same candidate.

## Luna gate

Before campaign scoring, Luna's rubric, prompt, schema, independently constructed references,
model alias/provider metadata, reasoning setting, two-pass rule, disagreement handling, retry rule,
and held-out judge suite are hash-frozen. Development and held-out qualification are disjoint.
Neither prompt nor expected labels may be selected because they favor P.

Every response receives two isolated passes. Only independently checkable facts or explicit frozen
rules resolve a disagreement; otherwise the field is unresolved. A campaign cannot declare
success while any primary or guardrail label required for that declaration remains unresolved.
Best/worst-case sensitivity remains in the progress report. More study responses cannot repair a
judge category that failed held-out qualification.

The existing `luna-model-judge-v1` failed development qualification and is **ineligible**. Thus no
campaign is active under this protocol. A new judge version must be declared and qualify without
using confirmatory campaign answers.

## Replication

Fresh configuration identities are reserved before discovery begins. Replication uses the exact
selected method, R baseline, evidence contract, prompts, tools, thresholds, Luna configuration,
and analysis hashes. It reuses no discovery response, mask, paraphrase, or configuration.

Replication succeeds only if its separately allocated corrected lower bound is above +0.15 and all
three guardrails pass on the fresh cohort. More calls over discovery episodes are sensitivity
analysis, not replication. A final claim of a genuine diagnostic advantage requires both a
successful candidate campaign and this successful replication.

## Retention and progress reporting

Every candidate and campaign is immutable after evaluation begins. Retain its registration,
sampling schedule, valid and invalid runs, evidence, raw/final answers, Luna passes, unresolved
fields, deterministic measurements, costs, hashes, monitor outputs, and termination reason.

`docs/DIAGNOSTIC_CAMPAIGN_PROGRESS.md` is the living public-facing ledger. Each update reports
independent cluster counts and realized strata, effect estimates and anytime bounds, all four gate
states, Luna qualification/agreement/unresolved status, alpha consumed, resource use, exclusions,
and the next collection or development action. Difficult or disputed responses stay in the
denominator and sensitivity analysis.

## Activation checklist

A campaign remains `NOT_READY` until all are true:

1. P and strongest R are selected only from development evidence and hash-frozen.
2. Information, tool, model, and resource parity is audited.
3. All target strata have independently validated configuration generators and recording gates.
4. A new Luna version passes development and untouched held-out qualification.
5. One primary question/reference and sufficiency label are frozen per cluster.
6. Sampling RNG/seed, exclusions, alpha allocation, maximum N, and progress-report paths are fixed.
7. Fresh replication configurations are reserved and overlap-audited.
8. The monitor and campaign manifest pass regression and dry-run checks without study outcomes.

Reproduce the zero-outcome check with:

```bash
python analysis/sequential_diagnostic_monitor.py \
  configs/fixtures/diagnostic-sequential-empty-dry-run.json
```

If these conditions cannot be met, the obstacle is reported and no confirmatory campaign starts.
