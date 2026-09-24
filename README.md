# CRANE Explain

Evidence-checked natural-language explanations of autonomous robot navigation decisions and
failures. This umbrella repository is the single reproducibility root for the TRUSTMORE 2026
submission. The workshop advertises **October 4, 2026 AoE**, but the live portal currently closes
earlier than literal end-of-day AoE; the project keeps October 3 as its completion/review buffer.
The central failure mode is fluent but unsupported language—not awkward wording.

The forward-looking contribution is a diagnosis-to-language method: validated physical/execution
diagnostics plus runtime/source provenance, checked planning, language, and final verification. It
is not a generic robot adapter, graph store, logging format, universal root-cause system, or LLM
wrapper. The frozen provenance study remains a separate legacy evidence set.

`physical observations + execution/source evidence → validated diagnosis → checked plan → language → final-text check`

The TRUSTMORE evaluation is intentionally narrower than CRANE's platform scope. Land/Nav2 is the
primary controlled and ecological navigation domain; the integrated, protected RoboBoat baseline
is the focused physically distinct surface diagnostic domain. Existing aerial and underwater
environments are retained as validated/developing infrastructure but are
`DEFERRED_POST_SUBMISSION`, not advertised as explanation-study results.

## Clone and initialize

Clone the pinned primary components, then initialize astro_dock's nested dependencies and the
separately pinned explanation packages:

```bash
git clone --recurse-submodules https://github.com/1unarzDev/crane_explanation_fidelity.git
cd crane_explanation_fidelity
scripts/setup_workspace.sh
```

Do not depend on developer-specific absolute paths. Project scripts resolve the umbrella root from
their own location. Exact repository commits and destinations are recorded in
`manifests/workspace.lock.json`.

## Current status

- **IMPLEMENTED, TESTED:** evidence records, checked answer plans, final-text verification,
  deterministic fallback, Dock/Slalom regressions, terminal-status distinctions, bounded
  runtime-to-source provenance, claim classes, deterministic runtime presentations, pre-call F/G/H
  information-unit auditing, and hash-checked runtime configuration identity, covered by the
  CPU-only regression suites.
- **TESTED (CALIBRATION):** e042 retained the effective TurtleBot3/Nav2 launch configuration,
  image/package identities, player hashes, and six exact Git artifacts without evaluator leakage;
  the reusable calibration validator and seven-unit F/G/H parity audit passed.
- **TESTED (DEVELOPMENT ONLY):** parity-controlled provenance pilot v2 on retained e037, with one
  evidence-rich recovery-mechanism question and one evidence-limited physical-cause question. Four
  new H/G calls were made; the two unchanged F calls were reused exactly from cache. Unblinded
  single-annotator review found one material error for F and none for G/H; two questions from one
  episode remain diagnostic, not an effect estimate.
- **TESTED (DEVELOPMENT ONLY):** expanded parity-controlled F/G/H pilot to four independent land
  episodes across recovery-success and repeated-recovery-abort families. Unblinded rates are F 4/8,
  G 0/8, and H 0/8 at full substantive coverage; H is more specific than G (52/52 versus 40/52
  units). The F–G clustered difference is −0.50 with a highly discrete four-cluster bootstrap
  interval [−0.875, −0.125]; response-level McNemar is 0.125. These are planning evidence only.
- **TESTED (DEVELOPMENT ONLY):** predeclared model-strength control selected `gpt-5.6-luna` at low
  reasoning over `gpt-5.6-sol` for future matched F/G/H runs. Luna stayed within every quality
  margin, matched aggregate specificity (140/156), and used fewer tokens and 29.8% less aggregate
  latency across 24 calls. Monetary cost was unavailable; this is configuration selection, not an
  equivalence claim.
- **TESTED:** ROS package tests, Jazzy build, live BT/action/harness capture, and exact BT retention.
- **TESTED:** CRANE build, one valid aquatic terminal-success capture pilot, a graphics-free
  land/Ackermann success smoke with populated costmap snapshots, and a valid-as-expected land
  client-cancellation capture under a full blocker.
