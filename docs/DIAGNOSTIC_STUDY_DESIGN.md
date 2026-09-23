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

Before either independent annotator returned a label, we fixed one development planning endpoint
for each of six eligible clusters in
`research/explanation_fidelity/experiment_configs/development/diagnostic-pilot-primary-endpoints-v1.json`.
The selection admits the independently implemented S-turn case, prospective nominal case,
pre-model-audited warehouse recovery, supported command--motion case, compensation case, and
delivered-plan case. It excludes the two non-independent-reference families, the retrospective
nominal failed induction, evidence masks, and the matched command--motion control from the primary
planning count. All remain annotated and reported. After adjudication, the fixed selection may
estimate paired discordance and increase the 92-cluster planning target or reject the credibility
of a superiority freeze; its six unstable clusters may never lower that target or motivate a
post-label endpoint substitution.

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

## Command-motion qualification update at 2026-09-23

The passive ROS observer now retains delivered `/nav2/cmd_vel` commands and independently delivered
`/crane/odom` motion with explicit non-consumption/non-acceptance semantics. A predeclared held-arm
development pair showed nominal success and held-condition abort; a separate instrumentation rerun
was used only to qualify the new time-resolved streams. It is not another scenario cluster.

The blind method-visible export strips the intervention-coded acquisition identifier and contains
376 command samples, 1,598 goal-interval odometry samples, exact runtime/source hashes, and the
bounded recovery-classifier derivation. The proposed computation and a separately implemented
evaluator reference both identify the earliest qualifying 7–17 s interval: median command
0.800 m/s, calibrated healthy measured response 0.2597 m/s, and discrepancy response 0.000 m/s.
Two FollowPath failures and two source-qualified Wait recoveries were recorded before a third
FollowPath attempt and action abort.

The matched time-resolved nominal rerun succeeded after 9.480 m displacement with zero FollowPath
failures and zero source-qualified Wait invocations. Both implementations return `not_triggered`,
and the checked answer explicitly rejects the false failure premise. This passes the engineering
gate for a second mechanism, but not the prospective study gates.

One no-retry R/P/T/N comparison was then retained for each member of the pair. R received the blind
samples, exact CRANE/core source, and the same executable window computation as P. On project
review, R and raw P identified the supported discrepancy; N described it only as suggested without
the aligned computation. R, raw P, and N all rejected the nominal failure premise. These are not
human labels and do not establish a P-over-R effect. The then-current final-text gate rejected both
P candidates for lexical false positives, so the immutable final P outputs used deterministic
fallback (2/2). A later post-hoc audit under corrected bounded matching accepts both raw candidates
after evidence-ID-only repair and rejects all six authored mutations; it does not alter the original
outputs or estimate verifier error rates.

Three blinded four-response packets now cover the supported member, nominal member, and a
predeclared missing-odometry evidence mask. They share one
`command-motion-held-nominal-pair-001` statistical cluster because they are a paired
intervention/control/evidence-mask family. In the mask, 376 command samples remain but all
independent odometry samples are absent. The independently computed reference labels the
command-motion mechanism insufficient while retaining the abort, two FollowPath failures, and two
source-qualified Wait invocations as answerable sequence evidence. R, raw P, and N all withhold the
missing mechanism on project review; no P-over-R advantage is apparent. The original P output again
fell back, and a later post-hoc verifier fix does not alter that result.

Before the compensation case below, the development annotation inventory contained 44 responses
over seven clusters, with
human annotation and adjudication still `NOT_RUN`. Independent scenario collection, protocol
freeze, and held-out evaluation remain `NOT_RUN`. The development thresholds are not frozen, and
the three variants cannot be counted as separate scenario instances.

A separately predeclared compensation scenario then applied the unchanged development thresholds
to a transient command--motion discrepancy with a different terminal outcome. Its blind export
contains 485 goal-bounded command samples and 2,232 independent odometry samples. An independent
implementation reproduces the supported 8--18 s interval (0.800 m/s delivered command versus
0.000 m/s measured response), the later 20--21 s recovery window (0.2597 m/s measured response,
ratio 1.0), one FollowPath failure, one source-qualified Wait invocation, and eventual action
success after 9.469 m displacement. The evaluator intervention identity remains excluded.

