# Diagnostic sequential-campaign progress

Updated: 2026-09-24

Protocol: `diagnostic-sequential-protocol-v2`
Current status: **NO ACTIVE CONFIRMATORY CAMPAIGN**

## Readiness

| Gate | Status | Evidence / next action |
|---|---|---|
| Candidate P frozen | NOT_READY / V3 PILOT ACTIVE | Candidate v3 run 001 is a valid tie; complete the remaining fixed development runs and mask before applying the readiness gate |
| Strongest baseline R frozen | DESIGNATED, NOT_HASH_FROZEN | Tool-enabled repository-aware R; freeze exact model/prompts/resources with candidate |
| Information/tool/resource parity | DRAFT | Audit at campaign freeze |
| Target land strata | DEVELOPMENT_NAMESPACE_QUALIFIED | V5 build/binding smoke passed; live ROS candidate cases and future confirmatory/replication reservation remain required |
| Target surface strata | NOT_READY | Both geometric and command--motion admission required; do not reallocate weight |
| Luna historical qualification | V4 HIGH FAILED / PRESERVED | Both fresh passes failed; never retroactively qualified |
| Luna v5 endpoint qualification | FAILED / PRESERVED | P1 passed; P2 missed core by one field and one protected subcheck |
| Luna v6 endpoint qualification | FAILED / PRESERVED | P1 false rejection 3/17 exceeded 15%; P2 passed every gate |
| Luna v7 reference-audited qualification | QUALIFIED | Both passes: 20/20 composite, 32/32 units, zero observed FR/FA, all protected gates |
| V7 amendment/sensitivity enforcement | IMPLEMENTED, TESTED | Nonempty v2 results must bind exact v7 hashes and clear nominal plus adverse sensitivity gates |
| Replication configurations reserved | NOT_RUN | Reserve before discovery collection |
| Sequential null simulation | PASS_QA | 20,000 replicates per endpoint; all boundary estimates below component alpha 0.02 |
| Alternative budget sensitivity | COMPLETE | +0.30 scenarios reach 0.9946/0.9366 joint success by 1,600; this is not observed power |

## Program error-budget ledger

| Allocation | Alpha | Status | Campaign |
|---|---:|---|---|
| `candidate-v1-confirmation` | 0.020 | AVAILABLE | none |
| `candidate-revision-reserve` | 0.010 | AVAILABLE | none |
| `selected-method-replication` | 0.020 | AVAILABLE | none |

Consumed alpha: **0.000 / 0.050**. An allocation becomes consumed when its first confirmatory
response is inspected, not when a favorable result appears. Machine-readable state is retained in
`manifests/study/diagnostic-sequential-error-ledger-v2.json`; before the first response is opened,
the chosen allocation must be atomically bound to that campaign and cannot later be refunded.

## Cumulative evidence

| Quantity | Current value |
|---|---:|
| New independent confirmatory clusters | 0 |
| Diagnosable confirmatory clusters | 0 |
| Ambiguous confirmatory clusters | 0 |
| Discovery configurations reused in replication | 0 |
| Luna confirmatory judgments | 0 |
| Unresolved confirmatory labels | 0 |

No effect estimate, confidence sequence, guardrail result, or replication conclusion exists.
Legacy and the eleven diagnostic-development clusters are intentionally absent from these counts.

## Candidate-v3 development readiness pilot

The prospectively declared six-configuration candidate-v3 pilot is in progress. Run
`cmv3-dev-001` was attempted once and governed as one valid independent development cluster. The
exact player and scenario binding passed, Unity recorded zero errors/exceptions, and the independent
reference matched the checked diagnostic before any model call. Both P and R passed the supported-
diagnostic-success endpoint without material error in both isolated Luna-v7 passes, so cumulative
P-minus-R was 0 in each pass for the unmasked run. This tie is retained and does not alter the fixed
run order or stopping rule.

