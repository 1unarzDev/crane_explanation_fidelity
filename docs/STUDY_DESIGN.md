# Study Design (pre-final-collection draft)

This document must be frozen after pilot/power analysis and before sealed-test evaluation. Items
marked **TBD-PILOT** are not yet frozen.

## Research questions and hypotheses

- RQ1 — **Representation:** with identical underlying evidence and the same generator, does
  structured runtime/decision evidence improve trustworthiness over well-written prose logs?
- RQ2 — **Verification:** do checked plans and final-text verification reduce unsupported claims,
  incorrect details, false explanatory relationships, and causal overclaims versus direct
  generation, retrieval-only generation, or LLM self-checking?
- RQ3 — **Selective explanation:** under missing, contradictory, incomplete, or causally
  insufficient evidence, can the system answer supported portions while correctly withholding the
  rest?
- RQ4 — **Evidence + source provenance:** does linking runtime/physical evidence to the exact
  source/configuration governing observed behavior produce explanations that are more specific,
  auditable, repeatable, and trustworthy than unrestricted repository-agent debugging?
- RQ5 — **Practical robustness:** do improvements persist across realistic navigation/failure
  scenarios and feasible robot embodiments without sacrificing useful coverage?

Cross-domain evidence is a robustness/stress test, not architecture-independence evidence.

The provisional primary H1 is that G reduces response-level material errors relative to strong
repository-agent baseline F at non-inferior substantive coverage. It remains mutable only through
the predeclared model-strength and annotation-reliability pilot, after which it will be frozen before
sealed evaluation. The original
A-versus-D hypothesis remains a representation/checking comparison rather than the novelty claim.
Mechanistic secondary comparisons are B versus A, D versus B, D versus C, H versus G, D versus G,
and E versus D.

## Conditions

- A: well-written free-text record → direct LLM.
- B: structured record with exactly the same facts → same direct LLM.
- C: free text → extraction → checked generation.
- D: native structure → checked plan → generation → output verification/fallback.
- E: structure → deterministic checked template.
- F: raw robot-visible episode evidence + exact repository checkout → generic read-only coding
  agent, with no evaluator-only truth.
- G: structured runtime/physical evidence + runtime-to-source anchors + bounded source retrieval →
  checked plan → generation → final verification/fallback.
- H: structured runtime evidence + exact repository checkout → unrestricted read-only repository
  agent.

Every episode is captured once. A/B information parity is audited proposition-by-proposition;
neither format receives privileged facts. Model, decoding, system prompt, and answer prompt are
identical for A/B. F/G/H use matched model family and effort where their roles permit. G receives
no evaluator truth, additional retry, or source fact unavailable to F/H through the exact checkout;
its advantage is the retained runtime-to-source relationship and checking procedure. Calls are
single-sample and cached with raw/final output, model/version,
parameters, prompt hash, latency, tokens, cost, and verification result.

Before each F/G/H call, a deterministic audit hashes question-relevant information units and their
raw derivation selectors. F receives the raw capture; G and H receive one byte-identical structured
runtime presentation. G's narrow internal episode must validate as a projection of that
presentation before checked planning. Exact source links, bounded retrieval, checked planning, and
final verification remain G's declared treatment. A failed or stale audit blocks model execution.

## Primary outcome

A response has a material error if any substantive assertion is contradicted/unsupported, has an
incorrect comparison/count/status/source attribution, or makes an unjustified causal,
counterfactual, or explanatory relationship. Primary unit: response. Annotation is blind to
condition where formatting permits.

Jointly report substantive answer coverage, full/partial/abstained proportions,
answerable-information coverage, correct abstention, risk–coverage curves, and matched-coverage
comparisons. Also report unsupported/contradicted claims, evidence-citation precision/recall,
numeric/detail and transition correctness, source-reference correctness, runtime/source
correspondence, physical-evidence correctness, causal overclaim, qualification correctness, false
acceptance/abstention, latency, cost, and repeatability. Claim-level error categories are
secondary. Fluency/preference is not correctness.

