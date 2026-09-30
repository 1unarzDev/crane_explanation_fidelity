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

### Reviewed atomic reassessment (development successor)

The complete bank must finish and all 31 unique source answers must have complete faithful project reviews before preparation. Inspect the live extraction process before resuming it; do not launch a second extraction process. Support reassessment preserves all 36 original answer/evidence instances, including exact-text duplicates, and original sentence-inventory scores stay published separately.

```bash
python analysis/run_roboboat_atomic_reassessment.py prepare
python analysis/run_roboboat_atomic_reassessment.py run
```

The preparation command writes `marine_atomic_reassessment_declaration_v1.json` only once, freezes every blind packet and relevant source/qualification/review hash, and fails closed on incomplete/mismatched inputs. The run command submits at most two packets concurrently, caches finalized terminals, and rejects unresolved per-packet intents. It must not be used to retry quality failures. Output: `artifacts/roboboat-terminal-atomic-reassessment-v1`; evaluator join is separate from judge inputs. Completion of support calls still requires developmental endpoint derivation and judge-sensitivity analysis; it does not promote a confirmatory endpoint.

Current regression command (the historical September 26 live-source freeze assertion is a separately documented boundary):

```bash
PYTHONPATH=analysis python - <<'PY'
import subprocess
from pathlib import Path
files = [str(p) for p in sorted(Path('tests').glob('test_roboboat*.py'))
         if p.name != 'test_roboboat_external_validity_registry.py']
files += ['tests/test_export_terminal_margin_diagnostic.py',
          'analysis/test_reference_terminal_margin.py',
          'analysis/test_terminal_margin_diagnostic_adapter.py']
raise SystemExit(subprocess.call(['python', '-m', 'pytest', '-q', *files]))
PY
```

Result: 67 passed. The frozen historical platform's Git objects were also read-only verified against its four declared hashes; current launcher/fixture differ, current profile/route match. Neither freeze nor inherited test was edited.

Both commands above have now executed: preparation passed and all 36 packets are frozen; support run is live in session `58415`. Extraction session `97278` completed with all 62 returns. Do not restart either live/resolved request identity. All 31 project reviews and their retained histories are under `artifacts/roboboat-terminal-atomic-inventory-v1`; the reassessment declaration binds exact bytes. At initial publication there are two support intents and no finalized annotations. Use the existing session to poll; only resume the command after verifying the previous process ended and checking for unresolved intents. No provisional score should be inferred from packet publication or transport progress.

### Fixed two-recording internal-stopping development extension

`settling_pilot_registry_v1.json` fixes two fresh variants on the already inspected known/direct approaches. Only internal StoppedGoalChecker translational/yaw stopping thresholds change from 0.05 to 0.02 in separately committed crane_ml profile `0df6838`; the validated baseline profile and independent task contract remain byte-identical. No controller dynamics, physics or environment changes. Two configuration-diff and hash/path regressions pass; six runtime/callback regressions also pass. These variants add no independent approach-cluster N. They are not confirmation or replication and cannot repair the missing original direct-route counterpart. All unexpected valid results and failures are retained; zero retries, stop at technical failure, no desired-label resampling. They can establish sampled kinematic settling if observed, while contact limitations still prevent full compound success.

```bash
python analysis/run_roboboat_terminal_capture.py \
  --registry docs/roboboat_terminal_evidence/settling_pilot_registry_v1.json \
  --output-root artifacts/roboboat-terminal-settling-v1/captures --limit 2
```

Use one immutable graphics-enabled player at a time. ROS domain 181/port 10481 are unchanged isolated marine resources. Verify live resource/process validity first; preserve strict admission. Runtime readback must match the declared node/plugin and all three internal threshold overrides before publishing method packets. Capture completion alone is not a physical-outcome label.

Both stopping captures and all twelve declared responses completed. The immutable player and baseline profile remain unchanged; component `0df6838` adds only the separate internal-stopping profile. The core support queue is terminal with one retained timeout, not resumable for that failed identity. Do not rerun it to obtain a favorable/complete result.

