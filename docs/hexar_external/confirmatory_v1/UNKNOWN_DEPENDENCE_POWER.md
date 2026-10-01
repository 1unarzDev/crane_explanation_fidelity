# Outcome-dependent unresolved-label power sensitivity

`mixture_unknown_dependence_power.py` produces the immutable candidate report `mixture_unknown_dependence_power_v1.json`: 720 hypothetical regimes, 40,000 replications each, seed 2026100105. It reads no acquired episode, answer or annotation. The adopted prospective uniform-mixture statistic is used, with N still unselected and no alpha activation.

The prior family report assumed unknown flags independent of complete endpoints and each other. This report adds a common within-pair flag independent of outcomes, and a correlated outcome-dependent construction. In the latter, both methods' unknown flags concentrate first on the same favorable pairs. Least-favorable mapping converts each affected favorable pair into a reverse pair. Remaining budgets target successful-contract ties and failing-prompt ties. The budgets are separate per-method, per-family upper bounds on whole-episode unknown probability. This construction attains the smallest mean mapped effect allowed by those budgets; it is not a universal worst-case power bound. Episode pairs remain independent. Neither missingness nor unfavorable valid outcomes authorize exclusions, retries, replacement or N changes.

The degraded balanced example has discordance .50 and favorable probabilities [.55,.60,.65,.75,.80,.85], giving a complete-endpoint average difference .20. At 5% unknown budget per method, outcome-independent flags give mapped difference .14, while favorable-targeted flags give .10. Shared independent flags also give .14 but change the discordance distribution and power.

| Valid independent N | Independent flags | Shared independent flags | Favorable-targeted flags |
|---:|---:|---:|---:|
| 384 | .6551 | .6032 | .2109 |
| 768 | .9761 | .9618 | .6076 |
| 1,296 | .9998 | .9996 | .9204 |
| 1,536 | 1.0000 | 1.0000 | .9679 |

Maximum Monte Carlo standard error is .0025. Homogeneous rows additionally contain analytic mixture power, checked against simulation in tests. Targeted mapping preserves discordance when both flags fit within favorable probability; the homogeneous d=.50/q=.70 example becomes d=.50/q=.60 under these 5% budgets. It is not legitimate to select N solely from an outcome-independent missingness simulation while ignoring this sensitivity.

All six families are retained in balanced rows. Weighted rows use prospectively specified sensitivity weights and change the population; they are not a way to choose favorable families. Technical invalidity/reserve completion remains separate from power conditional on a full valid cohort. A per-call or per-request unresolved rate cannot be substituted for the whole-episode budgets here. Qualification must address both transport failure and evaluator unresolved outcomes, along with the final six-request battery.

This report supplies neither a measured unknown-rate bound nor proof of general evaluator accuracy. Final N requires an accepted scientifically meaningful effect/degradation regime and a justified acquisition/annotation reliability assumption. Existing development results remain development evidence; no confirmation outputs or observed p-values entered this report.
