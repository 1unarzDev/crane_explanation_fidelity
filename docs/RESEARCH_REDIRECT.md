# Research redirect: physical diagnosis before language

Status: **ACTIVE PROSPECTIVE DIRECTION, 2026-09-22**. This document is additive. It does not
amend or reinterpret the frozen provenance study, its questions, outputs, labels, or analysis.

## Submission clock

The workshop page says October 4, 2026 AoE, while the live OpenReview invitation currently gives
October 5 06:59 UTC (October 4 18:59 UTC-12; 01:59 America/Chicago) as its due date and 07:29 UTC
as its hard expiration. The portal due date is earlier than literal end-of-day AoE. The project
therefore targets a complete, user-reviewable package on **October 3** and will not rely on the
grace period or a possible extension. Sources and exact conversions are retained in
`docs/research/PHYSICAL_DIAGNOSIS_FOUNDATIONS.md`; the portal must be checked again before
submission.

## Legacy-study disposition

The frozen provenance collection is **CLOSED_EARLY_BY_PROSPECTIVE_REDIRECT at 33 included
episodes**: 17 recovery-followed-by-success and 16 terminal-recovery-abort instances. This is below
the frozen minimum of 40 and target of 50. The study was not completed according to its original
stopping plan, and its originally projected power must not be claimed. No additional ordered row
will be scheduled automatically.

This decision is based on the changed scientific scope and remaining time, not an observed sealed
effect size. No sealed response has a material-error annotation or adjudicated label. Existing
answer text and verification/fallback metadata were necessarily exposed to collection tooling,
and agents/operators saw some answers while checking runs; the project is not operator-blind to
all response content. No sealed labels or condition-joined effect estimate exist or have been
inspected.

The retained cohort remains a separate evidence set about software-mechanism explanation,
runtime-to-source provenance, factual restraint, and evidence insufficiency. It does not establish
physical diagnosis. It will be packaged once at the final 33-episode boundary, independently
dual-annotated under the frozen guide, adjudicated, key-joined only after adjudication, and analyzed
with the frozen code. The shortfall and limited physical evidence will be reported explicitly.

## Current-state audit

Audited against umbrella commit `04b1fe7` and current governed storage on 2026-09-22.

| Area | Authoritative current state | Consequence |
| --- | --- | --- |
| Legacy captures | 33 robot-visible manifests (792 files) and 33 evaluator-only manifests (495 files); all retained sizes/SHA-256 values validate | Cohort is internally complete for the 33 included rows, but below its frozen minimum |
| Legacy model outputs | 33 manifests, 66 question envelopes, 198 one-shot F/G/H calls and 264 output/cache artifacts | No retry/resampling observed in manifests; A--E inside envelopes are non-model smoke outputs |
| Annotation | Historical packets exist, but primary `sealed-primary-v2` stops at episode 21; sealed annotation and adjudication are `NOT_RUN` | Build one final packet/key pair for 33 episodes before annotation; do not analyze historical packet snapshots as complete |
| Fallback | G used deterministic fallback for 46/66 responses (69.7%): 33/33 recovery-mechanism and 13/33 physical-cause answers | Describe final G as predominantly template-rendered; separately report candidate acceptance and final-answer results |
| Current planner | Expresses FollowPath failure, recovery eligibility, Wait invocation/order, source/configuration identity, terminal status, and causal withholding | It cannot express geometric restriction, command-to-motion discrepancy, perception/model inconsistency, or a physical failure chain |
| Ecological land | Three governed development exports: warehouse recovery, complete blockage, corrected S-turn. They retain trajectory samples/summaries, BT/action/recovery data, costmap summaries, and runtime hashes with evaluator truth separate | Useful diagnostic inputs exist, but no explanation comparison or annotation exists; exports do not retain successive global paths or command-to-measured-motion chains |
| RoboBoat | Command signs/response, long paths, turns, docking and independent settle/containment predicates are measured. Eight post-correction docks succeeded; a goal-checker-margin failure and wrong-side/infeasible goal are retained | Ready as a calibration/diagnostic source, not yet a prospective explanation study; wave/current attribution is unsupported |
| Manuscript | `paper/main.tex` is a reproducibly compiled, visually inspected five-page short/WIP draft with 11 checked references and explicit red result gates | The draft is not submission-ready; blinded labels, prospective results, clustered uncertainty, and final sample accounting remain missing |
| Archive restoration | **PASS:** a clean `origin/main` clone configured its local R2 remote, pulled all seven governed roots, and matched all 1,551 artifacts referenced by 99 episode/model manifests | Reproduction requires private credentials and the documented local remote-configuration step; builds and staging data are intentionally outside this snapshot |

The model-artifact auditor now dispatches between the older aggregate schema and current
per-episode artifact-list schema. It hash/size-validates all 33 retained per-episode manifests and
continues to reproduce the aggregate development audit. Frozen manifests and artifacts were not
changed.

