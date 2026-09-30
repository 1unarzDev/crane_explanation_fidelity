# Blind development review of continuation A — 2026-09-30

## Scope

All 44 continuation A answers and their 402 atomic stance/kind/polarity judgments were reviewed
against the unchanged v2r2 role codebook using blind answer/inventory text and retained returns.
No method key, robot evidence packet, support label, or evaluator truth was opened. This is
agent-assisted project review, not support annotation or independent human validation. Together
with the original-prefix review it covers 113 known A answers and 1,071 A judgments. The original
unknown A request covers the other 13 inventory atoms and remains quarantined without replacement.
The still-running B pass is outside this fixed review snapshot.

## Findings and prospective treatment

- **A concrete polarity error:** `ax-c1d98a11f06df96b8a782cfc7873b542`,
  `ri-3f586b8d2413f5a65792`, states “The recorded navigation action aborted.” Its return is
  `ASSERTED_FACT` / `TASK_OUTCOME` / `NEGATIVE`. Under the qualified codebook, polarity follows
  the normalized occurrence proposition: this asserts that the abort occurred. The negative tag
  conflicts with that rule. Preserve the raw return for later disposition; this review does not
  replace it with a corrected tuple or count it as a scientific endpoint failure.

- **Outcome-kind variance continues:** explicit NavigateToPose success/abort receives both
  outcome and software-event tags, including software-event tags for the success assertion in
  `ax-c31d4b61d1cea7b138f58f2e25daa27e` and the abort assertion in
  `ax-b7c675effc18c4a5f7624a6f10149946`. Claim meaning and scope must determine attachment;
  blanket elevation of software-event kinds would create artificial diagnostic depth.

- **Question-dependent affirmative scope remains open:** the normalized bare `Yes.` atoms in
  `ax-e45bb092d71d1f5ef9cc0162cff7110c` and `ax-f64508c4a53502524cf470b9e9ed61d1` affirm
  “a navigation failure occurred in the successful episode,” but receive outcome versus software
  event kinds. Their surrounding answers distinguish local FollowPath failures from the overall
  successful goal. Retain the question-bound inventory provenance and literal affirmative text;
  resolve scope under a prospective rule before false-premise or endpoint interpretation. Do
  not blanket-score `Yes.` or silently substitute a narrower proposition.

- **Software resolution is not automatically a physical causal diagnosis:**
  `ax-d80abe3b7d2b0fffa2717ca37ba4aff7`, `ri-575b4e553218fcc94228`, says the configured
  Wait/retry sequence “handled” the FollowPath execution failure and receives
  `RECOVERY_CAUSAL_RELATION`. Preserve the asserted relationship. Its software-resolution scope
  needs explicit attachment before applying evidence requirements for claims that recovery caused
  measured motion or task outcome. The broad kind alone does not settle that mapping.

- **Three additional explicit negative-causation assertions remain assertions:** the unchanged
  measured-response rationale supplies atoms in `ax-dcd3f68016654f68660b5583e5d92ac3`,
  `ax-e5216e37edea88f7ef5a5d45f569e390`, and `ax-f6219b0719b5e82031b1b026a438de90` asserting
  that measured response recovery did not cause the eventual outcome. Their
  `ASSERTED_FACT` / `RECOVERY_CAUSAL_RELATION` / `NEGATIVE` returns correctly distinguish that
  assertion from non-establishment. Combined with the original prefix, all six old assertions
  remain visible. Future wording repairs do not rescore or rewrite these answers.

- **Other earlier limitations persist:** command validity varies between command and source/config
  kinds; numerical intervals vary between source/config and other kinds; literal “these specific
  physical causes” limitations lack supplied antecedents. Episode trace contents and configured
  policy still require claim-specific support. No source-kind exemption, supplied cause antecedent,
  or blanket numerical rank follows from these tags.

## Boundary

This application review exposes concerns within retained development returns; it does not regrade
the frozen synthetic qualification. It supplies no corrected roles, support labels, mechanism
flags, ranks, paired effects, or p-values. Complete B review, disagreement disposition, missing-A
treatment, and assertion-aware contract attachment remain open. The neutral-input support
qualification is separately declared and does not supply endpoint rank. P11 remains closed;
confirmation and replication independent N remain zero.
