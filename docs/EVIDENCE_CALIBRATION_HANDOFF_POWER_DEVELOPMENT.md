# Development paired superiority power

Exact paired binomial calculations at alpha 0.01. N counts independently acquired primary episode/configurations; masks and annotations add no N. This analysis spends no alpha and freezes no design.

The ledger permits 0.01 candidate alpha, with 0.02 already consumed and 0.02 protected for replication. A prospectively directional B4 superiority test is compatible: the unfrozen redirect specifies exact McNemar without requiring a two-sided primary test, and the ledger allocates alpha without fixing sidedness. Both directions, absolute failure rates, paired risk difference and a two-sided episode interval must still be reported.

| B2-only | B4-only | Reduction | Invalidity | Power N=100 one/two | N80 one/two | N90 one/two |
|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 0.01 | 0.04 | 0% | 10.0% / 5.3% | 381 / 440 | 477 / 541 |
| 0.05 | 0.01 | 0.04 | 10% | 7.4% / 3.7% | 423 / 489 | 531 / 602 |
| 0.05 | 0.01 | 0.04 | 20% | 5.2% / 2.3% | 477 / 551 | 597 / 677 |
| 0.10 | 0.02 | 0.08 | 0% | 37.9% / 29.2% | 190 / 220 | 238 / 270 |
| 0.10 | 0.02 | 0.08 | 10% | 32.1% / 23.9% | 211 / 244 | 265 / 300 |
| 0.10 | 0.02 | 0.08 | 20% | 26.4% / 18.8% | 238 / 275 | 298 / 338 |
| 0.15 | 0.03 | 0.12 | 0% | 65.5% / 55.0% | 126 / 146 | 158 / 180 |
| 0.15 | 0.03 | 0.12 | 10% | 57.9% / 47.7% | 141 / 163 | 176 / 200 |
| 0.15 | 0.03 | 0.12 | 20% | 49.6% / 40.0% | 158 / 183 | 198 / 225 |
| 0.20 | 0.05 | 0.15 | 0% | 73.3% / 63.2% | 114 / 131 | 144 / 161 |
| 0.20 | 0.05 | 0.15 | 10% | 67.1% / 55.9% | 127 / 146 | 161 / 179 |
| 0.20 | 0.05 | 0.15 | 20% | 59.5% / 48.0% | 143 / 164 | 181 / 202 |
| 0.25 | 0.05 | 0.20 | 0% | 92.0% / 87.2% | 76 / 88 | 95 / 107 |
| 0.25 | 0.05 | 0.20 | 10% | 88.3% / 81.8% | 84 / 97 | 105 / 119 |
| 0.25 | 0.05 | 0.20 | 20% | 83.1% / 74.6% | 95 / 110 | 118 / 134 |

The available 100 unmaterialized v6 layouts would provide at most 100 acquired primary episodes if all are prospectively reassigned to the primary population. Including 30% controls reduces that to about 70 primary episodes. Thus the pool is inadequate for small effects and leaves no untouched v6 replication pool if fully consumed. Generate further independent configurations when needed; do not increase N using masks.

Assumptions: independent episodes sampled from an equal mechanism mixture, with supplied probabilities applying to that mixture; independent technical invalidity. Fixed equal stratum quotas with heterogeneous discordances require a separate stratified calculation when development stratum estimates are available. Coverage success is additional to these superiority-only powers. Raw failure rates require the common-failure probability, which is not supplied here.

Sources: `manifests/study/diagnostic-sequential-error-ledger-v2.json`, `manifests/study/evidence-calibration-error-budget-audit-v1.json`, `docs/EVIDENCE_CALIBRATION_PROTOCOL.md`, `manifests/study/command-motion-layout-freshness-audit-v1.json`.
