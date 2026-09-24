# Sequential study protocol for new physical-diagnosis campaigns

Protocol: `diagnostic-sequential-protocol-v2`

Declared: 2026-09-23

Status: **REGISTERED FRAMEWORK / NO CAMPAIGN ACTIVE / ZERO ALPHA CONSUMED**

This is the canonical forward-looking statistical contract for new physical-diagnosis campaigns.
It does not apply to frozen F/G/H data, the nine inspected diagnostic-development clusters, or any
other outcome already reviewed. The earlier `diagnostic-sequential-protocol-v1` remains in Git as
an unused design calibration: before any confirmatory response or alpha consumption, analytic and
simulation checks showed that its conservative bet grid, equal Bonferroni split, and 400-cluster
ceiling made the ambiguity guardrail impractical. V2 preserves the scientific thresholds while
correcting the prospective analysis.

Machine-readable sources:

- protocol: `research/explanation_fidelity/experiment_configs/prospective/diagnostic-sequential-protocol-v2.json`;
- cumulative alpha ledger: `manifests/study/diagnostic-sequential-error-ledger-v2.json`;
- result schema: `research/explanation_fidelity/schemas/diagnostic-sequential-results-v1.schema.json`;
- monitor: `analysis/sequential_diagnostic_monitor.py`;
- retained simulation: `analysis/results/diagnostic-sequential-simulation-v2.json`;
- progress report: `docs/DIAGNOSTIC_CAMPAIGN_PROGRESS.md`.

## Population, unit, and sampling

The target population is prospectively generated land and RoboBoat surface-navigation scenario
configurations under the frozen mixture: 80% land and 20% surface, 50% geometric restriction and
50% command--motion discrepancy, and 20% ambiguous-evidence cases. Adverse diagnosable behavior,
nominal/false-premise controls, successful compensation, and missing-decisive-evidence cases are
all represented by declared strata.

One independently generated scenario cluster is the statistical unit. Shared layouts, paired
interventions, exact-condition reruns, evidence masks, question variants, paraphrases, and judge
passes retain one cluster identity. Each cluster's stratum and configuration seed are drawn from
the fixed mixture before robot or method outcomes are observed. A seed must materially change the
configuration; renamed copies are not independent.

Valid unexpected outcomes remain included. Invalid recordings remain in the run ledger and may be
excluded only under predeclared recording-validity rules that do not inspect method answers. No
outcome-dependent family reallocation, favorable-case replacement, or quality-driven resampling is
allowed. If surface strata are not ready, the mixed campaign does not start; a land-only target
requires a new prospective protocol before any outcomes.

The confidence sequence assumes independent target-mixture draws and a stable conditional target
mean. Stateful simulator inheritance, adaptive scenario promotion, finite-catalog sampling without
the corresponding finite-population method, or post-outcome exclusions invalidate the advertised
bound rather than becoming analysis details.

## Primary comparison and fairness

The sole confirmatory comparison is P versus tool-enabled R.

- **P:** frozen physical diagnostic computations, runtime/source provenance, checked answer plan,
  language realization, and final verification/fallback.
- **R:** the strongest development-selected repository-aware agent, given the same robot-visible
  evidence, exact source/configuration, executable diagnostic tools, and tool descriptions.

Model/version, reasoning and sampling settings, call ceilings, tool calls, input-token ceiling,
wall-clock allowance, and permitted external resources are matched. Actual calls, tokens, latency,
and fallback remain measured treatment properties. If P uses an extra resource that cannot fairly
be exposed to R, it is disclosed as part of the treatment and cannot be described as a prompting
or provenance-only advantage. Condition identity, evaluator truth, P's checked plan and verifier
state, previous labels, and other methods' answers remain hidden.

R was selected because inspected development work showed it was stronger than N and frequently
matched P/T when given the same executable diagnostics. T and N remain descriptive unless a future
allocation is registered before their confirmatory data.

## Endpoint, worthwhile difference, and guardrails

For one predeclared diagnosable question per cluster, **supported diagnostic success** is binary:

> The final answer identifies the independently required supported physical or execution
> mechanism and contains no material unsupported or contradicted assertion.

The primary estimand is the target-distribution P-minus-R paired success difference conditional on
the prospectively declared diagnosable strata. Semantic labels are Luna-assessed only after a
frozen judge passes held-out qualification. Deterministically recomputed geometry, motion, timing,
count, and provenance predicates are reported separately.

The minimum worthwhile improvement is `+0.15`. Added diagnostic and verification complexity is not
worth a smaller gain. Success requires a one-sided anytime lower bound strictly above `+0.15`, not
a positive estimate or a test against zero.

Three simultaneous nondegradation guardrails are mandatory:

| Guardrail | P-minus-R estimand | Required bound |
|---|---:|---:|
| Material-error risk | `risk_P - risk_R` | upper bound `< +0.02` |
| Useful required-unit coverage | `coverage_P - coverage_R` | lower bound `> -0.05` |
| Correct ambiguous-case handling | `correct_P - correct_R` | lower bound `> -0.05` |

