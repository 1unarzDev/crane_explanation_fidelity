# HEXAR EXTERNAL-VALIDATION HANDOFF
## Evidence Calibration for Modular Robot Navigation Explanations

Develop a focused external evaluation showing whether CRANE's existing
evidence-contract method improves evidence-calibrated explanations when added
to HEXAR.

This is supporting evidence for the main paper, not another simulator,
architecture-independence project, or general robot-debugging system.

Save this handoff under:
`docs/hexar_external/HANDOFF.md`

Seek a statistically supported benefit on one prospectively defined endpoint.
Accept and report tradeoffs. Do not manufacture a win by weakening HEXAR,
selecting only its known failures, changing scoring retrospectively, or giving
our method privileged evidence.

## 1. WORKSPACE, OWNERSHIP AND CURRENT CONTEXT

Work only in the assigned isolated checkout, preferably:
`/home/lunarz/worktrees/hexar-evidence-calibration`

Verify branches, worktree registration, submodule paths, revisions, and dirty
state. Do not edit the main research checkout or the RoboBoat worktree.

If nested repositories are not safely isolated, use an approved sibling clone.
Do not copy mutable Unity caches or force destructive Git operations.

You own:
- HEXAR source/data inventory and reproduction;
- read-only bag extraction/replay;
- the thin CRANE-to-HEXAR evidence adapter;
- the external evidence-sufficiency benchmark;
- scoped evaluation artifacts and manuscript material.

You do not own:
- active land or boat method versions;
- their freezes, source data or annotation bindings;
- the global inferential-budget ledger;
- simulator physics, scenes, robot models or navigation tuning;
- shared manuscript claims outside your assigned section.

Read current AGENTS.md, latest project checkpoint, evidence-calibration
architecture, annotation bindings, campaign protocols and statistical ledger.

The September 30 checkpoint centers on evidence calibration and B0-B4.
Older P/R and Luna instructions may be historical. Resolve actual current
bindings from manifests; do not silently select an old model or judge.

Import/reuse a pinned version of the main evidence-contract core. Do not fork
its semantics locally without recording and proposing the change.

Keep documents, caches, outputs and tests under hexar_external-specific paths.
Publish integration-ready commits; do not merge other active branches or
advance shared component pins without coordination.

## 2. PRIMARY RESEARCH QUESTION

Does adding explicit evidence contracts to a modular robot explainer improve
appropriately specific, supported navigation explanations under incomplete
execution evidence, beyond a sensible prompt-only calibration improvement?

The desired behavior:
- retain useful diagnoses when the supporting evidence exists;
- retain supported execution facts when the specific cause is unknown;
- stop asserting a cause when its evidential support is genuinely unavailable;
- remain stable when only irrelevant evidence is removed.

This is an extension to HEXAR, not a claim that HEXAR is generally ineffective.

Do not claim universal root-cause discovery, human trust, new hardware
experimentation, or measured geometry unavailable in the recordings.

## 3. SOURCE MATERIAL AND RECONNAISSANCE

Paper:
https://arxiv.org/abs/2601.03070
https://arxiv.org/html/2601.03070v1

Authors' code/data:
https://github.com/fgebelli/HEXAR

