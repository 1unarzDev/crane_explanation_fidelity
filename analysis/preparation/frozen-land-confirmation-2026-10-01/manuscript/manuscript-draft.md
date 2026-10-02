# Evidence-calibrated explanations versus a strong tool-enabled agent in land/Nav2 episodes

**Preparation draft. Confirmation results are deliberately unavailable here.** This text is grounded in the committed prospective declaration, not historical draft gates. Bracketed confirmation fields may be filled only after the registered terminal release. Do not fill them from the nonterminal 600-pair continuation decision.

## Methods

### Study question and prospective design

We tested whether B4, an evidence-calibrated explanation pipeline, reduces episode-level unsupported or deeper-than-visible-evidence diagnostic claims relative to B2, a strong repository-aware, tool-enabled agent, while retaining useful supported diagnostic information. The declaration was frozen on 1 October 2026 at 07:02:44.370858 UTC before the first confirmatory semantic output. Methods, measurement, admission rules, allocation, sample size, stopping, failure handling, useful-coverage criteria, and statistical analysis were bound prospectively. Confirmation was not used to tune either method or the measurement instrument. The primary comparison was B4 versus B2; secondary analyses could not rescue a failed primary result.

The independent sampling unit was one uniquely seeded land/Nav2 simulator episode/configuration. Each episode produced four nested evidence conditions for both methods. Conditions, questions, response generations, and annotation passes were repeated measurements within an episode and did not increase independent N. The prospective allocation reserved 2,000 confirmation candidates; one candidate exposed before freezing was excluded, leaving an acquisition cap of 1,999. A separate allocation of 1,600 unobserved configurations was reserved for possible replication under a distinct prospective declaration.

Candidate generation used an IID equal mixture of four response profiles (persistent low response, persistent intermittent response, partial recovery, and full recovery) and an IID equal mixture of two geometry types (connected detour and nominal clear route), with varied timing and gain. Profile identities and simulator intervention parameters were evaluator-only and were not diagnostic evidence available to either method. The primary population was conditional on technical validity and command–motion discrepancy established by the registered reference computation. Both persistent discrepancy and discrepancy followed by measured response recovery were included; realized mechanism frequencies were reported without forcing equal quotas. The name of an intervention profile was not treated as the observed mechanism. Nominal/untriggered episodes were outside the primary population.

### Evidence and methods

The four-level evidence ladder comprised E0, action/result or observed active-at-cutoff state; E1, additional source-qualified behavior-tree observations; E2, additional delivered commands; and E3, additional synchronized odometry and the shared validated primitive computation. A recovery-action occurrence alone did not establish measured response recovery. Execution observations could support a command–motion discrepancy without identifying its hidden physical cause.

B2 used the unchanged repository/tool-enabled `gpt-6-sol` model with high reasoning effort, the original prompt and schema, and a 900-second per-condition timeout. It received the same level-specific evidence packet, relevant behavior-tree/configuration context, and permitted primitive computations as B4. It could invoke the same evidence computation; it was not deprived of source context or weakened to induce an effect. Each condition received one semantic attempt, with no retries of poor answers.

B4 was the frozen deterministic v7 pipeline, combining validated computations, evidence/claim contracts, selection of the maximal supported diagnosis, constrained realization, verification, and local fallback. The frozen implementation retained available trace information, distinguished partial measured recovery from complete restoration of tracking, and preserved uncertainty at nonterminal cutoffs. Its implementation and dependencies were bound by the declaration's source hashes. No confirmation-driven method change was permitted.

### Measurement and endpoints

The primary endpoint, PrimaryFailure, was an endorsed unsupported or deeper-than-supported mechanistic or diagnostic proposition anywhere in an answer. For each method and episode, failure was the union across the four evidence levels and both predeclared annotation passes. Thus an episode contributed exactly one binary failure indicator per method. Ordinary factual/numerical inaccuracies were reported separately unless they met the frozen primary diagnostic criterion; a more favorable exploratory error category was not substituted for PrimaryFailure.

Two method-blind passes used `gpt-6-astra` with high reasoning effort, candidate-v5 annotation prompt, schema v1, no tools, and a 900-second timeout. Each request contained one episode's eight answers, with opaque response identifiers and independently ordered answers for each pass. Judges were not supplied with method labels or evaluator-only causes. Exact identifiers, evidence/unit inventories, quotations, and failure/count consistency were checked deterministically. A separate key joined identities only after the required blind annotations were complete. Writing style could still reveal a method to a judge; blinding did not guarantee that identity was unguessable.

