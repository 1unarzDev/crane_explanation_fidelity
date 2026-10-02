# Plan-bound condition session candidate — 2026-09-30

## Gap and candidate

The original condition guard accepted a caller-supplied plan hash without checking
plan contents, scope membership or permitted configuration. Preserve that candidate.
Separate `analysis/evidence_calibration_condition_session_v2.py` retains its MCP v5
ownership/execution path and adds validation before registry creation and admission.
Study callers and installed-client observers do not migrate.

The development plan binds exact raw bytes, its canonical absolute path, one campaign,
one canonical registry path, the selected coordinator/MCP/broker/ledger/executor
source hashes and a bounded list of allowed condition/method configurations. Duplicate
scope identities are rejected even if their budgets differ. All five methods use the
same rule. The plan accepts only `DEVELOPMENT_INFRASTRUCTURE_ONLY` with model
authorization false; it cannot represent a scientific confirmation authorization.

Configuration hashes exclude only `plan_sha256` to avoid a hash cycle. They include
plan path, registry path, scope, workspace identity, session record path and all
budgets/limits. A session must match exactly one entry. Plan bytes/schema/source
and registry descriptor are checked before exclusive ownership is created. Source,
budget, identity, scope, path or plan changes fail admission. A copied plan cannot
initialize a different registry or be read under another declared path.

Ownership remains keyed by campaign/episode/condition/method. Matching an allowed
entry does not bypass an existing reservation. Failed construction, interrupted
intent/terminal retention and unknown state remain consumed, with no adoption or
replacement. Owner intent additionally binds plan path and the selected planned
configuration hash. Method-facing tool replies do not contain plan/scope metadata.

## Evidence

`python -m pytest -q tests/test_evidence_calibration_condition_session_v2.py`:
**27 passed**. Checks cover all methods, changed configurations/scopes/registry/plan
paths, raw-byte drift, recomputed modified plan digests, source/authorization/schema
drift, duplicate entries, source drift at admission, construction/retention failure,
actual subprocess stdio computation and restart denial.

Retained ignored root:
`output/infrastructure/planned-condition-session-development-v2/`. Client intent
and execution plan precede execution. Five fixed B0–B4 assignments share one plan
and registry. Four predeclared unplanned variants are denied before any owner/session:
new condition, larger CPU total, alternate registry and copied plan path. No alternate
registry is created. All permitted completed scopes subsequently reject restart.

| Assigned inventory | Literal CPU | Failed CPU | Remaining threshold | Total CPU | Overshoot |
| --- | ---: | ---: | ---: | ---: | ---: |
| B2 | 32.459 ms | 298.550 ms | 277.541 ms | 331.009 ms | 21.009 ms |
| B3 | 34.817 ms | 319.435 ms | 275.183 ms | 354.252 ms | 44.252 ms |
| B4 | 35.314 ms | 301.251 ms | 274.686 ms | 336.565 ms | 26.565 ms |

All use a synthetic 310 ms total and 300 ms per-call threshold. B0/B1 expose zero
tools; B2/B3/B4 expose identical definitions and exact literal/Unicode output. Failed
CPU is charged, later computation denied and full 4096-character reads preserved.
All **six** computation services are absent. Variable overshoot remains retained;
these assignments are infrastructure checks, not method effects or independent N.
Artifacts are hash-bound in
`manifests/operations/evidence-calibration-planned-condition-session-v2-development.json`.

## Limits and next gate

Membership and configuration are now checked against a supplied development plan.
That does not prove its scientific validity or approve its creation. An operator can
still create another plan/campaign, alter storage or bypass this unadopted candidate.
The bound source set covers selected components, not every dependency, runtime byte,
kernel or provider. Mutable files and time-of-check changes are not an immutable
deployment. Distributed/power-loss durability, installed-client integration for v2,
full provider/model-facing tools, rendering/capacity, complete turn accounting and
overshoot policy remain open. No actual model turn is bound or executed.

No semantic output, automated annotation, method-key join, pilot score, physical
acquisition, alpha spending or P11 freeze occurs. Preserve failed combined support,
unlaunched C and unanswered measurement reopening. P11 retains nineteen open
conditions and confirmation/replication independent N=0. The five-method comparative
reporting plan remains unchanged. This development execution plan freezes no
scientific population, endpoint, budgets, sample size or allocation.
