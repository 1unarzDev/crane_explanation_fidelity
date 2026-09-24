# Analysis

Statistical analysis and figure-generation code belongs here. Analysis must read retained raw data
through committed manifests, preserve episode/scenario clustering, and never treat paraphrases as
independent observations. Generated figures and tables should be reproducible from a frozen data
manifest and configuration hash.

`sequential_diagnostic_monitor.py` is the prospective, fail-closed anytime monitor for new
diagnostic campaigns. It cannot ingest legacy or inspected development data. Its protocol, result
schema, and synthetic zero-outcome dry run are linked from
`docs/SEQUENTIAL_STUDY_PROTOCOL.md`.

## F/G/H runtime parity gate

Build the shared runtime presentation and question-specific parity audit before any repository-agent
call:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/build_fgh_runtime_presentation.py \
  --capture-dir data/robot_visible/dev/EPISODE/capture \
  --structured-episode data/robot_visible/dev/EPISODE/CASE/structured.json \
  --question-kind recovery-mechanism \
  --output-dir data/robot_visible/dev/EPISODE/provenance-parity/QUESTION
```

`run_provenance_agent_pilot.py` requires the resulting `runtime-presentation.json` and
`information-parity-audit.json`. It recomputes the audit, validates the checked-plan episode as a
projection of the presentation, and refuses stale, incomplete, or mismatched inputs before creating
a model caller. Raw and generated artifacts remain outside Git; commit their hashes and provenance
through `manifests/`.

## Ecological recovery-mechanism development case

Reconstruct the bounded warehouse recovery sequence from the governed robot-visible export:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src \
python analysis/export_recovery_execution_diagnostic.py \
  data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json \
  --source-reference data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json \
  --output data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/recovery-execution-diagnostic.json
```

The computation validates unique invocation IDs, bounded classifier provenance, and the ordered
planner-failure/recovery-eligibility sequence. It treats incomplete history as a lower bound,
never equates Nav2 feedback counts with invocation identity, and withholds the unresolved physical
cause.

## RoboBoat retained-grid disconnection development case

After pulling governed development data, recompute the bounded navigation-model diagnosis without
the historical raw fixture:

```bash
PYTHONPATH=analysis:packages/astro_dock/src/crane_explain/src \
python analysis/recompute_roboboat_grid_disconnection.py \
  data/robot_visible/dev/diagnostic-pilot-v1/roboboat-grid-disconnection/evidence-and-diagnostic.json \
  --output /tmp/roboboat-grid-disconnection-recomputed.json
```

The compact export contains the delivered hash-checked grid and exact parsed Navfn messages. The
diagnosis is retrospective development evidence only because the exact dirty source snapshot was
not retained; it must not enter the confirmatory cohort.

## Bounded diagnostic-language verifier audit

Audit the immutable raw P candidates without changing their archived exact-verifier decisions:

```bash
PYTHONPATH=analysis:packages/astro_dock/src/crane_explain/src \
python analysis/audit_diagnostic_language_candidates.py \
  --output /tmp/diagnostic-language-verifier-audit.json
```

The audit is explicitly post-hoc development work. It cannot be used as an independent verifier
accuracy estimate or to reclassify archived outputs.

## Prospective diagnostic power sensitivity

Regenerate the exact paired-binary design sensitivity with:

```bash
PYTHONPATH=analysis python analysis/plan_diagnostic_power.py \
  --output /tmp/diagnostic-study-power-sensitivity-v1.json
```

The inputs are planning assumptions, not pilot effect estimates. Only genuinely distinct scenario
instances count toward the primary sample size; repeated questions, paraphrases, or seed-only
identity changes do not.
