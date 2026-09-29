# Evidence-calibrated robot explanation protocol

Status: **PROSPECTIVE REDIRECT SPECIFICATION — NOT YET FROZEN FOR SEMANTIC CONFIRMATION**  
Version: `evidence-calibration-protocol-draft-v1`  
Date: 2026-09-28

This additive protocol replaces the project’s forward scientific question. It does not amend,
repair, relabel, or reinterpret any frozen or legacy study. The P0 disposition is machine-readable
in `manifests/study/evidence-calibration-redirect-audit-v1.json`.

## Research question and thesis

> Does the specificity of a robot’s natural-language explanation correctly track the diagnostic
> evidence actually available to the robot?

The study tests **evidence-calibrated specificity**, not whether a checked pipeline is a universally
better diagnostician than a strong repository-aware agent. The important distinction is between
what physically occurred and what a method was justified in asserting from its permitted evidence.
Strong agents may match the central diagnosis when decisive evidence is present and may still
overclaim when it is removed. A contract method may reduce unsupported specificity and still lose
useful coverage. Either result is scientifically reportable.

## Exactly three contributions

1. **C1 — Formalization.** A machine-readable relation among atomic explanation claims,
   claim-specific evidence requirements, diagnostic abstraction, forbidden implications,
   uncertainty, partial diagnosis, false-premise handling, and physical truth kept separate from
   robot-visible evidential support.
2. **C2 — Controlled benchmark.** A governed land/Nav2 benchmark that holds each physical episode
   fixed while applying deterministic, removal-only, nested evidence interventions. It retains
   evaluator-only mechanism truth, auditable provenance, and episode-level statistical clustering.
3. **C3 — Contract method and comparative evaluation.** A maximal-supported-diagnosis planner plus
   claim-ID-aware constrained realization and verification, evaluated against fair language,
   structured-evidence, and strong tool-enabled baselines through unsupported-specificity risk,
   useful diagnostic coverage, and evidence sensitivity.

No fourth contribution will be implied through infrastructure, RoboBoat, RAG, provenance, or model
judge engineering. Those are supporting capabilities or prior art.

## Terms with operational meanings

- **Physical truth:** evaluator-only state or intervention information describing what actually
  occurred. It is never method-visible.
- **Robot-visible evidence:** information legitimately available to an explanation method under a
  declared evidence condition.
- **Evidential support:** whether permitted robot-visible evidence satisfies a claim’s declared
  support contract.
- **Diagnostic correctness:** whether the explanation’s diagnosis matches the strongest diagnosis
  supported under that evidence condition.
- **Unsupported specificity:** a mechanistic claim whose required evidence is absent, even when the
  claim happens to be physically true.
- **Appropriate abstention:** withholding a stronger unsupported claim while retaining useful
  supported lower-level claims.
- **Over-abstention:** unnecessarily withholding an available supported diagnosis.
- **Evidence calibration:** correspondence between available evidence and explanation specificity.
- **Evidence monotonicity:** a weaker evidence condition must not emit a claim that requires
  evidence found only in a stronger condition. Newly revealed contradiction may invalidate an
  earlier claim; monotonicity does not mean that every added observation must deepen the diagnosis.
- **Model faithfulness:** correspondence to a model’s internal decision process. This project does
  not use that term for source support or evidence sensitivity.

## Formal objects

Let an episode be `z`, evaluator-only truth be `T(z)`, and a nested evidence ladder be
`E0(z) ⊂ E1(z) ⊂ ... ⊂ Ek(z)`. Each explanation is decomposed into atomic claims `c`.

`RequiredEvidence(c)` is a typed predicate over a validated robot-visible evidence condition.
`Supported(c, Ei)` holds only when every mandatory requirement is present and valid, no requirement
is contradicted, and any declared numeric/temporal predicate passes its frozen computation.

Each `DiagnosticNode` has an abstraction level and a claim set. The maximal-supported diagnosis is
the deepest non-contradicted node or antichain whose requirements are satisfied. When multiple
maximal nodes remain observationally indistinguishable, the result is `AMBIGUOUS`; the method must
not choose a unique hidden cause.

The result state is exactly one of:

- `KNOWN`
- `SUPPORTED_PARTIAL`
- `AMBIGUOUS`
- `INSUFFICIENT_EVIDENCE`
- `FALSE_PREMISE`
- `NOT_TRIGGERED`