```bash
python analysis/analyze_roboboat_atomic_failure_bounds.py \
  --output artifacts/roboboat-terminal-atomic-reassessment-v1/atomic-timeout-sensitivity-v1.json
python analysis/build_roboboat_settling_batch.py \
  --capture-root artifacts/roboboat-terminal-settling-v1/captures \
  --output-root artifacts/roboboat-terminal-settling-v1/batches
python analysis/inspect_roboboat_post_dwell_positions.py \
  --root artifacts/roboboat-terminal-settling-v1 \
  --output artifacts/roboboat-terminal-settling-v1/post-dwell-position-observations-v1.json
python analysis/run_roboboat_settling_responses.py --available-only
python analysis/run_roboboat_settling_atomization.py
```

The analysis output is sealed and refuses overwrite; inspect it rather than rerunning the first command after release. Batch/reference and completed response commands verify/reuse exact retained artifacts. The final extraction command is live in session `82608` (PID `1363996`); poll the live handle before any resume, never start another queue. Intent/return records reject unresolved or failed identities. Eleven unique answer texts yield 22 planned extraction returns, not new N. Exact source responses remain immutable and abstraction tags unqualified; every complete answer/inventory still requires project completeness review before support calls.

Panel commands add `--terminal-detail --mark-dwell` to `plot_roboboat_terminal_evidence.py`; both SVG/PNG panels are under `docs/roboboat_terminal_evidence/figures/settling_{known,direct}_terminal_panel`. The fixed five-second samples appear in green; the later capture appears in blue. These visible later observations cannot move the registered dwell. Standard Matplotlib renders were inspected, with the path legend moved outside the axes to preserve the target and trajectory.

Current scoped regression command above now reports 81 passed. The six new strong-agent calls have median isolated transport latency 62.34 s; deterministic v3 uses zero model calls. Dollar cost and standalone certificate computation latency remain unmeasured. Original sentence-based and core atomic sensitivity outputs are not pooled with this new method/physical-variant development comparison.

The completed core timeout-accounting capsule uses the existing isolated coordinator intake, explicitly marked incomplete annotation with complete judgment accounting:

```bash
python analysis/publish_roboboat_terminal_capsule.py \
  --version atomic-v1 \
  --artifact-root artifacts/roboboat-terminal-atomic-reassessment-v1 \
  --results-file atomic-timeout-sensitivity-v1.json --expected-answers 36 \
  --additional-artifact-root artifacts/roboboat-terminal-atomic-inventory-v1 \
  --additional-artifact-root artifacts/roboboat-terminal-v1 \
  --additional-artifact-root artifacts/roboboat-terminal-v3
```

Do not rerun after immutable publication. This capsule is core development/failure accounting, not a claim that the fresh stopping-extension annotations or full study are complete. No shared DVC/storage pointer or inference look is released.

### Settling reviewed support and development coverage sensitivity

All eleven inventories are project-reviewed; both commands below have executed, and the support run is live in session `45424` (PID `1377578`). Do not start a second queue while the process exists or retry any unresolved/failed intent.

```bash
python analysis/run_roboboat_settling_support.py prepare
python analysis/run_roboboat_settling_support.py run
python analysis/analyze_roboboat_settling_support.py \
  --output artifacts/roboboat-terminal-settling-support-v1/development-results-v1.json
```

Preparation is one-shot and freezes 12 episode-specific packets, all exact reviews/returns/source answers, public evidence and current qualified binding. Deadline remains 300 s; original core timeout stays immutable. The analysis is not yet released; it fails closed while any judgment is missing. It revalidates the complete return inventory, reproduces agreement and disagreement-only adjudication, then reports inherited four-unit and added L2 partial-compliance coverage separately for both passes and final labels. The extra unit was declared after inspecting the method responses and before support calls; its result is developmental sensitivity and cannot be promoted to confirmatory superiority. Complete supported supplemental facts remain admissible. The two internal-stopping variants remain inside existing approach clusters, adding no independent N.

```bash
python analysis/audit_roboboat_terminal_numbers.py \
  artifacts/roboboat-terminal-settling-v1/responses \
  --batch-root artifacts/roboboat-terminal-settling-v1/batches \
  --output artifacts/roboboat-terminal-settling-v1/numeric-audit-v1.json
```

Executed: 12/12 pass. Numeric audit covers rounded value/unit matches, not full association/temporal semantics. Current scoped test command above: 84 passed.

