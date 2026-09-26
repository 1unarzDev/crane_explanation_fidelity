# High-throughput diagnostic execution

Status: **execution amendment active; RoboBoat canary passed; exact arm freeze/restore gate open**

This runbook accelerates the frozen focused study without changing its claim, methods, evidence,
judge, endpoint, population, alpha, stopping rule, or replication reserve. The authoritative
operational amendment is
`focused-supported-diagnostic-communication-v1-execution-amendment-4.json`.

## Reconciled starting point

The older 13/64 briefing is stale. The repository contains 31 fixed-order land attempts: 30 valid
physical configurations and one retained invalid recording. Independent computation supports 25
primary references. Run 042 is a physical reference but contributes zero semantic N because its
candidate text was exposed during packet closure. The first look therefore uses 24 untouched
eligible configurations. All 24 references and 18 immutable P/R pairs through run 062 are
governed; 063--068 remain. No Luna study call or comparative label exists, so semantic N remains
zero.

## Coordinator interface

`analysis/diagnostic_batch_pipeline.py` is the sole scheduling seam. It owns durable claims,
leases, dependency admission, hash-checked completion, and registered ordered release. Existing
scientific runners remain adapters and are never combined into one model context.

Typical coordinator operations:

```bash
python3 analysis/diagnostic_batch_pipeline.py init --plan PLAN.json --ledger LEDGER.json
python3 analysis/diagnostic_batch_pipeline.py claim --ledger LEDGER.json --pool luna --worker luna-1
python3 analysis/diagnostic_batch_pipeline.py complete --ledger LEDGER.json \
  --job-id JOB --worker luna-1 --artifact-manifest JOB.manifest.json
python3 analysis/diagnostic_batch_pipeline.py release --ledger LEDGER.json \
  --arm land --eligible-n 24
```

Every R answer and every Luna answer/pass is a distinct logical request. The request identity must
hash the configuration, evidence, source, method, model/settings, prompt, schema, reference builder,
judge version, and pass. Duplicate logical identities are rejected. Completion requires an
immutable artifact manifest whose file sizes and SHA-256 values still match.

## Pools and initial limits

| Pool | Initial limit | Scale condition |
| --- | ---: | --- |
| Land simulation | 2 | compare against one worker; advance to four only if valid/hour improves |
| RoboBoat simulation | 1 | retain graphics/water path; increase only after measured GPU/runtime QA |
| CPU references/validation | 4 | increase only if CPU is the measured bottleneck |
| R agent | 2 | shared provider budget; back off on throttle/tail-latency regression |
| Luna | 4 | one answer/pass per request; never reuse a pass |
| Publication | 1 | only immutable completed batches; DVC before Git pointer |

Physical capture may run ahead of semantics, but configuration admission never depends on P/R
outcomes. References begin after capture admission; P renders without waiting for a model; R starts
when parity inputs are ready; each blinded answer can enter its two isolated Luna queues
immediately. Reconciliation and release remain coordinator-only.

## Release and storage rules

Workers write only job-local scratch/output roots. One publisher verifies counts and hashes,
creates immutable manifests, moves the set atomically, pushes DVC, tests restoration, and then
commits pointers. Producers never refresh shared DVC pointers or run Git. Operational dashboards
may show queue depth, completion, latency, resource pressure, and technical failures—not condition
labels or partial P-minus-R outcomes.

Land release remains the registered ordered eligible looks at 24, 36, and 47/schedule end. A look
requires the entire physical-order prefix through that eligible configuration, including controls,
to be reconciled and sealed. Fast later jobs cannot replace slow prefix jobs.

## RoboBoat readiness gate

Land production scale-up is blocked until the separate boat readiness gate passes. Retained
development evidence covers nominal successful docking, terminal-margin failure, bounded grid
disconnection, and a missing-speed mask. The marine-specific Luna qualification and current P/R
two-pass development canary now pass. Remote restoration and the exact prospective arm freeze
remain open. RoboBoat remains separate from land N and the reserved land replication.

The active boat is holonomic at the four-thruster interface, but current RPP has only emitted surge
and yaw, not lateral command. Unactuated sway under that controller is not a command-interface
defect. “Wave drift” is prohibited without validated wave-related evidence; use “observed” or
“uncompensated lateral disturbance” when that is all the record supports.

The canary is recorded in `manifests/data/roboboat-readiness-canary-v1.json`. It validates the
retained robot-visible capture, separate reference computation, parity-checked current P/R pair,
blinded packet, four isolated Luna calls, and conservative reconciliation without adding
statistical N. P received concordant complete-endpoint labels. R's two passes agreed on mechanism
correctness and absence of material error but disagreed on whether radial-error growth communicated
the distinct displacement unit; the endpoint field remains unresolved.

Production scale-up remains blocked for two explicit reasons: the canary batch must be published
and restored from governed storage, and the exact prospective 6-10-configuration boat schedule is
not frozen. The prefreeze requires independent configurations with exact starts, goals, supported
conditions, masks, questions, references, and order. Do not fill the arm with repeated seeds of one
docking setup or invent unsupported wind/current/wave mechanisms. If the existing platform cannot
produce the required bounded families without controller or physics redesign, narrow the arm and
record that limitation before freeze.