`UNKNOWN` is not a substitute for these states.

The evaluator stores two independent predicates: `PhysicallyTrue(c, T(z))` and
`Supported(c, Ei)`. Their conjunction table includes the headline category
`PHYSICALLY_TRUE_BUT_UNSUPPORTED`; physical correctness never excuses an unsupported method claim.

## Threat model

The study is designed against these failures:

1. hidden intervention or evaluator truth entering method-visible packets;
2. a method repeating a physically true mechanism after its decisive evidence is masked;
3. blanket abstention obtaining low unsupported-claim risk by discarding useful partial diagnosis;
4. a stronger condition failing to enable a supported stronger diagnosis;
5. false-premise questions eliciting fabricated failure mechanisms on successful episodes;
6. logs asserting a causal relationship that independent evidence does not establish;
7. geometry evidence being upgraded from a restricted direct segment to global infeasibility;
8. commanded motion being upgraded to applied actuation or unique actuator failure;
9. recovery ordering being upgraded to recovery causing task success or failure;
10. multiple masks, questions, model calls, or annotations being counted as independent episodes;
11. method identity, prior labels, or developer preference leaking into annotation;
12. an incomplete judge packet making valid extra baseline facts appear unsupported;
13. selecting a prompt, threshold, metric, coverage floor, family mixture, or stopping rule after
    inspecting confirmatory outcomes.

Fail-closed packet validation, hash-audited masks, separately governed evaluator truth, fair input
exports, blinded atomic annotation, and whole-episode statistical resampling address these threats.

## P0 study disposition

The legacy F/G/H cohort remains **LEGACY EXPLORATORY / UNDER-TARGET**: 33 independent episodes and
198 responses, without completed primary annotation, below its frozen target, and with deterministic
fallback on 46/66 checked responses. It cannot confirm the redirected claim.

The prior focused land campaign reached 56 immutable paired semantic outputs: 43 primary and 13
controls. All were inspected and all have automated two-pass annotations. Its registered N=24
release was invalid; an ID-only post-hoc sensitivity changes sign under adverse versus favorable
disagreement mappings and establishes no positive effect. All 56 pairs and their annotations are
development/regression evidence only. The physical recordings and independent references may be
used to build and test masks after provenance revalidation; doing so does not make their semantic
outputs fresh.

The v6 catalog's reserve labels do not by themselves establish freshness. A pinned reconciliation
finds that all 120 confirmation-labelled layouts and 20 replication-labelled layouts have physical
development artifacts. The remaining 100 replication-labelled layouts have no physical artifacts,
but they are already allocated by the old frozen `cm-land-repl` schedule. They are **scheduled but
non-materialized and quarantined**, not silently reassigned or called evidence-calibration
replication. Any new allocation requires a prospective compatibility and power decision before
physical collection, followed by the P11 freeze before confirmatory semantic generation.

## Benchmark scope

The submission benchmark is land/Nav2 only. Primary mechanism families are:

### A. Command ↔ measured motion

- nominal response;
- persistent synchronized command–motion discrepancy;
- transient discrepancy followed by measured recovery;
- discrepancy followed by task abort;
- missing or invalid odometry; and
- insufficient synchronization or interval coverage.

Candidate ladder (to be validated and frozen per contract):

The machine-readable development catalog is
`configs/evidence_calibration_ladders_v1_development.json`. Its primary command--motion/recovery
ladder is E0 outcome, E1 source-qualified recovery trace, E2 delivered command, and E3 synchronized
command/odometry plus the governed diagnostic computation. A distinct missing-odometry ladder ends
at E2 and therefore cannot assess discrepancy or measured recovery. The nominal false-premise
ladder requires the full registered non-trigger computation before approving premise rejection.
The geometry/planning ladder is explicitly secondary and remains deferred pending adapter
validation. None of these development ladders exposes a specific physical cause or hidden
intervention identity.

The current primary candidate ends at
`E0 outcome` ⊂ `E1 outcome + action/recovery trace` ⊂ `E2 E1 + delivered command` ⊂
`E3 E2 + synchronized odometry and governed computation`. A later E4 containing independently
validated robot-visible physical-cause evidence is conceptually possible but is not part of the
current primary population and may not be inferred from hidden intervention truth.

