# Replacement handoff: marine temporal-evidence transfer case

## New goal and scope

The user requests a paper-focused replacement for the current `roboboat-terminal-evidence` goal. Prioritize a completed, compact marine application of the **same evidence-calibration principle** used in the land/HEXAR paper. Stop expanding the marine platform, fresh populations, qualification chains and independent superiority campaign for this submission.

Deliver a reproducible descriptive result using existing recordings: **what can an explanation legitimately say about task completion when software status, sampled physical behavior, temporal coverage, and unobserved conditions differ?** This is a temporal-observability transfer case. It is not a new navigation/control paper or an attempt to obtain marine significance.

Read the companion [positioning research](MARINE_PAPER_POSITIONING_RESEARCH_2026-10-01.md) and primary branch sources before editing claims. Last reviewed branch tip: `123a7c39`; inspect newer committed checkpoints first. Current snapshots can advance; use explicit hashes and a recorded reporting cutoff.

## Why marine belongs in the core paper

Land/HEXAR ask whether a claim is justified by the evidence actually available. Marine applies that same question to **time-qualified physical completion**:

- navigation action success supports a software outcome;
- a pose/velocity sample supports bounded observations at its time;
- a trajectory may supply a violation witness or sampled interval evidence;
- incomplete observation or missing contact coverage can leave full completion unknown.

This extends the central claim without adding another unrelated domain objective. Marine matters because post-result motion makes the distinction concrete. Pose and speed alone cannot identify waves, current, wind, actuator defects, or another unique cause.

Use a subsection such as **“Temporal evidence in simulated surface navigation.”** Claim implementation-level portability and a tested evidence-boundary example. Do not claim zero-shot cross-domain transfer: adapters, public task contracts, clocks, thresholds, and marine-specific computations are part of the implementation.

Document which core interfaces/algorithms are actually reused and which are marine adapters or revised source versions. Pin their identities. If only the evidence-contract principle is shared, say “application of the same principle” rather than implying byte-identical unchanged method transfer. The significance to robotics is the distinction between an autonomy module's terminal predicate and the user's task-completion predicate, not simply that a boat was added. A mismatch with a stricter separate contract is not a navigation-stack bug.

## Immediate campaign handling

Inventory only this branch's owned live collectors/queued jobs. Do not affect land, HEXAR, shared services or unrelated workers. This replacement goal supersedes instructions to complete additional large marine populations or reach a confirmation freeze.

Stop scheduling new robot configurations or automatic successor cycles. Preserve current in-flight captures to a clean terminal where feasible, then perform owned-process cleanup. Record the administrative stopping time/reason and the full original scheduled denominator, distinguishing completed, invalid, unattempted, and interrupted attempts. Do not wait for hundreds of queued cases merely to satisfy an old expansion objective.

Check queued jobs whose guard waits for the original full batch: preserve their manifests and explicitly cancel/defer them instead of fabricating predecessor completion or leaving permanent waits. Do not hot-patch live sources, salvage rejected captures, or retry old failures. No new hardware runs, simulator/controller changes, confirmation activation, alpha allocation, or protected replication use is needed.

An existing raw record with incomplete temporal coverage can still be useful evidence of **unknown**, if its retained observations and identity are sound. Do not equate incomplete task evidence with a technically invalid recording, and do not infer task failure from fixture timeout alone.

## Existing evidence to use first