- **TESTED:** genuine land controller-progress recovery/exhaustion after fixing the missing
  simulated clock, plus a headless TurtleBot3 Waffle-class warehouse/Nav2 success smoke using
  canonical semantic geometry separated from visuals.
- **IMPLEMENTED, TESTED (ECOLOGICAL CALIBRATION):** an eight-layout manifest-driven land proving
  ground with canonical/visual separation, semantic evidence IDs, headless QA, inspection views,
  and eight behaviorally qualified scenario motifs spanning weave, corrected S-turn, offset gates,
  alternate route, narrow doorway, U-trap, dynamic-gate recovery-success, and bounded blockage
  abort. The original straight-through slalom remains a negative geometry calibration; direct
  keyboard view switching passes on the additive v2 revision. Corrected S-turn, dynamic recovery,
  and bounded blockage each pass a three-run exact-condition repeatability gate; these repetitions
  are not independent study episodes. Later development comparisons use selected governed land
  exports, but no explanation from this inventory has an independent human label.
- **IMPLEMENTED, TESTED (ECOLOGICAL CALIBRATION):** the warehouse temporary-enclosure scenario
  passes a prospective three-run recovery-followed-by-success repetition gate with exact manifest,
  route, obstacle, seed, and configuration identity. Recovery feedback varies across runs; these
  operational repetitions are not independent study episodes or evidence of physical causation.
- **ECOLOGICAL PILOT INPUT CLOSED (DEVELOPMENT ONLY):** the pilot-ready set is exactly warehouse
  recovery, complete blockage, and corrected S-turn. Their separated evidence, truth, QA, and
  provenance records are governed under `data/{robot_visible,evaluator_only}/dev/ecological-pilot-v1/`.
  `dynamic-gate-v1` is historical calibration only; U-trap has no current qualified export and is
  excluded. Environment/platform development now stops in favor of explanation evaluation.
- **PROSPECTIVE NOMINAL DIAGNOSTIC CONTROL (DEVELOPMENT ONLY):** one predeclared current-source
  narrow-doorway run succeeded and is governed with robot-visible route/costmap/odometry evidence,
  separate evaluator truth, and an independent reference. Its checked answer rejects the false
  failure premise while reporting bounded clearance/deviation evidence. One no-retry R/P/T/N
  comparison and blinded packet are retained; human annotation remains `NOT_RUN`, so it is not
  confirmatory evidence.
- **IMPLEMENTED, TESTED:** deterministic F1TENTH PNG/YAML contour-to-collider generator and Unity
  importer, qualified headlessly on the externally retained pinned Spielberg map. Full-lap ROS
  control and source-simulator comparison remain unrun.
- **VALIDATED INFRASTRUCTURE / DEFERRED_POST_SUBMISSION:** PX4 `walls.sdf` primitive reconstruction
  with pinned provenance, semantic wall IDs, separate collision/visual layers, and headless
  aerial/contact/ray checks.
- **VALIDATED INFRASTRUCTURE / DEFERRED_POST_SUBMISSION:** PX4 ArUco render-only landmark invariant
  and pinned windy scenario with repeatable measured CRANE response; camera detection and physical
  wind calibration remain unrun.
- **IMPLEMENTED, TESTED:** offline Clearpath 2.9.4 pipeline SDF/resource manifest and Unity import;
  generated upstream assets stay out of Git. Geometry/layers/contact passed, as did a local 1 m
  ROS/Nav2 motion and sensor-transport smoke. Representative route and native-Gazebo comparison
  remain unrun.
- **TESTED (PIPELINE SMOKE):** A/B/C/D/E over real success and cancellation episodes with a
  rule-based generator; identical outputs validate parity and routing but are not an LLM comparison
  or evidence for RQ1/RQ2.
