# Development repository source binding — 2026-09-30

## Gap and bounded repair

Coordinator v5 checks six selected source hashes before ownership. Its static repository
imports also execute code from other files, including the JSON helper and the
qualification runner supplying `_write_once`. Executor v10 launches the namespace
wrapper by path. Those dependencies were absent from the six-file plan identity.
Full dependency/runtime binding was already documented as open; preserve the old
coordinator and its valid observations within their stated scope.

A separate coordinator v6 changes only `source_hashes()` and the owner schema. It
selects unchanged MCP v5, broker v7, CPU ledger v2, executor v10 and response writer v3.
The new helper recursively parses static absolute repository imports, including
imports inside function bodies and conditional branches, without executing them.
The coordinator, binding helper and path-launched namespace wrapper are explicit roots.
The current closure contains **30 Python files**. Plan creation, registry creation and
admission compare this exact mapping; budgets/configuration/scope ownership are unchanged.

The helper reads regular files through no-follow/nonblocking descriptors, rejects
symlinks and nonregular files, and limits inspection to 512 files, 8 MiB per file and
64 MiB total. Relative imports, local packages and dotted local imports require separate
support and are rejected. Imported stdlib/third-party packages are outside this
repository mapping and remain a runtime gate. No repository source is rewritten by
the scanner. Discovery includes static code even if its branch is not exercised.

## Evidence

**49 distinct focused checks** pass across two invocations (46, then three added
limit/failure-retention checks). These cover transitive/nested imports, cycles,
explicit launch roots, dependency additions/deletions/byte changes, unsupported
layouts, nonregular sources, bounded inspection, and plan rejection before ownership.
Inherited coordinator checks cover exact configuration membership, response denial,
partial transport retention, real stdio computation and restart rejection. The
standalone fixed observer preserves a failure and rejects reuse without launching
a model or service in its injected pre-server failure check.

One predeclared retained observation at
`output/infrastructure/repository-source-binding-v1/` uses a shared development plan
for B0–B4 and unchanged local server implementations. B0/B1 advertise zero tools and
flush 229 bytes each. B2/B3/B4 advertise identical read/computation tools, return exact
`42\n` from a fixed computation and flush 1,152 bytes each. All five local sessions
reach actual retained terminal state and reject unchanged constructor admission.
All three computation services have `LoadState=not-found`; actual CPU is retained
(31.503, 33.228, 35.197 ms), with no method-effect claim.

Two separate copied-source probes append an inert comment to the JSON helper and
namespace wrapper respectively. The preserved v5 six-file mapping remains unchanged;
the v6 mapping changes and admission fails before any owner/session is created.
The operator probe temporarily directs source inspection to those copies; it does not
execute modified copied code or alter original source, old plans, recordings or caches.
Raw plans, copies, RPC/egress records, terminals and summaries are hash-bound in the
operation manifest. No failure artifact is replaced and no failed call is retried.

## What remains open

This binds static repository imports and one explicitly known path-launched script;
it is not full Python dependency resolution or an immutable runtime. Dynamic imports,
other scripts/data, installed package identities, interpreter search-path shadowing,
already-loaded module identity and races between hashing and execution remain outside
the guarantee. Writable storage, operator bypass, alternative plans/campaigns and
power-loss/distributed durability are still open. The runtime archive/restoration
records remain separate; this candidate still uses the existing runtime route.

Installed-client observer v9 still selects coordinator v5. It and existing study
callers do not migrate. The new retained evidence is local server execution, not
provider/model inventory, peer receipt, model-visible rendering or tokenizer/capacity
verification. Scientific authorization and complete one-shot model-turn accounting
remain required before fresh five-method execution.

No semantic output, automated annotation, method-key join, pilot score, physical
acquisition, alpha allocation or P11 freeze occurs. The failed combined-support canary
and unanswered measurement reopening remain controlling. P11 retains nineteen open
conditions, zero component hash mismatches, confirmation/replication N=0, unchanged
alpha and quarantined layout accounting. B2/B4 remains primary; B0/B1/B3-versus-B4
episode effects, intervals and three-contrast Holm-corrected p-values must include
unfavorable and inconclusive outcomes. No scientific endpoint or budget is frozen.