This is one new independently configured **development** scenario, not a held-out or confirmatory
result. Inspection of the first checked response exposed that the v1 plan reported only the
terminal success and did not measure recovered response. The v2 recovery computation and improved
answer were therefore developed post-observation and are regression evidence, not a prospective
effectiveness estimate.

After the physical evidence was governed, a separate predeclared no-retry R/P/T/N comparison used
the same blind input and executable v2 computation for P and tool-enabled R. Project review finds
that R identifies the mechanism and recovery but reports an incorrect 8--20 s / 12 s discrepancy;
the independent result is 8--18 s / 10 s. Raw P reports the checked values but the operating
verifier rejects it for a missing controller-failure-sequence proposition, so final P falls back to
T. N lacks the aligned computation and associates the Wait/retry with success more strongly than
the retained evidence warrants. These observations are not labels or a method-effect estimate.
The blinded four-response packet raises the development inventory to 48 responses, twelve packets,
and eight clusters; human annotation and adjudication remain `NOT_RUN`. Its paired governed data
manifests are `diagnostic-motion-development-cm-002.*.json`.

After output retention, future policy `bounded-diagnostic-language-v2` corrected that section-scope
false negative: the exact raw candidate passes when its explicit `FollowPath` failure is read from
decisive evidence, while mutations that omit `FollowPath` or claim Wait caused response recovery
fail closed. This is post-hoc development tuning, not verifier-accuracy evidence. The archived v1
rejection, deterministic final P, packet, and 12/12 observed fallback frequency remain unchanged.

### Delivered-plan development extension

One separately predeclared no-retry land run qualified independently auditable delivered-plan
geometry. The first instrumentation attempt remains a partial result because it discarded the
poses needed to reproduce its summaries. The corrected run retained 12,975 poses across 70 unique
plans; an independent implementation reproduced every hash, length, and deviation without
mismatch. It supports an initially direct delivered plan, later non-direct plans spanning
-1.175 m to +1.035 m, delivered-odometry deviation, and action success. It does not support
controller consumption, a physical trigger, or costmap-to-plan causation.

A prospectively declared one-shot R/P/T/N comparison asked only for the supported route change,
outcome, and unresolved trigger. Tool-enabled R received the same complete fixture, source, and
executable v2 computation as P. Project review finds R matches the checked answer closely; N uses
stronger plan-following and approximately-per-metre update language; raw P is aligned but the fixed
verifier rejects `route change from` under a narrower lexical matcher and final P falls back to T.
These are not labels. The packet raises the development inventory to 52 responses, thirteen
packets, and nine clusters, with human annotation/adjudication, protocol freeze, held-out
collection, and inference still `NOT_RUN`. Aggregate immutable fallback is 13/13.

## Other retained development cases at 2026-09-23

- A retained unexpected land success now passes a false-premise-aware `not_triggered` check and has
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

## Prospective collection decision at 2026-09-23

Protocol freeze remains `NOT_READY`. The immediate dependency is two independent blinded
development annotators followed by a distinct adjudicator for disagreements. Until those labels
exist, no defensible pilot discordance estimate, verifier error estimate, or response-quality
assessment exists. Project-author review cannot fill that role.

The retained land catalog and command--motion family establish two runnable mechanisms, but the
catalog alone cannot supply the 92 independent clusters in the design sensitivity and current
project review does not suggest a P-over-tool-enabled-R advantage. The post-annotation decision
must therefore be prospective and explicit: either (a) demonstrate a feasible route to the
predeclared powered target using genuinely distinct scenario configurations, or (b) freeze a
deadline/resource-limited, explicitly underpowered study and report effects and clustered
uncertainty without equivalence claims. No held-out episode or model output may be inspected before
that choice, the split, stopping rule, prompts, thresholds, and analysis are frozen.