The paired no-odometry mask is now governed as the required valid ambiguous variant and adds zero
independent clusters. P fully covered the supported partial answer and correctly withheld a
discrepancy conclusion in both passes; R was partial and failed the composite endpoint in both.
Run `cmv3-dev-002` is also governed as one valid transient-compensation cluster. P passed both Luna
passes; R failed both after citing ephemeral local paths and omitting required information. Current
v3 readiness state: 2/6 valid independent clusters, 1/1 valid ambiguous variants, cumulative
P-minus-R +2 in each pass, zero P material errors, and no P coverage degradation. Although the
numerical advantage threshold is currently met, the predeclared pilot must continue through every
fixed run and requires at least four valid independent clusters before any readiness decision.
At that checkpoint confirmation remained inactive at `0.000/0.050`, and the sole attempt of
`cmv3-dev-003` proceeded without replacement based on outcome.

Run `cmv3-dev-003` is now governed as a valid nominal false-premise cluster. The computation did
not trigger, although the successful action retained three FollowPath attempts, two failures, and
two qualified Wait invocations. P passed and R failed the primary endpoint in both Luna passes;
both were partial under a generic next-check reference that does not match P's non-triggered
diagnostic recommendation. The mismatch is retained and counts as a P coverage omission, but not a
relative coverage degradation because R is also partial. Current state: 3/6 valid independent
clusters, 1/1 valid ambiguous variants, cumulative P-minus-R +3 in each pass, and zero P material
errors. The pilot remains pending; `cmv3-dev-004` is next and alpha remains `0.000/0.050`.

Run `cmv3-dev-004` is governed as a valid persistent-discrepancy tie: P and R passed both Luna
passes with full coverage and no material error. Current state is 4/6 valid independent clusters,
1/1 ambiguous variants, cumulative P-minus-R +3 in each pass, and zero P material errors. The
minimum numerical gates are provisionally satisfied, but the fixed pilot cannot stop early;
`cmv3-dev-005` and `cmv3-dev-006` remain mandatory. Confirmation is inactive at `0.000/0.050`.

Run `cmv3-dev-005` is governed as a valid transient-compensation tie. Current state is 5/6 valid
clusters, 1/1 ambiguous variants, cumulative P-minus-R +3 in each pass, and zero P material errors.
The sole fixed `cmv3-dev-006` attempt remains mandatory before readiness classification.

Candidate v2 now has an executable development runner. P is the exact checked deterministic
diagnostic rendering with zero model calls; R gets the identical blind input, source, diagnostic
tool, and one high-reasoning model call. This accurately treats the proposed method as specialized
diagnosis plus deterministic natural-language rendering instead of attributing repeated fallback
text to successful LLM reasoning. It remains unfrozen and has produced no new response or label.

The candidate-v2 annotation path now requires a complete-reference audit before packet creation.
The independent computation retains comparator/discrepancy/recovery intervals, thresholds,
provenance semantics, action/sequence fields, and recovery-classifier derivation; it is checked
against the v3 diagnostic and source IDs without exposing P's answer plan. This addresses the
specific omission that invalidated the composition packet, but each fresh reference still must
pass the audit before any Luna call.

A six-cluster candidate-v2 development pilot is now prospectively declared but not run. Its fixed
mixture has two persistent, two compensated, and two nominal configurations plus one clustered
missing-odometry variant. The screen requires a two-net-success P advantage in each Luna pass with
zero P material errors and no coverage/ambiguity regression. It cannot consume alpha or establish
significance; its only role is deciding whether candidate v2 is credible enough to freeze.

## Fresh candidate-development capacity (2026-09-24)

CRANE commit `7cafab0` adds the separate `crane-land-proving-ground-v5` catalog for candidate-v2
development only. It contains 12 connected-detour and 12 nominal-clear-route geometries with IDs
and generator seeds disjoint from the unchanged v4 inventory. Its catalog SHA-256 is
`dd693444df842a97570bbf65e1cd07737bead48314acbf54d5a1c4c0b8f093d6`; deterministic
regeneration and 35 focused generator/runtime-contract tests pass. The sealed v4 bytes remain at
SHA-256 `c2603491c16b99ba007085237097fc0cd66ee2453d1b9e4e1fc7f490bd1a0f8a`.

