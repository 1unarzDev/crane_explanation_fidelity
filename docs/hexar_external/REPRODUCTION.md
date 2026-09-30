# Reproduction record

All work is in the assigned registered checkout `/home/lunarz/.codex/worktrees/fcc9/crane_explain`, initially clean at `9a81db860f9eec66557240b2297cd122fba9ca06`. No applicable AGENTS.md was found in this checkout or its ancestor instruction paths. The shared submodule registrations are `packages/astro_dock@36202373ae186a8fd247a20b7b477312a744de99` and `packages/crane_ml@bcab3547baccb9c2dcb041b1f146c77876cf89d5`; both are uninitialized here and were left unchanged. No main research or RoboBoat files were edited. HEXAR is a separate clean clone inside the scoped data directory, not a shared nested submodule.

Upstream pin: `https://github.com/fgebelli/HEXAR`, commit `f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc`. `data/hexar_external/audit/source_data_manifest.json` records every released tracked file's SHA-256 and size, historical model/dependency limits, exact main-core hashes and governance-file hashes. `dependencies.lock.txt` is the external audit environment, distinct from the release's incompatible contemporary dependency set. Code and recording licenses are treated separately; raw bags, extracted event streams and fetched paper HTML remain local/ignored rather than being redistributed. Preserve the authors' repository and paper attribution. See SOURCE_AUDIT.md.

Category A recalculates the released annotation columns without editing them. There are 180 declared queries, 540 result rows, three released methods, 60 executions and 18 navigation executions. All 180 experiment keys have exactly one row per method; no duplicate key, missing method pair, annotation-majority mismatch, per-rater accuracy-composition mismatch, or bag/question/category correspondence mismatch was found. Two baseline generated texts are empty but remain in the authors' denominator. Accuracy is the majority of per-rater accuracy, not a newly computed conjunction of majority correctness and majority wrong-info. The source method names differ from current driver names; neither is silently renamed in machine-readable results.

The inventory reconciles message counts from every navigation bag's metadata and read-only SQLite database. SQL can register extra zero-message topics omitted from metadata; these are reported rather than treated as delivered evidence. Across these bags no raw scan, path or costmap measurement topic was found. Clearing requests and path handoffs appear as ROS logs and must not be upgraded to measured geometry. Family/module breakdowns are retained in `historical_results.json`; full selector results are historical context, while fresh work is component-level.

Category B/C first development replay selects `bagfile_6_1.bag` before comparative-output inspection. It extracts 3,422 navigation/task/state inputs from 3,428 bag messages; six speech messages are not navigation component inputs and are excluded from all method/tool contexts. SQL is opened read-only/immutable; original bag hashes do not change. Original AST callback, task bookkeeping, latest-task selection, requested time-window and prompt bodies are executed. No independent approximation of their filtering/state logic is substituted.

A real ROS Humble DDS replay at 1× passed all 3,422 selected common-message deserializations, full callback state, task-window and captured-prompt equality against an offline replay using the exact native dispatch trace. Elapsed replay was 138.23 seconds. This is a **component-level parity test under receipt-clock instrumentation**, not a full end-to-end or historical model reproduction. Native clocks are frozen/traced at each callback entry; the offline reproduction uses those traced times. Later deterministic packet generation uses original bag receipt times. The original unpadded `sec.nanosec` conversion, filtered log lists, duplicate suppression, globally retained override flags and decrementing covariance counter remain unchanged and are covered by regression tests. No speedup alters buffering or event ordering.

The native container uses a pinned image digest, no external network, a private ROS domain, a non-root user and remapped explanation-input topics. It creates no robot-control publisher, lifecycle/action server or selector request. No privileged flags, Unity, GPU model or copied cache is used. An initial pre-replay logging error under the non-root user was repaired by setting a scoped ROS_LOG_DIR; the separate compatibility disposition retains this infrastructure failure and all adaptations. It is not counted as a semantic failure.

Historical model weights cannot be reproduced: the release specifies `phi4:latest` but provides no weight/quantization digest, and the released host cannot resolve here. No local Ollama endpoint is available. Fresh responses instead use the explicitly declared main development B2 configuration (`gpt-6-sol`, high effort), identically for HX-ORIGINAL and HX-PROMPT. The structured ephemeral no-tool CLI wrapper differs from historical chat completions and exposes no retrieved episode files. A hosted model name is not a weight hash: server-side immutability remains unknown, a held-out provenance gate rather than a fabricated artifact identity. HX-CONTRACT replaces realization deterministically and uses no model. No fresh/historical difference is attributed to CRANE.

Run and resume commands from the repository root:

```bash
# Only needed in a fresh checkout; don't replace a populated clone.
git clone https://github.com/fgebelli/HEXAR.git data/hexar_external/upstream
git -C data/hexar_external/upstream checkout --detach f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc
python -m venv data/hexar_external/.venv
data/hexar_external/.venv/bin/pip install -r data/hexar_external/dependencies.lock.txt
data/hexar_external/.venv/bin/python analysis/hexar_external/audit_release.py
data/hexar_external/.venv/bin/python analysis/hexar_external/extract_events.py --bag bagfile_6_1.bag
mkdir -p data/hexar_external/replay/ros-log
docker pull ros:humble-ros-core@sha256:d2bbb43b75b4b73b0552fcedf0aa195d8e9bdd21fe50c02e5c0a791951a55f8e
docker run --rm --network none \
  --env ROS_DOMAIN_ID=189 \
  --env ROS_LOG_DIR=/workspace/data/hexar_external/replay/ros-log \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD,dst=/workspace" --workdir /workspace \
  ros:humble-ros-core@sha256:d2bbb43b75b4b73b0552fcedf0aa195d8e9bdd21fe50c02e5c0a791951a55f8e \
  bash -c 'source /opt/ros/humble/setup.bash && python3 analysis/hexar_external/native_parity.py'
data/hexar_external/.venv/bin/python analysis/hexar_external/build_development.py
python analysis/audit_b2_transport_readiness.py --output data/hexar_external/transport-preflight.json
data/hexar_external/.venv/bin/python analysis/hexar_external/run_development.py --canary-only
data/hexar_external/.venv/bin/python analysis/hexar_external/run_development.py --workers 2
data/hexar_external/.venv/bin/python analysis/hexar_external/qualify_external.py --build-only
data/hexar_external/.venv/bin/python analysis/hexar_external/qualify_external.py
data/hexar_external/.venv/bin/python analysis/hexar_external/build_blind_bank.py
data/hexar_external/.venv/bin/python -m unittest discover -s tests/hexar_external -v
data/hexar_external/.venv/bin/python analysis/hexar_external/report_development.py
data/hexar_external/.venv/bin/python analysis/hexar_external/validate_artifacts.py
```

Retained model failures are not retried; the same cached request is deduplicated. A failed qualification-result file is reused with its failed status, never overwritten or repaired retrospectively. The first canary's misplaced literal instruction and separate v2 request repair are both recorded. Model caches are retained locally under scoped ignored paths; responses, references, declarations and qualification summaries are integration artifacts. The publication manifest lists local archive hashes for the coordinator; this run makes no shared DVC update.

These commands reproduce the **completed development tranche only**. They do not authorize reserved semantic outputs or confirmation. Resume expanded evaluation only after independent qualification-construction review and a fresh prospectively bound external qualification, all-family mask/reference validation, fixed endpoint-role/technical-disposition rules, available-model provenance and coordinated quotas. Confirmatory use additionally requires the publication owner's explicit allocation through the existing ledger. Do not run this failed candidate again on its held-out qualification cases, lower its gates or use baseline ties to tune away a strong control.

## Resumed V2 commands

Use the existing isolated checkout and scoped virtual environment. Each script refuses immutable declaration/reference mismatches; model/annotation outputs are reused on resume, with no quality/technical retry. Do not run model and annotation queues simultaneously: each is capped at two inference workers.

```bash
data/hexar_external/.venv/bin/python analysis/hexar_external/qualify_v2.py
data/hexar_external/.venv/bin/python analysis/hexar_external/build_v2_packets.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/build_references_v2.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/run_v2.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v2.py --cohort development --stage bank
```

The blind developer claim inventory must be complete before `--stage packets` and `--stage annotate`. The latter uses the current support schema/pipeline plus the exact externally qualified v2 amendment for A/B/C; it does not upgrade developer extraction to qualified annotation.

```bash
data/hexar_external/.venv/bin/python analysis/hexar_external/audit_inventory_v2.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/numerical_audit_v2.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v2.py --cohort development --stage packets
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v2.py --cohort development --stage annotate
data/hexar_external/.venv/bin/python analysis/hexar_external/after_pilot_v2.py
```

The ordered release waits for the development annotation summary, computes the declared pilot endpoint, admits only the descriptive frozen design, builds all twelve reserved recordings' transformed packets and independent references, then regenerates all three methods and exports their blind bank. It never allocates alpha, changes a model/source pin or runs annotation simultaneously with model generation. If a stage fails, inspect its retained log and resume the same script; completed immutable outputs are reused. Reserved inventory and qualified annotations remain a separate final gate, followed by `report_v2.py --cohort reserved`, `validate_v2.py` and `archive_v2.py`. Do not reinterpret a frozen technical failure as a semantic result or silently regenerate it.

## Current v3 route; old release watchers retired

V2 closed below its technical gate. Its `after_pilot_v2.py` auto-release watcher was stopped before reserved activation; do not restart it. All failed returns, valid labels and descriptive bounds remain unchanged. V3 changes only the annotation applicability clarification, prospectively qualified on eight fresh fixtures. Production methods, masks, endpoint and independent reference rules remain unchanged. The fresh q1 compatibility pilot has 54 valid outputs; it adds no physical N. Its qualified assessment must close at ≥90% completion before a descriptive reserved freeze. No confirmatory allocation is available.

```bash
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v3.py --cohort development --stage bank
# Independent blinded inventory is required; do not synthesize support labels.
data/hexar_external/.venv/bin/python analysis/hexar_external/audit_v3.py --cohort development
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v3.py --cohort development --stage packets
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v3.py --cohort development --stage annotate
# Executes only after the unchanged technical gate passes:
data/hexar_external/.venv/bin/python analysis/hexar_external/release_reserved_v3.py
# Then independently inventory all reserved answers before these commands:
data/hexar_external/.venv/bin/python analysis/hexar_external/audit_v3.py --cohort reserved
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v3.py --cohort reserved --stage packets
data/hexar_external/.venv/bin/python analysis/hexar_external/annotate_v3.py --cohort reserved --stage annotate
data/hexar_external/.venv/bin/python analysis/hexar_external/report_v3.py --cohort reserved
data/hexar_external/.venv/bin/python analysis/hexar_external/archive_v3.py
```

The release is twelve reserved recordings, all three original questions and three conditions (108 packets, 324 method outputs). Generation and annotation queues remain sequential, each with at most two inference workers. Resume reuses immutable completed outputs; zero technical or quality retries are allowed. The final archive hashes ignored local call/cache assets separately from integration artifacts. Recording redistribution rights remain unresolved.
