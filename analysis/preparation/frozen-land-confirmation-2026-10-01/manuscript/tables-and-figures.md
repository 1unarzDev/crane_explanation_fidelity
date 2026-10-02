# Tables and figure templates

This is a layout specification, not a new analysis. Confirmation fields stay as `PENDING_REGISTERED_RELEASE`; do not turn that value into zero. Tables use unique episode/configuration denominators. Development is a separate block and is never pooled with confirmation. No confirmation data were read to prepare these templates.

## Table 1. Main paired endpoint and useful coverage

| Quantity | Final development, exposed | Confirmation, terminal release |
|---|---:|---:|
| Independent complete paired N | 42 | [600 futility / 1,200 final] |
| Persistent / measured-recovery episodes | 21 / 21 | [n / n] |
| B2 PrimaryFailure | 0/42 (0%) | [n/N (%)] |
| B4 PrimaryFailure | 0/42 (0%) | [n/N (%)] |
| B2 fails / B4 passes, b | 0 | [b] |
| B4 fails / B2 passes, c | 0 | [c] |
| Paired reduction, B2−B4 | 0.00 pp | [RD] pp |
| Whole-episode interval | [−9.91, +9.91] pp | [L, U] pp |
| Study one-sided p | Not confirmatory; descriptive 1 | [1 futility / terminal exact p] |
| Descriptive two-sided exact p | 1 | [p] |
| B2 mean episode coverage | 99.35% | [%] |
| B4 mean episode coverage | 100% | [%] |
| B4−B2 mean coverage difference | +0.65 pp | [pp] |
| B2 pooled useful units | 438/441 | [covered/required] |
| B4 pooled useful units | 441/441 | [covered/required] |
| B4≥95% mean coverage and loss≤5pp | Development only | [both pass / fail] |
| Frozen scientific success | Not applicable | [yes / no / incomplete] |

Caption: PrimaryFailure uses union across four levels and A/B passes; coverage uses intersection across passes and equal episode weights. Positive reduction favors B4. The development interval uses single-look category projection; confirmation uses its frozen two-look-adjusted projection with overall coverage≥95%. Pooled unit coverage is supplementary. Complete results include unfavorable and null values.

## Table 2. Cohort and missingness

| Stage/disposition | Unique configurations | Denominator/meaning |
|---|---:|---|
| Allocated confirmation candidates | 2,000 | Before freshness exception |
| Prefreeze exposed candidate excluded | 1 | Frozen exception, candidate0001 |
| Maximum acquirable candidates | 1,999 | Frozen cap |
| Scheduled for capture | [n] | Assignment, not completion |
| Attempted captures | [n] | Distinct started configurations |
| Retained capture failures | [n] | No automatic retry |
| Technically invalid captures | [n] | Admission before method calls |
| Technically valid captures | [n] | Includes eligibility assessed/pending |
| Outside primary discrepancy population | [n] | Report separately from technical invalidity |
| Primary-eligible, method attempted | [n] | Admission/eligibility established |
| Complete method pairs | [n] | All four conditions for both methods |
| Incomplete method pairs | [n] | Whole pair excluded; counterparts retained |
| Pending method attempts | [n] | Unresolved, not permanent failures |
| Complete A/B annotation | [n] | Required before registered join |
| Annotation scoreless failures | [requests] | Attempts; adds no independent N |
| Eligible unpaired M | [n] | Explicit scope and cutoff |
| Worst-case full-eligible RD bounds | [L, U] pp | Missing-outcome bounds, not CI |
| Pending captures/unascertained eligibility | [n] | Separate from known eligible M |

Do not force these rows into one additive chain where metadata stages overlap. Use a reconciled terminal snapshot with a UTC cutoff and categories defined by the accounting preparation. Explain provider-denied condition counts as requests within excluded episodes, never as new N. Eligible episodes acquired after the selected ordered terminal cohort should be identifiable as unused; do not silently add them to the terminal missingness denominator.

## Table 3. Prespecified sensitivity summaries after terminal release

