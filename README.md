# CRANE Explain

Evidence-checked natural-language explanations of autonomous robot navigation decisions and
failures. This umbrella repository is the single reproducibility root for the TRUSTMORE 2026
submission (deadline: **October 4, 2026 AoE**). The central failure mode is fluent but unsupported
language—not awkward wording.

The intended contribution is an evidence- and source-provenance explanation method, not a generic
robot adapter, graph store, logging format, or LLM wrapper. It links what the robot observed and
did to the exact versioned program/configuration elements governing that behavior, distinguishes
observation from inference, and checks what the final language actually claims.

`runtime/physical evidence + exact source provenance → checked propositions → language → final-text check`

The TRUSTMORE evaluation is intentionally narrower than CRANE's platform scope. Land/Nav2 is the
primary controlled and ecological navigation domain; RoboBoat is the intended physically distinct
surface demonstration if its parallel workstream qualifies it. Existing aerial and underwater
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
  keyboard view switching passes on the additive v2 revision. Repetition, explanation generation,
  and blinded annotation remain unrun.
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
- **IN_PROGRESS / SEALED:** twenty-seven independent final F/G/H episodes are included (fourteen
  recovery-success, thirteen terminal-abort), with 162 one-shot Luna-low calls retained and no
  exclusions. This remains far below the frozen 40-episode minimum; answers have not been scored,
  and no sealed effect estimate has been calculated.
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
  implementing `docs/ANNOTATION_GUIDE.md`. Hash-matched snapshots contain 126 primary-arm responses
  through `pn-0021` and 54 Claude-arm responses, with keys confined to evaluator-only storage. The
  primary packet must be regenerated once after final collection freeze. Scoring remains `NOT_RUN`.
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

Run the provider-neutral analysis, freeze-integrity, umbrella, and core suites without invoking a
model or ROS runtime:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src:packages/astro_dock/src/crane_explain_ros:analysis \
python -m pytest -q analysis tests packages/astro_dock/src/crane_explain/tests
```

ROS package tests additionally require the Jazzy/ament environment; a blanket host-shell
`pytest` is not the supported ROS test command.

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
