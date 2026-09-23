# Analysis

Statistical analysis and figure-generation code belongs here. Analysis must read retained raw data
through committed manifests, preserve episode/scenario clustering, and never treat paraphrases as
independent observations. Generated figures and tables should be reproducible from a frozen data
manifest and configuration hash.

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