1. **Closed early development bank:** `RESULTS.md`, `MANUSCRIPT_SECTION.md`, `CONTACT_V2_RESULTS.md` and the isolated contact-comparison capsule. These contain actual compared/scored answers, negative witnesses, sampled kinematic/hull compliance, unknown contact, and tied useful-content results.
2. **Completed fixed development collection:** `artifacts/roboboat-clock-repaired-development-v12-001/profile-v23.json` and `completed-development-summary-v22.json`, documented as 48 attempts/46 admitted recordings/22 complete physical geometry pairs. Verify current bytes and scope. These are a closed denominator useful for descriptive measurement.
3. **Recent diversity collection:** the last reviewed campaign note has 51 admitted recordings/23 physical pairs; its 37-record fair snapshot has 111 deterministic outputs including timeout-scope examples. These have internal mechanical checks, not independent support or B2 comparison scores. Treat them accordingly.
4. **Temporal coverage audit:** `POST_RESULT_SIMULATION_COVERAGE_V28.md` reports cases with only 0.30/0.58 simulator seconds after roughly eight wall seconds. This is an observation-window limitation, not proof of physical disturbance or failure.
5. **Fixture-timeout distinction:** `CLEAN_TIMEOUT_RETENTION_AND_EXPANDED_INPUTS_V32.md` documents retained timeouts with no terminal action result. Preserve “fixture deadline reached; action result unobserved,” rather than inventing cancellation, action abort or failed docking.

The closed 46-record summary reports **46 navigation successes**, **23 L2 task states false and 23 unknown**, with contact unknown in all 46. Independently reproduce the temporal/physical categories before putting them in the paper. This can make a concise empirical table about the difference between software status and the separately declared sustained task requirement. It is **not** a 50% navigation-error rate, a baseline explanation-error rate, or population prevalence. A correct navigation-success flag need not satisfy a stricter separately declared task contract.

Do not sum these inventories: they contain reused outputs, repeated variants, overlapping recordings, different source versions and zero-independent-N operational replays. Keep older settled semantic comparisons separate from newer mechanical-only outputs.

## Minimum analysis

Create an episode/geometry-keyed inventory and fixed eligible cohort **before analyzing aggregate findings**. Prefer one closed collection with consistent build/task semantics as the main descriptive cohort. Other versioned banks are supplementary examples; do not pool incompatible observations to enlarge N.

For every retained eligible record in that cohort, reconstruct from authentic raw evidence:

- reported action status and actual result-receipt presence/identity;
- exact declared task interval and its anchor;
- delivered simulator/header time range, sample count and maximum gap;
- position, wrapped heading, measured translational velocity and yaw rate, with units/frames;
- hull and contact evidence availability;
- first supported within-interval violation and its signed margin, where one exists;
- sampled satisfaction of observed components, separately from full-task support;
- missing conditions, incomplete interval coverage, and unknown terminal outcome.

Use independent raw numerical/temporal recomputation, rather than treating production certificate acceptance or answer text as gold. Reuse already independently verified quantities where applicable; a small separate deterministic check is enough if it verifies the actual relevant facts. Do not build a new general runtime-verification platform.

Apply the following logic consistently:

| Available evidence | Supported completion statement |
|---|---|
| Valid software success alone | Navigation reported success; sustained physical completion unestablished |
| An authenticated violation of a required condition inside the valid declared interval | The specified interval requirement was violated; identify the witness and keep cause unknown |
| Complete sampled kinematic/hull compliance, but contact evidence absent | Observed components satisfy sampled checks; full completion remains unknown |
| Incomplete interval with no observed violation | Completion unestablished; no violation observed in the available portion |
| Fixture timeout, no recorded action result | Fixture deadline reached; terminal software/task outcome unobserved |

An observed violation can refute a conjunctive interval requirement even if other components are unobserved. Claiming satisfaction requires coverage of every required component; sampled satisfaction is still not continuous-time proof without justified intersample bounds. A later violation outside the fixed dwell does not falsify compliance within that dwell. Do not move the anchor or extend the task interval after observing crossings.

Retain every technically eligible outcome, including incomplete windows and sampled compliance. Do not select only success/violation mismatches as the aggregate population. Any selected illustration is explicitly illustrative, chosen by a documented evidence category, not a representative-frequency claim.

## Paper artifacts

Produce **one compact figure** with two linked parts:

