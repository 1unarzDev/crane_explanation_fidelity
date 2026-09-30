# Uncalled neutral-level support candidate — 2026-09-30

## Problem and bounded change

The qualified v4 support task received supplied per-atom abstraction strings. The inspected-pilot
extractor's abstraction strings are not qualified for support anchoring or endpoint scoring, and
the qualified v2r2 role task provides only stance, kind, and polarity. The blind prefix review
also shows why broad kind tags cannot supply unique evidence requirements or ranks.

The candidate supplies `null` for every atomic `asserted_abstraction_level`. It retains the
qualified Astra-high model, no-tool transport, annotation prompt, and v2 return/adjudication
schemas. Exact answer text remains available. The candidate has not changed the existing
qualified disposition, packet builder, study outputs, role requests, caches, or contracts.

This is a new input qualification question: can the support task evaluate the five support
categories and communication fields without a supplied level anchor? It is not another attempt
to promote a failed v4 annotator. The old v4 qualification and its final-cycle boundary remain
preserved. A passing extension would not qualify response rank or the endpoint map.

## Construction and offline checks

`analysis/build_evidence_calibration_neutral_level_suite.py` builds 20 new synthetic cases:
four development cases and sixteen candidate held-out cases. No study output or evaluator key
was used to construct references. The cases exercise all five labels, explicit record
attribution, policy versus episode occurrence, command-field presence versus actual delivery,
missing odometry, measured recovery versus software recovery, useful partial coverage, explicit
negative causation versus non-establishment, negative physical-cause assertions, nominal
non-trigger/false-premise handling, literal unresolved deixis, numerical contradiction, and two
prompt-injection cases. Each case contains a construction reference note.

The companion offline helpers validate return identities and exact positive spans before scoring
the four reference fields. The raw `highest_asserted_abstraction_level` remains structurally
required and retained under the unchanged schema, but has no reference rank and contributes no
qualification credit or endpoint score. Tests show that changing this field between permitted
values cannot change the support score. They also check that an unsupported measured-recovery
claim does not erase supported event coverage, and that invented spans are rejected. These tests
verify mechanical behavior with synthetic returns; they provide no model accuracy evidence.

The sixteen cases are held out from the candidate model, not from their authors. Before model
execution, review every reference and packet against the unchanged prompt, check complete
answer/span coverage and task parity, and bind that construction disposition. If reference
ambiguity is found, version the repair before calls. Preserve any later observed error.

## Gates before use

1. Complete and bind reference review, including support/coverage independence and the intended
   treatment of unsupported negative findings and literal unresolved limitations.
2. Declare a separate synthetic input-extension qualification with exact hashes, held-out gates,
   two isolated passes, durable intents, a separate output root, and stop-on-first-failure/no-retry
   execution. Do not use the old runner's raw-rank accuracy as a support gate.
3. Pass transport preflight and a separate non-study schema canary before qualification calls.
4. Retain all raw returns and failures, score the declared fields on each isolated pass, and
   adjudicate qualification disposition. A failed extension cannot be silently replaced or used.
5. Only a passing, hash-bound prospective payload amendment may authorize neutral-level pilot
   support forms. The current packet builder's v4 metadata is not evidence that this new input
   was qualified.

Real-pilot support annotation still requires two isolated blinded passes and a distinct
disagreement-only adjudication invocation. Preserve raw rank disagreements as measurement records;
no adjudicated raw highest-level field directly determines endpoint rank. Whole-bank role review,
the quarantined missing-A disposition, contract attachment, asserted/hedged/negative/unresolved
endpoint treatment, and whole-episode sensitivity remain separate prerequisites for interpreting
the pilot. Fresh aligned B0–B4 development evidence is still required before P11.

No qualification model call, pilot support label, endpoint score, P11 freeze, physical allocation,
or alpha expenditure is authorized by this candidate. Confirmation and replication independent N
remain zero.
