# B4 candidate request and return interface — 2026-09-30

The new pure helper `analysis/prepare_evidence_calibration_b4_candidate.py` prepares a structured
candidate request for the existing claim-aware v2 realizer. It adds no provider call, caller,
execution declaration, retry, annotation or study activation.

## Preparation and return

Preparation reuses the frozen B3 helper's shared evidence/facts/plan and five-method parity checks
without executing B3. It derives the same diagnostic result, binds the complete plan and selected
propositions/limitations, and asks for ordered claim/non-entailment clauses with exact numeric slots.
Request identity binds evidence, packet set, ontology, facts, result, plan, prompt template and
selected realizer version. The response ID is deterministic for the condition and plan.

The output schema closes the candidate/clauses/numeric objects, binds response and plan identities,
and excludes a free-prose channel. Contract IDs remain strings: unsupported contract selections
must reach the existing verifier rather than disappear through an approved-ID-only schema.
A structurally valid empty clause list also reaches verification, exposing full reconstruction.

Return processing recomputes the exact request from supplied inputs, checks successful technical
status and prompt/schema identity, retains the raw record hash and unchanged parsed candidate,
and invokes the unchanged v2 realizer once. Wrong finite quantities, unsupported IDs and omissions
remain visible in the candidate and deterministic audit. No semantic quality retry or response
selection is implemented. Transport, duplicate JSON keys, raw/parsed inconsistencies, wrong
identities, extra prose fields and invalid numeric structures stop compilation. The enclosing
caller must durably retain every raw/failed record before invoking the helper; rejection here
neither rewrites that record nor invents a replacement candidate.

## Scientific limits

This is constrained selection/order plus deterministic template realization, not unrestricted
prose generation or an empirical demonstration of semantic verification. B3's ordinary prose
path versus this B4 path combines realization and verification differences; it does not identify
a pure verifier causal effect. Model effort/cost, tool permissions, source access, capacity and
full harness overhead must be prospectively bound in an enclosing runner. Shared-input reuse
also binds the B3 preparation helper and prompt as dependencies, although no B3 model call runs.

The failed combined support canary remains binding and C remains unlaunched. No current pilot
answer is interpreted or scored. Fresh aligned B0–B4 development outputs, qualified claim/rank
measurement, episode discordances, coverage and power remain open. P11 remains closed; alpha,
physical quarantine and confirmation/replication independent N remain unchanged. All prospective
B0/B1/B3 comparisons against B4 and their corrected episode-level reporting remain required.

## Verification

Fourteen synthetic checks verify complete candidate acceptance and exact v2 output equivalence,
local repair with candidate preservation, technical/identity/structural rejection, stable requests,
plan/limitation binding, duplicate raw JSON rejection and Boolean-number rejection. Eleven existing
B3 and eight v2 realizer checks also pass. No model invocation or retained pilot rescore is involved.
