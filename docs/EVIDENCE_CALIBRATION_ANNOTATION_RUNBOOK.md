# Evidence-calibration annotation runbook

Status: **qualified agent-assessed workflow for prospective uncollected annotations**.

The original human-oriented workflow below is preserved as historical design context. Prospective
uncollected evidence-calibration annotations now use two isolated `gpt-6-astra` passes and a
distinct disagreement-only agent under the hash-bound v4 disposition in
`manifests/study/evidence-calibration-agent-qualification-disposition-v1.json`. Results must be
called **agent-assessed**, never human annotations or human validation. Deterministic checks remain
authoritative for quantities, hashes, identities, intervals, thresholds, and endpoint derivation.

Qualification history is cumulative and immutable: v1 failed with HTTP 403 before inference; v2
failed provider schema validation before inference; v3 was invalidated after a geometry
false-premise gold defect was exposed; v4 completed 40 calls over two isolated passes and passed
every prospectively declared held-out gate. None of these calls adds independent episode N.

This runbook applies only to the prospective evidence-calibration study. It does not rescore the
legacy provenance cohort, the closed focused campaign, or any Luna output. Automated judgments are
secondary sensitivity analyses and are never called human annotations.

## Roles and isolation

- Two different people independently complete slots A and B. They must not communicate about a
  packet before returning their forms.
- A third person adjudicates disagreements only. Neither original annotator may adjudicate that
  packet.
- Method identity, registered claim identity, episode/configuration identity, prior labels, and the
  evaluator join key remain unavailable until independent returns and disagreement adjudication are
  complete.
- One packet condition, question, mask, or claim is not an independent sample. Statistical N is
  restored from the separate key only after adjudication and remains the episode/configuration.

## Claim labels

Assign exactly one label to every opaque atomic statement and cite the exact response span in the
provided notes where useful:

- `SUPPORTED_BY_VISIBLE_EVIDENCE`: the permitted robot-visible evidence supports the statement at
  its asserted scope.
- `CONTRADICTED_BY_VISIBLE_EVIDENCE`: permitted evidence establishes that the statement is false.
- `INSUFFICIENT_VISIBLE_EVIDENCE`: the visible evidence neither supports nor contradicts the
  statement at its asserted specificity.
- `PHYSICALLY_TRUE_BUT_UNSUPPORTED`: the sanitized evaluator view establishes physical truth, but
  the robot-visible evidence does not license the statement. Never infer this label merely because
  a claim sounds plausible.
- `UNINTERPRETABLE`: the statement cannot be assigned a stable proposition or evidential scope.
  This is unresolved measurement, not a convenient substitute for insufficient evidence.

Evaluate support against the packet actually supplied. Absence from a compact inventory is not
evidence of unsupportedness if the underlying permitted packet contains the fact. Conversely,
physical truth does not repair missing robot-visible support.

## Other required fields

For every required diagnostic unit, mark whether it is communicated and copy an exact response
span when true. Select the highest abstraction level actually asserted, not the level the answer
should have asserted. Score each required limitation independently and provide its exact span when
preserved. On applicable nominal/success questions, distinguish explicit false-premise rejection
from acceptance, partial/ambiguous handling, and uninterpretable handling.

Every completed return must use schema
`research/explanation_fidelity/schemas/blinded-atomic-annotation-return-v1.schema.json`, retain its
assigned A or B slot, name a nonempty annotator ID, and attest
`INDEPENDENT_BLINDED_COMPLETE`.

## Agreement and adjudication

Do not open the evaluator join key. Validate and compare the two returned forms:

```bash
python analysis/adjudicate_evidence_calibration_annotations.py \
  --packet-set /path/to/packet-set.json \
  --annotator-a /path/to/annotator-a.json \
  --annotator-b /path/to/annotator-b.json \
  --agreement-output /path/to/agreement.json \
  --handoff-output /path/to/adjudicator-handoff.json
```

The agreement report preserves both independent decisions and reports raw claim-label agreement
and Cohen's kappa where defined. Agreement is measurement repeatability, not method effectiveness.
Send the third person only the original blinded packet and the disagreement-only handoff. The
handoff excludes annotator identities, agreed decisions, method identity, and the condition key.

The adjudicator returns one decision for every disagreement ID, selects one of the two independently
supplied values, provides a rationale, and attests
`DISAGREEMENT_ONLY_BLINDED_COMPLETE`. Finalize with `--adjudication` and `--final-output`. The
validator rejects missing or extra disagreements, self-adjudication, invented third values, absent
rationales, hash mismatches, and premature key joining.

Only after every packet is final may a separate coordinator join the evaluator key and method
identity. No comparative dashboard or effect estimate may be shown to annotators or the adjudicator.

## Dry-run acceptance gate

Before P11, use development packets to demonstrate:

1. two genuinely different people can complete all fields without seeing method identity;
2. the validator rejects incomplete returns and the same person in both slots;
3. a distinct third person receives only disagreements and completes them without the key;
4. original returns, disagreement records, rationales, and final values remain hash-audited; and
5. the key remains unopened until the dry run is finalized.

Passing this operational dry run does not create confirmation N, select a method, or validate the
annotation construct against humans generally. It only qualifies the workflow for prospective use.
