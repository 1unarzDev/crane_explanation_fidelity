# Experiments and resume commands

All commands run from `/home/lunarz/worktrees/roboboat-terminal-evidence`. Artifacts are isolated under `artifacts/roboboat-terminal-v1`; never invoke shared DVC add/push or mutate another checkout's Git. Capture and model requests are one-shot and failure-retaining. Resuming never replaces a failed logical request. Successful immutable artifacts may be reused byte-for-byte.

## Tests and historical reproduction

```bash
PYTHONPATH=analysis python3 -m pytest -q tests/test_roboboat_temporal_certificate.py tests/test_roboboat_terminal_capture.py tests/test_export_terminal_margin_diagnostic.py
python3 analysis/build_roboboat_terminal_batch.py --historical --output-root artifacts/roboboat-terminal-v1/batches
```

The initial 24 focused tests pass, including actual callback capture via an AST-extracted real method, plugin selection, missing contacts, fully observed sampled success, unknown continuous success, single violations, short windows/gaps, yaw wrap, nonfinite values, frame/clock errors, uncertainty, and genuine ladder removal. Production and independent reference match the historical packets numerically and in support state. Initial pre-final-render batches remain under `batches-initial-retained`; they are unpromoted development outputs.

## Fresh physical pilot

```bash
python3 analysis/run_roboboat_terminal_capture.py --output-root artifacts/roboboat-terminal-v1/captures
python3 analysis/build_roboboat_terminal_batch.py --capture-root artifacts/roboboat-terminal-v1/captures --output-root artifacts/roboboat-terminal-v1/batches
```

First command has executed: 001 and 002 complete; 003 technical failure, queue stopped. Running it again skips the successful prefix then fails closed at the retained failed row. It does not retry 003 or start 004. A revised attempt requires a prospective technical repair and successor declaration. One worker uses ROS domain 181, TCP port 10481, fresh player per row, unique run identities, independent scratch roots, atomic ledgers, unchanged strict harness, ordinary Vulkan/HDRP water graphics, and the established hidden-render wrapper. Base YAML hash and exact internal-tolerance launch override are retained separately. Physical action successes can still fail the terminal contract.

## Figures

```bash
uv run --with matplotlib python analysis/plot_roboboat_terminal_evidence.py artifacts/roboboat-terminal-v1/batches/historical-replay --output docs/roboboat_terminal_evidence/figures/historical_terminal_panel.svg
```

The plot uses standard Matplotlib in an isolated uv environment. It shows measured odom path, position error, measured physical speed, and wrapped heading. It does not show evaluator contact truth or suggest an identified disturbance cause.

## Annotation qualification

```bash
python3 analysis/run_roboboat_marine_qualification.py
```

Uses current `gpt-6-astra`/high, unchanged qualified support prompt and v2 schemas, two isolated no-tool calls per construction-defined marine case, no quality retry. The v1 runtime failure remains retained; successor v2 binds the repaired runtime before calls. Its immutable transport snapshot is `tool_snapshots/qualification_transport_v2.py`; it must not be confused with a later strong-tool runtime correction. All judgments remain agent-assessed. Complete semantic comparison is gated on a passed marine qualification and functioning strong-tool canary; neither model name nor successful JSON alone satisfies those gates.

## Executed method/annotation comparison

```bash
python3 analysis/run_roboboat_terminal_comparison.py --batch-root artifacts/roboboat-terminal-v1/batches --output-root artifacts/roboboat-terminal-v1/comparison
python3 analysis/analyze_roboboat_terminal_comparison.py artifacts/roboboat-terminal-v1/comparison --output artifacts/roboboat-terminal-v1/comparison-results.json
```

The comparison declaration binds the code, prompt and runtime before B2 calls. B2 uses the current project's `gpt-6-sol`/high tool condition; it receives the exact same contract, primitives, observations, full production certificate code and renderer as the deterministic marine B4 condition. Method inputs exclude full-source/evaluator access; a real terminal canary verified calculation and hidden-root absence. Blinded exact-span sentence inventories retain negation, temporal scope and compound statements. This is a project-authored development inventory, not the land atomization/role pipeline or a frozen confirmatory atomic endpoint. New temporality/contact concepts passed the separately bounded eight-case two-pass Astra qualification. Existing support annotation/adjudication code, prompt and schemas are reused unchanged; final identities are joined only after finalized annotations.

Resume skips retained complete B2 answers and finalized annotations and reuses exact cached calls. Failed calls remain failures; no poor answer is retried. An incomplete comparison cannot produce a complete-pair endpoint. Results are agent-assessed. One fresh paired route cluster cannot provide a useful confidence interval, confirmatory significance, or pilot discordance adequate for power planning; do not substitute 18 responses for independent N.

## Isolated immutable coordinator intake

```bash
python3 analysis/publish_roboboat_terminal_capsule.py --artifact-root artifacts/roboboat-terminal-v1
```

Run only after all comparison annotations finalize and the results file exists. This creates a deterministic gzip/tar capsule and uses the existing `diagnostic_batch_pipeline.initialize/claim/complete` interface in a **separate publication ledger**. It is post-execution development artifact intake, not a backdated scientific registration or a statistical release. No shared DVC pointer, alpha ledger or main branch is touched. The main coordinator may ingest the immutable capsule/manifest under its normal storage procedure. Capsule content includes evaluator material in separately named folders and must never be mounted wholesale for methods.

## Final validation and numerical audit

```bash
PYTHONPATH=analysis python3 -m pytest -q analysis/test_reference_terminal_margin.py analysis/test_terminal_margin_diagnostic_adapter.py tests/test_export_terminal_margin_diagnostic.py tests/test_roboboat_terminal_capture.py tests/test_roboboat_temporal_certificate.py tests/test_roboboat_terminal_batch.py
python3 analysis/audit_roboboat_terminal_numbers.py artifacts/roboboat-terminal-v1/comparison --batch-root artifacts/roboboat-terminal-v1/batches --output artifacts/roboboat-terminal-v1/numeric-audit-v1.json
```

Executed: 38 tests pass; 18 answer numeric audits pass. The numeric audit has a red-capable check: an unobserved `0.1234 m/s` in L0 is rejected, while the declared `0.4000 m` bound passes. Numeric association/temporal correctness remains evaluated with the complete qualified semantic packet; rounded value/unit matching alone is not explanation correctness. The optional legacy evidence exports were restored as byte copies into this isolated ignored data namespace for regression testing, without modifying DVC pointers.

Capsule publication completed and hash/size/member count verified. A separate relative-root and atomic coordinator-intake regression passed: `PYTHONPATH=analysis python3 -m pytest -q tests/test_roboboat_capsule_publication.py`. Published capsule excludes the retained incomplete packaging attempt.