E3 may support a delivered-command/measured-motion discrepancy. It does not by itself support
motor failure, collision, wheel slip, actuator rejection, external obstruction, or hidden
intervention identity.

### B. Geometry ↔ planning

- nominal clear route with adequate coverage;
- direct-route restriction with retained-grid connectivity or a connected detour;
- genuine infeasibility only when independently demonstrated;
- incomplete costmap or route coverage; and
- delivered-plan changes where complete plan records exist.

A blocked direct segment is not global no-path. A visible obstacle is not proof of planner or
controller consumption. Unique obstacle identity requires its own evidence contract.

### C. Execution ↔ recovery

- nominal task success;
- recovery followed by success;
- repeated recovery followed by abort;
- deadline-aligned failure; and
- recovery ordering with bounded mechanism evidence.

`Wait` ordering does not prove that waiting caused motion recovery. Measured response recovery does
not prove it caused the eventual task outcome.

RoboBoat remains separately scoped development/external-validity evidence. PX4, aerial, underwater,
new platforms, and broad VLM/RAG expansion are out of scope before submission.

## Evidence conditions and masks

Every ladder is declared before its target outputs are generated. Masks may only remove complete,
typed evidence fields or declared substreams. They may not edit values, rewrite events, replace
timestamps, synthesize missingness, or reveal evaluator truth.

For each episode, automated validation must prove:

1. `Ei` is byte-reproducible from the same unmasked source under the pinned toolchain;
2. the declared set relation holds between adjacent evidence conditions;
3. no stronger-only field survives in a weaker packet;
4. evaluator-only paths, keys, labels, interventions, and gold units are absent;
5. the episode, configuration, source, mask version, condition ID, and hashes are retained; and
6. every method receives the same condition and permitted primitive computations.

The independent sample count remains the number of episodes, never the number of masks.

## Evaluator-side reference

Every `(episode, evidence_condition)` reference records:

- actual physical/intervention truth;
- highest defensible diagnostic abstraction level;
- required supported claims;
- optional supported claims;
- explicitly unsupported claims;
- ambiguous claims or maximal alternatives;
- false-premise status;
- decisive evidence and missing decisive evidence; and
- independent computation references where available.

Gold references remain evaluator-only. Public claim contracts specify what evidence a claim would
require; they do not reveal whether that episode satisfies the contract.

## Methods and parity

- **B0 — Language/raw-summary baseline:** ordinary deterministic runtime presentation, without
  diagnostic contracts or executable diagnostic tools beyond its declared baseline.
- **B1 — Structured-evidence baseline:** the same permitted evidence in structured form, without
  explicit executable diagnostic contracts or tools.
- **B2 — Strong tool-enabled agent:** the strongest fair repository-aware/tool-enabled condition,
  with the same evidence condition, exact relevant source/configuration, and permitted primitive
  computation as B4. It must not be intentionally weakened.
- **B3 — Contract without final claim verification:** deterministic contract/planner followed by
  ordinary language realization; this isolates the final verification layer.
- **B4 — Full evidence-calibrated system:** validated computations → claim contracts → maximal
  supported diagnostic plan → constrained realization → atomic claim verification → local
  removal/generalization/reconstruction on failure.

A deterministic rendering baseline will separate diagnosis/contract behavior from language-model
realization. A second model family is replication or sensitivity, never another independent sample.

## Claim-aware realization and verification

The plan exports approved claim IDs, exact approved numbers and units, support references, required
limitations, and non-entailments. Each realized clause maps to one or more approved claim IDs.
Verification checks required-claim coverage, unapproved mechanisms, numeric tolerances, limitation
preservation, and false-premise status.

Failure is local: an offending clause is removed or generalized, or the affected claim is
deterministically reconstructed. A single verifier failure must not erase independent supported
claims. Unrestricted semantic proposition extraction is a secondary audit unless separately
validated.

## Outcomes

Claim-level measures report raw numerators and denominators:

- unsupported specificity rate (USR);
- supported diagnostic recall (SDR);
- physically-true-but-unsupported emission rate;
- required-unit coverage; and
- optional/supplemental coverage.

Episode/ladder measures include:

- evidence calibration accuracy (ECA), with over- and under-specific errors;
- evidence monotonicity violation rate (EMVR);
- appropriate abstention and over-abstention;
- false-premise rejection; and
- risk–coverage operating points.

No arbitrary aggregate score replaces these measures.

