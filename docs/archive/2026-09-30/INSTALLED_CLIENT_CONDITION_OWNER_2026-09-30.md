# Installed-client condition ownership — 2026-09-30

## Candidate

Preserve observer v5. Separate
`analysis/observe_evidence_calibration_app_server_mcp_v6.py` selects the condition-
session coordinator, which wraps unchanged MCP v5/broker v7/ledger v2/executor v10.
Each offline observation creates one fresh operator registry with its synthetic
campaign/episode/condition/method identity and plan hash before client launch.
The observer retains the strict settings, network namespace and RPC allowlist;
no model turn or provider execution is available.

Read-only auditing verifies exact registry/owner scope, full configuration hash,
workspace identity, source hashes and CPU budgets. After client cleanup it checks
the actual owner state again. A missing owner terminal stays
`PENDING_OR_UNKNOWN_NO_RESTART`; the observer does not manufacture graceful completion.
If a completed owner terminal exists, it must match the retained session status,
terminal hash and ledger snapshot. No owner or ledger is adopted.

One predeclared direct constructor probe then supplies the same scope and registry
with fresh session records and a larger 5 s CPU total. It must be rejected before
session creation, with empty stdout. This is an admission-rejection probe, not a
study retry or a second installed-client invocation. It does not establish the
installed client's behavior when asked to reconnect/restart its server.

The new observer also retains raw client bytes and a failed sanitized disposition
when client cleanup or the subsequent owner audit raises. Two deliberately injected
post-cleanup errors verify this path without a model turn.

## Evidence

Final source passes **69 focused checks** across two invocations: 61 installed-
client/profile/CPU/ledger and post-cleanup retention checks, then eight owner-binding
corruption checks. The latter reject changed registry plan, scope, configuration,
source, total, missing intent and unjustified/incorrect terminal records without a
client. Earlier exploratory test invocation is not counted again.

Five separate pre-bound retained observations pass on CLI **0.159.2**. Private raw
root: `/tmp/crane-owner-installed-client-20260930-24tty548`. The plan, raw client and
denied-constructor framing, request logs, configurations, owner/session/CPU records
and sanitized summary are hash-bound in
`manifests/operations/evidence-calibration-installed-client-condition-owner-v6.json`.
Raw framing remains private because it may contain host instructions/paths.

| Assigned inventory | Literal CPU | Failed CPU | Remaining threshold | Total CPU | Overshoot |
| --- | ---: | ---: | ---: | ---: | ---: |
| B2 | 32.653 ms | 299.905 ms | 277.347 ms | 332.558 ms | 22.558 ms |
| B3 | 33.401 ms | 334.334 ms | 276.599 ms | 367.735 ms | 57.735 ms |
| B4 | 35.963 ms | 325.963 ms | 274.037 ms | 361.926 ms | 51.926 ms |

All use a 310 ms synthetic total and 300 ms per-call threshold. Exact assigned
inventories, Unicode/literal outputs, failed-work charging, null cutoff/denied
compute replies and successful full reads remain verified. B0/B1 have zero tools;
B2/B3/B4 have identical definitions. All six retained services are absent. Client
stderr bytes and turn/item notification counts are zero for all five observations.

All five dedicated app-server groups require recorded SIGTERM cleanup. All five
owner intents remain pending/unknown, with unchanged intent hashes, and all five
direct replacement constructors are denied without a new session. Pending ownership
is evidence of retained uncertainty, not evidence of graceful completion or a
scientific method failure. Variable overshoot is retained; no hard cap or worst-
case bound follows. Infrastructure assignments do not increase experimental N.

## Open boundaries

Direct assigned-server RPC through the installed client is verified. Full provider/
model-facing tools, alternative routes, rendering/truncation and exact capacity
remain open. Registry enforcement is operator-local: plan contents/scope membership,
one governed global registry, eventual full model-turn boundary, other costs,
overshoot policy, immutable runtime and power-loss/distributed durability remain
unverified. Existing study callers and the failed measurement gate remain unchanged.

No semantic output, automated annotation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched C and unanswered measurement reopening remain controlling. P11 retains
nineteen open conditions and confirmation/replication independent N=0. Prospective
B2/B4 primary and B0/B1/B3 versus B4 secondary reporting remain required, including
episode effects, intervals, corrected p-values and inconclusive/unfavorable results.
