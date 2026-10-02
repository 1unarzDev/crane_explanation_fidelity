# Realizer finite-number repair — 2026-09-30

Inspection of the existing realization seam found a numeric-audit defect: `abs(NaN - expected)
> tolerance` is false. With an otherwise complete synthetic candidate, v1 accepts a supplied
`NaN`, reports `ACCEPTED` and lists no numeric mismatch. It renders the approved value rather
than the candidate's `NaN`, so this reproduction demonstrates an audit-detection defect, not an
unsupported final-response number. No retained model return is claimed to contain this defect.
The reproduction supplies a Python floating-point value in memory; `NaN` is not a valid standard
JSON number and no provider or model invocation was used.

The separate v2 development implementation preserves v1 byte-for-byte and changes only the
version identifier, one `math` import and a finite-float check at the existing numeric-verification
seam. It uses the same ontology, plan, candidate/output schemas, approved numbers, tolerance rules
and local repair machinery. A nonfinite candidate value invalidates its clause, records the
numeric mismatch and reconstructs the affected required claim. Independent supported outcome
and limitation clauses remain present. A nonfinite approved plan value is still rejected before
realization. Valid finite candidates have identical outputs apart from the version identifier.

Six focused tests retain the v1 synthetic failure, check NaN and both infinities, preserve
independent clauses, compare valid finite outputs and reject an invalid approved plan. Together
with two integrity checks and the four existing realization tests, twelve checks pass. The read-only diff audit binds the
sources and verifies exactly these three changes. This is deterministic development regression
evidence, with no semantic accuracy claim or independent experimental N.

The new realizer is a prospective candidate. Existing callers, old pipeline outputs, immutable
caches and the aligned five-method packet snapshot still refer to their retained state. A future
execution declaration must explicitly bind its realizer version and exercise the chosen version.
No historical output is rewritten or rescored, no method/annotation call is authorized, and the
failed combined support gate remains unchanged. P11, alpha and physical-allocation boundaries
remain open; no comparative effect or manuscript result follows from the repair.

The B3/B4 execution seam also remains unresolved: the protocol specifies ordinary language
realization for B3 and constrained realization plus verification for B4, while the current
executable realizer compiles claim IDs to registered text. A verification flag in a packet does
not implement B3 or prove that only final verification differs. Future execution design must
explicitly bind the realization paths and report the actual scope of that ablation, preserving
this older protocol rather than silently replacing it with a shared-candidate experiment.

Reproduce integrity with `python analysis/audit_claim_aware_realization_v2.py` and the regression
checks with `python -m pytest -q tests/test_claim_aware_realization_v2.py tests/test_claim_aware_realization.py`.