- **TESTED (DEVELOPMENT ONLY):** eighteen real land episodes, 109 questions per condition and 545 total
  A/B/C/D/E responses, cached single-sample model calls, parity audits, and provisional material
  error/coverage annotation. A has 6/109 errors, B 0/109, and C/D/E 1/109 each. Checked methods
  retain lower answerable-information coverage; eighteen episode clusters do not support inference.
- **TESTED:** a bounded evaluator-only TurtleBot3 mobility interruption produced the first captured
  recovery-followed-by-success episode with one exact Wait attempt. The first run was excluded
  when a volatile DDS startup race lost its goal boundary; reliable transient-local harness QoS
  was then validated on the retained replication. Three further predeclared independent
  configurations passed; a fourth is retained but excluded because it produced zero recoveries.
- **COLLECTION_CLOSED_EARLY / SEALED:** 33 independent final F/G/H episodes are included (17
  recovery-success, 16 terminal-abort), with 198 one-shot Luna-low calls retained. This is below
  the frozen 40-episode minimum and 50-episode target. No sealed answer is annotated/adjudicated,
  and no sealed effect estimate exists. See [research redirect](docs/RESEARCH_REDIRECT.md).
- **TESTED (DIAGNOSTIC DEVELOPMENT ONLY):** physical-diagnosis contracts and a separate study
  draft cover geometric restriction and command-to-motion discrepancy. One governed retrospective
  RoboBoat run and its speed-masked variant now have parity-audited R/P/T/N outputs and blinded
  four-response packets. Tool-enabled R matched the unmasked P/T mechanism; on the mask, R/N
  preserved a supported positional failure chain that P/T omitted. P fell back to T in both cases.
  These are one episode cluster, unannotated, and not an effect estimate.
- **TESTED (DIAGNOSTIC DEVELOPMENT ONLY):** a prospectively declared independent land scenario
  records a sustained command--motion discrepancy, later measured-response recovery, and eventual
  navigation success under unchanged development thresholds. The blind export and separate
  reference agree; evaluator intervention identity remains excluded. The recovery-plan refinement
  followed inspection of the first deficient answer, so this is post-observation regression
  evidence, not a confirmatory effect estimate. A later predeclared R/P/T/N comparison produced a
  blinded four-response packet: R reports an incorrect discrepancy interval/duration on project
  review, raw P preserves the checked values, and final P again falls back to T. Human annotation
  remains `NOT_RUN`, so this is a differentiation candidate rather than a scored method result.
- **TESTED (DIAGNOSTIC DEVELOPMENT ONLY):** a current-source v4 connected-detour run succeeded
  with a retained cost-253 restriction on the requested direct route and 1.036 m of delivered
  odometry deviation. An independent raster/A* implementation reproduces the bounded restriction,
  retained-grid connectivity, and successful outcome. This is one unannotated development case;
  it does not identify the physical obstacle, prove exact Nav2 snapshot consumption, or prove that
  the restriction caused the detour.
- **COLLECTED, NOT_ANNOTATED (DIAGNOSTIC DEVELOPMENT):** the complete R/P/T/N inventory contains
  52 blinded responses in 13 packets over nine statistical clusters. Final P used deterministic
  fallback for 13/13 questions. This is a development inventory, not a held-out result; no P-over-R
  effect is established and no campaign-specific method/judge/resource freeze exists.
- **REGISTERED FRAMEWORK / NO CAMPAIGN ACTIVE:** new diagnostic confirmation uses a prospective
  P-versus-tool-enabled-R sequential protocol with a +0.15 minimum worthwhile improvement,
  simultaneous material-error/coverage/ambiguity guardrails, a closed 0.05 program error ledger,
  and separately reserved fresh-config replication. It cannot use legacy or inspected development
  outcomes. The reference-audited Luna v7 arm remains historically qualified, but its later
  prospective command--motion endpoint-threat extension failed composite/core and protected gates
  in both passes. Candidate-v3 semantic confirmation is therefore blocked; no confirmatory response
  was judged and alpha remains 0.000/0.050. The original finite-qualification bounds remain
  historical and the extension's smaller bounds are ineligible; see
  [sequential protocol](docs/SEQUENTIAL_STUDY_PROTOCOL.md)
  and [campaign progress](docs/DIAGNOSTIC_CAMPAIGN_PROGRESS.md).