## Revised prospective questions

- **Q1 — Diagnostic value:** do validated physical diagnostic computations plus runtime/source
  provenance improve supported diagnostic success over a strong repository-aware agent with the
  same permitted evidence and tools?
- **Q2 — Faithful communication:** does final language preserve the diagnosis, decisive
  measurements, mechanism, and limitations without unsupported additions or useful-detail loss?
- **Q3 — Appropriate specificity:** does the system diagnose supported mechanisms and narrow its
  answer when decisive evidence is absent or ambiguous?

The mapping is deliberate: frozen RQ4/F-vs-G remains the legacy provenance analysis; new Q1 tests
diagnostic value. Frozen specificity/abstention measures inform Q2/Q3, but the new endpoint and
rubric are separately piloted, powered, and frozen. No old response is retroactively treated as a
prespecified physical-diagnosis evaluation.

## Claim-to-evidence map

| Intended paper claim | Existing evidence | Missing evidence | Planned prospective test | Allowed conclusion now |
| --- | --- | --- | --- | --- |
| Provenance/checking reduces material error versus repository agents | 33 paired F/G/H episodes and complete outputs | Blind labels, adjudication, frozen analysis; sample is below minimum | Finish original annotation/adjudication and analysis only | A governed under-target cohort exists; no sealed effect claim yet |
| G communicates software recovery mechanisms conservatively | Checked plans, exact BT/source hashes, final verification; 46/66 fallbacks | Blind correctness/specificity labels | Legacy annotation | Mechanism/source linkage is implemented; trustworthiness effect unmeasured |
| Physical diagnostics improve useful explanations | None in the legacy study; current planner explicitly withholds cause | Validated diagnostic results, matched R/P/T/N outputs, independent labels | New held-out diagnostic study | Not yet supported |
| Land geometry meaningfully affects behavior | Governed warehouse/proving-ground runs retain detour, blockage, recovery, trajectories and costmap summaries. Current-source `diagnostic-land-dev-002` independently reproduces a direct-route cost-253 restriction, retained-grid connectivity, 1.036 m lateral deviation, and successful completion | Successive-plan differences, independent labels, and a prospective test that distinguishes observed association from causal influence | Geometric-restriction, path-comparison, and ambiguous-evidence pilots | One development run supports a bounded route restriction plus detour and success; obstacle identity, exact planner consumption, and restriction-caused-deviation remain unestablished |
| Command-to-motion analysis finds execution failures | Land and boat runs retain commands/motion in runtime artifacts and boat plots; healthy boat response is calibrated | Versioned response diagnostic, tolerances, uncertainty, held-out failures | Calibrated command-to-motion pilot with nominal controls | Signals exist; no prospective diagnostic accuracy result |
| RoboBoat supports a focused surface diagnostic domain | Stable command mapping, path tracking, independent docking, goal-margin and planning failures | Prospective robot-visible diagnostic packets and matched comparisons; no validated wave attribution | One geometric and one execution/disturbance family, bounded pilot | RoboBoat is ready for bounded pilots, not a wave-drift claim |
| Final language is faithful to an internal diagnosis | Exact legacy sentence verifier and fallback | Diagnostic-plan schema, diagnostic-language verifier, diagnosis-to-language annotation | Score internal diagnostic output separately from final answer | Legacy verification exists but does not verify physical diagnoses |
| System improves human trust | No human trust study | User study | None before deadline unless independently designed | Do not claim human trust; report factual/diagnostic outcomes |
| Results transfer to real robots | Simulation and software evidence only | Hardware experiments | None planned pre-submission | Claim simulation-based ecological relevance only |

## Immediate priorities

1. Finalize the 33-episode blinded legacy packet and begin annotation early.
2. Implement the smallest versioned diagnostic-result schema and one end-to-end geometric or
   command-to-motion diagnosis whose final answer is materially more useful than terminal-event
   narration.
3. Pilot two mechanism families with nominal and ambiguous controls; prospectively define
   thresholds and sufficiency labels before held-out runs.
4. Freeze the compact R/P/T/N diagnostic study only after response-quality review and pilot-based
   power planning.
5. Write the manuscript while pilots run. Do not resume platform breadth, aerial, underwater, or
   broad environment work.

## Progress checkpoint — 2026-09-22

The first parity-audited land and RoboBoat comparisons are now retained. Each has one unmasked
question and one paired evidence mask, yielding four final responses per question but only two
independent episode clusters. Tool-enabled R matched the central diagnosis on both unmasked cases;
there is no development evidence that P outperforms R. P's realization failed exact verification
on all four development questions and final P fell back to T each time.

The boat speed mask exposed over-withholding: missing return speed prevents claiming that the
physical platform satisfied Nav2's stopped-speed threshold, but retained pose evidence still shows
that 0.1876 m of post-return motion exceeded 0.0262 m of positional margin and ended outside the
task tolerance. The original output is immutable; a post-hoc v2 checked plan preserves this partial
diagnosis. Blinded packets exist, but independent human annotation, independent reference
computations, nominal controls, power planning, protocol freeze, and held-out collection remain
`NOT_RUN`.

