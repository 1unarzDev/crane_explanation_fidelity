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

Each annotator writes one JSONL file, one row per packet response, with the 25 fields
`docs/ANNOTATION_GUIDE.md` requires. Every row in a pass carries the same `annotator_id`, and the
two passes must use different ones.

Flag `evidence_problem` rather than guessing when the gold inventory, allowed packet, or question
looks inconsistent. Such responses are quarantined at the whole-episode level; condition-specific
exclusion is forbidden.

## 3–5. Agreement, adjudication, finalization

```bash
# agreement only; no final labels are emitted
PYTHONPATH=packages/astro_dock/src/crane_explain/src:analysis \
python analysis/adjudicate_annotations.py \
  --packet model_outputs/annotation_packets/sealed-primary-v2/packet.jsonl \
  --annotator-a <a>.jsonl --annotator-b <b>.jsonl \
  --output analysis/results/sealed-primary-agreement.json

# after a third annotator labels the disagreements
... --adjudication <c>.jsonl --output analysis/results/sealed-primary-adjudicated.json
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

`status` stays `AWAITING_ADJUDICATION` and `labels` stays `null` until every disagreement is
resolved. `condition_key_joined` is always `false` in this tool's output; joining the key is a
separate, deliberate step.

## Current state

- A fresh primary pair is retained at `sealed-primary-v2`: 126 model-condition responses covering
  the first 21 included primary episodes, with its matching key physically under
  `data/evaluator_only/annotation_keys/`. It predates the 12 responses from `pn-0022`–`pn-0023` and is a
  packaging/recovery snapshot, not the final analysis packet. Regenerate one final pair only after
  collection freeze. The historical `sealed-luna-v1` pair is retained only for audit and covers
  nine episodes; do not use either historical snapshot for the full-arm analysis.
- The selected Claude-family sealed replication is **collected**: 18 envelopes and 54 model-condition
  responses over `pn-0001`–`pn-0009`. Its fresh `sealed-claude-v2` packet/key pair is retained
  separately because the Claude response format can reveal the provider and harness. The original
  `sealed-claude-v1` packet is unusable because its key was never uploaded and cannot be restored;
  never reconstruct that key. Note that 16 of 18 G responses use the deterministic checked
  template; byte-identical G text across arms must receive identical labels.
- **Annotation itself is `NOT_RUN`.** No primary-arm sealed response has been scored, and no sealed
  effect estimate exists.
- The development model-strength controls are separate: unblinded, single-annotator, and
  development-only by design. They are not part of this workflow and must not be reported as if
  they were.
