# Blinded dual-annotation workflow

Operational companion to `docs/ANNOTATION_GUIDE.md`. The guide is hash-frozen and states *what* to
label; this file states *how* to run the process with the committed tooling, and is not frozen.

Nothing here changes a rubric. If the two disagree, the guide governs.

## Order of operations

1. **Package.** Build one blinded packet per arm, plus its evaluator-only key.
2. **Annotate.** Two annotators label every response in the packet, independently, without
   discussing labels until both passes are complete.
3. **Check agreement.** Run the adjudicator without `--adjudication` to get raw agreement, Cohen's
   kappa, and the list of disagreements. This step joins no condition key.
4. **Adjudicate.** A third annotator labels only the disagreements, using the guide and the same
   allowed evidence.
5. **Finalize.** Re-run with `--adjudication`. A final label set is emitted only when every
   disagreement is resolved.
6. **Only then** join the evaluator-only key and score by condition.

## 1. Package

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src:analysis \
python analysis/build_blinded_annotation_packet.py \
  --arm primary=model_outputs/final \
  --packet model_outputs/annotation_packets/sealed-primary-v2/packet.jsonl \
  --key data/evaluator_only/annotation_keys/sealed-primary-v2.json
```

Each packet row carries only `response_id`, `question`, `question_kind`, `gold_unit_inventory`,
`answerable_units_total`, `allowed_evidence`, and `response_text`. Condition-revealing fields are
dropped, not reordered: a G output's `checked_plan`, `verification_accepted`,
`unsupported_sentences` and `used_template_fallback`, and an F/H output's `disposition:
uncontrolled`, never reach the annotator. The builder re-checks this after writing and deletes the
packet if anything leaked.

Response IDs are HMACs under a per-packet secret, and rows are shuffled with a seed derived from
that secret, so neither the ID nor the packet order encodes arm, condition, episode, or question.

**Build one packet per arm whenever response format can reveal the provider or harness.** Pooling is
supported and the key keeps arms separable, but it does not create independent observations. In the
current Claude-family development outputs, models often serialize JSON into the answer string where
the primary arm wrote prose. A pooled packet would therefore identify the arm at a glance and
defeat the blinding.

The key is evaluator-only. It holds the secret, the arm, episode, condition, and model for every
response, and it never goes to an annotator.

## 2. Annotate

Before either annotator opens `sealed-primary-v3`, both independently label the same six-response
development calibration packet, then discuss disagreements using the frozen guide and permitted
evidence:

```bash
python analysis/build_legacy_annotation_form.py \
  --packet model_outputs/annotation_packets/legacy-calibration-e043-v1/packet.jsonl \
  --output /tmp/legacy-calibration-e043-v1-annotator-a.jsonl \
  --annotator-id annotator-a
```

Repeat for annotator B. Use `analysis/adjudicate_annotations.py` to identify disagreements, but do
not describe this exercise as independent study evidence. The six responses are retained F/G/H
outputs for the development-only `land-nav-20260919-e043` episode (two question kinds, one episode
cluster), not a sample from any sealed split. Its evaluator-only key may be revealed only after
both independent calibration passes, for discussion; the older project-author development notes
are training context, not an adjudicated gold standard. Record completion and substantive rubric
clarifications before either annotator begins the sealed packet.

Each annotator writes one JSONL file, one row per packet response, with the 25 fields
`docs/ANNOTATION_GUIDE.md` requires. Every row in a pass carries the same `annotator_id`, and the
two passes must use different ones.

Generate a blank form directly from the final packet so no annotator has to invent or copy hidden
metadata:

```bash
python analysis/build_legacy_annotation_form.py \
  --packet model_outputs/annotation_packets/sealed-primary-v3/packet.jsonl \
  --output /tmp/sealed-primary-v3-annotator-a.jsonl \
  --annotator-id annotator-a