- **PHYSICAL/REFERENCE COLLECTION ACTIVE; SEMANTIC CAMPAIGN INACTIVE:** four of the frozen 100
  land command--motion confirmation configurations have been attempted once and are valid. Run 003
  preserves useful execution facts while correctly withholding the masked motion mechanism; run
  004 records recovered measured response followed by task abort. No P/R response, Luna label,
  effect estimate, confidence sequence, or alpha use exists. Replication remains untouched.
- **TESTED (SECONDARY-ARM DEVELOPMENT):** the provider-neutral model-call contract now has a
  Claude Code adapter as its first non-GPT instance. A predeclared control rejected Haiku and fixed
  `claude-sonnet-5` at low effort. See [model-family replication](docs/MODEL_FAMILY_REPLICATION.md).
- **COLLECTED, NOT_ANNOTATED (SECONDARY ARM):** the sealed nine-episode Claude replication over
  `pn-0001`–`pn-0009` retained 18 result envelopes and 54 one-shot calls with accepted parity, a
  verified read-only workspace, and no retry or resampling. G used its deterministic checked template
  on 16 of 18 responses. It reuses retained episodes, so it adds **zero** independent clusters, does
  not amend the primary freeze, and does not relieve the 40-episode minimum. No sealed Claude answer
  has been scored and no cross-family effect estimate exists.
- **IMPLEMENTED, TESTED:** blinded response packaging and dual-annotator adjudication tooling
  implementing `docs/ANNOTATION_GUIDE.md`. Final legacy packet `sealed-primary-v3` contains 198
  primary F/G/H responses over all 33 retained episodes; its key is confined to evaluator-only
  storage and its manifest is tracked. The separate Claude packet contains 54 responses. Two
  isolated handoff archives contain the legacy and 52-response diagnostic inventories, blank forms,
  guides, and an optional fail-closed resumable workbench. Scoring, adjudication, and key joining
  remain `NOT_RUN`.
- **NOT_RUN:** blinded dual annotation, final statistics/figures, and final A–E model evaluation.
- **NOT_RUN:** source-to-binary rebuild verification.
- **DEFERRED:** arbitrary-LLM proposition extraction until independently evaluated.

## CPU-only demo

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e 'packages/astro_dock/src/crane_explain[dev]'
python -m pytest -q packages/astro_dock/src/crane_explain/tests
crane-explain validate configs/fixtures/dock_policy.json
crane-explain explain configs/fixtures/dock_policy.json --alternative Slalom
```

The fixture policy is synthetic and exists only to test arithmetic; it is not CRANE's policy.

After `dvc pull data/robot_visible/dev.dvc`, reproduce the compact development diagnosis from its
retained source summary and exact historical Nav2 configuration with:

```bash
python analysis/export_terminal_margin_diagnostic.py \
  --summary /path/to/PerformanceResults/roboboat-gate5-known-dock-1/fixture-summary.json \
  --config-repository packages/crane_ml \
  --config-commit 4ae5124c12c39af93ee5b256e33778aec490ecd3 \
  --task-tolerance-m 0.40 \
  --source-reference PerformanceResults/roboboat-gate5-known-dock-1/fixture-summary.json \
  --output /tmp/roboboat-terminal-margin-evidence.json
```

The retained compact export is restorable without the large source summary; byte-for-byte
regeneration additionally requires that hash-identified development summary. The exporter refuses
summaries without the declared independent-odometry provenance.

Recompute the post-hoc v2 partial diagnosis for the retained speed mask without the large summary:

```bash
python analysis/recompute_terminal_margin_diagnostic.py \
  data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin-masked-speed/evidence.json \
  --config-repository packages/crane_ml \
  --output /tmp/roboboat-terminal-margin-partial-v2.json
