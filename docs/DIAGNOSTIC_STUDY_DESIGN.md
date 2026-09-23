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

## Power sensitivity and effective sample size

No independent development labels exist, and project-author review found several R/P ties.
Therefore the design does **not** use the unblinded pilot impressions as an effect estimate. The
reproducible exact sensitivity analysis is
`research/explanation_fidelity/experiment_configs/development/diagnostic-study-power-sensitivity-v1.json`.
It assumes one predeclared primary binary endpoint per independent scenario instance and a
two-sided exact paired sign/McNemar test at alpha 0.05.

The prospectively declared smallest practically meaningful improvement is a +15 percentage-point
net supported-diagnostic-success difference, represented for planning as 20% P-success/R-failure
discordance versus 5% R-success/P-failure discordance. This threshold is a design judgment—not an
observed effect—and reflects the extra diagnostic-computation and verification cost. Exact power
reaches 80% at 92 independent primary clusters and 90% at 119. A target of 96 would provide 82.0%
power under that particular pattern; 40 clusters would provide only 36.4%. If R and P are more
often symmetrically discordant or the effect is smaller, substantially more clusters are required.

The current proving-ground seed changes the configuration identity but not obstacle geometry.
Repeated seeds of one layout are therefore **not independent scenario instances** and cannot be
used to reach the target. Before protocol freeze, the collection path must demonstrate genuinely
distinct, versioned geometry/configuration instances and validate their throughput. If 92 valid
independent primary instances are infeasible by the collection cutoff, collection stops for the
predeclared deadline/resource reason, and the paper reports achieved effects/intervals as
underpowered rather than claiming planned power or equivalence.

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

- Land has six parity-audited R/P/T/N development comparisons over five episode clusters,
  including one paired evidence mask; RoboBoat has one comparison plus a paired evidence mask.
  This is six episode clusters, not eight independent questions.
- In all three diagnosable unmasked comparisons, tool-enabled R expressed the central mechanism at
  least as well as P/T. In the retrospective nominal control, every method rejected the false
  premise, but R additionally overclaimed complete route clearance from a partial rolling grid.
  This exposed and fixed a shared tool defect; the immutable R output was not resampled. Current
  development evidence still does not establish a P-over-R effect.
- P used deterministic fallback in all six land and both boat comparisons (8/8 development
  questions). The final method is therefore template-rendered at the current operating point.
- A post-hoc bounded-language verifier accepts 7/8 raw P candidates after evidence-ID-only repair
  and rejects 24/24 simple adversarial mutations. The masked-speed candidate remains rejected for
  unplanned derivations and a missing limitation. This is development tuning, not independent
  accuracy evidence; archived outputs remain unchanged, and the new policy must be frozen before
  any prospective use.
- The speed-masked boat case remains positionally diagnosable: observed post-return motion exceeded
  the retained positional margin. Missing speed prevents only the stronger stopped-speed claim.
  The original over-withholding output is retained, and a post-hoc v2 checked-plan correction is
  not counted as prospective evidence.
- Eight blinded packets (32 responses) exist and cover six episode clusters. Separately
  implemented evaluator-side boat arithmetic and land raster/A* references reproduce the bounded
  development findings without importing P's diagnostic code. The S-turn reference was computed
  before its model comparison; the earlier references were authored after output inspection.
  Independent reviewer validation
  remains `NOT_RUN`; these post-output development implementations are not confirmatory gold.

## Catalog qualification update at 2026-09-23

The generated v4 catalog now contains 48 prospective connected-detour candidates and 24 nominal
controls. Eight stable blockage layout IDs remain only as `development-calibration /
failed-induction-calibration`; the 48 unrun confirmatory blockage identities were removed. Three
live blockage calibrations—open 8 m, closed 8 m, and closed 5 m—continued to produce planner paths
and reached the client deadline. They do not establish planner-grid disconnection despite the
offline canonical raster being disconnected.

One connected-detour run and one nominal run succeeded with materially different retained path
shapes, so the catalog remains useful for obstacle/path evidence. It cannot by itself supply the 92
independent primary clusters in the design sensitivity. Protocol freeze therefore remains
`NOT_READY`: a second mechanism must pass end-to-end development qualification, or the study must
prospectively adopt an explicitly underpowered deadline/resource stopping plan. No held-out
collection has begun and no observed effect was used to make this decision.
  A retained unexpected land success now passes a false-premise-aware `not_triggered` check and has
  a blinded R/P/T/N packet, but it was not prospectively collected and has no human labels.
- One separately governed, prospectively declared nominal land episode now supplies complete-route
  costmap coverage, successful action status, and low-deviation delivered odometry. Its independent
  reference, corrected checked rendering, and single-sample R/P/T/N comparison are retained.
  Project review found that R used an incorrect 70 s deadline despite the exact 90 s XML, while N
  introduced an unsupported hypothetical external evaluator; those observations await blind human
  scoring and are not labels. Human annotation, power planning, protocol freeze, and held-out
  evaluation remain `NOT_RUN`.
- The retained warehouse recovery sequence adds a predeclared development ambiguity case. R and
  P/T all reconstruct at least four source-qualified invocations and eventual task success while
  withholding physical causation; N lacks the validated planner-failure/eligibility linkage. This
  is a negative differentiation result on project review, pending blinded scoring.
- A retrospective RoboBoat wrong-side-goal run now has a compact, independently recomputable
  retained-grid disconnection diagnosis: result cell cost 0, goal cell cost 253, no connection
  below 253, 23 matching Navfn failure messages, then action abort. Its exact dirty source snapshot
  was not retained, so it is development-only, adds no confirmatory cluster, and has no R/P/T/N
  comparison or human label.