```

The frozen guide lists `episode_id`, `scenario_family`, and `condition_blinded_id` in the row
schema, but the sealed packet intentionally withholds the first two and exposes no condition. They
are not human judgments. The form therefore writes the explicit
`BLINDED_PENDING_KEY_JOIN` sentinel for the first two and uses the opaque `response_id` as the
condition-blinded identifier. True grouping and condition metadata are joined only after complete
adjudication. This operational clarification changes no question, unit inventory, rubric, label,
packet, key, or analysis rule.

Flag `evidence_problem` rather than guessing when the gold inventory, allowed packet, or question
looks inconsistent. Such responses are quarantined at the whole-episode level; condition-specific
exclusion is forbidden.

## 3–5. Agreement, adjudication, finalization

```bash
# agreement; final labels are emitted only if the two passes fully agree
PYTHONPATH=packages/astro_dock/src/crane_explain/src:analysis \
python analysis/adjudicate_annotations.py \
  --packet model_outputs/annotation_packets/sealed-primary-v3/packet.jsonl \
  --annotator-a <a>.jsonl --annotator-b <b>.jsonl \
  --output analysis/results/sealed-primary-v3-agreement.json

# after a third annotator labels the disagreements
... --adjudication <c>.jsonl --output analysis/results/sealed-primary-v3-adjudicated.json
```

The tool refuses a pass that is incomplete, annotates a response outside the packet, uses two
`annotator_id`s, repeats a `response_id`, records `material_error` without a category or a category
without `material_error`, contradicts its own `disposition` with `substantive_answer`, claims more
correct units than the inventory holds, or leaves an empty rationale. It also refuses an
adjudication file that covers responses the annotators agreed on, or one whose annotator is not a
distinct third person.

Reported: raw agreement and Cohen's kappa for `material_error`, `substantive_answer` and
`correct_abstention`, plus agreement on `disposition` and `answerable_units_correct`. Kappa is
reported as `null`, not as a number, when a rater used a single category throughout and it is
undefined.

When disagreements exist, `status` stays `AWAITING_ADJUDICATION` and `labels` stays `null` until
every disagreement is resolved. If the two complete passes agree, no unnecessary third pass is
required. `condition_key_joined` is always `false` in this tool's output; joining the key is a
separate, deliberate step.

After `status` is `COMPLETE`, join the sealed key and frozen scenario-family mapping exactly once:

```bash
python analysis/join_legacy_annotation_key.py \
  --adjudication analysis/results/sealed-primary-v3-adjudicated.json \
  --key data/evaluator_only/annotation_keys/sealed-primary-v3.json \
  --split research/explanation_fidelity/dataset_splits/provenance-final-v1.json \
  --output analysis/results/sealed-primary-v3-analysis-input.jsonl \
  --report analysis/results/sealed-primary-v3-key-join.json
```

The join verifies the packet hash and complete response inventory, restores episode, scenario,
condition, arm, and model metadata from governed sources, and applies the predeclared
whole-episode quarantine when either annotator flagged an evidence problem. Its JSONL output is
the input to `analysis/analyze_provenance_study.py`. It refuses incomplete adjudication,
pre-exposed grouping metadata, mismatched IDs, and packet/key hash mismatch.

## Current state

- Legacy collection was prospectively closed early at 33 included episodes by
  `manifests/study/research-redirect-20260922.json`; this is below the frozen 40-episode minimum.
  The final primary packet/key pair is `sealed-primary-v3`: 198 F/G/H responses over all 33
  retained episodes. Its content hashes are tracked in
  `manifests/annotation/sealed-primary-v3.json`. This pair supersedes prior primary packet
  snapshots for annotation, without deleting them or altering any frozen response.
- A fresh primary pair is retained at `sealed-primary-v2`: 126 model-condition responses covering
  the first 21 included primary episodes, with its matching key physically under
  `data/evaluator_only/annotation_keys/`. It predates the 36 responses from `pn-0022`–`pn-0027` and is a
  packaging/recovery snapshot, not the final analysis packet. The historical `sealed-luna-v1`
  pair is retained only for audit and covers nine episodes; do not use either historical snapshot
  for the full-arm analysis.
- The selected Claude-family sealed replication is **collected**: 18 envelopes and 54 model-condition
  responses over `pn-0001`–`pn-0009`. Its fresh `sealed-claude-v2` packet/key pair is retained
  separately because the Claude response format can reveal the provider and harness. The original
  `sealed-claude-v1` packet is unusable because its key was never uploaded and cannot be restored;
  never reconstruct that key. Note that 16 of 18 G responses use the deterministic checked
  template; byte-identical G text across arms must receive identical labels.
- **Annotation itself is `NOT_RUN`.** No primary-arm sealed response has been scored, no
  adjudication exists, and no sealed effect estimate exists. Two independent annotators must use
  only the `sealed-primary-v3` packet; neither receives its evaluator-only key.
- The development model-strength controls are separate: unblinded, single-annotator, and
  development-only by design. They are not part of this workflow and must not be reported as if
  they were.

## Prospective diagnostic-study dry run

The physical-diagnosis study uses the separate draft rubric in
`docs/DIAGNOSTIC_ANNOTATION_GUIDE.md`. It does not alter or reuse the frozen legacy rubric. Build
the current four-response development packet and its evaluator-only key with:

```bash
python analysis/build_diagnostic_annotation_packet.py \
  --result model_outputs/dev/diagnostic-land-pilot-v3/land-blockage-global-002/mechanism-and-outcome.json \
  --reference research/explanation_fidelity/annotations/development/diagnostic-land-pilot-v3-reference.json \
  --packet model_outputs/annotation_packets/diagnostic-land-pilot-v3/packet.jsonl \
  --key data/evaluator_only/annotation_keys/diagnostic-land-pilot-v3.json