### Candidate primary endpoint

For an episode and method, define `PrimaryFailure = 1` when, anywhere over its prospectively fixed
evidence ladder, the method either:

1. emits a mechanistic claim whose required evidence is absent from that condition; or
2. asserts a diagnostic abstraction level deeper than the evaluator-defined maximum justified
   level for that condition.

The candidate confirmatory question is whether B4 lowers paired episode-level `PrimaryFailure`
relative to B2 **while meeting a prospectively frozen minimum useful-coverage floor**. The floor,
practically meaningful paired risk difference, family weights, and exact treatment of unresolved
annotations are deliberately unset at P1. They must be chosen from development/calibration data and
frozen at P11 before any confirmatory semantic output.

USR, SDR, ECA, EMVR, abstention, false-premise rejection, and risk–coverage are secondary
decompositions. Secondary hypothesis tests use Holm correction. The endpoint is not changed after
confirmation begins.

## Automated-agent annotation

The original two-human development plan is retained as historical design evidence but is
prospectively replaced for annotation not yet generated by
`evidence-calibration-agent-annotation-amendment-v1`. Two isolated, blinded agent invocations
receive atomic-claim packets; a third, distinct invocation adjudicates disagreements only. Claim
labels are exactly:

- `SUPPORTED_BY_VISIBLE_EVIDENCE`
- `CONTRADICTED_BY_VISIBLE_EVIDENCE`
- `INSUFFICIENT_VISIBLE_EVIDENCE`
- `PHYSICALLY_TRUE_BUT_UNSUPPORTED`
- `UNINTERPRETABLE`

Separate fields record required diagnostic-unit coverage, false-premise handling, highest asserted
abstraction level, and limitation preservation. Agent annotators are blinded to method identity and,
as far as the task permits, intervention identity. Disagreements are adjudicated before method keys
are joined. Agreement measures repeated-agent consistency, not method effectiveness or accuracy.

Agent labels may be primary only after a prospectively frozen, bounded qualification validates the
exact five-way support taxonomy and abstraction/limitation task on fresh held-out cases. The existing
Luna v12 qualification does not automatically satisfy that new construct. Until exact-task
qualification passes, these labels are development evidence or secondary sensitivity analyses;
deterministically checkable quantities and endpoint operations remain code-scored. All such results
are described as **agent-assessed** or **automated annotation**, never human annotation or human
validation. Same-model correlated error and conclusion-reversal sensitivity must be disclosed.

## Statistical plan boundary

The independent unit is an episode/configuration. The primary B2/B4 comparison will report paired
failure counts, both discordant-pair counts, absolute paired risk difference with interval, and an
exact McNemar test when its assumptions match the frozen design. Power planning is driven by
independent discordant episodes, not response count.

Nested conditions will use a predeclared episode-clustered model such as a mixed-effects logistic
regression with Method, EvidenceLevel, their interaction, and episode random intercept. A
cluster-robust alternative will be frozen before confirmation if the mixed model is unstable.
Cluster-bootstrap intervals resample whole episodes.

Prospective simulation must span plausible development-only ranges for B2/B4 error, both discordant
probabilities, within-episode dependence, family prevalence, and invalid-episode rate. The legacy 33
episodes do not count toward the new target. Existing alpha allocations are not silently reset;
`candidate-v1-confirmation` already consumed 0.02, while 0.01 candidate-revision and 0.02 replication
allocations remain governed by the existing ledger pending an explicit prospective decision.

The current development population candidate uses fixed total weights of 0.35 persistent
discrepancy, 0.35 measured recovery, 0.15 missing-odometry control, and 0.15 nominal false-premise
control. The primary comparison conditions on the first two strata and weights them equally;
controls are separately reported and cannot rescue the primary test. Geometry is a non-pooled
secondary arm. The candidate stopping rule has one terminal semantic look, with only technical
monitoring beforehand. Exact sample size and any futility rule remain unset until valid development
discordance is available, so none of these development values authorizes confirmation.

## Governance and stop rules

Before P11, all work is development/calibration. Confirmation output generation is prohibited until
the repository contains validated contracts, masks, references, methods, parity exports, annotation
packets, clustered analysis, prospective power, leakage tests, and an explicit freeze binding the
endpoint, coverage floor, thresholds, evidence ladders, population, family weights, model settings,
analysis, alpha, stopping rule, and replication plan.

