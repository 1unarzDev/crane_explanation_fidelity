# B2 vs B4 frozen claim/evidence scoring (2026-10-02)

## Frozen comparison implementation

`analysis/score_b2_b4_frozen_claims.py` applies one deterministic rubric to both methods:

1. split each answer into atomic sentence/clause claims;
2. assign each claim its required abstraction/evidence level;
3. compare that requirement with the declared visible ladder level;
4. assign `SUPPORTED_BY_VISIBLE_EVIDENCE`, `CONTRADICTED_BY_VISIBLE_EVIDENCE`, `INSUFFICIENT_VISIBLE_EVIDENCE`, `PHYSICALLY_TRUE_BUT_UNSUPPORTED`, or `UNINTERPRETABLE`;
5. mark an episode as failed if any substantive claim on its fixed ladder is adverse.

The scorer uses only answer text, the declared evidence level, and robot-visible reference facts. It does not read B4 clauses, B4 metadata, or method identity while assigning labels. Evaluator-only references are used only to retain physical-truth separation and never to turn unavailable evidence into support.

The prior lexical analysis remains retained in `b2-b4-exploratory-2026-10-02.json`.

## Claim labels

Across all available method/level records:

| Label | B2 | B4 |
|---|---:|---:|
| Supported | 13,121 | 19,644 |
| Contradicted | 45 | 0 |
| Insufficient visible evidence | 420 | 0 |
| Physically true but unsupported | 4 | 0 |
| Uninterpretable | 0 | 0 |

The labels are reduced at episode level; claims, clauses, and levels are not independent samples.

## Episode-level failure results

For the 511 episodes with at least one paired evidence level:

- B2 failures: 338/511 (66.14%), Wilson 95% CI [61.93%, 70.11%].
- B4 failures: 0/511 (0.00%), Wilson 95% CI [0.00%, 0.75%].
- B2-only discordances: 338.
- B4-only discordances: 0.
- Risk difference (B4 − B2): −66.14 percentage points.
- Exact two-sided McNemar p = 3.57e−102.

This is a large apparent specificity/failure improvement under this frozen deterministic scoring implementation.

## Evidence-level paired sensitivity

| Level | B2 failures | B4 failures | Risk difference (B4 − B2) | Exact McNemar p | Holm p across levels |
|---|---:|---:|---:|---:|---:|
| E0 | 225/507 | 0/507 | −44.38 pp | 3.71e−68 | 1.48e−67 |
| E1 | 23/509 | 0/509 | −4.52 pp | 2.38e−07 | 2.38e−07 |
| E2 | 155/507 | 0/507 | −30.57 pp | 4.38e−47 | 1.31e−46 |
| E3 | 39/507 | 0/507 | −7.69 pp | 3.64e−12 | 7.28e−12 |

The intervals for the level-wise discordance proportions and all claim-level records are in the machine-readable output.

## Interpretation and limitations

Under this rubric, B4 contracts specificity to the visible ladder and B2 frequently asserts details above the available ladder. The result supports a diagnostic-failure reduction claim for this retained paired artifact set.

This pass is a deterministic frozen-rubric implementation over existing answers, not a new model annotation invocation. It should therefore be reported as automated method-independent scoring, with the implementation hash and complete claim records retained. `PHYSICALLY_TRUE_BUT_UNSUPPORTED` remains a distinct adverse category; it is not merged into contradiction or treated as support.

The accounting record identifies 494 complete paired episodes. On that complete-pair subset, B2 failed 325/494 (65.79%), B4 failed 0/494, risk difference −65.79 percentage points, exact two-sided McNemar p=2.93e−98, with discordance proportion 95% Wilson CI [61.50%, 69.84%]. The broad paired analysis above uses all 511 episodes with at least one paired level and reports level-specific denominators. The JSON retains episode IDs, source hashes, claims, labels, and failure flags.

## Reproduction

```bash
python analysis/score_b2_b4_frozen_claims.py \
  --worktree-root /home/lunarz/.codex/worktrees/f235/crane_explain \
  --output analysis/results/confirmation/b2-b4-frozen-claim-scores-2026-10-02.json
```