### Additional development checkpoint — 2026-09-22

The retained corrected S-turn now supplies a third statistical cluster. A separately implemented
Bresenham/A* reference, run before model comparison, reproduced the bounded findings: the direct
route crossed a cost-253 cell near x=3.55 m; the retained grid remained connected; delivered
odometry deviated 1.699 m; and the abort was 0.918 s from the exact 70 s deadline. It independently
rejects global no-path, unique obstacle identity, proven planner consumption, and direct observation
of the terminal timeout tick.

The parity-audited R/P/T/N comparison remains a negative development result for differentiation:
tool-enabled R communicated the same central mechanism and limits as P/T. P's candidate was
substantively aligned but failed the exact-text gate, so final P again equaled T. Across five
development questions in three episode clusters, P fallback is 5/5. The new blinded packet brings
the inventory to 20 responses, but human labels, a true prospective nominal control, stable power
planning, protocol freeze, and held-out evaluation remain `NOT_RUN`.

### False-premise development checkpoint — 2026-09-22

The retained nominal success exposed a plan-level defect: the checked answer originally said only
that a failure mechanism was not established, rather than rejecting the false premise. The
diagnostic now records `no_failure_observed`, leads with the successful action status, states that
no terminal failure chain occurred, and limits its claim to this episode. A second defect appeared
in the immutable R output: the rolling costmap covered only part of the requested route, but the
tool interpreted “no blocked sampled cell” as complete direct-route clearance. The wrapper now
reports incomplete coverage and returns an unknown route classification; the R output was retained
and not resampled.

All four methods rejected the failure premise, and P again fell back to T. The blinded development
inventory is now 24 responses in six packets over four clusters, with fallback 6/6. This nominal
episode is retrospective development evidence from a failed fault induction, not the prospectively
declared nominal control still required before freeze.

### Prospective nominal development checkpoint — 2026-09-22

Exactly one predeclared current-source `narrow-doorway-v1` run was executed and retained without
retry. NavigateToPose succeeded after 17.477 m of delivered motion. A pre-model independent audit
found complete requested-route coverage, no cost-253 intersection, retained-grid connectivity,
0.379 m minimum lethal-cell clearance, and only 0.084 m maximum lateral deviation. The checked
answer rejects the false failure premise while retaining those bounded physical measurements and
withholding universal obstacle freedom and exact Nav2 consumption.

One single-sample R/P/T/N comparison is retained. Project review found that R used a 70 s deadline
although the executed hash-pinned XML configures 90 s, while N introduced a hypothetical external
failure criterion not present in the evidence. These are not human labels. P again failed exact
verification and fell back to T. A subsequent predeclared warehouse recovery-sequence case also
fell back and tool-enabled R matched its bounded mechanism, making fallback 8/8 at that checkpoint.
The blinded inventory at that checkpoint was 32 responses in eight packets over six clusters. Human
annotation/adjudication, stable pilot-informed
power planning, protocol freeze, and held-out evaluation remain `NOT_RUN`.

### Command-motion development checkpoint — 2026-09-23

A separately governed held-condition/nominal pair now qualifies synchronized delivered command
and odometry evidence. One no-retry R/P/T/N comparison per run gives tool-enabled R the same blind
samples, pinned source, and executable diagnostic as P. Project review finds that R and raw P
identify the supported discrepancy, while every model condition rejects the nominal false premise;
these observations are not human labels and do not establish P-over-R improvement. Both original P
outputs fell back under lexical false positives, raising immutable development fallback to 10/10.
A post-hoc corrected-verifier audit is retained separately and does not rewrite those outcomes.

The supported and nominal packets share one paired scenario cluster. A subsequently predeclared
missing-odometry mask adds an ambiguous specificity case to that same cluster. R, raw P, and N all
withhold the command-motion mechanism on project review, while retaining the recorded abort and
recovery sequence; these remain unscored observations. P again used immutable deterministic
fallback, bringing development fallback to 11/11. The current inventory is therefore 44 responses
in eleven packets over seven clusters. Human annotation/adjudication, protocol freeze, independent
held-out collection, and inferential analysis remain `NOT_RUN` at that checkpoint.

A separately predeclared compensation run adds the same supported discrepancy with later measured
response recovery and action success. Its no-retry R/P/T/N packet is a distinct eighth development
cluster. Project review finds an incorrect interval/duration in R, checked values in raw P/T, and a
stronger Wait/retry association in N; these are not labels. Final P again falls back to T, bringing
the current inventory to 48 responses in twelve packets over eight clusters and immutable fallback
to 12/12. Human annotation/adjudication and all inferential gates remain `NOT_RUN`.
