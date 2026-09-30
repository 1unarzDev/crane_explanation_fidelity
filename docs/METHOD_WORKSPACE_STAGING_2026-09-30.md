# Offline method workspace staging — 2026-09-30

`analysis/stage_evidence_calibration_workspace.py` stages the existing five-method source packets
in temporary directories. It adds no caller, execution declaration or model authorization.
B0/B1 directories are empty: their separately versioned requests supply inline evidence.
B2/B3/B4 receive identical robot-visible evidence, exact source/configuration bytes and the
existing primitive inventory tool. B3/B4 additionally receive the public v2 contract asset.
No approved diagnosis or evaluator reference is copied into B2's workspace.

## Checks and identity

Before writing, the helper checks the condition's robot-visible certification, evidence hash,
method packet hash, episode/condition/evidence-basis identity, question, source presentation,
asset inventory, versions and actual source hashes. Asset IDs resolve through a fixed registry;
unknown IDs, missing/duplicate assets, wrong categories and source symlinks are rejected.
There are no caller-supplied source or destination paths. Temporary directories are always cleaned.

The B2 filenames and evidence serialization match the retained legacy runner. Old runners,
packets, caches and outputs are unchanged. Workspace identity binds method/condition/source-packet
identity and exact file hashes/directories without random temporary paths. Inventory checks run
before yielding and on context exit; callers can also invoke `verify` immediately before/after
future calls. Changed/added files, extra directories, symlinks and special files fail checks.
These checks detect final inventory changes, not transient reads or modifications later restored.

## Remaining execution boundaries

File staging is **not harness confinement**. It does not prevent a process from reading the original
repository, accessing evaluator files elsewhere, using undeclared tools or making network calls.
Permissions/tool/network isolation and permitted primitive computations must be bound and checked
in a separate enclosing runner before execution. Do not infer confinement from a read-only cwd.
The legacy B2 primitive tool still runs from the staged paths; its original capabilities are
preserved. Staging does not finalize the complete B2 computation/tool surface.

Actual-route capacity/tokenizer and full prompt/harness/output budgets remain unresolved. The failed
combined support canary remains binding, C remains unlaunched, and real pilot annotation is closed.
Semantic attachment/rank measurement, fresh aligned B0–B4 outputs, coverage and episode discordances
remain open. All B0/B1/B3 comparisons with B4, episode effects/intervals and corrected p-values,
including inconclusive/unfavorable results, remain required. This helper contributes no independent
sample, observed effect, alpha allocation, fresh layout or P11 authorization.

## Verification

Fifteen focused tests cover method parity and stable identity, technical input rejection,
post-stage tampering and cleanup, source symlink rejection, packet/condition binding and actual
execution of the staged primitive tool. The latter is deterministic and invokes no model.