Coverage is a frozen required-unit fraction, not answer length. Ambiguity handling requires useful
supported information plus withholding the unresolved mechanism. Packet defects are
`evidence_problem`, not candidate errors. An unresolved required primary or guardrail label blocks
success and remains in best/worst-case sensitivity rather than disappearing from the denominator.

## Anytime-valid analysis and multiplicity

For a paired difference `X_t` in `[-1,1]`, null mean `mu > -1`, and each frozen fraction
`c in (0,1)`, V2 uses

```text
lambda_c(mu) = c / (1 + mu)
M_t(mu,c) = product_i [1 + lambda_c(mu) (X_i - mu)].
```

The minimum factor is `1-c > 0`. Under `E[X_t | F_(t-1)] <= mu`, each factor has conditional
expectation at most one, so each capital process and their fixed uniform mixture are nonnegative
supermartingales. The `mu=-1` boundary is handled exactly. Ville's inequality makes threshold
crossing anytime-valid; monotone inversion yields one-sided confidence sequences. Upper bounds use
`-X`. Simulation checks implementation and budgets but is not the validity proof.

Overall success is an intersection--union claim: all four component nulls must be rejected.
Therefore each component uses the campaign alpha. If the overall claim is false, at least one
component null is true, and the probability of falsely rejecting every component is no greater
than the alpha of that true component. No within-campaign Bonferroni split is required. This logic
does not cover trying multiple candidates: program-level online Bonferroni spending allocates the
one-sided familywise `0.05` budget as `0.020` candidate v1, `0.010` one revision reserve, and
`0.020` fresh replication. The allocation is atomically bound before the first response is opened
and is never refunded after failure, futility, abandonment, or invalidity.

## Planning, stopping, and futility

Framework success cannot occur before 100 total, 70 diagnosable, and 15 ambiguous independent
clusters. Nonbinding futility reviews occur at 100, 150, 200, 300, 400, 600, 800, and 1,200. At a
review, a 95% anytime upper bound at or below `+0.15` triggers frozen-method review. The hard
framework maximum is 1,600 clusters; a campaign-specific qualified-pilot plan should normally set
a lower ceiling. Stopping at the maximum without all four gates is negative or unresolved, never
success by sample size.

The retained seeded audit uses 20,000 boundary-null replicates per endpoint and 10,000 joint
replicates per alternative scenario. Boundary crossing estimates were 0.0079--0.0116 at component
alpha 0.02. Under a true `+0.30` primary difference, joint success by 1,600 was 0.9946 in the
low-guardrail-discordance sensitivity and 0.9366 in the moderate sensitivity. At the exact
`+0.15` boundary it was 0.0027, correctly demonstrating that a true effect must exceed the
worthwhile threshold to establish a lower bound above it. These are implementation checks and
budget sensitivities, not observed effects or guarantees. Campaign planning must rerun after a
qualified development judge supplies realistic paired discordance, invalid-run, and unresolved
rates.

Reproduce the planning audit with the pinned analysis dependency:

```bash
python -m pip install -r requirements-analysis.txt
PYTHONPATH=analysis python analysis/simulate_sequential_diagnostic_design.py \
  --output /tmp/diagnostic-sequential-simulation-v2.json
cmp /tmp/diagnostic-sequential-simulation-v2.json \
  analysis/results/diagnostic-sequential-simulation-v2.json
```

## Luna gate and replication

Before confirmation, freeze and hash the Luna rubric, prompt, schema, model/provider/settings,
independent references, two isolated passes, deterministic disagreement rules, retry policy, and
held-out qualification report. Judge development and held-out cases are disjoint. Luna judge
versions v1--v3 failed development qualification and are ineligible; v3 additionally exposed an
omitted-versus-incorrect required-unit reference-taxonomy conflict. More study responses cannot
repair judge validity.

Reserve fresh configuration identities before discovery. Replication uses byte-identical P/R,
evidence contract, prompts, tools, thresholds, judge, and analysis hashes; it reuses no discovery
response, mask, paraphrase, or configuration. A genuine-advantage claim requires both candidate
confirmation and fresh replication independently to clear `+0.15` and all guardrails under their
separate allocations.

## Activation and retention

No campaign is active. Activation requires frozen P/R and resource-parity hashes, admitted target
generators, a held-out-qualified Luna arm, one frozen question/reference/sufficiency label per
cluster, a fixed sampler/exclusion contract, reserved replication configurations, and successful
schema/monitor dry runs. Every candidate—including failed and futile versions—retains its
registration, runs, exclusions, raw/final answers, judge passes, deterministic measurements,
costs, bounds, ledger state, and termination reason.

Run the synthetic zero-outcome transport check with:

```bash
python analysis/sequential_diagnostic_monitor.py \
  configs/fixtures/diagnostic-sequential-empty-dry-run.json
```

It establishes no scientific result and consumes no alpha.
