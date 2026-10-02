# Uniform-mixture family, missingness and reserve sensitivity

`mixture_family_power.py` reads no episode, explanation or judge artifact. The versioned `mixture_family_power_sensitivity_v1.json` contains 360 seeded hypothetical planning rows with 40,000 replications each (maximum Monte Carlo standard error .0025). The uniform-mixture procedure remains a candidate, distinct from the leading original McNemar design and fixed-.4 candidate. Neither procedure, N nor reserve is selected.

All simulations count independent episode pairs. Six families have homogeneous or differing discordance/direction probabilities, including opposing family effects with average null. Balanced allocation is primary design preparation; unequal proportions are a separately labeled sensitivity that changes the target population. No weights are chosen using pilot outcomes. The effective six-request battery must inform plausible whole-episode probabilities but never multiplies inferential N.

Illustrative balanced conditional power estimates for the mixture candidate:

| N | Regime | No unknowns | 1% episode unknown probability per method | 5% per method |
|---:|---|---:|---:|---:|
| 72 | Discordance .50; favorable .80 | .660 | .599 | .326 |
| 114 | Discordance .50; favorable .80 | .917 | .878 | .612 |
| 192 | Discordance .50; favorable .80 | .997 | .994 | .911 |
| 192 | Adverse family covariation | .933 | .886 | .565 |
| 192 | Degraded direction | .700 | .610 | .240 |

The original exact McNemar planning point of .903 at N=72 is preserved under its own assumptions. This table uses another, more conservative heterogeneity-compatible candidate and does not revise that calculation.

The missingness model applies pessimistic whole-episode unknown mapping: contract unknown becomes failure, prompt unknown becomes success. Unknown flags are independent of latent outcomes for this sensitivity only. It does not estimate evaluator error, reproduce the answer-level adjudication process, or erase known definite failure from an actual recorded battery. The tie-failure share is hypothetically .5. These assumptions must be reviewed before interpreting any row as a planning floor.

Separate exact binomial reserve calculations cover family invalidity rates .05/.10/.20 and a heterogeneous .05/.05/.10/.10/.20/.30 profile, with four, eight, twelve or twenty-four extra attempts per family. Completion probabilities are distinct from power conditional on a full valid cohort. They assume independent technical validity events and cannot establish that exclusions preserve the intended population. The outcome-blind acquisition predicate and observed process reliability still require qualification. No semantic optional stopping or enlargement of reserves is authorized.

Tests reproduce homogeneous analytic mixture power, verify conservative missingness cannot improve the paired effect, check episode allocations and opposing-family null rejection. These checks validate the planning implementation, not the scientific assumptions or actual study power.