This removes the immediate namespace-capacity blocker for a bounded fresh development pilot, but
it supplies no episode, response, Luna label, effect estimate, or alpha consumption. Each layout
can contribute at most one independent development cluster; intervention/control variants,
evidence masks, and reruns remain clustered. V5 identities are permanently ineligible for
confirmation or replication.

The clean-source v5 infrastructure smoke subsequently passed under CRANE `8d1d308`: the player
proved its exact source commit and embedded catalog, the three-second headless run had zero logged
errors/exceptions and 15 LiDAR scans, and all 14 scenario-binding checks passed. Layout
`diagnostic-candidate-v2-development-nominal-clear-route-001` is now calibration-only and excluded
from candidate-effect work, leaving 23 potential development layouts. No ROS/Nav2 episode was run.
The compact audit is `manifests/checkpoints/diagnostic-v5-development-smoke-v1.json`; large Unity
players remain ephemeral. The next gate is a prospectively declared, small candidate-v2 pilot.

The fresh land-binding qualification `diagnostic-land-binding-dev-006` was rejected and retained:
the selected Unity bundle instantiated legacy clear-corridor truth rather than the declared v4
layout. It adds zero qualified clusters. Actual land captures now require prospectively pinned
build-manifest and managed-assembly hashes plus a pre-launch source/scene compatibility audit; the
audit also requires the exact selected catalog payload in Unity runtime resources. The post-run
exact scenario-binding audit remains required. No replacement run is currently declared.

## Qualified-judge development result (2026-09-24)

The six clusters selected before annotation supplied 24 immutable R/P/T/N responses. Two isolated
qualified-Luna passes produced P-versus-R mechanism-success differences of +0.20 (1/5 versus 0/5)
and 0.00 (0/5 versus 0/5), with two primary endpoint disagreements. This is development-only and
provides no interval or significance claim.

Audit showed an information-completeness defect: P's deterministic fallback usually communicated
the supported mechanism and required units but cited governed hashes absent from the blinded judge
packet. Luna treated those source links as unsupported. R also made wrong deadlines, intervals,
source details, and causal links. Do not freeze current P. Preserve these outputs and create fresh
development responses only after citation identities are either exposed equally to P, R, and judge
or omitted from final language.

The v1 framework was retired unused after pre-outcome feasibility checks. No v1 or v2 allocation
was consumed. The v2 fixed-fraction e-process and intersection--union decision rule are documented
in `docs/SEQUENTIAL_STUDY_PROTOCOL.md`; retained simulation is planning evidence only.

## Citation-complete command--motion development result (2026-09-24)

The citation-contract repair was exercised prospectively on four fresh R/P/T/N answers for the
existing compensated command--motion cluster. All governed identifiers cited by P/T were exposed
to the blinded judge. Pass 1 scored P/R/T successful and N unsuccessful; pass 2 scored only P
successful. R's pass-2 failure identified a genuine temporal-scope invention (“earlier healthy
odometry”) from a calibrated healthy-response value. T's pass-2 failure concerned
“independently delivered odometry,” which pass 1 accepted and the packet did not explicitly define
as independent from the command stream.

This result adds zero independent clusters, consumes no alpha, and cannot select or freeze a
candidate. P also reached its final answer by deterministic fallback, so it is not evidence that
model realization outperformed T. The next bounded development step is fresh configurations across
multiple scenario families that prospectively avoid invented measurement scope and undeclared
source relationships. Existing labels remain immutable and are not rerun.

## Language-v4 multi-family physical result (2026-09-24)

