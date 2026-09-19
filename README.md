# CRANE Explain

Evidence-checked natural-language explanations of autonomous robot navigation decisions and
failures. This umbrella repository is the single reproducibility root for the TRUSTMORE 2026
submission (deadline: **October 4, 2026 AoE**). The central failure mode is fluent but unsupported
language—not awkward wording.

`robot decision/execution → retained evidence → checked propositions → language → final-text check`

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
  deterministic fallback, Dock/Slalom regressions, terminal-status distinctions, and the A/B/C/D/E
  harness (17 tests).
- **TESTED:** ROS package tests, Jazzy build, live BT/action/harness capture, and exact BT retention.
- **TESTED:** CRANE build, one valid aquatic terminal-success capture pilot, a graphics-free
  land/Ackermann success smoke with populated costmap snapshots, and a valid-as-expected land
  client-cancellation capture under a full blocker.
- **TESTED (PIPELINE SMOKE):** A/B/C/D/E over real success and cancellation episodes with a
  rule-based generator; identical outputs validate parity and routing but are not an LLM comparison
  or evidence for RQ1/RQ2.
- **NOT_RUN:** land failure/recovery collection and the main powered benchmark.
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
- `scripts/`: root-relative setup, governance, manifest, and checkpoint commands
- `docs/`: architecture, benchmark, study, experiments, research, and decisions

Raw data and model outputs never enter Git. The two data domains are physically separate and are
joined only through opaque episode IDs during evaluation.

## Runtimes and checkpointing

Run the existing full Nav2 fixture from the umbrella root:

```bash
packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh
```

For graphics-free land development, use the dedicated Ackermann/LaserScan corridor fixture. It
selects `Land Vehicle Validation`, `train-cpu`, `-batchmode`, and `-nographics`; it does not open
the aquatic Unity window:

```bash
packages/crane_ml/Tools/Performance/run_land_nav2_fixture.sh
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

- [Architecture](docs/ARCHITECTURE.md)
- [Study design](docs/STUDY_DESIGN.md)
- [Benchmark](docs/BENCHMARK.md)
- [Experiment ledger](docs/EXPERIMENTS.md)
- [Research audit](docs/RESEARCH.md)
- [Decision log](docs/DECISIONS.md)
- [Environment requests](docs/ENVIRONMENT_REQUESTS.md)

## Troubleshooting

- Missing submodules: rerun `git submodule update --init --recursive`, then setup.
- Nested checkout mismatch: do not manually advance it; update `workspace.lock.json` deliberately.
- `ModuleNotFoundError`: rerun setup, then install the nested core package with the command above.
- LLM wording rejected: use the checked template fallback. Unparsed clauses do not pass.
- ROS topic absent: verify navigator lifecycle, namespace/remapping, ROS domain, and DDS IPC.
