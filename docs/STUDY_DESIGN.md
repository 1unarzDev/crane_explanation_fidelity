# Study Design (freeze candidate v1)

This design is frozen by the content-addressed study manifest before collection of `pn-0001`.
Changes after freeze require a dated amendment that preserves the original files and states whether
sealed evidence had been inspected.

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

The primary H1 is that G reduces response-level material errors relative to strong repository-agent
baseline F while its substantive coverage is no more than five percentage points lower. The
smallest practically meaningful risk reduction is 15 percentage points. Primary success requires
the episode-cluster bootstrap 95% interval for G-minus-F error risk to exclude zero in the favorable
direction and the coverage-difference interval not to cross below -0.05. The original A-versus-D
hypothesis remains a representation/checking comparison rather than the novelty claim.
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

The two frozen questions are exactly “Why did the autonomy software enter recovery?” and “Did a
physical obstacle cause the navigation failure?” They intentionally pair an evidence-rich software
mechanism request with an evidence-limited physical-cause request.

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
answers. The binary unit inventories and no-within-unit-partial-credit rule are frozen in
`docs/ANNOTATION_GUIDE.md`: eight units for recovery mechanism and five for physical cause.

## Model-strength control

Method comparisons must not give G a stronger model than baselines. No tiered routing is used in the
sealed study.

The predeclared four-episode control compared `gpt-5.6-sol` and `gpt-5.6-luna` at low reasoning on
the same 24 F/G/H requests. Luna's errors were F 3/8, G 0/8, H 1/8 versus Sol's F 4/8, G 0/8, H
0/8; aggregate specificity was 140/156 for both, and coverage was 1.0 for every condition. Luna met
all predeclared margins and used 8.7% fewer input tokens, 20.5% fewer output tokens, and 29.8% less
aggregate latency. Therefore **`gpt-5.6-luna`, low reasoning** is selected for the main matched
F/G/H study. Monetary cost was not reported and no equivalence claim is made. The retained decision
is reproducible from `analysis/results/provenance-model-strength-20260919.json`.

## Units, split, and inclusion

Independent unit is scenario instance/episode, never a paraphrase. The sealed split contains 60
opaque, ordered configurations balanced 30/30 between recovery-followed-by-success and terminal
recovery-abort. Minimum/target/preferred included counts are 40/50/60. Run in frozen order, stopping
at 50 included episodes; entries 51–60 replace capture-quality exclusions or extend to 60 only if
compute and the September 28 deadline permit. Outcomes or model answers never control stopping.

An episode is included only if, before model calls: capture start/stop boundaries exist; exactly one
accepted goal and one matching terminal result exist; BT XML and runtime-manifest hashes validate;
the runtime provenance calibration checks pass; costmap evidence is populated; both F/G/H parity
audits accept; and the predeclared family activates (one distinct Wait invocation followed by task
success, or two distinct Wait invocations followed by action abort). Exclude the whole episode for a
failed gate and retain it with one predeclared reason. Never exclude one condition or inspect answers
first. Both frozen questions are included for every included episode. Deliberate causal
insufficiency is required, not an exclusion.

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
bootstrap intervals, not this planning approximation. These older A–E planning assumptions do not
determine the provenance-study sample size.

The parity-controlled provenance subset contains four legacy episodes and two
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
if collection/model cost permits. The observed four-episode 50-point reduction is sensitivity-only
and is not used to reduce the target. A separate fair-configuration e043 diagnostic retained the
exact running parameter identity and observed F/G/H errors 1/0/0 over two questions; it supports the
rubric's configured-versus-observed causal boundary but is not an effect estimate.

The initial powered analysis is land/navigation. Surface CRANE scenarios are ecological validation;
underwater/aerial scenarios are descriptive stress tests unless their independent episode counts
become adequate. Domain interactions are exploratory unless frozen after pilot power analysis.

## Freeze and stopping rules

F/G/H run on every included episode. A–E run on the first 20 included episodes (ten per family) as
sealed mechanistic secondary evidence; this subset is not independently powered. All methods use
`gpt-5.6-luna` at low reasoning where a model is required, one call per declared stage, no retries or
resampling. Prompts, question text, model, strict verifier/fallback policy, instrumentation,
inclusion rules, split, seeds, annotation guide, and analysis code are hash-frozen. G makes one
realization call; if any final sentence is not exactly licensed by the checked plan, no repair call
is made and the deterministic checked template replaces the candidate. The verifier threshold is
therefore binary exact acceptance, not a tuned probability.

Do not inspect sealed labels to tune. Collection stops under the split rule or the September 28
deadline/compute ceiling, whichever comes first; report shortfall honestly. Essential experiments
do not run October 4.

## Leakage prevention

Robot-visible and evaluator-only artifacts live in physically separate roots with opaque IDs.
Fault names and gold outcomes never appear in model-visible filenames, metadata, prompts, or
retrieval indexes. Model workspaces contain only an exact `crane_ml` archive plus an allowlisted
robot-visible packet. `scan_robot_visible_leakage.py` rejects evaluator-only path fragments and JSON
keys before calls. The mapping from opaque ID to intervention/family remains evaluator-only during
generation and annotation.