All four prospectively fixed physical configurations were run once and retained as two development
clusters. The command--motion pair qualified as intended: the persistent case supports a sustained
discrepancy followed by two recovery invocations and abort, while the compensated case supports the
same discrepancy followed by measured recovery and success. Both use prospective diagnostic
contract v3 and passed independent numeric/reference parity.

The requested land detour did not occur: both runs succeeded with zero lateral deviation. A later
evaluator-truth audit established that neither requested v4 layout was bound; both used the legacy
clear-corridor truth schema. The recordings and false-premise outputs remain preserved, but the
pair contributes zero scenario-binding-qualified clusters and no route-change evidence. No
candidate is frozen and alpha remains unconsumed.

## Language-v4 multi-family Luna result (2026-09-24)

All 32 predeclared qualified-Luna measurements completed without retries or failures. Across the
two diagnosable command--motion configurations, pass 1 tied P and R at 1/2; pass 2 scored P 2/2 and
R 0/2. Those two configurations belong to one development cluster, so neither pass is an
independent-cluster estimate. Persistent P/R labels reversed by pass. Compensated P was
deterministic fallback and byte-identical to T, yet pass 1 accepted P and rejected T.

The post-run packet audit found that compact allowed evidence omitted the retained command-source
provenance and an explicit attempt-status relationship, producing packet-sensitive source and
failure-chain judgments. The immutable labels remain useful evidence of automated-judge and packet
instability, but they do not justify freezing P or opening confirmation. The no-computation N arm
failed both diagnosable cases in both passes, indicating development value in the diagnostic
computation without establishing a statistically independent method advantage.

The land pair is additionally invalid for its intended catalog comparison: retrospective truth
validation found legacy clear-corridor runs rather than the requested v4 detour/nominal layouts.
This is now a fail-closed admission error, not merely a negative fault induction.

## Full-bundle land qualification result (2026-09-24)

One different fresh development layout, `diagnostic-development-connected-detour-007`, passed both
the new prelaunch full-bundle/catalog gate and exact post-run evaluator-truth binding. NavigateToPose
succeeded; 74 independently recomputed delivered plans changed from an initially direct plan to
non-direct geometry spanning -1.407 m to +1.231 m, and delivered odometry reached 1.301 m lateral
deviation. This is one qualified development physical episode and adds no confirmatory cluster,
model comparison, Luna judgment, or alpha expenditure.

The final rolling costmap did not cover the complete requested route. The supported mechanism is
therefore a recorded plan change with unresolved physical trigger—not obstacle causation. Future
language use requires a separate prospective declaration and equal evidence/tool access for P and
tool-enabled R.

## Qualified route-change language result (2026-09-24)

The prospectively declared one-cluster language gate completed with one R/P/N call and deterministic
T. Tool-enabled R gave a useful, causally restrained route-change answer. Raw P did as well, but
bounded verifier v4 rejected “then success” in its Failure chain because that wording was outside
the policy's literal success phrases, so final P fell back to T. N also extracted substantial
route-change evidence from the supplied plan summaries without decoded geometric computation.

No semantic labels were generated, so this is not a P--R endpoint result. It adds no confirmatory
cluster and consumes no alpha. The result weakens the case for freezing the current candidate:
R is already strong on this qualified episode, final P is deterministic, and the verifier has a
prospective robustness defect. Do not retry or rescore this output. A future verifier repair must
be versioned and tested beyond this phrase; candidate selection still requires independent
physical clusters and a separately registered blinded evaluation.

## Required update for each collection batch

Record, without deleting earlier rows:

- campaign/candidate/freeze hashes and alpha allocation;
- independent cluster counts by frozen target stratum;
- valid recordings, invalid recordings, exclusions, and predeclared reasons;
- P/R paired estimates and corrected anytime lower/upper bounds;
- primary, material-error, coverage, and ambiguity gate status;
- Luna model/settings, held-out qualification, pass agreement, unresolved fields, and sensitivity;
- deterministic measurement/reference checks;
- model/tool calls, tokens, latency, compute, and cost where available;
- stopping/futility state and the next collection or separate development action.