Settling support/analysis completed: session `45424` ended normally; all twelve terminals validated, 26 valid support/adjudication calls, no retries. The immutable `development-results-v1.json` is released; do not overwrite it. Inherited strict B2 4/6/B4 6/6; added L2 coverage B2 2/2/B4 0/2; extended score tie 4/6. A/B/final scores agree. The inherited strict difference is driven by undefined contact-flag meaning in the public task packet and must not be promoted as method superiority. See RESULTS/STATUS for exact defects and subsequent versioned repair gate.

```bash
python analysis/publish_roboboat_terminal_capsule.py \
  --version settling-v1 --artifact-root artifacts/roboboat-terminal-settling-support-v1 \
  --results-file development-results-v1.json --expected-answers 12 \
  --additional-artifact-root artifacts/roboboat-terminal-settling-v1 \
  --additional-artifact-root artifacts/roboboat-terminal-settling-atomic-inventory-v1
```

Publication requires all twelve final judgments, unlike the separately labeled core timeout-accounting capsule. Preserve evaluated source/contract ambiguity and unpromoted v4 demos as distinct artifacts. Mixed evaluator archives are not method inputs. No shared DVC pointer or study look is updated.


Executed `PYTHONPATH=analysis python analysis/replay_roboboat_contact_policy_v2.py`: six inspected successor packets, two removal-only ladders, independent contact/kinematic references pass, zero new N. New output root `artifacts/roboboat-contact-policy-v2/replay`; source hashes bound. Executed targeted v2 tests (27 pass) and documented scoped regressions (111 pass). Launched `PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_qualification_v2.py`, session `44086`, log `/tmp/roboboat-contact-policy-v2-qualification.log`; freezes `contact_policy_qualification_suite_v2.json` and `contact_policy_qualification_freeze_v2.json`. Terminal `artifacts/roboboat-contact-policy-v2/qualification/qualification-result.json` or `retained-failure.json`. One-shot runner refuses overwrite; do not restart. No old experiment or score changed.


Contact-policy v2 numerical/replay validation is complete, but the separate semantic extension is **not qualified**. All twelve calls completed normally, with no retry. Each pass scored 14/15 atomic labels and 14/15 fields against the frozen reference; zero unsupported false acceptance and zero supported false rejection. Both fail the predeclared perfect-accuracy gates on case 04. Its authored response asserts continuous proof after saying it is unestablished; the expected limitation-preserved=true reference is inconsistent with whole-response stance. Both judges correctly retain the contrary assertion when assessing preservation, and both use contradicted rather than the frozen insufficient label for the proof assertion. Preserve the failed result, all gold and returns. `contact_policy_development_disposition_v2.json` records this project-agent reference review; it is not human adjudication or a revised passing score. Existing global/marine qualified bindings remain unchanged. No queue remains active. Next: prospectively audit/freeze fresh bounded reference cases and resolve materiality/coverage primary mapping; no same-case retry or confirmation activation.


Contact-policy successor intake verified: 141 unique safe relative-path files, 431,945 bytes, SHA-256 `9abae42e994e1c9b2726e797af5f69a0ba8e3c1a34582fb7b5d824b6cdf734a2`. This capsule explicitly retains failed semantic qualification and complete twelve-call accounting; it is not a qualified endpoint or complete comparison. Local coordinator API publication is completed, with no shared DVC/main integration. Manifest/ledger: `publication_artifact_manifest_contact-policy-v2.json` / `publication_intake_ledger_contact-policy-v2.json`. Final targeted tests 29 pass; full scoped regressions 113 pass, excluding the unchanged documented historical external-validity hash test. Configuration totals remain seven fresh valid recordings, three approach clusters, two original complete pairs; confirmation/replication N=0. No queue remains active. Largest bottleneck: prospective reference/primary-endpoint semantic qualification and coordinator allocation/resources. Next authorized development: resolve whole-response limitation/materiality and evidence-sufficiency label boundaries on fresh, prospectively audited references, then freeze an equal-source v2 development comparison. Do not retry this failed suite, rescore old banks or begin confirmation.


Safe inspection/resume commands for this successor (all one-shot jobs are terminal):

```bash
cd /home/lunarz/worktrees/roboboat-terminal-evidence
cat artifacts/roboboat-contact-policy-v2/qualification/qualification-result.json
cat docs/roboboat_terminal_evidence/contact_policy_development_disposition_v2.json
sha256sum artifacts/roboboat-contact-policy-v2/publication/development-capsule-contact-policy-v2.tar.gz
PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_temporal_certificate_v2.py
```