```

This correction preserves the supported positional-margin chain while withholding return-speed
criterion satisfaction and the physical source of residual motion. It is development-only and
does not replace the retained pre-correction model outputs.

Recompute the second retained RoboBoat development mechanism directly from its compact governed
costmap and planner-log export (the historical raw fixture is not required):

```bash
python analysis/recompute_roboboat_grid_disconnection.py \
  data/robot_visible/dev/diagnostic-pilot-v1/roboboat-grid-disconnection/evidence-and-diagnostic.json \
  --output /tmp/roboboat-grid-disconnection-recomputed.json
```

This establishes a disconnection in one retained navigation-model snapshot plus matching Navfn
failure messages. It does not establish physical berth infeasibility, a unique obstacle, or exact
planner consumption. The retrospectively selected run has incomplete source-snapshot provenance
and is therefore development-only and ineligible for confirmatory evaluation.

After pulling governed development data, reproduce the checked land geometric diagnosis with:

```bash
python analysis/export_geometric_route_diagnostic.py \
  data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/fixture-summary.json \
  --episode-id land-blockage-global-002 \
  --nav2-config packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml \
  --bt-xml packages/crane_ml/Tools/Performance/nav2_warehouse_replanning_deadline.xml \
  --robot-radius 0.22 --inflation-radius 0.55 --deadline-seconds 70 \
  --output /tmp/land-blockage-global-002-diagnostic.json
```

This development answer establishes a direct-route restriction and deadline-aligned abort. The
retained planner grid is still connected, so it deliberately withholds a global no-path claim.

Reproduce the current-source successful connected-detour diagnosis and independent reference:

```bash
python analysis/export_geometric_route_diagnostic.py \
  data/robot_visible/dev/diagnostic-land-dev-002/fixture-summary.json \
  --episode-id diagnostic-land-dev-002 \
  --nav2-config packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml \
  --bt-xml packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml \
  --robot-radius 0.22 --inflation-radius 0.55 --deadline-seconds 100 \
  --output /tmp/diagnostic-land-dev-002-geometric.json
python analysis/reference_land_geometric.py \
  data/robot_visible/dev/diagnostic-land-dev-002/fixture-summary.json \
  --episode-id diagnostic-land-dev-002 \
  --bt-xml packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml \
  --deadline-seconds 100 \
  --output /tmp/diagnostic-land-dev-002-reference.json
```

This is a development success control with a restricted direct route and measured detour, not a
failure episode or proof that the observed costmap restriction caused the path deviation.

Reproduce the independently auditable delivered-plan diagnosis from the one-run v2
instrumentation qualification:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/export_geometric_route_diagnostic.py \
  data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json \
  --episode-id diagnostic-land-dev-004 \
  --nav2-config packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml \
  --bt-xml packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml \
  --robot-radius 0.22 --inflation-radius 0.55 --deadline-seconds 100 \
  --computation-version geometric-route-restriction-v2 \
  --output /tmp/diagnostic-land-dev-004-geometric-v2.json
python analysis/reference_land_plan_geometry.py \
  data/robot_visible/dev/diagnostic-land-dev-004/fixture-summary.json \
  --episode-id diagnostic-land-dev-004 \
  --output /tmp/diagnostic-land-dev-004-plan-reference.json
```

Both implementations recompute every retained plan hash and geometry summary. The checked answer
supports a change from an initially direct delivered plan to later non-direct delivered plans and
the successful action outcome. It does not prove controller consumption, identify the physical
trigger, or establish costmap-to-plan causation. This is development instrumentation qualification,
not confirmatory effectiveness evidence.

