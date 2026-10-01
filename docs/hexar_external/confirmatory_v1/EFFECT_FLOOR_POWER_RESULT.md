# Conditional effect-floor power results

The declared 108 hypothetical regimes are complete. Using the working **.10 conservative mapped episode-effect floor**, the first sampled balanced N satisfying the declared rule is **3,072**. This is conditional planning only: final N, accepted effect floor, unknown budget and invalidity cap remain unset. No semantic inputs or new agent calls enter this report. The simultaneous Monte Carlo lower bound is above .947 across the N=3,072 primary regimes.

| Valid episodes | Minimum simulated power across primary regimes | Simultaneous Monte Carlo lower bound |
|---:|---:|---:|
| 72 | 0.0012 | 0.0009 |
| 114 | 0.0028 | 0.0023 |
| 768 | 0.1377 | 0.1341 |
| 1,296 | 0.4073 | 0.4021 |
| 1,920 | 0.7001 | 0.6953 |
| 3,072 | 0.9499 | 0.9476 |

The homogeneous discordance regimes illustrate how substantially the needed N changes. “Required” below means the first **sampled grid point**, not a minimal-N theorem. Family robustness also enters the overall decision.

| Total discordance | Conditional favorable probability at .10 effect | First sampled N with enumerated power ≥.90 |
|---:|---:|---:|
| 0.10 | 1.000 | 768 |
| 0.25 | 0.700 | 768 |
| 0.50 | 0.600 | 1,296 |
| 0.75 | 0.567 | 3,072 |
| 1.00 | 0.550 | 3,072 |

At N=3,072, balanced quotas would be 512 valid episodes per family. Conditional finite reserves for a ≥.99 union-bound completion probability are:

| Assumed technical invalidity cap | Reserve per family | Maximum attempts per family | Completion lower bound |
|---:|---:|---:|---:|
| 0.05 | 44 | 556 | 0.9926 |
| 0.10 | 82 | 594 | 0.9924 |
| 0.20 | 167 | 679 | 0.9911 |

The pending 144-attempt acquisition review must support any accepted technical cap. The binomial planning assumption is independent identical technical validity within family; the union guarantee does not assume independence across families. Reserve exhaustion cannot authorize additional attempts, and semantic method failures cannot cause recording replacement.

The .10 effect is after least-favorable unknown mapping. A .10 complete-label effect plus .05 unknown per method can map to zero; the report does not silently power that case as a positive .10 effect. The .30 historical planning anchor remains separate and is not allowed to rescue a failed .10-effect regime. The original answer-level +9.3-point development result and seven recording wins are not confirmatory observations or forecasts here.

Validation: three checks compare homogeneous enumeration against the independent standard-library calculation, exact reserve recurrence against direct rational binomial sums, minimum finite caps and preserved family means. Probability arithmetic and software versions are recorded in the JSON report. Exact rejection thresholds and reserve probabilities are distinguished from floating enumeration and Monte Carlo power.