The archive binds the output snapshot preceding its own intake manifest/ledger. Subsequent status paragraphs do not retroactively change it. Its contents include evaluator-only gold and qualification returns; never mount it wholesale to methods. No live job needs resumption. Both replay and qualification commands in CONTACT_POLICY_V2.md intentionally refuse rerun over retained outputs. A future fresh suite needs distinct identities, an independently reviewed prospective declaration and new output root; the current failure has no retry authorization.


Current continuation adds a proposed material-assertion/answerable-information endpoint with explicit method-blind relevance reviews, two whole-answer limitations, conditional unknown bounds and strict all-assertion sensitivity; no old bank is rescored. `MATERIAL_ENDPOINT_V1.md` defines boundaries. Arithmetic QA: 21 tests pass; inference activation remains refused because semantics are unqualified. Fresh eight-case contact/scope qualification completed 16 calls, no retry. Both passes match 31/31 atomic labels, all unit/limitation booleans and whole-response stance, but frozen qualification remains FAILED_RETAIN_NO_RETRY because five returned valid alternate citations omit the expected example sentences. Supplemental `contact_scope_development_disposition_v3.json` and four span-audit tests retain exact citations and project review without changing scores or promoting qualification. Same-family uncertainty remains; no human validation. Next qualified scorer/reference design must allow prospectively audited citation alternatives; no exact wording criterion for actual answers.


A distinct same-source v2 response replay is prospectively declared for every L0–L2 question from both settling recordings (`contact_policy_response_declaration_v2.json`). Sources include complete production certificate/renderer dependencies and the effective YAML reconstructed from node/plugin-specific checker readback; its hash matches every packet. Both methods have identical public evidence/configuration and executable tools. No reference/evaluator/candidate outputs or source joins are mounted. This is inspected contract-repair development, zero new physical/configuration N and zero alpha; no prior answers/scores are replaced. Session `61744` is live, one baseline call at a time, six registered calls, 300 s and zero retries. Log `/tmp/roboboat-contact-policy-v2-responses.log`; command `PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_responses_v2.py`. Resumption may reuse exact terminal identities only; unresolved intents stop without retry. Qualification session `20328` is terminal failed, not live. Finish responses and reviewed extraction before any new support packets; do not promote the unqualified primary mapping.


Current exact execution handles: contact/scope qualification `20328` completed normally with retained failed gates (16 valid calls); same-source response replay `61744`, PID `1431218`, remains live at five of six terminal response pairs. One response at a time; no restart while its handle/process is live. Full scoped tests 138 pass with the documented historical source-freeze exclusion unchanged. Both response/qualification declarations and all dependencies rehash exactly. Extraction preparation is implemented in `run_roboboat_contact_policy_inventory_v2.py`; prepare only when all six response terminals exist:

```bash
PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_inventory_v2.py prepare
PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_inventory_v2.py run
```

Preparation freezes the complete twelve-answer bank and a separate evaluator join; identical answer bytes share extraction only. The unchanged current qualified extractor gets only opaque text, never method/config/evidence/reference metadata. Two passes, at most two calls, zero retries. Full-source project review remains necessary after structural completion; no support or primary scoring is authorized by extraction. The construction builder for v3 is retained in `analysis/build_roboboat_contact_scope_qualification_v3.py` after execution; its output freeze was prospective, while the script-copy provenance is post-execution. It intentionally refuses to overwrite existing stimuli. No retrospective change to the failed v2/v3 freezes/results is allowed.


Contact-policy v2 response replay session `61744` completed normally: all six registered baseline calls valid, twelve source responses complete, no retry. Complete response accounting is retained in `artifacts/roboboat-contact-policy-comparison-v2/response-accounting.json`; provider cost remains unavailable. No comparative scores are released. Complete eleven-unique-text/twelve-instance blind bank preparation succeeded and `contact_policy_inventory_declaration_v2.json` freezes all source terminals and answers. Current live extraction session `85824`, log `/tmp/roboboat-contact-policy-v2-inventory.log`, runs unchanged current qualified atomizer with two isolated passes, at most two concurrent calls, no retries. Next: poll this handle, finish complete-source project inventory reviews, then prospectively declare new support packets/scoring. Do not rerun preparation or restart a live/unresolved extraction identity. Material endpoint remains unqualified; failed v3 exact-span qualification stays retained. Configuration N is unchanged (seven valid fresh recordings, three approach clusters, original paired N=2; confirmation/replication zero).