Useful coverage was based on a method-independent, evidence-level-specific inventory: action state/outcome, available source-qualified recovery trace, delivered command observation, supported discrepancy and interval, and later measured recovery when supported. A unit counted as communicated only under both annotation passes. For each method, the covered/required fraction was computed within an episode and then averaged with equal episode weights. The pooled unit fraction was supplementary and did not replace this primary coverage measure. Scientific success required B4 mean episode coverage of at least 95% and coverage loss relative to B2 of at most five percentage points, as well as significant primary superiority.

Development qualification used 20 targeted reference cases. Both passes matched all 20 reference PrimaryFailure labels; one useful-coverage ambiguity was retained. Final development annotation passes agreed on all 336 answer-level failure labels and all 882 useful-unit labels per pass. This documents automated reference qualification and agreement, not independent human validation or error-free measurement. Separate-pass results and the two contested qualified-phrase interpretations retained from development were prespecified sensitivities.

### Technical failures and missingness

Technical admission preceded semantic calls and required the bound scenario/profile/build and absence of endpoint, stale, rejected, cross-episode, or failed-observation errors. Expected task abort and active-at-cutoff outcomes were valid outcomes. Any failed method condition excluded the entire episode pair from the complete-pair primary analysis; valid counterpart outputs and all failed requests were retained. Exclusion and replacement decisions could not use method performance. A failed semantic attempt was not retried.

Only scoreless technical annotation failures could resume identical blind requests under the same prompt, schema, model, effort, and timeout until the first structurally valid score for each pass. Failed attempts were retained, valid scores were never replaced, and disagreements remained in the analysis. Missing annotation prevented a positive primary claim until the required complete N was available. Cohort flow separated capture failures, technical invalidity, outside-population cases, failed method pairs, pending pairs, complete method pairs, and fully scored pairs; counts used distinct configurations throughout.

Complete-pair estimates were accompanied by worst-case arbitrary missing-pair bounds. If N complete primary-eligible pairs yielded discordance difference b−c and M primary-eligible pairs lacked a complete method ladder, the possible full-eligible risk difference lay in [(b−c−M)/(N+M), (b−c+M)/(N+M)]. These are missing-outcome sensitivity bounds, not confidence intervals, and they do not assume technical missingness is ignorable. Pending collection or unascertained eligibility was reported separately rather than silently added to this denominator.

### Statistical analysis and stopping

Let b be the number of episodes on which B2 failed and B4 passed, and c the reverse. The absolute paired risk difference was Δ=(b−c)/N, positive when B4 reduced failures. Both discordance counts, both marginal failure rates, useful coverage, uncertainty, and retained failures were reported regardless of direction.

The first registered look consisted of the first 600 complete independent pairs in frozen candidate order, with both annotation passes complete. It checked only whether b+c=0. Zero discordances terminated the study for futility, with study p=1 and no superiority claim. Any nonzero discordance required continuation to the first 1,200 complete pairs; there was no interim superiority test or interim effect release. The final analysis used the upper-tail exact McNemar probability P{Binomial(b+c, 1/2)≥b} at one-sided α=0.01. A descriptive two-sided exact p-value was also required. The early rule could only remove fixed-1,200 rejection events and therefore did not increase the terminal test's type-I error.

At either terminal sample size, category proportions b/N and c/N received exact Clopper–Pearson bounds with tail probability 0.00625 on each side (98.75% marginal coverage per category). Projecting these bounds gave [L_b−U_c, U_b−L_c] for Δ. Bonferroni accounting across two categories and both possible terminal looks ensured at least 95% overall whole-episode coverage. The interval formula was fixed before outcomes and remained valid when discordances were zero.

The program alpha ledger retained the 0.02 spent by a prior study. This study permanently consumed the remaining 0.01 candidate allocation at freezing; 0.02 remained protected for replication. No unused-looking alpha was refunded after futility or administrative stopping. The directional hypothesis was prespecified and compatible with the remaining ledger allocation.

Exact power calculations incorporated zero-discordance early stopping rather than assuming an observed positive pilot effect. At the frozen design, illustrative probabilities (b/N, c/N) of (0.010, 0), (0.020, 0.005), (0.045, 0.020), and (0.070, 0.045) gave powers of 95.399%, 82.227%, 84.526%, and 56.206%, respectively. The last two scenarios share a 2.5-point reduction but differ in discordance noise. Adequate power was not universal across effect structures.

## Development findings — not confirmatory evidence

The final measurement configuration evaluated 42 complete independent development pairs, comprising 21 persistent-discrepancy and 21 measured-recovery episodes. B2 and B4 each had 0/42 PrimaryFailures; both discordance directions were zero. The paired risk difference was zero, with a conservative development 95% interval of −9.91 to +9.91 percentage points and descriptive exact p=1. There was no observed PrimaryFailure advantage to extrapolate optimistically.