```

This is a development workflow check, not a sealed packet or effectiveness evaluation. The
reference explicitly records that its geometric computation is not independent. Two real human
annotators and a third adjudicator for disagreements are still required. Do not join the key,
inspect condition identities during scoring, or describe project-author qualitative review as
blinded annotation.

The matched missing-cell packet is built separately so its evidence-sufficiency inventory remains
explicit:

```bash
python analysis/build_diagnostic_annotation_packet.py \
  --result model_outputs/dev/diagnostic-land-mask-pilot-v1/land-blockage-global-002-mask-no-costmap-cells/mechanism-and-outcome.json \
  --reference research/explanation_fidelity/annotations/development/diagnostic-land-mask-pilot-v1-reference.json \
  --packet model_outputs/annotation_packets/diagnostic-land-mask-pilot-v1/packet.jsonl \
  --key data/evaluator_only/annotation_keys/diagnostic-land-mask-pilot-v1.json
```

Annotate both four-row packets under the same draft rubric, but do not count the evidence mask as
another episode. Both belong to statistical cluster `land-blockage-global-002`. The masked packet
contains the retained pre-correction outputs; the post-hoc deterministic correction is not mixed
into this dry run.

Validate each pair and compute agreement without joining the evaluator-only key:

```bash
python analysis/adjudicate_diagnostic_annotations.py \
  --packet model_outputs/annotation_packets/diagnostic-land-pilot-v3/packet.jsonl \
  --annotator-a <annotator-a.jsonl> \
  --annotator-b <annotator-b.jsonl> \
  --output analysis/results/diagnostic-land-pilot-v3-agreement.json