Read-only live/main ledger recheck matches local SHA `d6e67e9d4c8da68c434fa639a67ce34de53039f85734c51714a83973bca2dfbe`; no explicit marine allocation in this file. It is not proof of the full current ledger authority and does not authorize use of land reserves. Twelve contact-v2 response numeric value/unit audits pass; semantic/time associations remain pending. First unique-text inventory has both returns and complete-source project review (22 retained atoms), without source answer changes or human-validation claims. Extraction handle `85824` remains live.


Contact-v2 full-source inventories are 9/11 project-reviewed at this update, with complete retained quantity/time/motion/contact and modal scope; source answers remain unchanged. New support/analysis modules reuse the current qualified global/marine pipeline, with development-only independent partial-answerability selection and two whole-answer limitations. Eighteen new targeted QA tests pass, total scoped suite 156 pass. The support runner requires complete extraction and every source review before one-shot preparation, and a separately locked analysis plan before calls. The original bank and unqualified material-primary mapping are not scored/promoted. No inferential effect is estimated from this inspected replay. Extraction `85824` is still live; no restart.


Contact-v2 extraction completed normally: 22 valid returns/calls, eleven unique texts and all twelve answer/evidence instances retained. Complete-source project reviews cover 226 unique-text asserted atoms; no human validation or new physical N. `project-review-summary.json` binds complete review disposition. One-shot support preparation succeeded: twelve distinct blinded packets, unchanged current qualified Astra/high binding, existing marine support gate, independently selected positive sampled-information unit and two whole-answer limitations. `contact_policy_support_declaration_v2.json` and `contact_policy_support_analysis_plan_v2.json` were frozen before support calls; all hashes reproduce. Newer failed qualification scores and unqualified material primary mapping remain unchanged. Current live queue: session `15140`, log `/tmp/roboboat-contact-policy-v2-support.log`, at most two packets, original 300 s deadline, disagreement-only adjudication, zero retries. Prior extraction session `85824` is terminal. No comparative scores released yet. Next: poll `15140`, reproduce complete-bank validation/agreement/adjudication, then release only declared development sensitivities and publish a separate capsule. Confirmation/replication still zero and unauthorized pending coordinator disposition/resources, qualified primary mapping and untouched freeze.


Exact contact-v2 support commands from this isolated checkout:

```bash
# Already executed; prepare is one-shot and refuses overwrite.
PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_support_v2.py prepare
# Live in session 15140: do not start another instance.
# After a terminal state, reuse only finalized identities; unresolved intents require disposition, not retry.
PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_support_v2.py run
# Run only after all twelve development-summary.json terminals are finalized.
PYTHONPATH=analysis python analysis/analyze_roboboat_contact_policy_support_v2.py --output artifacts/roboboat-contact-policy-support-v2/development-results-v2.json
```

The analyzer rehashes the frozen inputs and reproduces both pass labels, agreement and disagreement-only finalization. It refuses missing/duplicate/partial banks and immutable-result overwrite. The reported scores are strict common/extended development sensitivities, not the proposed no-material-unsupported-assertion primary or inferential estimates. Original complete pairs/old settling support remain separate. The preparation and analysis-lock inline command executions are retained through complete dependency bindings and immutable output declarations; no retrospective metric switch is allowed.


Completed contact-v2 support replay: twelve finalized packets, 27 valid calls (24 passes + three abstraction-only adjudications), no retry/timeout. Analysis fully reproduces. Both methods cover 24/24 common units and 2/2 positive sampled-compliance intervals. Strict development score B2 5/6, B4 6/6 in A/B/final; the only B2 failure is a 0.000144942 m growth discrepancy from a 20 ms pre-dwell starting observation, independently checked. Supported physical outcome/compliance and answerable coverage are unchanged, so this is not demonstrated material useful-outcome superiority. No effect/CI/p-value or primary promotion. See CONTACT_V2_RESULTS.md. All queues are terminal; 163 scoped tests pass with the historical source-freeze exclusion unchanged. Next: immutable separate capsule publication, then prospective material-primary/citation qualification and coordinated allocation/resources/untouched design. Full goal remains incomplete.


