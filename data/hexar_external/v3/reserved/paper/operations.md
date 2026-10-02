| Method | Median realization ms | Model calls | Template | Fallback | Blanket abstention² | Required-unit control consistency³ |
|---|---:|---:|---:|---:|---:|---:|
| HX-ORIGINAL | 8768.91 | 108 | 0.0% | 0.0% | 20.4% | 80.6% |
| HX-PROMPT | 17674.28 | 108 | 0.0% | 0.0% | 0.0% | 83.3% |
| HX-CONTRACT | 1.58 | 0 | 100.0% | 0.0% | 0.0% | 100.0% |

Timings measure realization from prebuilt packets, not whole replay/extraction latency or pure model compute. Hosted cost/immutable weights are unavailable.
² Finalized assessments; detects limitation-only blanket refusal missing required units, not all unnecessary hedging. ³ Endpoint and required-unit equality among complete intact/control pairs; selected packets are byte-identical. No complete semantic invariance claim.