## Next action

Do not start confirmation from the v4 language batch or the one-cluster route-change result. Luna
v7 no longer blocks prospective annotation, but P/R method/resource hashes, admitted fresh target
generators, surface mechanism strata, and replication reservations remain unfrozen. Prioritize a
deeper physical diagnostic and genuinely independent qualified configurations over further wording
iteration. No confirmatory campaign is active and no alpha has been consumed.

## Held-out judge result (2026-09-24)

The selected v2-medium configuration was run exactly once over 14 untouched cases in each of two
isolated passes. Pass 1: 15/17 required-unit statuses, 97/107 core fields, zero false acceptances,
three false rejections, zero unresolved, correct 2/2 answerability boundaries and 1/1 injection
case, but failed material-error presentation invariance. Pass 2: 17/17 units, 98/107 core fields,
zero false acceptances, two false rejections, zero unresolved, and passed boundary, injection, and
presentation-invariance gates. Both failed the small-category zero-false-rejection rule, especially
for diagnostic omission. There were 28 valid calls, no retries, no call failures, and no exposed
tools. This consumes no confirmatory alpha and creates no study labels or effect estimate.

## Invalid composition attempt (2026-09-24)

The single prospectively declared `diagnostic-land-composition-dev-008` attempt is retained but
inadmissible. Full-bundle preflight passed; Unity then rejected the proving-ground layout combined
with the legacy mobility-hold intervention before scenario construction. There is no exact scenario
truth, no binding audit, no hold marker, and no terminal action/BT result. The subsequent timeout,
zero odometric displacement, commands, and recovery activity cannot be interpreted as a physical
diagnostic case.

No diagnostic exports, references, answers, or Luna calls were created. The run adds zero qualified
clusters and consumes no alpha. It will not be retried or replaced. Candidate P remains
`NOT_READY`; the next engineering change is only a fail-closed prelaunch rejection for this known
incompatible argument combination, after which paper-value work should return to independent valid
mechanisms, annotation, analysis, and manuscript preparation rather than another layout search.

## Qualified route-change semantic result (2026-09-24)

An information-complete blinded packet for scenario-binding-qualified run 007 was scored exactly
twice under frozen Luna v7. Both passes marked P, tool-enabled R, and deterministic T successful;
both marked N unsuccessful. P minus R is 0.0 in each pass. The systematic absent-citation problem
from the earlier selected cohort did not recur, so this is a substantive single-mechanism tie.

P and T are byte-identical. Their primary endpoint agreed, but pass 2 called P partial and T full,
showing secondary disposition instability even under identical inputs. No third vote is permitted.
The result adds zero confirmatory clusters and consumes no alpha. Together with the invalid
composition attempt, it leaves current P `NOT_READY`: the project should not expand easy
route-change collection and should require genuinely deeper composition or a separately developed
method change before freezing a confirmation candidate.

## Scenario-bound composition infrastructure (2026-09-24)

CRANE `3ebba7b` now supports a separately authenticated proving-ground execution intervention.
Legacy corridor intervention flags remain rejected, the no-intervention configuration identity is
unchanged, and active hold/release boundaries extend the proving-ground configuration hash and
evaluator truth. The umbrella binding audit rejects undeclared or mismatched boundaries.

A non-study, ROS-disabled headless smoke test compiled and exercised this seam successfully. It
adds zero physical clusters, responses, labels, or alpha. The intended next development case uses
a fresh nominal-clear-route configuration so geometry can act as a competing negative mechanism
while command/odometry evidence tests an execution restriction. This is higher value than another
easy route-change variant, but it cannot freeze P unless the actual retained evidence supports a
compositional contract and a later fair P/R development comparison warrants a fresh candidate.

## Authenticated composition attempt outcome (2026-09-24)