Completed session `15140` exited normally. Safe reproduction:

```bash
PYTHONPATH=analysis python analysis/inspect_roboboat_contact_v2_growth_scope.py --output artifacts/roboboat-contact-policy-support-v2/growth-scope-reference-v1.json
# The released-result CLI refuses overwrite; use read-only in-memory reproduction.
PYTHONPATH=analysis python - <<'PYCODE'
import json
from analyze_roboboat_contact_policy_support_v2 import analyze, OUT
assert analyze() == json.loads((OUT/'development-results-v2.json').read_text())
print('complete locked development analysis reproduces')
PYCODE
# One-shot isolated publication; execute only once.
PYTHONPATH=analysis python analysis/publish_roboboat_contact_policy_capsule_v2.py
```

No response, extraction or support queue remains live. Do not regenerate the completed banks or retry retained failed qualification identities. Publication requires complete-bank hash/annotation reproduction and includes all original source answers, reviews, labels and failed qualifier versions separately. It changes no shared DVC pointer or main branch.


Completed contact-comparison-v2 capsule verified and isolated coordinator intake completed: 623 unique safe files, 9,642,758 bytes, SHA-256 `290846d37f5a9112ca10b062e149a236a9392fce74914035677ddae3d8985855`. Source integration checkpoint `1c889ad`, unchanged crane_ml `0df6838` and astro `3620237`; manifest/ledger are `publication_artifact_manifest_contact-comparison-v2.json` / `publication_intake_ledger_contact-comparison-v2.json`. Mixed evaluator/qualification material must never be mounted wholesale to methods. All pipeline stages are terminal. No shared DVC/ledger/main integration or submission. This completes the inspected contact-repair development replay, not the whole registered study: prospective material-primary/citation qualification, coordinated allocation/resources, untouched confirmation and fresh replication remain absent.


## Material/citation qualification operational continuation

A ten-case prospective construction suite and endpoint/scorer v2 were independently checked and frozen before twenty registered judge requests. Same authorized Astra/high model, prompt/schema and isolated transport; two sequential passes, 300-second deadline, zero quality retries. Whole-answer materiality distinguishes consequential unsupported assertions from supplemental discrepancies; strict atomic sensitivity remains retained. No inspected comparison bank is rescored. Valid alternative verbatim citations are accepted by the automatic scorer, but complete-source semantic citation review is required before a separate qualification disposition.

The original v2 runner failed after its first valid provider return because it supplied an unsupported keyword to the bound two-argument validator. Original code/freeze/failure/return are retained. The separately bound v3 adapter calls the real signature and independently validates source spans without changing the packet hash. Four adapter regressions pass; full scoped suite: 183 pass with the unchanged historical external-validity source-freeze exclusion. The exact first valid return is reused byte-for-byte; zero requests reissued, nineteen untouched requests remain under the same registration. Operational correction adds no physical or independent N.

Current session `41268`, log `/tmp/roboboat-material-v3-qualification.log`, artifact root `artifacts/roboboat-material-qualification-v3/`. Pass A completed; pass B running at this checkpoint. The command already launched is:

```bash
cd /home/lunarz/worktrees/roboboat-terminal-evidence
PYTHONPATH=analysis python analysis/run_roboboat_material_qualification_v3.py > /tmp/roboboat-material-v3-qualification.log 2>&1
```

Do not launch it again: output-root creation is one-shot. Poll the live handle/log and, after termination, inspect `qualification-result.json` or `retained-failure.json`. A passing automated gate leaves complete-source semantic citation review pending; any failure is retained without tuning/retry. Do not rerun original v2 or alter bound dependencies. Full goal remains active/incomplete: coordinator allocation/resources, untouched confirmation/replication freezes and execution remain missing. Seven valid fresh recordings, three approach clusters, two original complete pairs; confirmation/replication N=0, marine alpha=0.


## Completed bounded material/citation extension (supersedes running state above)

Session 41268 is terminal. Twenty unique valid returns, no reissued request/retry/timeout; first return reused exactly after the retained v2 adapter failure. Both passes match 41/41 atomic labels and all frozen boolean fields. Complete-source project review covers all 86 fields/citations. Separate disposition `material_qualification_development_disposition_v3.json` records bounded-development pass; original automatic citation-review-pending result remains untouched. See MATERIAL_QUALIFICATION_V3_RESULTS.md. This is agent-assessed with same-family shared-error risk; no population error rate, human validation, physical N or comparative effect is inferred.

