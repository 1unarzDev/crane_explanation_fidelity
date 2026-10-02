# Condition session ownership candidate — 2026-09-30

## Gap and implementation

MCP v5 charges serial computation CPU in one server lifetime. A fresh sibling
server could otherwise acquire a fresh ledger. Separate
`analysis/evidence_calibration_condition_session.py` wraps the unchanged v5
server with exclusive ownership before server construction. Existing study
callers and earlier adapters remain unchanged.

A fresh operator registry declares campaign identity and prospective plan hash.
The ownership key contains campaign, episode, evidence condition and method.
Configuration hashes, source versions, workspace hashes, record paths and budgets
are retained in intent but deliberately do not change the key. Changing those
fields cannot reserve another session for the same declared identity in the same
registry. All five methods use the same ownership rule; distinct conditions and
methods get distinct owners, without treating them as independent episodes.

An exclusive directory reservation precedes intent retention and server creation.
File and directory fsync are requested. An existing owner is never adopted,
completed, replaced, resumed or reset. Partial registry initialization is unusable.
Interrupted intent retention, construction failure and terminal storage failure
leave ownership consumed. Operator terminal records bind the MCP session terminal
hash and final computation ledger snapshot. Scope/ownership metadata is not sent
in method-facing tool replies. The coordinator has no provider/model execution
API and creates no semantic output.

## Evidence

`python -m pytest -q tests/test_evidence_calibration_condition_session.py`:
**19 passed**. Checks include configuration/source binding, changed record/budget/
identity/metadata/plan rejection, distinct scope identities, two-process exclusive
claim contention, actual subprocess stdio computation, construction failure,
intent/terminal storage failure, invalid scope/placement and partial registry.

Ignored retained root:
`output/infrastructure/condition-session-development-v1/`. Its client and
pre-call plan bind three fixed offline flows. The operation manifest retains
artifact hashes, raw stdio, configurations, owner/session/CPU records and summary.

1. A literal computation consumes 34.805 ms. A failed detached CPU computation
   consumes 406.082 ms against the remaining 275.195 ms threshold. Actual total
   **440.887 ms** is charged against a 310 ms synthetic total; **130.887 ms**
   overshoot is retained. Later computation is denied and a full 4096-character
   Unicode read succeeds. A sibling coordinator with fresh records and a larger
   5 s total is denied before a new session is created.
2. Invalid server construction retains a failure owner terminal. Correcting the
   configuration does not authorize a replacement.
3. An operator-injected owner-intent storage error leaves an empty ownership
   directory, creates no session and blocks replacement. This deliberately injected
   failure is not an observed model/method failure.

Both retained computation services have `LoadState=not-found`. These are
infrastructure observations, not comparative outputs, independent episode N or a
hard CPU cap. Preserve the larger observed overshoot.

## Limits and governance

This is an operator-local guard within **one declared registry**, not a global
authorization system. Creating a different registry/campaign or changing scope
identifiers is outside its enforcement. The caller supplies the plan hash; this
candidate does not validate plan contents, scope membership or scientific freeze.
Registry access, placement and durability are operator-controlled, and power-loss,
distributed storage, immutable runtime and hostile-operator guarantees are not
established. Fsync and a local process-race check are narrower evidence.

One session per condition does not prove that the eventual model invocation uses
that session for its full turn. Installed-client integration for this coordinator,
full provider/model-facing tools, rendering/capacity, complete turn accounting,
other read/control/provider costs, overshoot policy and durable one-shot model
execution remain open. The prospective schedule must bind one registry and exact
scope identities before use; this candidate does not freeze those choices.

No semantic call, automated annotation, method-key join, pilot score, physical
acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched adjudication C and unanswered measurement reopening remain controlling.
P11 retains nineteen open conditions and confirmation/replication independent N=0.
The five-method comparative reporting requirement remains unchanged.