**Evidence specificity** is the proportion of relevant concrete answerable evidence units correctly
exposed in a response. It prevents generic but safe answers from scoring like detailed supported
answers. Its unit inventory and partial-credit rule are **TBD-PILOT** and must be frozen before the
sealed test.

## Model-strength control

Development compares a small fixed grid of balanced/strong models at low/moderate reasoning on the
same evidence and prompts. Select the least expensive configuration within a predeclared practical
margin of the best on material errors, evidence specificity, coverage, causal overclaim, and
source-reference correctness. Method comparisons must not give G a stronger model than baselines.
A tiered stronger model for difficult source interpretation is adopted only if development evidence
justifies it, and its calls/cost are counted.

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

Current explanation-evaluation sample: eighteen valid land episodes and 545 A/B/C/D/E responses (436
model-mediated). Families are three client-cancellation instances, four unblocked-success instances, six independently configured
terminal recovery/exhaustion instances, planning `NO_VALID_PATH`, and four independently configured
bounded-mobility recovery-followed-by-success instances. A single unblinded development annotation
observed A 6/109, B 0/109, and C/D/E 1/109 material errors. The retained checked error conflated eventual task success with
absence of an explicitly recorded intermediate FollowPath failure; retained outputs were not
regenerated after correcting the planner. A/B substantive coverage is 91/109 versus C/D/E 90/109.
A/B cover 228/245 answerable information units and C/D/E 220/245. The mobility-hold configurations
exercise the same recovery mechanism and do not add mechanism diversity. Eighteen clusters remain
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

The parity-controlled provenance subset currently contains four independent episodes and two
questions per episode: two recovery-followed-by-success instances and two repeated-recovery terminal
aborts. Development-only, unblinded material-error rates are F 4/8, G 0/8, and H 0/8; all eight
responses per condition are substantive. Specificity is F 48/52, G 40/52, and H 52/52. The
episode-clustered planning summary is retained in
`analysis/results/provenance-pilot-four-episode-summary-20260919.json`. Its bootstrap interval is
highly discrete with four clusters and does not replace blind annotation or a sealed test.

For RQ4 planning, a 15-point absolute F-to-G error reduction is the provisional smallest practical
effect: smaller gains are unlikely to justify runtime-source instrumentation over a generic coding
agent. With two questions per episode, ICC 0.15, paired latent correlation 0.50, and 5,000 simulated
clustered datasets, power is 0.802 at 40 episodes, 0.884 at 50, and 0.936 at 60. The provisional
target is **50 provenance-audited episodes**, with 40 the minimum 80%-power target and 60 preferred
if collection/model cost permits. This remains mutable until the model-strength pilot and annotation
guide are frozen; the observed four-episode 50-point reduction is sensitivity-only and is not used
to reduce the target.

The initial powered analysis is land/navigation. Surface CRANE scenarios are ecological validation;
underwater/aerial scenarios are descriptive stress tests unless their independent episode counts
become adequate. Domain interactions are exploratory unless frozen after pilot power analysis.

## Freeze and stopping rules

Before final collection freeze: metric/annotation guide, H1/F-vs-G primary comparison, A–E
mechanistic comparisons, prompts, model,
verifier threshold, templates, instrumentation, inclusion rules, split manifest, seeds, and
analysis code. Hash frozen files. Do not inspect sealed labels to tune. Collection stops at the
power-planned independent episode target or the September 28 deadline/compute ceiling, whichever
comes first; report shortfall honestly. Essential experiments do not run October 4.

## Leakage prevention

Robot-visible and evaluator-only artifacts live in physically separate roots with opaque IDs.
Fault names and gold outcomes never appear in model-visible filenames, metadata, prompts, or
retrieval indexes. A release builder performs an allowlist copy and scans for forbidden fields.
