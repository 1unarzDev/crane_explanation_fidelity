# B2 vs B4 confirmation artifacts: exploratory paired analysis (2026-10-02)

## Scope and data integrity

This report analyzes the retained `evidence-calibration-b4-b2-confirmation-2026-10-01` artifacts. It does not alter the immutable model outputs or retry technical failures.

- B2 condition records: 2,030 (E0 507, E1 509, E2 507, E3 507).
- B4 condition records: 2,580 (645 per level).
- Episode IDs with at least one paired level: 511.
- Episode IDs with all four paired levels: 504.
- The execution-accounting record reports 494 complete paired episodes; the intersection of those IDs with the four-level set is 494.
- B4 records uniformly carry `endpoint_status=UNSCORED_REQUIRES_METHOD_INDEPENDENT_SCORING`.

The independent unit is the episode. Evidence levels are averaged within an episode and are never counted as independent observations.

## What was tested

For each episode, B2 and B4 answers were reduced to five deterministic realization measures: character count, word count, sentence count, numeric-token count, and lexical cause-term count. The tested contrast is B4 minus B2.

For each measure, the script computes:

1. the paired episode mean difference;
2. a seeded percentile bootstrap 95% interval (10,000 resamples of episodes);
3. an exact two-sided paired sign-test p-value;
4. Holm-adjusted p-values across the five measures.

The reproducible implementation is [analyze_b2_b4_confirmation_exploratory.py](../analysis/analyze_b2_b4_confirmation_exploratory.py), and its machine-readable output is [b2-b4-exploratory-2026-10-02.json](../analysis/results/confirmation/b2-b4-exploratory-2026-10-02.json).

## Results: all 504 four-level episodes

| Measure | Mean B4 − B2 | Bootstrap 95% interval | Sign-test p | Holm-adjusted p | Positive / zero / negative |
|---|---:|---:|---:|---:|---:|
| Characters | +107.52 | [98.02, 116.56] | 1.12e-93 | 2.24e-93 | 475 / 0 / 29 |
| Words | +20.94 | [19.85, 22.01] | 2.56e-125 | 7.69e-125 | 500 / 0 / 4 |
| Sentences | +3.46 | [3.37, 3.54] | 3.82e-152 | 1.91e-151 | 504 / 0 / 0 |
| Numeric tokens | +2.72 | [2.67, 2.78] | 2.03e-142 | 8.12e-142 | 503 / 0 / 1 |
| Cause terms | +0.664 | [0.522, 0.806] | 1.29e-09 | 1.29e-09 | 302 / 32 / 170 |

The 494 accounting-complete subset gives the same direction and remains highly significant for every realization measure (for example, characters +116.93, 95% interval [109.51, 124.23], Holm p=5.35e-102; cause terms +0.749, interval [0.619, 0.882], Holm p=3.81e-11). Family-stratified results are included in the JSON output.

## Interpretation boundary

These p-values establish that B4 produced systematically longer and more structured text than B2 in the retained paired artifacts. They do **not** establish a lower unsupported-specificity rate, better evidence calibration, higher useful coverage, or any other primary diagnostic improvement. No method-independent atomic scoring exists in these records: B4 is explicitly marked unscored, and a B2/B4 episode-level failure indicator cannot be reconstructed without inventing labels from the answers. Therefore a valid endpoint risk difference, McNemar p-value, endpoint confidence interval, or corrected endpoint p-value is not identifiable from this artifact set.

The strong lexical effects are still useful development evidence: they confirm that the two methods differ substantially in realization and that output length/cause-term count would be confounded proxies for the scientific endpoint. They should not be reported as confirmatory evidence of explanation fidelity.

## Reproduction

```bash
python analysis/analyze_b2_b4_confirmation_exploratory.py \
  --worktree-root /home/lunarz/.codex/worktrees/f235/crane_explain \
  --output analysis/results/confirmation/b2-b4-exploratory-2026-10-02.json
```