Reproduce the blind development command-to-motion diagnosis and its independent evaluator-side
check after pulling both development DVC roots:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/export_command_motion_diagnostic.py \
  --events data/robot_visible/dev/diagnostic-motion-instrumentation-held-001/capture/events.jsonl \
  --capture-manifest data/robot_visible/dev/diagnostic-motion-instrumentation-held-001/capture/manifest.json \
  --runtime-manifest data/robot_visible/dev/diagnostic-motion-instrumentation-held-001/capture/runtime_manifest.json \
  --bt-xml data/robot_visible/dev/diagnostic-motion-instrumentation-held-001/capture/behavior_tree.xml \
  --nav2-config packages/crane_ml/Tools/Performance/nav2_land_fixture.yaml \
  --episode-id diagnostic-motion-dev-cm-001 \
  --output /tmp/command-motion-evidence.json
python analysis/reference_command_motion.py /tmp/command-motion-evidence.json \
  --output /tmp/command-motion-reference.json
```

The exporter command above reconstructs a fresh blind export from the raw capture using the
current default computation version. To reproduce the exact versioned diagnosis retained for the
paper without exposing its precomputed result to the computation, run:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/recompute_command_motion_diagnostic.py \
  data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json \
  --output /tmp/command-motion-recomputed.json
```

The CLI projects only the robot-visible `method_input`, recomputes the version named there, and
fails if the version or source-qualified recovery-policy hash is unsupported.

The source acquisition name is evaluator-sensitive and must not be supplied to an explanation
method. Only the blind export (or its `method_input` projection) is permitted. The result supports
a delivered-command/measured-motion discrepancy, not a unique motor, slip, collision, obstruction,
or hidden-intervention attribution. It is development instrumentation qualification, not an
independent episode or an effectiveness result.

Run the provider-neutral analysis, freeze-integrity, umbrella, and core suites without invoking a
model or ROS runtime:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src:packages/astro_dock/src/crane_explain_ros:analysis \
python -m pytest -q analysis tests packages/astro_dock/src/crane_explain/tests
```

ROS package tests additionally require the Jazzy/ament environment; a blanket host-shell
`pytest` is not the supported ROS test command.

Build the anonymous IEEE-format paper with the pinned toolchain:

```bash
scripts/build_paper.sh
python scripts/audit_submission_readiness.py --category short
```

This writes `output/pdf/main.pdf`. The current manuscript is an anonymous six-page short/WIP paper
with no unresolved result placeholders. It reports deterministic development measurements,
information-parity negative findings, 13/13 proposed-method fallback, and the failed bounded Luna
judge qualification; it makes no semantic superiority claim. The original human workflow remains
available but incomplete, and automated labels are never represented as human annotations.
The build pins `SOURCE_DATE_EPOCH` to the latest checked-out paper-source commit unless the caller
explicitly sets it, so repeated builds of one paper revision are byte-identical.
The readiness audit passes only when the selected page category, anonymity, PDF, and numeric
traceability gates all pass. It is a mechanical gate, not peer review or submission authorization.

After the governed DVC roots are materialized, reproduce the submission-critical paper and two
independently checked diagnostic results together:

```bash
scripts/verify_submission_reproduction.sh
```

This fails unless the short-paper readiness audit passes, the delivered-plan diagnostic and its
independent reference regenerate byte-for-byte, and the blind command-motion recomputation matches
the retained versioned diagnosis and checked answer.

## Layout

- `packages/astro_dock/`, `packages/crane_ml/`: pinned Git submodules
- `packages/astro_dock/src/crane_explain/`: pinned nested CPU-only evidence-checking package
- `packages/astro_dock/src/crane_explain_ros/`: pinned nested ROS capture package
- `configs/`: committed fixtures and experiment configuration
- `analysis/`: statistics and figure-generation code
- `paper/`: anonymous paper and supplement sources
- `manifests/`: dependency locks, data inventories, and run checkpoints
- `data/robot_visible/`: untracked evidence supplied to explanation systems
- `data/evaluator_only/`: untracked fault truth, gold propositions, and labels
- `.dvc/` and `*.dvc`: credential-free pointers for ignored artifacts synchronized through private
  Cloudflare R2
- `scripts/`: root-relative setup, governance, manifest, and checkpoint commands
- `docs/`: architecture, benchmark, study, experiments, research, and decisions

Raw data and model outputs never enter Git. The two data domains are physically separate and are
joined only through opaque episode IDs during evaluation. Primary and secondary model-family arms
never share an output root, cache root, manifest name, or annotation file.

After setup, DVC/R2 synchronization is documented in [governed artifact storage](docs/DATA_STORAGE.md).
R2 does not provide a hard free-tier spending cap; the project wrapper requires account-wide
metrics and stops at conservative 90% guard thresholds, but it cannot guarantee zero fees.
To materialize the governed ecological pilot inputs from a fresh checkout, configure the private
remote as documented there and run `scripts/dvc_r2_sync.sh pull`; do not substitute historical
runtime directories or evaluator truth for robot-visible model input.

## Runtimes and checkpointing

Run the existing full Nav2 fixture from the umbrella root:

```bash
packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh
```

For graphics-free land development, use the land fixture or its TurtleBot3 wrapper. Both select
`train-cpu`, `-batchmode`, and `-nographics`; neither opens the aquatic Unity window:

```bash
packages/crane_ml/Tools/Performance/run_land_nav2_fixture.sh
packages/crane_ml/Tools/Performance/run_turtlebot3_nav2_fixture.sh
```

The default 3 m goal is a vertical-slice check, not a powered-study scenario. Raw fixture output is
ignored and evaluator-only unless explicitly transformed into a governed benchmark artifact.

After each validated run, generate a content-free data manifest and commit the exact component
pointers:

```bash
scripts/checkpoint_validated_run.sh RUN_ID \
  data/robot_visible/RUN_ID data/evaluator_only/RUN_ID