1. A time plot for an existing audited example: actual observed result marker or honestly labeled first post-result observation; shaded declared dwell; measured position/speed or another decisive condition; requirement line; violation/coverage witness. Show data only where observed. State simulation and measurement scope.
2. A three-level evidence ladder for the same record: L0 software status → L1 adjacent measurement → L2 interval trajectory. Show the allowed statement at each level and the withheld stronger claim. Do not simulate three different physical outcomes by rewriting evidence.

Add **one compact descriptive table** giving attempted/admitted/observed-result/full-window counts and categories of observed violation, sampled observed-component satisfaction, and unresolved full completion. These categories can overlap; either make a mutually exclusive outcome partition or label marginal counts and intersections explicitly. Deduplicate geometry variants/replays when describing independent diversity. No p-value or superiority claim is required.

If a second example adds essential information, use the existing known-route settling case: 251 sampled kinematic/hull-compliant observations over the fixed five-second dwell with contact unknown, followed by a position crossing outside that dwell. Keep its different provenance/version and illustrative selection explicit. Do not use an out-of-dwell endpoint as the in-dwell failure witness.

Reuse existing figures such as the settling terminal panel when their scope is accurate. Prefer a legible integration figure over a six-panel platform-performance collage. Include original packet/ref/certificate hashes and one reproduction command.

## Comparative claims and evaluation

Use the already closed B2/B4 development comparisons to disclose that useful outcome coverage was tied and baseline supplemental detail can be greater. Do not require new marine baseline/judge calls to complete this transfer-case subsection. Do not turn strict-score differences from public-contract ambiguity or a 0.000145 m timing discrepancy into effectiveness claims.

Newer internally audited deterministic answers can illustrate contract execution, but their engineering checks do not establish independent language correctness. If semantic validation is needed, have an available independent reviewer assess the small fixed illustration set against raw evidence; otherwise identify the check as numerical/contract conformance and state that independent semantic validation is absent. Do not launch large extraction/judging qualification programs for this deadline.

Any optional additional response comparison is exploratory, fixed before its new scores, with fair inputs and full retained denominator. It is secondary and cannot hold this handoff's deliverables hostage. No altered baseline, outcome-selected sample, borrowed alpha, or pooled land/marine significance.

## Manuscript integration and boundaries

Deliver approximately **350–500 words**, one figure and one small table for the main paper; detailed capture/controller/source engineering belongs in the supplement. If page space is tight, retain the concept and figure and move aggregate table/details to the supplement.

Suggested opening:

> We apply the same evidence-contract principle to simulated surface navigation, where navigation-software success and interval-qualified physical task completion are distinct propositions. Removal-only evidence conditions distinguish reported status, instantaneous measurements, and sampled post-result behavior, while preserving unknown conditions rather than upgrading them into successful docking.

Connect directly to the main benchmark's truth-versus-support distinction. Cite first-party goal-checker semantics and marine motion models for context, and existing explainable-docking work for positioning. Do not claim first maritime explanation, a novel controller, a validated disturbance model, a newly invented temporal logic, or hardware transfer.

Separate three levels of evidence: tested portability of implementation; descriptive behavior of retained simulator records; and comparative effectiveness. This subsection can establish the first two. The third is not established by the recent raw collection or mechanical answer audits.

## Done criteria

- One pinned, auditable reporting cohort with complete administrative/technical flow and overlap accounting.
- Independently checked numbers and temporal scopes for the reported observations.
- One compact evidence-ladder/timeline figure, one truthful descriptive table, and reproduction manifest/command.
- Integration-ready subsection and short related-work/limitations paragraph; existing tied comparisons preserved.
- A terminal branch status saying this **paper-integration goal is complete**, with unfinished confirmation/platform work explicitly deferred.

Return the artifacts and exact limitations. Success is a coherent, reproducible application of the core claim to temporal evidence in a different embodiment—not a favorable method difference or completion of the old expanding campaign. Do not push, merge, publish, or modify other branches unless separately instructed.
