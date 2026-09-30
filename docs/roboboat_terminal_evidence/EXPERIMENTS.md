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

## September 30 bounded continuation and capture diagnosis

```bash
python analysis/replay_roboboat_capture_validity.py artifacts/roboboat-terminal-v1/captures/boat-terminal-pilot-003
PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_render_deadline.py tests/test_roboboat_runtime_parameters.py tests/test_roboboat_pilot_continuation_analysis.py
python analysis/run_roboboat_terminal_capture.py --registry docs/roboboat_terminal_evidence/pilot_continuation_v3.json --output-root /home/lunarz/worktrees/roboboat-terminal-evidence/artifacts/roboboat-terminal-v3/captures
python analysis/build_roboboat_terminal_batch.py --registry docs/roboboat_terminal_evidence/pilot_continuation_v3.json --capture-root artifacts/roboboat-terminal-v3/captures --output-root artifacts/roboboat-terminal-v3/batches
python analysis/run_roboboat_terminal_comparison.py --declaration docs/roboboat_terminal_evidence/method_comparison_declaration_v3.json --available-only --batch-root artifacts/roboboat-terminal-v3/batches --output-root artifacts/roboboat-terminal-v3/comparison
python analysis/analyze_roboboat_pilot_continuation.py artifacts/roboboat-terminal-v1/comparison artifacts/roboboat-terminal-v3/comparison --output artifacts/roboboat-terminal-v3/development-results-final.json
```

Replay returns exit 1 as expected: the actual production strict validator rejects row003. Temporary-copy gate minimization identifies worker.valid, staleActions and rejectedActions; no original bytes are modified or counterfactuals admitted. Retained trace brackets stale camera queue events before the action result, but lacks timestamps for the rejected action and cannot identify the underlying stall. Diagnostic report: `artifacts/roboboat-terminal-v2/diagnostics/capture-diagnosis-v1.json`.

The v2 continuation of untouched rows004–006 failed before the row004 player launched because the render wrapper rounded an epoch deadline into scientific notation. A pinned real-expression regression failed by 1120.125 s and passed after explicit decimal formatting. That failed attempt remains retained. V3 declares a new row004 request identity, preserving approach-02 and physical N; it does not retry row003. Original transport cause remains unresolved. Both continuation declarations are development only, stop on first technical failure and never select outcomes.

Runtime readback canaries retain failures v1–v3 and successful v4. Nav2 plugin parameters require lifecycle configuration; simulation time must be running for the actual fixture lifecycle. The opt-in query runs after warmup, before the acceptance action, with a fixed deadline; it records node/plugin values and never sets parameters. Readback overhead can change pre-action drift, so starting pose is measured and the setup difference is declared. Batch building rejects a measured tolerance differing from the registered launch override.

Never run a second capture command while the current one-worker queue is alive. `--available-only` permits response/annotation overlap on published development batches and explicitly reports deferred batches. It is not a complete-result or confirmation gate. The final combined analysis preserves original paired-cluster IDs and excludes partial pairs from the primary descriptive cluster mean.

Continuation publication (run only after all 18 v3 answers and their annotations finalize):

```bash
python analysis/audit_roboboat_terminal_numbers.py artifacts/roboboat-terminal-v3/comparison --batch-root artifacts/roboboat-terminal-v3/batches --output artifacts/roboboat-terminal-v3/numeric-audit-v3.json
python analysis/publish_roboboat_terminal_capsule.py --artifact-root artifacts/roboboat-terminal-v3 --version v3 --results-file development-results-final.json --expected-answers 30 --additional-artifact-root artifacts/roboboat-terminal-v2
```

The combined result contains 30 fresh answers: 12 from v1 plus 18 from the continuation, excluding six historical replay answers. Historical evidence adds no N. V3 publication includes retained v2 launch/canary/diagnostic failures; the original immutable v1 capsule is a separate hash-bound dependency. The intake ledger/manifest names carry v3 and cannot overwrite v1. Never rerun publication after its immutable capsule exists. Exact provider dollar cost remains unavailable from the login-backed adapter.

The separately versioned precision renderer is exercised with `PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_temporal_renderer_v2.py`; its inspected row005 answer is retained under `artifacts/roboboat-terminal-v3/renderer-successor-development`. It is not a scored comparative response. The example panels add `--terminal-detail` to the plotting command for yaw-rate/hull evidence.

## Fractional cluster QA and bounded extraction qualification

```bash
PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_cluster_analysis.py
python analysis/plan_roboboat_cluster_throughput.py
python analysis/run_roboboat_atomization_extension_v3.py --output-root artifacts/roboboat-terminal-atomization-v3
```

Planning is simulation only, using the inherited e-process primitives and hypothetical alpha, not a marine allocation or look. The qualified method-blind atomizer is resolved from the current v2 inventory disposition and freeze (`gpt-6.1-sol` high); its prompt/schema remain unchanged and abstraction tags remain unqualified. Each extension case receives two isolated no-tool passes. V1 retained a two-call tool-policy failure from mistakenly asking for a file read. V2 passed structural extraction on all eight cases, but independent project review found incomplete construction-defined gold, so no score is promoted. V3 freezes eight fresh held-out cases with explicit component/requirement/relation closure before calls. All calls/failures remain retained, no quality retries, no land binding changes, no physical or confirmatory N. Successful structural returns still require separate semantic/completeness review before qualification.

The v4 sub-suite did not qualify: both passes added odometry-result actor specificity to an unspecified receipt. V5 is a separately declared marine appendix candidate, not a silent replacement of the land prompt. Four fresh construction-defined held-out cases and 27 critical meanings per pass passed independent project review in both isolated passes. This qualifies only bounded text/span extraction of the stated actor/clock/phase/completeness concepts, not abstraction tags, real-bank completeness, support labels, human validity or confirmation. No earlier failed/reference-invalid suite is rescored.

```bash
python analysis/run_roboboat_atomization_extension_v5.py --output-root artifacts/roboboat-terminal-atomization-v5
```

## Complete blind development inventory reassessment

```bash
python analysis/run_roboboat_pilot_atomic_inventory.py
```

Declared before calls, all 36 retained answers included. There are 31 unique exact texts; each receives A/B isolated extraction passes. The blind bank contains only opaque text hashes and answer text; its evaluator join remains outside extractor input. Qualified source model/base prompt/schema and separately checked marine appendix are hash-bound. Do not run concurrent copies. Resumption uses retained terminal records and fails closed on unresolved intents or structural failures. Structural completion does not authorize support annotation. Full method-unaware project inventory review must establish faithful actors, phases, quantities, scope, negation, component facts and relations first. Abstraction tags remain unqualified and cannot enter endpoint/rank scores. Subsequent support passes must retain the current qualified Astra binding and full evidence packet.