Safe resume/reproduction: `PYTHONPATH=analysis python analysis/verify_roboboat_material_qualification_v3.py`. Do not restart terminal qualification runners. Next: coordinator allocation/resources, prospective complete endpoint/workflow/analysis freeze and untouched physical/replication registries. Whole goal remains active/incomplete; no confirmation, replication, shared pointer change, merge or submission is authorized by this development result.


Material-qualification-v3 publication completed through the isolated established coordinator intake. Capsule: 77 unique safe relative-path files, 169,363 bytes, SHA-256 `32cea505c31de63ebfb31d1e35951f43cdf878e2bac6850cb1f49086dea88dba`. Path: `artifacts/roboboat-material-qualification-v3/publication/development-capsule-material-qualification-v3.tar.gz`. Manifest and completed ledger: `publication_artifact_manifest_material-qualification-v3.json`, `publication_intake_ledger_material-qualification-v3.json`. Includes all exact bound dependencies, original operational failure/cache, automatic scores, complete source citation review and separate bounded disposition. Evaluator-only: never mount the capsule wholesale to methods. Source checkpoint `278428a`; subsequent publisher integration is separately committed. No main/shared DVC/alpha changes.

Read-only verify: `PYTHONPATH=analysis python analysis/verify_roboboat_material_qualification_v3.py`; `sha256sum artifacts/roboboat-material-qualification-v3/publication/development-capsule-material-qualification-v3.tar.gz`. Publisher command already completed: `PYTHONPATH=analysis python analysis/publish_roboboat_material_qualification_v3.py`; it is one-shot and must not be restarted. All queues terminal. Full goal remains active; next work is the coordinated prospective readiness/freeze, followed by registered execution once authorized.


## Prospective material workflow bridge v3

`roboboat_material_workflow_v3.py` now connects complete source/extraction provenance, independent partial answerability, identical blind forms, validated support returns and the fixed six-question paired-cluster score. Missing claim decisions fail closed; explicit unknowns remain adverse/favorable conditional bounds. Evaluator-only kinematic isolation never replaces contact evidence. Exact source spans are structural checks and still require complete-source semantic review. Twelve targeted bridge tests and 195 full scoped regressions pass; the documented historical external-validity source-freeze exclusion remains unchanged. No old bank rescored or provider/GPU calls added.

`material_workflow_candidate_v3.json` binds sources, tests, public contract, current B2, current qualified extractor/judge and bounded marine extension for prospective development review. It is not an experiment freeze: configuration registry empty, resources/alpha unallocated, inference false. Read-only main ledger recheck matches `d6e67e9d4c8da68c434fa639a67ce34de53039f85734c51714a83973bca2dfbe` and still supplies no boat allocation. See MATERIAL_WORKFLOW_V3.md for exact verification commands. Next required action is the coordinated population/resource/allocation and complete experiment freeze, then registered execution; constructing another manifest cannot waive those prerequisites. Physical N/results unchanged; all queues terminal and full goal incomplete.


## Revalidated external activation block

Full current requirement audit is COMPLETION_AUDIT.md. Main ledger read-only SHA remains `d6e67e9d4c8da68c434fa639a67ce34de53039f85734c51714a83973bca2dfbe`; inspected main study manifests/current/progress records provide no boat allocation or explicit exploratory disposition. All seven isolated publication intake ledgers are COMPLETED; material qualification and 39 workflow candidate hashes reproduce. There is no live pipeline handle to wait for. This allocation/resources gate has persisted across three consecutive goal turns; the last two completed development work, and another inspected replay cannot supply registered independent confirmation/replication. Goal status is to be set blocked, not complete.

Resume requires coordinator authoritative ledger/disposition, explicit allocation or exploratory status and resource ceilings/scheduling authority, followed by a genuine untouched complete protocol/registry freeze and actual execution. Current results remain seven valid physical recordings, three approach clusters, two complete original pairs, confirmation/replication N=0 and marine alpha=0. Tests remain 195 scoped passing at the latest implementation checkpoint; no new provider/GPU or shared mutation. Do not reassign reserves, restart terminal identities or infer approval from silence.