Primary files:
README.md
experiments.csv
detailed_results.csv
run_experiments.py
launch_explainability.launch.py
requirements.txt
bagfiles/*/metadata.yaml

Implementation entry points:
component_explain_navigation/component_explain_navigation/component_explainer_impl.py
skill_explain/skill_explain/skill_impl.py

Pin the actual repository commit, file hashes, dependencies and model artifact
identity. Do not rely on a moving model tag as complete provenance.

Inventory code and data licensing separately. Inspected package metadata declares
Apache-2.0, but do not assume that automatically resolves every dataset/asset
redistribution right. Preserve attribution and notices.

Inspect the navigation prompt, filtering, callbacks, task/time-window selection,
state initialization, derived diagnostic messages, and model invocation.

Test—not assume—the implications of symptom-to-cause examples, discarded logs,
state persistence and time-window handling.

HEXAR already supports an insufficient-information answer. Our hypothesis is
better evidence calibration, not merely adding an abstention sentence.

Do not redesign the selector or add multi-component aggregation. Those are
different research questions.

## 4. REPRODUCE BEFORE CLAIMING IMPROVEMENT

Recompute the original published metrics from the released annotation columns.
Keep original labels immutable.

Check:
- method names and actual row counts;
- pairing by testcase, execution and question;
- duplicates and missing outputs;
- majority-label aggregation;
- results by module and situation family;
- correspondence between metadata, recordings and answers.

Do not reinterpret their original labels using our stricter support rubric and
call the resulting number their published accuracy.

Keep three result categories explicit:
A. Recalculation of released historical results.
B. Fresh matched-model reproduction/adaptation.
C. Our new evidence-sufficiency extension.

Build a bounded faithful replay first.

Prefer an isolated ROS 2 Humble environment matching the release. If practical,
extract bags into deterministic event records and reproduce the component's
logic offline, but first verify input/state/prompt parity against native replay.

Record any compatibility patches. Do not copy broad privileged-container flags
without a demonstrated need.

If only the navigation component is executed, call it a component-level
comparison—not a full end-to-end HEXAR reproduction.

Preserve time ordering, task windows, state updates and relevant buffering.
Do not speed up replay in a way that silently changes those semantics.

Infrastructure fixes necessary for a fair comparison must be separated from
the evidence-calibration treatment.

If exact historical model artifacts are unavailable, say so. Run all fresh
conditions on the same pinned available model. Do not compare a newer flagship
model against historical phi4 outputs and attribute the difference to CRANE.

## 5. START WITH THE NAVIGATION SUBSET

Select the released navigation category before inspecting comparative failures.

Include its complete declared situation set:
obstacle, manual-control, charging, localization, dynamic-environment and
nominal-navigation cases, subject only to recorded technical eligibility.

Inventory actual bag content before defining questions or reference requirements.

The sampled navigation metadata contains logs, task state, override signals and
localization estimates. It does not establish that raw scans, paths or costmaps
are available. Do not invent missing measurements.

Use public scenario/gold fields only for evaluation and dataset accounting.
Never give methods testcase names, hidden interventions, ground-truth causes,
original answers, annotation labels or method performance.

Rename file/task handles opaquely where needed without changing meaningful
episode content. Public-data familiarity remains a limitation; do not claim
opaque filenames eliminate possible model memorization.

Record inspected development IDs. Split before further tuning. Keep all outputs,
questions and masks from one recording together.

A bag-level split supports new-recording evaluation within known families.
It does not establish transfer to unseen mechanisms unless whole families
are genuinely held out.

## 6. BUILD ONE REMOVAL-ONLY EVIDENCE EXTENSION

For each eligible recording/question, construct:
- intact permitted evidence;
- irrelevant-removal control;
- decisive-removal condition that retains useful execution information.

Apply transformations BEFORE deriving state, diagnostic summaries and prompts.
Start each transformed replay with clean state.

Do not run the full bag, preserve a remembered cause, and then mask only the
visible prompt.

Audit removal closure across:
- logs and task error strings;
- manual/charging state messages;
- derived diagnostic statements;
- cached explainer state;
- metadata and filenames;
- source/example context containing episode-specific answers;
- tool-visible files and alternate representations.

Missing evidence is not a false value. Do not replace missing joystick state
with false, missing covariance with zero, or absent error messages with success.

If retained evidence still establishes the cause, label the condition answerable.
Do not force abstention simply because the intended mask removed one source.

Leave the physical event unchanged. These are information-availability
interventions, not counterfactual robot trajectories.

Use the original navigation questions initially. Add at most a small fixed set
of evidence-specific questions if necessary. Do not require timestamps, long
lists or exact wording merely because our method emits them.

A concrete reference distinction:
- retained navigation failure: supports describing the recorded failure;
- retained relevant override evidence: may support a bounded override explanation;
- missing decisive override/obstacle evidence: does not license substituting
  a guessed physical cause.

Original full-evidence ground-truth labels are NOT gold answers for a reduced
packet. Construct packet-specific answerability/support references separately.

Regenerate HEXAR answers for every transformed input. Comparing an old
full-evidence answer with a newly masked packet is not a missing-evidence
experiment on HEXAR.

## 7. THREE METHODS, ONE PRINCIPAL COMPARISON

HX-ORIGINAL:
Pinned upstream behavior, retained for reproduction and historical context.

HX-PROMPT:
Upstream system with a prospectively fixed calibration instruction requiring
observed events, supported causes and unknowns to remain distinct.

HX-CONTRACT:
The same strengthened system plus CRANE's evidence-contract layer.

Primary comparison:
HX-CONTRACT versus HX-PROMPT.

Secondary comparison:
HX-CONTRACT versus HX-ORIGINAL.

Between HX-PROMPT and HX-CONTRACT, preserve:
- component selection and task/time window;
- allowed observations and source/configuration;
- common primitive evidence derivations;
- public task requirements;
- model/settings where models are used;
- comparable output allowance and recorded resource use.

Give the prompt-only system the same relevant facts and evidence-availability
information. Do not give only our method a filled answer or privileged cause.

Correct clearly unjustified instruction examples in HX-PROMPT rather than
deliberately leaving an easy prompt defect for HX-CONTRACT to beat.

Respect the original system's concise-answer purpose. If the new endpoint
requires a richer format, give both new conditions that format. Do not grade
a one-sentence baseline against an unfair multi-detail answer contract.

Define the CRANE layer narrowly:
allowed event registry -> supported/unknown claim requirements -> checked
propositions -> concise final answer -> support/completeness validation.

Source code can define a conditional rule; it does not prove that its condition
occurred in this episode.

If the implementation replaces the navigation component's realization with
deterministic rendering, state that explicitly. Do not call wholesale component
replacement a post-hoc verifier.

Measure useful answer preservation as well as unsupported-claim rejection.
A blanket "insufficient evidence" system must not win.

## 8. REFERENCES, ANNOTATION AND METRICS

Keep evaluator reference construction separate from production diagnosis.
Do not use the original ground-truth cause as our method's input.

Test numerical, identity and timing predicates deterministically where available.
Use the current qualified agent annotation pipeline for semantic support, with
a bounded external qualification for any new claim categories.

The original human labels can help audit an evaluator on their original task.
They cannot directly label new answers, new masks or a new definition of
evidence support.

Distinguish:
- true according to scenario truth;
- supported by the permitted packet;
- contradicted;
- unknown from this packet.

An answer can happen to name the true hidden cause without being evidence-backed.

Do not penalize correct information absent from a compact required-unit list.
The judge must have access to all relevant permitted evidence.

Preserve polarity, modality and temporal scope. A sentence denying that a cause
was established is not an assertion of that cause.

Suggested primary endpoint:
Per-recording average success over fixed query/evidence conditions, where
success requires:
- the required supported explanation or useful partial explanation;
- no material unsupported causal/mechanism assertion;
- appropriate treatment of the unavailable conclusion.

Freeze precise required units and weighting before held-out evaluation.

Report separately:
- unsupported causal-assertion rate;
- answerable-information coverage;
- unnecessary abstention;
- intact-data performance;
- irrelevant-removal consistency;
- extraction/technical failures;
- runtime/cost and template/fallback rates.

Accept transparent supplemental-detail or flexibility tradeoffs. Do not add
an all-metrics-dominance requirement or select the easiest endpoint afterward.

Use "agent-assessed" for new automated labels. Do not borrow the authors'
human-validation claim for our outputs.

## 9. STATISTICS AND FRESHNESS

The public dataset is finite. Masks, paraphrases and model repetitions do not
create independent physical executions.

Use recording-level pairing and explicitly address shared situation families.
Report the population as the declared released navigation situations, not
all robotic navigation.

For unseen-family claims, use a family-held-out design and accept its smaller N.
Do not switch clustering assumptions because a stricter analysis loses significance.

Before any confirmatory activation:
- freeze candidate, baseline, masks, split, questions, references and judge;
- select one primary endpoint;
- evaluate pilot discordance and realistic precision/power;
- coordinate allocation with the main study's actual error-budget ledger.

A separate worktree does not create another alpha budget. Do not consume the
main or replication reserve without explicit coordination.

Use the established approved fixed/sequential procedure. No repeated ordinary
testing, failure-only subsets, hidden alpha resets or metric switching.

If the released sample cannot support the desired inference, report the
external evaluation descriptively. Do not create hundreds of nominally new
masks to claim statistical power.

An optional single CRANE companion cohort is permitted only when it:
- tests exactly the same calibration hypothesis;
- reuses existing scenarios/evidence tooling;
- requires no new simulator/domain work;
- supplies a faithfully adapted HEXAR baseline with audited interfaces;
- is prospectively governed and analyzed separately.

Call that a CRANE-instantiated HEXAR comparison, not a reproduction of the
original TIAGo results. Do not synthesize charging or sensor facts from hidden
CRANE fault labels merely to fit the interface.

Preserve baseline ties. A prompt-only control matching the contract layer is
a useful negative result, not a reason to weaken the control.

## 10. PARALLEL EXECUTION AND SCOPE CONTROL

This work should not require Unity for the main external-data experiment.

Extract/validate recordings once, retain hashes, and reuse immutable inputs.
Run model calls and isolated annotations in bounded parallel queues.

Use fresh explainer state per recording/mask, unique job IDs, atomic output,
deduplicated caching, and recorded retry rules. Technical failures must not
be silently counted as semantic failures or favorable abstentions.

Coordinate GPU/model quotas with the land and boat agents. Do not launch a
large local model that starves the boat's required rendering.

Use separate ROS domains/ports if native replay is needed. Never connect replay
topics to an active physical robot or another simulation's control domain.

Do not race shared DVC updates or Git operations. Prepare immutable scoped
batches for the existing publication coordinator.

Bound the work to:
1. data/results audit;
2. faithful navigation replay;
3. one evidence-contract integration;
4. three methods and one removal-based stress design;
5. paired analysis and a paper section.

No selector redesign, new causal-model family, VLM, new robot, or benchmark zoo.

## 11. DELIVERABLES AND NEXT ACTION

Maintain:
`docs/hexar_external/HANDOFF.md`
`docs/hexar_external/STATUS.md`
`docs/hexar_external/REPRODUCTION.md`
`docs/hexar_external/STUDY_DESIGN.md`
`docs/hexar_external/EXPERIMENTS.md`
`docs/hexar_external/PAPER_SECTION.md`

Deliver:
- source/data/license manifest;
- original-result recalculation;
- replay/input-parity tests;
- evidence-removal closure tests;
- independent support references;
- frozen method/benchmark definitions;
- retained responses and qualified annotations;
- paired results with uncertainty and limitations;
- one compact result table and evidence-level figure;
- exact run/resume commands;
- integration-ready commits and manuscript text.

The intended paper contribution is:

> "The same evidence-calibration principle used in CRANE can be added to an
> independently developed modular explainer and evaluated on released physical
> robot executions."

Only claim improvement if the comparison supports it. Do not claim overall
HEXAR replacement or a new record on the original benchmark from a changed task.

October 4 is a submission checkpoint. Coordinate a bounded deliverable that
does not delay the main study. Do not trade validity for a significant claim.

First execute:
recompute the released results, inventory navigation bag contents, and create
one faithful development replay with intact and genuinely decisive-missing
evidence. Then run all three methods and inspect evidence flow before expanding.

Do not stop after creating the scaffold. Once the protocol and permissions
permit, actually execute the scoped evaluation and produce the paper artifacts.


## Executed disposition

The complete scoped deliverable is summarized in STATUS.md and v3/COMPLETION_AUDIT.md. All 12 reserved recordings/324 answers and agent assessments closed. Contract-minus-strengthened-prompt useful-supported-answer gain is descriptively+9.3 points, with 7 favorable/5 tied recording pairs. Zero alpha; no statistically supported superiority claim. Both principal methods preserve full required-unit coverage and make zero specific-physical-cause flags. The paper reports deterministic realization, supplemental-detail/resource tradeoffs, limited native parity, known-family public-data/agent uncertainty and private restoration. No merge or publication is authorized.