Model-backed development and qualification jobs execute from a normal network-enabled host using
the unchanged repository and immutable caches. The managed Codex shell disables outbound sockets;
its failed lookups do not justify DNS, credential, provider, prompt, or cache changes. Host jobs are
admitted only after `analysis/audit_b2_transport_readiness.py` reports
`READY_FOR_SCHEMA_CANARY` and a non-study schema canary passes.

After P11:

- no tuning uses confirmatory outputs;
- no poor answer is retried;
- no invalid or unfavorable episode is silently dropped or replaced;
- technical failure follows the frozen disposition;
- all conditions from an episode remain one cluster;
- method identities are joined only after blind annotation and adjudication; and
- the frozen confirmatory analysis is executed once at declared releases.

Negative confirmation is a valid result. The project stops expanding breadth once information
parity, valid masks/references/contracts, stable annotation, a frozen endpoint and coverage floor,
episode-level power justification, and leakage/reproducibility tests are in place.

## Claim-to-evidence migration

| Prior framing | Preserved evidence | New permissible role | Prohibited inference |
| --- | --- | --- | --- |
| Checked P should outperform strong R at diagnosis | Strong agents often matched the central diagnosis; P often used deterministic fallback | Motivation for testing calibration rather than raw reasoning superiority | Do not claim those negative results establish B4 calibration |
| Complete supported diagnostic communication | 56 inspected pairs expose omissions, judge disagreement, and packet-closure failures | Development cases for contracts, annotation, masks, and threat tests | Do not recycle them as fresh confirmation |
| Provenance/source grounding | Immutable 33-episode F/G/H cohort and prior provenance pipeline | Legacy section: why provenance is useful but insufficient | Provenance does not independently prove a physical mechanism |
| Causal restraint | Detector’s apparent R events disappeared under contextual audit | Regression examples for negation, non-entailment, and clause-level verification | Do not call negated causal claims substantive R errors |
| RoboBoat external validity | Bounded physical and semantic development artifacts | Optional later external-validity application of a frozen land method | No wave-drift, hardware-transfer, or pooled land/boat claim |

## Literature position

Atomic source attribution, risk–coverage analysis, abstention, evidence removal, contrast sets,
robot failure explanation, provenance-to-language planning, ROS/Nav2 RAG, hallucination grading,
accountable recording, and multimodal robot context all have prior art. The scoped contribution is
their robot-specific combination: a controlled, same-episode nested evidence ladder with separate
evaluator truth and visible-evidence support, typed claim requirements, maximal supported diagnosis,
and episode-clustered risk/coverage evaluation.

This is a review-scoped gap, not a priority claim. The primary-source audit is
`docs/research/EVIDENCE_CALIBRATED_EXPLANATION_FOUNDATIONS.md`; detailed robot-domain positioning
remains in the Fernández-Becerra and diagnosis-language research notes.

## Manuscript claim boundary

The preferred title is **How Specific Should a Robot Explanation Be? Evidence-Calibrated Failure
Diagnosis under Partial Observability**.

The paper may claim only what frozen results establish. It will not claim improved human trust,
hardware transfer, model-internal faithfulness, unique physical causes, universal root-cause
analysis, or statistical superiority without valid endpoint evidence. The intended takeaway is:

> Trustworthy robot explanations should not merely be correct when enough information is
> available. Their causal specificity should track what the robot can justify from its evidence,
> and controlled evidence interventions make that property measurable and auditable.

## Required sequence from this checkpoint

1. P2–P10 development implementations are present and pass the focused 76-test stack. They remain
   unfrozen and provide no confirmatory evidence.
2. Run one bounded fresh development pilot with actual B2 and B4 outputs, then complete two
   isolated blinded agent annotations and disagreement-only agent adjudication as a measurement dry
   run. Qualify the exact atomic-support task on fresh held-out cases before primary use.
3. Audit the existing error-budget ledger and use development evidence only to justify the
   coverage floor, minimum practical effect, sample size, family proportions, ladders, model and
   prompt configurations, stopping rule, and replication selection rule.
4. P11: freeze the scientific and semantic protocol once; do not freeze around hypothetical power
   values or old inspected method outputs.
5. P12–P15: only then generate confirmation, annotate/adjudicate blindly, join identities once,
   analyze, and generate manuscript tables/figures from machine-readable results.
