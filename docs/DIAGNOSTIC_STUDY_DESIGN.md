# Prospective physical-diagnosis study design

Status: **DRAFT FOR DEVELOPMENT PILOT — NOT FROZEN, NOT A CONFIRMATORY PROTOCOL**.

This study is separate from the frozen 33-episode provenance cohort. It uses new namespaces,
splits, questions, labels, outputs, and analysis. No ecological/boat episode is pooled with legacy
mobility-hold episodes.

## Questions and primary endpoint

Q1–Q3 are defined in `docs/RESEARCH_REDIRECT.md`. The proposed primary endpoint is **supported
diagnostic success** on independently labeled diagnosable questions: the final answer identifies
the required mechanism and contains no material unsupported or contradicted assertion.

Secondary outcomes: diagnostic-result correctness; final-language faithfulness; material-error
risk; causal overclaiming; unnecessary abstention; appropriate ambiguity qualification;
mechanism/location/time identification; evidence coverage/citation correctness;
diagnosis-to-language omission; selected next-check correctness; latency, token use/cost where
known; and fallback frequency. Diagnostic output and final language are scored separately.

## Compact methods

- **R:** strong repository-aware agent with the same robot-visible physical evidence, exact
  source/configuration, and the same executable diagnostic tools/descriptions available to P.
- **P:** validated diagnostic computations + provenance + checked answer plan + language + final
  verification/fallback.
- **T:** deterministic rendering of the same checked diagnostic result.
- **N:** new-arm provenance/checking ablation without physical diagnostic computations; it does not
  alter or masquerade as the archived legacy G implementation.

Model/settings, evidence, tool access, and resource budgets are matched and retained. Tooling or
extra computation is reported as part of the treatment, not attributed to prompting alone.

## Pilot families

Start with two mechanisms and add a third only if both are healthy:

1. **Land geometric restriction:** nominal traversable route, observed restriction relative to
   physical footprint, configured-envelope restriction, ambiguous/local-only evidence, and an
   irrelevant visible obstacle.
2. **Command-to-motion discrepancy:** calibrated nominal response, successful compensation,
   saturated/insufficient correction, and missing/ambiguous decisive motion evidence. Use land or
   RoboBoat based on retained signal quality.

RoboBoat may additionally supply one geometric approach case and one execution/disturbance case.
Wave/current labels are prohibited unless separately validated. Basic command mapping must pass
before any disturbance case is eligible.

## Prospective controls and split

- Preserve robot-visible/evaluator-only physical separation and opaque episode IDs.
- Retain valid unexpected outcomes; report induction success separately from recording validity.
- Group shared layouts, paired interventions, evidence masks, and question variants into one
  statistical cluster and one split.
- Keep held-out scenario configurations; perform actual controlled reruns rather than
  recorded-state counterfactual replay.
- Freeze questions, sufficiency labels, thresholds, models, prompts, resource budgets, split,
  stopping rule, rubric, and analysis before held-out evaluation.
- Estimate paired discordance/cluster variance from development pilots and run a new power
  simulation. Do not reuse the legacy 40-episode calculation.

## Questions

Use a small inventory: diagnosis/mechanism, decisive evidence, failure chain, path/clearance or
motion-response comparison, ambiguity/causal restraint, false premise, and fixed-menu next check.
Every question must discriminate a declared capability; paraphrases do not add independent units.

## Admission gates before freeze

- At least one end-to-end measured diagnosis produces a materially useful answer beyond terminal
  narration.
- Independent reference computation and sufficiency label exist for each mechanism.
- Nominal, diagnosable, and ambiguous development cases all pass recording/governance checks.
- Information/tool parity for R/P is audited.
- Blind annotation packet, dual annotation, and adjudication workflow are dry-run on development
  outputs.
- Response-quality review confirms P/T lead with diagnosis and preserve limitations.

## Development status at 2026-09-22

- Land has two parity-audited R/P/T/N development comparisons, one with a paired evidence mask;
  RoboBoat has one comparison plus a paired evidence mask. This is three episode clusters, not
  five independent questions.
- In all three unmasked comparisons, tool-enabled R expressed the central mechanism at least as well as
  P/T; current development evidence does not support a P-over-R claim.
- P used deterministic fallback in all three land and both boat comparisons (5/5 development
  questions). The final method is therefore template-rendered at the current operating point.
- The speed-masked boat case remains positionally diagnosable: observed post-return motion exceeded
  the retained positional margin. Missing speed prevents only the stronger stopped-speed claim.
  The original over-withholding output is retained, and a post-hoc v2 checked-plan correction is
  not counted as prospective evidence.
- Five blinded packets (20 responses) exist but cover only three episode clusters. Separately
  implemented evaluator-side boat arithmetic and land raster/A* references reproduce the bounded
  development findings without importing P's diagnostic code. The S-turn reference was computed
  before its model comparison; the earlier references were authored after output inspection.
  Independent reviewer validation
  remains `NOT_RUN`; these post-output development implementations are not confirmatory gold.
  A retained unexpected land success now passes a deterministic `not_triggered` nominal check, but
  it was not prospectively collected and has no R/P/T/N or human labels. Human annotation, a
  prospectively declared nominal control, power planning, protocol freeze, and held-out evaluation
  remain `NOT_RUN`.
