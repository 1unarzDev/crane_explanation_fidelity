# Diagnostic throughput report

Updated: 2026-09-27

Status: **P-contract-v4 pilot queues drained; development promotion failed**

## Contract-complete fixed-suffix batch

The 19 scheduled one-attempt physical jobs ran in fixed order with two isolated headless workers.
Capture closed in approximately 35.1 minutes (about 32.5 scheduled configurations/hour); 17
valid full P/R/two-pass-Luna comparisons closed in approximately 40.9 minutes from the first
capture manifest (about 24.9 reconciled comparisons/hour). The two technical failures were retained
without replacement. CPU export/reference work, isolated R calls, and four Luna calls per valid
pair overlapped physical capture; no Luna transport call failed. The semantic promotion result is
reported separately and did not influence scheduling.

This batch added 17 R calls and 68 Luna calls. R median top-level latency was 84.225 s; P was
deterministic and used zero model calls. The model queues were the tail bottleneck after physical
capture ended. Publication remains single-writer and is performed as one immutable DVC batch.

| Measure | Current value |
| --- | ---: |
| Frozen focused land configurations | 64 |
| Land configurations with immutable P/R pairs | 56 |
| Land configurations with two complete Luna passes | 53 |
| Valid land Luna judgments | 219/224 |
| Eligible evaluator-only reconciliations | 41 |
| Registered land looks released | 0 |
| Boat prospective physical configurations attempted | 4 |
| Boat valid / terminal technical-failure configurations | 2 / 2 |
| Boat independent configurations with P/R semantics | 1 |
| Boat P/R packets including its paired mask control | 2 |
| Boat Luna judgments | 8/8 valid |

The land physical schedule is closed at its frozen discovery endpoint. The final captured rows
089--100 were derived with the frozen low-speed diagnostic configuration, independently
referenced, hash-manifested, and completed in durable batch ledgers. All 56 admitted response
pairs have now received their two isolated Luna passes. Five judgments are retained as invalid
without retry: one for 062, two for 067, and two for 078. The remaining 219 judgments are valid.

The registered land N=24 look cannot be released: its exact ordered prefix contains unusable
judgments for 062 and 067, and the frozen usable-answer retry budget is zero. Later configurations
were processed in order and retained, but they cannot replace failed prefix rows or create an
unregistered look. No effect estimate, confidence sequence, significance result, or replication
claim is licensed from this campaign state.

The boat arm remains prospectively narrow and separate from land N, alpha, and replication. Rows
001 and 003 are valid physical recordings; 002 and 004 are terminal technical failures after the
declared bounded retry policy. Row 003 has a complete P/R packet and two-pass Luna result, as does
its missing-return-speed evidence-mask control; the control adds zero independent boat N. Row 001
remains a valid nominal physical control without a semantic pair because the frozen terminal-margin
packet path did not support its distinct nominal-approach question. This limitation is retained
rather than retrofitting the method after inspecting the recording.

Execution used two isolated land workers, two R sessions, and up to four Luna sessions. Rows
089--100 produced 12 fully processed physical configurations in about 22 minutes of this resumed
run (approximately 32.7 physical configurations/hour); semantic work overlapped capture and then
drained after simulation stopped. This is an observed batch rate, not evidence about method
quality. The principal remaining bottleneck is governed publication/restoration, not collection.

Failures retained at this checkpoint include the earlier invalid land recordings, the five
no-retry Luna judgments above, the two terminal boat technical failures, and the invalid first
registered look. Unexpected action outcomes remain admitted when capture/reference validity held.
No provider throttling or quality-driven retry occurred in the final drain.

The completed snapshot pushed 463 data/model objects plus 49 evaluator-analysis objects to
governed remote `r2`; subsequent cloud status reported the cache and remote in sync. A clean
`dvc get` materialization recovered row 100's
robot-visible diagnostic, evaluator-only reference, annotation key, and Luna summary with matching
content hashes.