The one declared run 009 attempt passed clean-player and exact scenario-binding admission, and the
evaluator-only persistent execution restriction activated at its declared boundary. The retained
robot-visible record is a useful bounded observation of commands, odometry, plans, costmaps, and
recovery activity, but NavigateToPose remained active when the 100-second observation window ended.
There is no terminal result or complete recovery history.

The run is therefore retained but is not a terminal-failure explanation cluster and is ineligible
for P/R/N generation or Luna scoring under its current declaration. It adds zero confirmatory
clusters and consumes no alpha. Do not retry or replace it. Current P remains `NOT_READY`; the
result favors closing this development branch and returning to qualified evidence, analysis, and
the manuscript rather than searching for another favorable physical case.

## Bounded nonterminal diagnosis from the retained attempt (2026-09-24)

A prospectively declared post-outcome analysis used the robot-visible 100-second boundary without
inventing an action result. Independent computations agree that the record supports a sustained
10--51 s command--motion discrepancy (0.260 m/s command, 0.000 m/s measured response, calibrated
healthy response 0.25974 m/s). Geometry remains insufficient because the final rolling grid does
not cover the complete requested route and the retained plans/trajectory show only small lateral
deviation. It cannot explain the discrepancy.

The first geometric rendering falsely called the cutoff a terminal result; it is retained as an
ineligible tool failure. The corrected version explicitly withholds the eventual action outcome.
This improves the candidate's bounded composition behavior but adds no physical cluster, response,
label, or alpha. A separately declared, fair P/R language test is the next development gate; it
must give R the same two computations and cannot ask a terminal-failure question.

## Bounded deterministic composition result (2026-09-24)

The prospectively declared deterministic composer passed its exact final-text check and a separate
predicate reference. It leads with the supported command--motion discrepancy, communicates the
decisive interval and speeds, retains the pre-cutoff FollowPath/Wait context, and explicitly keeps
geometry and the eventual action outcome unresolved. It makes no terminal, global-route,
obstacle-causation, evaluator-intervention, or unique-physical-cause claim.

This is a method-readiness increment, not comparative evidence: it adds no cluster, response,
Luna label, or alpha, and current P remains `NOT_READY`. A one-shot P/R/N development comparison
may be considered only under a new declaration that gives tool-enabled R the same robot-visible
evidence, both diagnostic computations, source/configuration, model strength, and resource budget.

## Bounded composition language result (2026-09-24)

The declared three calls completed once. Raw P communicated the supported mechanism and limits but
failed the literal language gate on formatting and meaning-preserving wording, so final P fell
back to T. Tool-enabled R independently recovered the same command--motion mechanism, decisive
speeds, nonterminal boundary, geometric insufficiency, and unique-cause restraint. N discussed the
retry/recovery sequence but omitted the supported command--motion mechanism.

These are execution observations, not Luna semantic labels. They make another P/R tie plausible
and do not justify freezing P. The result adds one inspected development language cluster, three
model calls, zero judge calls, and zero alpha. Further prompt/verifier tuning on this case is lower
value than a bounded blinded audit followed by a stop/redirect decision, independent collection,
analysis, figures, and manuscript work.

## Composition audit evidence problem and stop decision (2026-09-24)

The two Luna passes produced seven valid records and one invalid pass-2 N record. Raw primary
labels gave P=R=failure in both passes, but a mandatory reference audit found that the packet
omitted exact robot-visible provenance, interval, grid-size, and event-timing facts that Luna used
to reject P/T/R claims. The labels are therefore ineligible for method comparison: packet
incompleteness is not method error. No rejudging or third vote is authorized.

Current P remains `NOT_READY`, and the composition candidate path is closed rather than tuned on
this inspected case. There is still no demonstrated P-over-R advantage and no alpha use. The next
scientifically useful work is fresh independent configurations only if a materially improved
method is prospectively frozen; otherwise prioritize retained-data analysis, figures, and an
honest short/WIP manuscript.
