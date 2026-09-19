# Study Design (pre-final-collection draft)

This document must be frozen after pilot/power analysis and before sealed-test evaluation. Items
marked **TBD-PILOT** are not yet frozen.

## Research questions and hypotheses

- RQ1: structured versus information-matched prose evidence.
- RQ2: checked plans/final verification versus direct generation and self-checking.
- RQ3: useful partial answers and correct withholding under insufficient/contradictory evidence.
- RQ4: trustworthiness at useful coverage, including matched-coverage comparisons.
- RQ5 (exploratory): robustness across land, surface, underwater, and aerial embodiments when
  enough data can be collected without weakening the powered primary land study.

Primary H1: method D reduces response-level material errors versus strong prose baseline A while
maintaining useful substantive coverage. Secondary: B>A representation effect; D>B checking
effect; D versus C native capture effect; D improves insufficient-evidence, contrastive, and
causal-claim handling. E versus D tests whether LLM realization adds enough usefulness to justify
its risk.

## Conditions

- A: well-written free-text record → direct LLM.
- B: structured record with exactly the same facts → same direct LLM.
- C: free text → extraction → checked generation.
- D: native structure → checked plan → generation → output verification/fallback.
- E: structure → deterministic checked template.

Every episode is captured once. A/B information parity is audited proposition-by-proposition;
neither format receives privileged facts. Model, decoding, system prompt, and answer prompt are
identical for A/B. Calls are single-sample and cached with raw/final output, model/version,
parameters, prompt hash, latency, tokens, cost, and verification result.

## Primary outcome

A response has a material error if any substantive assertion is contradicted/unsupported, has an
incorrect comparison/count/status, or makes an unjustified causal, counterfactual, or explanatory
relationship. Primary unit: response. Annotation is blind to condition where formatting permits.

Jointly report substantive answer coverage, full/partial/abstained proportions,
answerable-information coverage, correct abstention, risk–coverage curves, and matched-coverage
comparisons. Claim-level error categories are secondary. Fluency/preference is not correctness.

## Units, split, and inclusion

Independent unit is scenario instance/episode, never a paraphrase. Split by scenario family before
question realization; all paraphrases stay together. Include episodes passing frozen capture
quality checks and questions mapped to frozen families. Exclude corrupt/missing required artifacts
using reasons set before inspecting answers. Deliberate incomplete-evidence episodes remain in
scope. **TBD-PILOT:** minimum evidence per family and target family balance.

## Analysis

Use paired episode-cluster bootstrap confidence intervals for risk and coverage differences and a
mixed-effects logistic model if sample size/convergence supports it (condition fixed effect;
episode/scenario-family random effects). McNemar is a secondary response-pair sanity check, not the
main clustered inference. Report effect sizes and intervals regardless of significance. Adjust
secondary confirmatory comparisons with Holm; exploratory analyses are labeled.

Power planning uses development episodes only: estimate paired discordance/effect, define the
smallest practically meaningful reduction before seeing sealed test, simulate the clustered paired
design, and target ≥80% power (prefer 90%). The current development planning target is a five-point
absolute risk reduction (A 8% to D 3%), ICC 0.10, six questions per episode, and 60 independent
episodes; details and sensitivity limits follow below.

Current explanation-evaluation sample: thirteen valid land episodes and 395 A/B/C/D/E responses (316
model-mediated). Families are three client-cancellation instances, three unblocked-success instances, two independently configured
terminal recovery/exhaustion instances, planning `NO_VALID_PATH`, and four independently configured
bounded-mobility recovery-followed-by-success instances. A single unblinded development annotation
observed A 6/79, B 0/79, and C/D/E 1/79 material errors. The retained checked error conflated eventual task success with
absence of an explicitly recorded intermediate FollowPath failure; retained outputs were not
regenerated after correcting the planner. A/B substantive coverage is 66/79 versus C/D/E 65/79.
A/B cover 163/175 answerable information units and C/D/E 155/175. The mobility-hold configurations
exercise the same recovery mechanism and do not add mechanism diversity. Thirteen clusters remain
insufficient for a final inferential claim or a stable empirical cluster-variance estimate.

Development sensitivity is retained in `analysis/results/clustered-power-sensitivity-20260919.json`.
Before seeing sealed data, the current smallest practically meaningful target is a five-percentage-
point absolute response-risk reduction (A 8% to D 3%) at useful coverage. With six questions per
episode, ICC 0.10, paired latent correlation 0.50, and a conservative episode-equal-weight two-sided
95% cluster-normal planning test, 1,000 simulations estimate power of 0.771 at 40 episodes, 0.863
at 50, and 0.922 at 60. Therefore the provisional main collection target is **60 included
independent episodes**, with 50 the minimum target if validity or deadline constraints intervene.
A sensitivity scenario using the unblinded 2/37 versus 1/37 descriptive rates reaches only 0.772
at 100 episodes; it is not treated as a stable effect estimate. Final analysis still uses clustered
bootstrap intervals, not this planning approximation. Provider/model/prompts, verifier policy,
annotation rubric, and coverage units remain mutable pending blind/adjudicated development labels;
the study is not frozen.

The initial powered analysis is land/navigation. Surface CRANE scenarios are ecological validation;
underwater/aerial scenarios are descriptive stress tests unless their independent episode counts
become adequate. Domain interactions are exploratory unless frozen after pilot power analysis.

## Freeze and stopping rules

Before final collection freeze: metric/annotation guide, H1/A-vs-D comparison, prompts, model,
verifier threshold, templates, instrumentation, inclusion rules, split manifest, seeds, and
analysis code. Hash frozen files. Do not inspect sealed labels to tune. Collection stops at the
power-planned independent episode target or the September 28 deadline/compute ceiling, whichever
comes first; report shortfall honestly. Essential experiments do not run October 4.

## Leakage prevention

Robot-visible and evaluator-only artifacts live in physically separate roots with opaque IDs.
Fault names and gold outcomes never appear in model-visible filenames, metadata, prompts, or
retrieval indexes. A release builder performs an allowlist copy and scans for forbidden fields.