```

Review that commit, then push it. The checkpoint command refuses dirty component repositories or
staged governed data. Do not call `goalAttempts` a recovery count, replay a counterfactual, or
delivered odometry proven controller consumption.

## Documentation

- [Project language](CONTEXT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Study design](docs/STUDY_DESIGN.md)
- [Research redirect and legacy disposition](docs/RESEARCH_REDIRECT.md)
- [Physical-diagnosis contract](docs/PHYSICAL_DIAGNOSIS.md)
- [Prospective diagnostic study draft](docs/DIAGNOSTIC_STUDY_DESIGN.md)
- [Benchmark](docs/BENCHMARK.md)
- [Experiment ledger](docs/EXPERIMENTS.md)
- [Model-family replication protocol](docs/MODEL_FAMILY_REPLICATION.md)
- [Governed artifact storage and DVC/R2 setup](docs/DATA_STORAGE.md)
- [Blinded annotation workflow](docs/ANNOTATION_WORKFLOW.md)
- [Research audit](docs/RESEARCH.md)
- [Decision log](docs/DECISIONS.md)
- [Environment requests](docs/ENVIRONMENT_REQUESTS.md)
- [Environment catalog and empirical scope](docs/ENVIRONMENTS.md)
- [Environment architecture](docs/ENVIRONMENT_ARCHITECTURE.md)
- [Environment validation gates](docs/ENVIRONMENT_VALIDATION.md)
- [Reference-environment source audit](docs/research/REFERENCE_ENVIRONMENTS.md)
- [Nav2 Jazzy recovery provenance audit](docs/research/NAV2_JAZZY_RECOVERY_PROVENANCE.md)

## Troubleshooting

- Missing submodules: rerun `git submodule update --init --recursive`, then setup.
- Nested checkout mismatch: do not manually advance it; update `workspace.lock.json` deliberately.
- `ModuleNotFoundError`: rerun setup, then install the nested core package with the command above.
- LLM wording rejected: use the checked template fallback. Unparsed clauses do not pass.
- ROS topic absent: verify navigator lifecycle, namespace/remapping, ROS domain, and DDS IPC.