```

If disagreements exist, a distinct third annotator supplies rows only for those response IDs and
the same command adds `--adjudication <third-pass.jsonl>`. The tool rejects incomplete passes,
unknown responses/categories, wrong unit inventories, inconsistent material-error fields,
supported-success labels paired with a material error or incorrect mechanism, and a reused
annotator identity. `condition_key_joined` remains false even after adjudication; scoring by
condition is a later deliberate step.

Two boat packets, four additional land packets, and the paired command-motion packets are also
retained:

- `model_outputs/annotation_packets/diagnostic-boat-terminal-margin-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-boat-terminal-margin-masked-speed-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-land-s-turn-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-land-nominal-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-land-prospective-nominal-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-recovery-sequence-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-command-motion-supported-pilot-v1/packet.jsonl`
- `model_outputs/annotation_packets/diagnostic-command-motion-nominal-pilot-v1/packet.jsonl`

Their keys remain under matching directories in `data/evaluator_only/annotation_keys/`. Annotate
all ten diagnostic packets, but count only seven episode clusters: `land-blockage-global-002`,
`land-s-turn-unexpected-abort-001`, `land-unexpected-nominal-001`,
`diagnostic-land-nominal-20260922-001`, `eco-pilot-001`, and
`roboboat-gate5-known-dock-1`, plus `command-motion-held-nominal-pair-001`. The boat speed mask
retains the pre-correction P/T omission; the post-hoc v2 deterministic answer is not substituted.
The two command-motion packets also preserve their original P fallback rather than substituting
the post-hoc verifier-accepted raw candidates.
Separate evaluator-side reference calculations reproduce the bounded boat and land findings
without importing the proposed method, but they are still development code and do not replace the
required human review.

After all ten packets have complete adjudication outputs, join their condition keys with the
explicit development cluster inventory:

```bash
python analysis/join_diagnostic_annotation_keys.py \
  --inventory manifests/annotation/diagnostic-development-pilot-v1.json \
  --adjudication land-unmasked=analysis/results/diagnostic-land-pilot-v3-adjudicated.json \
  --adjudication land-missing-costmap-cells=analysis/results/diagnostic-land-mask-pilot-v1-adjudicated.json \
  --adjudication boat-unmasked=analysis/results/diagnostic-boat-terminal-margin-pilot-v1-adjudicated.json \
  --adjudication boat-missing-return-speed=analysis/results/diagnostic-boat-terminal-margin-masked-speed-pilot-v1-adjudicated.json \
  --adjudication land-s-turn-unmasked=analysis/results/diagnostic-land-s-turn-pilot-v1-adjudicated.json \
  --adjudication land-nominal-false-premise=analysis/results/diagnostic-land-nominal-pilot-v1-adjudicated.json \
  --adjudication land-prospective-nominal-false-premise=analysis/results/diagnostic-land-prospective-nominal-pilot-v1-adjudicated.json \
  --adjudication warehouse-recovery-sequence=analysis/results/diagnostic-recovery-sequence-pilot-v1-adjudicated.json \
  --adjudication command-motion-supported=analysis/results/diagnostic-command-motion-supported-pilot-v1-adjudicated.json \
  --adjudication command-motion-nominal=analysis/results/diagnostic-command-motion-nominal-pilot-v1-adjudicated.json \
  --output analysis/results/diagnostic-development-pilot-v1-analysis-input.jsonl \
  --report analysis/results/diagnostic-development-pilot-v1-key-join.json
```

The join verifies every packet and key hash, restores method/fallback/verification metadata only
after adjudication, and maps both evidence variants back to their source statistical cluster. Any
`evidence_problem` flag quarantines the entire source cluster across masked and unmasked packets.
The resulting 40 responses still represent only seven development clusters and cannot support a
confirmatory effect claim or a reliable new-study power estimate by themselves.

Once the joined file exists, generate the deliberately descriptive development summary with:

```bash
python analysis/summarize_diagnostic_development.py \
  analysis/results/diagnostic-development-pilot-v1-analysis-input.jsonl \
  --output analysis/results/diagnostic-development-pilot-v1-summary.json
```

This reports R/P/T/N response metrics, fallback frequency, and paired cluster-mean differences,
but intentionally emits no confidence interval, significance test, or power estimate. Those would
be unstable with seven clusters. The summary is an input to the prospective freeze decision, not a
substitute for additional independent pilots or a frozen held-out analysis.

### Generate blank diagnostic annotation forms

Give each annotator the diagnostic guide, the ten packet files above, and a separately generated
blank form. The form generator reads only a blinded packet—never its evaluator-only key—and emits
only opaque response IDs, a prefilled `required_units_total`, and explicitly unset rubric fields.
For example:

```bash
python analysis/build_diagnostic_annotation_form.py \
  --packet model_outputs/annotation_packets/diagnostic-land-pilot-v3/packet.jsonl \
  --output /tmp/diagnostic-land-pilot-v3-annotator-a.jsonl \
  --annotator-id annotator-a
```

Repeat for each of the ten packets and each annotator, using a distinct non-identifying
`annotator_id`. Annotators review packet rows in order and replace every `null` judgment in their
matching form; `required_units_total` is already derived from the packet and must not be changed.
Do not provide files under `data/evaluator_only/`, model/condition mappings, fallback status, or
verification outcomes. The generator refuses non-opaque or duplicate response IDs, malformed unit
inventories, overwrites, and evaluator-only output paths. Completed forms are inputs to
`analysis/adjudicate_diagnostic_annotations.py` as shown above.

Prepared local bundles containing the two legacy packets and all ten diagnostic packets are at
`artifacts/annotation-handoff-20260922/annotator-{a,b}.tar.gz`. Each has 12 packets and 244 blank
form rows. These ignored archives are convenience handoffs, not labels or governed results; verify
their current hashes against `artifacts/annotation-handoff-20260922/SHA256SUMS` before transfer.
