# B2/B4 secondary results (2026-10-02)

## Scope

The frozen primary scorer and result file were reproduced byte-for-byte before this additive analysis. The analysis unit is the episode; claims, clauses, and evidence levels are not independent samples. The 511-episode corpus and 494 accounting-complete sensitivity are retained unchanged.

The secondary analysis reuses the frozen claim rows and evidence requirements. It does not create a new annotation architecture or relabel the frozen primary result.

## Formal secondary results

| Metric | B2 | B4 | Paired effect (B4 − B2) | 95% interval | Raw p | Holm-adjusted p | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| Causal-overclaim episodes | 147/511 (28.77%) | 0/511 (0%) | −28.77 pp | [−32.84, −25.01] | 1.12e−44 | 2.24e−44 | B4 had no flagged unsupported causal/mechanistic episode |
| Material-contradiction episodes | 43/511 (8.41%) | 0/511 (0%) | −8.41 pp | [−11.14, −6.31] | 2.27e−13 | 2.27e−13 | Contradictions were confined to B2 |
| Unnecessary abstention, E3 | 191/511 (37.38%) | 123/511 (24.07%) | −13.31 pp | descriptive | descriptive | descriptive | B4 abstained less at the richest ladder level |
| Essential coverage, E3 | 0.897 | 0.952 | +0.055 | descriptive | descriptive | descriptive | B4 retained more frozen essential units |

The causal and contradiction tests are the two formal paired binary tests for which the frozen records supply direct labels; Holm correction is across the four planned core outcomes, with coverage and calibration reported as structured decompositions rather than separate discovery tests.

### Causal overclaim

The causal metric counts unsupported adverse claims whose frozen kind is a physical cause or whose text asserts an adverse causal/mechanistic relation. B2 had 147 episodes with at least one such claim, from 22 insufficient-evidence physical-cause labels and 4 physically-true-but-unsupported labels repeated across the fixed ladder records. B4 had zero. Causal-claim precision was 87.60% for B2 (1,187/1,355) and 100% for B4 (5,131/5,131); detailed claim counts are in the JSON artifact.

### Contradicted factual claims

B2 had 45 contradicted claim labels distributed over 43 episodes; B4 had zero. The deterministic contradiction categories were derived from frozen claim kinds and numeric markers. Representative B2 claims are retained in `b2-b4-contradictions-2026-10-02.json`; they are deterministic numeric contradictions, including wrong delivered-command or measured-motion quantities. No semantic arithmetic recomputation was used.

## Evidence-removal calibration

| Level | B2 supported specificity | B4 supported specificity | B2 unsupported-specificity episode rate | B4 unsupported-specificity episode rate |
|---|---:|---:|---:|---:|
| E0 | 1.916 | 1.759 | 44.03% | 0% |
| E1 | 2.881 | 2.759 | 4.50% | 0% |
| E2 | 3.431 | 3.759 | 30.33% | 0% |
| E3 | 4.483 | 4.759 | 7.63% | 0% |

B4 specificity rises monotonically with the ladder and reaches its highest supported specificity at E3. B2 has more supported detail at E0/E1 in this operational count, but it also has unsupported specificity at every level. B4 therefore shows the cleaner evidence boundary rather than a blanket abstention pattern.

The plots are:

- [Figure 1a: supported specificity](../analysis/results/secondary/figure-1-supported-specificity-overclaim.svg)
- [Figure 1b: unsupported specificity](../analysis/results/secondary/figure-1b-unsupported-specificity.svg)
- [Figure 2a: essential coverage](../analysis/results/secondary/figure-2-essential-coverage.svg)
- [Figure 2b: adverse claim rate](../analysis/results/secondary/figure-2b-adverse-claim-rate.svg)

## Essential answerable information and abstention

Essential units were fixed from the existing frozen claim kinds and evidence requirements: outcome and limitation at E0, recovery trace at E1, delivered command at E2, and command-motion discrepancy at E3. A unit counted as covered only when communicated with a supported frozen label. No unavailable unit was scored as an omission.

B4 coverage increased from 0.880 (E0) to 0.952 (E3). B2 coverage was 0.958, 0.960, 0.858, and 0.897 across E0–E3. At E3, B4's mean coverage exceeded B2 by 5.5 percentage points. No frozen noninferiority margin was available, so this is descriptive rather than a noninferiority claim.

Unnecessary abstention was defined as an answerable frozen unit not communicated when the answer contained no adverse claim for that unit. At E3, B2 had 191/511 (37.38%) such episode-level flags and B4 had 123/511 (24.07%). This directly argues against interpreting B4's reliability as mere refusal to answer.

## Supporting analyses

The current artifacts support the following bounded descriptive checks:

- E0–E3 supported specificity is monotone for B4; its unsupported-specificity rate is zero at every level.
- Family-stratified claim counts are retained in the normalized claims and summary files; both primary families show the same direction for adverse labels. No tiny-family significance claim is made.
- Reproducibility is limited to exact rerun of the deterministic scorer and byte-identical frozen reproduction. No repeated model generations are treated as new N.
- A clean numerical-fidelity rate and inference-efficiency comparison was not promoted because the retained normalized rows do not provide a complete method-independent value/unit/latency table for every answer. The 45 contradiction labels remain reported rather than replaced by a partial numerical audit.

## Scientific interpretation

Within the limits of the frozen deterministic rubric, B4 reduces unsupported causal/mechanistic attribution and factual contradiction while preserving or improving the essential answerable information represented by the existing contracts. Its supported specificity expands with evidence and its E3 unnecessary-abstention rate is lower than B2's. These are secondary analyses of the existing corpus; they do not reopen the frozen primary endpoint or create a new confirmatory sample.

## Reproduction

```bash
python analysis/score_b2_b4_frozen_claims.py \
  --worktree-root /home/lunarz/.codex/worktrees/f235/crane_explain \
  --output /tmp/frozen-repro.json
cmp /tmp/frozen-repro.json analysis/results/confirmation/b2-b4-frozen-claim-scores-2026-10-02.json
python analysis/analyze_b2_b4_secondary.py \
  --frozen analysis/results/confirmation/b2-b4-frozen-claim-scores-2026-10-02.json \
  --output-dir analysis/results/secondary
python analysis/validate_secondary_scoring_adversarial.py
```
