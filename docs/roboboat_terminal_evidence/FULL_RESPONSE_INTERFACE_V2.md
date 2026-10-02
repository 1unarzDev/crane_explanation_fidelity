# Full marine paired response interface v2

This additive runner prepares and executes a **development method-reuse sensitivity**, pairing full deterministic CRANE v2 with `gpt-6-astra/high`, tools enabled. It does not relabel historical renderer responses, freeze confirmation, promote a primary comparison, consume alpha or add independent observations. No real response/capture/provider execution was performed in preparing this tooling.

B4 executes the actual `roboboat_full_crane_v2.explain` pipeline: source-derived requirement facts and numeric slots, shared maximal supported diagnosis, maximal realization plan, closed-template realization, atomic verification and local repair. It uses zero model calls. B2 receives the same evidence, effective configuration, complete full-CRANE adapter/catalog/planner/realizer/ontology sources, and all inherited marine certificate/renderer helpers. It may run or reuse any of them. This deliberately strong reuse baseline must remain labeled as such; a separate architectural baseline design would require another prospective development interface.

## Preparation and admission

`analysis/run_roboboat_full_population_responses_v2.py prepare` accepts a development population registry, its shared capture root, and a new declaration path. An incomplete population requires explicit `--allow-completed-subset`. Every completed technically valid row contributes all L0–L2; failed and pending rows remain in accounting. No task outcome or response content selects entries.

A valid terminal is insufficient by itself: required raw worker, navigation summary, fixture trajectory and runtime-parameter records must exist; inherited strict admission checks are recomputed; launcher completion must be valid; supplemental export provenance/raw hashes must agree when present. Packet, effective configuration, terminal and raw inputs are hash-bound before execution. Missing packets/configuration fail preparation rather than silently dropping a level.

Preparation validates the inherited method-source declaration, expands local imports from the full adapter/shared core, adds the v2 claim-contract catalog, and snapshots all method sources. Sources preserve relative `analysis/` and `configs/` paths so the adapter's `CATALOG` resolution works. No reference implementation, evaluator, annotation, ground-truth label, simulator record, precomputed answer or candidate output is staged for B2. Exact effective configuration and its interpretation basis are staged.

The new declaration/source-snapshot namespace uses exclusive creation. It binds originals and snapshots, runner, transport, capture-admission source, prompt, registry, settings, schema, entries, accounting and prior declarations. Same-interface prior declarations must match population, methods, source hashes, prompt, return schema and deadline; their entries are skipped. Historical v1 renderer declarations cannot be misidentified as this successor interface.

## Execution and retention

Before requests, the locked declaration, source originals/snapshots and every bound capture/input are verified. In-memory declaration edits, original-input edits or snapshot tampering fail before any provider call. Up to two workers may execute isolated entries. Each entry creates an exclusive intent; unresolved intents/output directories refuse restart, and a matching completed/failure terminal returns unchanged without reissue.

After the declaration is locked, B4 runs in a separate temporary workspace **from the snapshotted source closure**. The baseline receives a fresh workspace containing identical source/evidence/configuration bytes, with no generated B4 text or intermediate facts/plans. The B4 deterministic subprocess has its own60-second infrastructure deadline. B2 uses the qualified original300-second provider deadline, exactly one caller invocation per new entry, no quality retries and no deadline extension. Provider failures remain terminal failures; a successfully generated B4 remains retained even when B2 fails.

The response layout is:

- `responses/<entry>/B2.json`: answer, provider cache key/latency and one model call.
- `responses/<entry>/B4.json`: final answer, zero model calls, method identity and generation provenance.
- `responses/<entry>/full-pipeline-B4.json`: complete facts, diagnostic result, plan, source-bound numeric values, candidate, realization and audit.
- `responses/<entry>/response-terminal.json`: declaration/entry identity, status and hash bindings for every retained output, including `B4_candidate`.
- `intents/<entry>.json`: immutable pre-execution source identity.

Prospective declaration entries retain `id`, `row_id`, `cluster_id`, `level`, packet/configuration/capture bindings and a `candidate_generation` contract. Actual candidate output hashes are bound in the post-generation terminal, since B4 output is intentionally generated only after declaration locking.

These answer records follow the existing inventory/support response shape. Existing v1 inventory, support and release admission still hardcode legacy certificate/renderer comparisons and **cannot admit full B4 unchanged**. Additive v2 admission must validate the terminal's candidate/full-pipeline bindings and generation provenance against the full source closure. Never fabricate legacy certificates or relabel full outputs to bypass that check. Annotation remains unrun.

## Validation and current readiness

`PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_full_population_responses_v2.py` passes12 tests. Tests perform real B4 generation from temporary source snapshots and inject a baseline caller that imports/runs the staged v2 adapter with its correctly resolved catalog. They verify forbidden-file exclusion, source parity, completed-subset admission, missing/inconsistent capture rejection, tamper refusal, immutable identities, retained failures, prior-entry exclusion and terminal candidate provenance. No live provider or GPU call is involved.

The coordinator identified sample-clock/reference-alignment fail-closed gaps in the v2 adapter and is repairing those before any actual method-source freeze. This tooling does not override that dependency: real declarations should follow successful adapter repair/qualification. Current tests use only disposable source snapshots and fixtures; they do not constitute a study-source freeze or scientific result.