B2 communicated 438/441 required units (99.32% pooled), versus 441/441 for B4 (100%). Mean episode coverage was 99.35% and 100%, respectively. Of 48 scheduled development configurations, one was technically invalid and five lacked complete method pairs, leaving 47 physically eligible configurations. Worst-case full-eligible risk-difference bounds were −10.64 to +10.64 points. The development decomposition recorded factual/numerical flags on 19 B2 conditions and zero B4 conditions; conditions were not independent episodes, and these exploratory flags were not promoted to the primary endpoint.

Earlier B4 failures, the original failed combined-format canary, qualification disagreements, and superseded development annotation configurations remained retained. Development changes were completed before freezing. These historical iterations do not constitute multiple confirmatory wins and are not pooled with confirmation.

## Confirmation results — fill only at registered terminal release

The study reached [TERMINAL_LOOK: 600-futility / 1,200-final / administrative-incomplete]. Of [ATTEMPTED] attempted configurations, [CAPTURE_FAILURES] had capture failures, [TECHNICALLY_INVALID] failed technical admission, [OUTSIDE_PRIMARY] were outside the primary population, and [INCOMPLETE_METHOD_PAIRS] primary-eligible episodes lacked complete method pairs. [COMPLETE_METHOD_PAIRS] complete method pairs were retained and [FULLY_SCORED_PAIRS] had both blind passes complete. [PENDING] episodes remained pending at the cutoff [UTC_TIMESTAMP]. Confirmatory outcome text below is supplied by the matching terminal-language block only after release.

For an evaluable terminal sample, B2 PrimaryFailure was [B2_FAILURES]/[N] ([B2_RATE]%), versus [B4_FAILURES]/[N] ([B4_RATE]%) for B4. Favorable and reverse discordances were [b] and [c]. The paired reduction was [RD_PP] percentage points, with frozen overall ≥95% interval [LOWER_PP, UPPER_PP]. Study p was [ONE_SIDED_OR_FUTILITY_P], and descriptive two-sided exact p was [TWO_SIDED_P]. Mean episode coverage was [B2_COVERAGE]% and [B4_COVERAGE]%, with B4−B2 difference [COVERAGE_DIFFERENCE_PP] points; the two frozen coverage conditions [PASSED/FAILED]. Missing-outcome bounds were [MISSING_LOWER_PP, MISSING_UPPER_PP]. See the terminal-language file for inference appropriate to stopping status.

## Limitations

This comparison estimates behavior within a simulator-generated, conditionally admitted land/Nav2 discrepancy population and a fixed evidence interface. It does not demonstrate calibration for unrestricted robot tasks, real hardware faults, other model families, or geometry/planning diagnoses. Independent seeds reduce repeated-configuration dependence but share simulator dynamics, software, prompts, and source context. The equal candidate profile mixture need not produce equal realized mechanisms after admission.

PrimaryFailure is a deliberately narrow diagnostic endpoint. Supported useful content is addressed by explicit coverage thresholds, while numerical accuracy, evidence-level behavior, resource use, and unsupported-specificity decompositions are secondary. Passing the coverage thresholds does not establish complete practical usefulness, correctness of every number, or human user benefit.

Automated judges may share systematic errors even when their passes agree. Two passes, targeted reference qualification, deterministic structural checks, union failure, intersection coverage, and sensitivity analyses reduce particular vulnerabilities but do not provide independent human validation. Qualified-language interpretation and inferred style-based identity remain limitations. Method-complete missingness can affect the target population and is exposed through retained failure accounting and worst-case bounds.

The strong B2 baseline reached a zero-failure development floor, making small advantages difficult to establish. Nonsignificance or zero discordances does not establish equivalence. The frozen interval, both discordances, and plausible effects excluded or retained by that interval are necessary for interpretation. A statistically significant reduction must also satisfy the two coverage criteria; practical magnitude and generalization require separate judgment. Replication, if activated, uses fresh configurations and a new prospective declaration under the protected alpha allocation.

## Sources and binding

- Declaration: `manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json`, SHA256 `77e0c6ac4f8da3eccfeeb5ed31990d504a907953f63e8c19822e4e0c4e540ac2`.
- Alpha: `manifests/study/diagnostic-sequential-error-ledger-v2.json`.
- Development: `analysis/results/development/evidence-calibration-final-v7-development-prompt-v5/paired-result.json`.
- Retained development history: `docs/EVIDENCE_CALIBRATION_RESPONSE_DEVELOPMENT_2026-09-30.md`.

Prepared without opening confirmation responses, annotation returns, join keys, comparative effects, or provider caches; no experimental model calls were made. This draft is a preparation artifact, not a scientific protocol amendment.