| Summary | N episodes | B2 failures | B4 failures | b | c | RD pp | Interval | Coverage B2/B4 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Frozen union/intersection primary | [N] | [n] | [n] | [n] | [n] | [pp] | [L,U] | [%/%] |
| Annotation A alone | [N] | [n] | [n] | [n] | [n] | [pp] | [L,U] | [%/%] |
| Annotation B alone | [N] | [n] | [n] | [n] | [n] | [pp] | [L,U] | [%/%] |
| Qualified-phrase interpretation 1 | [N] | [n] | [n] | [n] | [n] | [pp] | [label descriptive] | [%/%] |
| Qualified-phrase interpretation 2 | [N] | [n] | [n] | [n] | [n] | [pp] | [label descriptive] | [%/%] |

Caption: Sensitivities do not replace valid frozen labels or create a new primary test. Interpretation sensitivities must use the two existing prespecified definitions; if no executable definition is available, say unavailable rather than inventing one from confirmation.

## Table 4. Secondary evidence-level and numerical outcomes

| Phase/method | Evidence level | Episode denominator | Failure episodes at level | Useful units covered/required | Episode-mean coverage | Episodes with factual/numeric flag |
|---|---|---:|---:|---:|---:|---:|
| Development B2/B4 | E0/E1/E2/E3 | 42 per level | 0 for both each level | See exposed result | [development] | [episode aggregation] |
| Confirmation B2/B4 | E0/E1/E2/E3 | [N] per level | [n] | [n/n] | [%] | [n] |

Development pooled useful units by level: B2 42/42, 84/84, 123/126, 189/189; B4 42/42, 84/84, 126/126, 189/189. The exposed decomposition has 19 flagged B2 conditions and 0 B4 conditions; do not report 19/42 episodes without aggregating unique episode IDs. Level comparisons are within-episode descriptive summaries, not independent sample expansion.

## Figure 1. Cohort flow

Use a vertical flow: candidate allocation → frozen freshness exception → capture attempts → technical admission → primary eligibility → complete paired ladders → both annotation passes → registered600 decision. Branch the decision to “zero discordances: terminal futility, p=1” and “nonzero: continue to1,200, terminal exact superiority analysis.” Side boxes retain capture/validation failures and incomplete method pairs. Print unique configuration counts and UTC cutoff; request failures get their own labeled request-count inset. All counts except allocation/cap remain blank until the reconciled metadata snapshot. This figure can be completed from metadata without semantic release; the stopping branch is filled only when registered.

## Figure 2. Paired primary endpoint and coverage

Panel A: a 2×2 paired table with B2 pass/fail rows and B4 pass/fail columns; label favorable b and reverse c directly. Panel B: paired RD point and frozen interval, x-axis in percentage points centered at zero, labeled “B2−B4; positive favors B4.” Development and terminal confirmation are separate rows, with distinct phase labels and interval captions. Panel C: episode-mean coverage for B2/B4, showing the95% B4 floor and numeric coverage-loss criterion beside it. Use a shared0–100% coverage axis; do not visually magnify a tiny loss by an undisclosed truncated axis. Caption includes stopping status, N, exact p, and threshold status.

## Figure 3. Evidence-level behavior (secondary)

Two panels, E0→E3 on the horizontal axis: level-specific failure fraction and episode-mean useful coverage. Two method lines with no implication that a line point adds independent N. Numerical-error episodes may be an inset. Resampling intervals, if used under the separate exploratory plan, resample whole paired episodes across all levels; they are labeled descriptive and never replace the frozen primary CI. Do not infer a robot's hidden physical cause from profile labels.

## Figure 4. Resources (optional exploratory)

Plot paired whole-episode wall time, provider requests/tokens when available, and retained technical failure counts with explicit missing telemetry. Keep deterministic B4 computation and B2 provider work distinguishable. Report annotation resources separately from method resources. Host overload/provider availability can dominate observed wall time; resource comparisons do not imply model-independent cost advantages. Omit a panel if its required metadata are unavailable; do not estimate absent telemetry from answer length.

## Release checklist for authors

- Copy the terminal stopping status before selecting prose. A continuation flag is not a result release.
- Preserve both discordances and marginal failure counts even at zero discordances.
- Express proportions and differences consistently; distinguish percentage points from percent change.
- Use equal-weight episode coverage for both frozen requirements.
- Label development, primary confirmation, and exploratory analyses separately.
- Show missing-pair bounds separately from sampling CI and retained failures separately from pending jobs.
- Keep the manuscript source declaration/hash and final analysis artifact path together.
- Do not claim equivalence, broad hardware generalization, or human validation from a null/automated result.
