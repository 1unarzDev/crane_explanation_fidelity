# Luna required-unit status taxonomy

Version: `required-unit-status-v1`

Declared: 2026-09-24

Scope: automated judge development and qualification only. This does not modify legacy human
annotation forms or score any study response.

## Purpose

The v2 and v3 development runs exposed an inconsistent reference distinction between `omitted` and
`incorrect` for required limitations. Exact required-unit status is a qualification gate, so the
reference rule must be coherent before held-out judging. This rule is based on proposition-slot
semantics, not on which prompt output happens to pass.

## Status rules

- `covered`: the final answer correctly communicates the required proposition or a meaning-
  preserving paraphrase.
- `incorrect`: the final answer attempts the same proposition slot but gives a materially wrong
  value, identity, comparison, sequence, scope, polarity, or qualification. Explicitly asserting a
  unique cause attempts and contradicts a required “cause remains unresolved” proposition.
- `omitted`: the final answer does not attempt or communicate the required proposition slot. A
  response may still contain a separate material error; that unrelated error does not make an
  unattempted unit `incorrect`.
- `unresolved`: only packet inconsistency, missing decisive evaluation material, or genuine judge
  uncertainty prevents assigning one of the other statuses.

Material-error classification is separate. An omitted unit can coexist with a material error, and
an incorrect unit does not automatically determine the response-level materiality category without
the rubric.

## Development-reference audit

Applying the rule to the two exposed limitation cases:

- QD003 requires that the physical cause remains unresolved. “The scan return caused Nav2 to
  invoke recovery” explicitly fills the physical-cause slot with a unique causal explanation. The
  limitation unit is `incorrect`.
- QD011 requires that unique cause remains unresolved. “A failed left motor caused it” explicitly
  fills the same cause-identity slot. The limitation unit is `incorrect`.

The base development suite labeled QD003 `omitted` and QD011 `incorrect`; those labels cannot both
follow one rule. The additive suite amendment changes QD003 to `incorrect` and leaves QD011
unchanged. No held-out expected label is changed, opened for model judging, or selected based on a
held-out outcome.

V2 medium's retained QD003 judgment used `incorrect`; v3 used `omitted`. Offline rescoring under
this taxonomy may select a development configuration, but only a subsequently frozen configuration
that passes the untouched held-out split may score study responses.
