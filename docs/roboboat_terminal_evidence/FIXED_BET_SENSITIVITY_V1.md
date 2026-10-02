# Fixed-bet finite-sample sensitivity — prospective development v1

This additive design sensitivity uses no real outcome banks, provider/GPU calls or confirmatory observations. It compares every registered candidate on the existing complete six-question geometry-score scenarios, six equally weighted balanced family strata and fixed-N grid. It selects neither a final test nor N and changes no earlier source, declaration or endpoint. The artifact `fixed_bet_sensitivity_v1.json` binds this runner and both scenario dependencies by SHA256 and records NumPy version, PCG64 seed 42003 and 10,000 Monte Carlo repetitions per scenario/N. It contains 374 scenario/N rows, three candidates and all alternative/null/missing-annotation cases from the previous cluster-score investigation.

All registered bets and weights are disclosed:

| Candidate | Fixed lambdas | Fixed weights |
|---|---|---|
| Single meaningful-effect bet | .25 | 1 |
| Narrow four-component mixture | .1, .2, .3, .4 | .25 each |
| Retained eleven-component mixture | .01, .025, .05, .075, .10, .15, .20, .30, .40, .60, .80 | 1/11 each |

The provisional meaningful effect is a ten-percentage-point improvement. Under the hypothetical maximal-dependence case with geometry-score second moment .4, the quadratic approximation `E[log(1+lambda*X)] ≈ lambda*delta - lambda²*E[X²]/2` suggests lambda ≈`delta/E[X²]=.25`. This motivates a separately registered fixed-bet sensitivity; it is not an empirical estimate, exact growth optimum or selected confirmation setting. With smaller paired-question ICC the geometry second moment differs from question discordance, so applying the same formula directly to question discordance would be inappropriate. The narrow mixture allows several growth rates while paying a smaller mixture penalty. Every candidate is evaluated with the same simulated score counts within each row; none is replaced by the row's observed maximum.

For each candidate, `E_N = sum_k w_k product_i(1+lambda_k*X_i)`. The single fixed bet is one component with weight one. At its single prospectively fixed N, the proposed rule rejects only when `E_N >= 1/.025`. Independent bounded configuration scores, potentially heterogeneous across families, satisfy

`E[product_i(1+lambda*X_i)] = product_i(1+lambda*E[X_i]) <= (1+lambda*average_i E[X_i])^N <= 1`

under the fixed-N nonpositive-average null. Positive factors allow AM-GM. Fixed nonnegative weights summing to one preserve the expectation bound; Markov establishes type-I error at most .025. Thus a broad mixture is not necessary for fixed-N validity. Balanced allocations make the pooled mean equal the equal-six-family estimand. Unequal allocations would require a prospectively explicit estimand-compatible design; silent pooling is disallowed here. This argument is **not** an anytime-valid weak-average-null e-process. Ordered strata, unadjusted repeated threshold checks or choosing the best lambda from confirmation outcomes are not authorized.

At the hypothetical ten-point effect, discordance .4 and perfect within-geometry difference dependence, the same simulated samples give:

| Geometry N | Fixed lambda .25 power | Narrow four-component power | Retained eleven-component power |
|---:|---:|---:|---:|
| 420 | .6896 | .6092 | .5151 |
| 600 | .8419 | .8035 | .7495 |
| 840 | .9370 | .9385 | .9229 |
| 1200 | .9817 | .9908 | .9894 |

At N=420 the fixed-bet MC interval is [.6805, .6986], narrow-mixture [.5996, .6187] and broad-mixture [.5053, .5249]. A fixed bet improves power over the broad mixture under this planning assumption, but does not attain 90% at N=420. The first listed grid N whose individual Wilson lower bound reaches 90% is:

| Ten-point effect discordance | Paired-difference ICC | Single .25 | Narrow four | Retained eleven |
|---:|---:|---:|---:|---:|
| .2 | .25 | 240 | 240 | 240 |
| .2 | 1 | 420 | 420 | 420 |
| .4 | .25 | 420 | 420 | 420 |
| .4 | 1 | 840 | 840 | 840 |
| .6 | .25 | 420 | 420 | 600 |
| .6 | 1 | 4020 | 1800 | 1800 |

These are coarse grid observations with per-row MC intervals, not exact minimum sample sizes, joint power guarantees or selected study N. The disadvantage of committing to a single risk level is visible even at the meaningful effect: for discordance .6 and ICC=1, N=1200 gives fixed-bet power .7088 versus narrow-mixture .9040 and broad-mixture .8983. The broader uncertainty envelope must be considered before selecting a bet from development estimates.

Smaller effects expose a stronger failure. With a shared ternary score distribution, fixed-bet log growth is

`g = [(q+delta)/2]*log(1+lambda) + [(q-delta)/2]*log(1-lambda)`.

It is positive only when `delta > -q*log(1-lambda²)/log((1+lambda)/(1-lambda))`. For lambda .25 and q=.4 this threshold is about .0505; with q=.6 it is about .0758. Therefore a fixed .25 bet can have negative log growth despite a real positive mean. For delta=.05, q=.6, ICC=1, expected log growth is -.0065909 per geometry. Simulated power rises to .0548 at N=600 and then falls to .0078 at N=4020. At N=4020 the narrow mixture reaches .7287 and the broad mixture .7946 for that same positive effect. Increasing N cannot repair a fixed bet whose evidence product typically decays. Finite mixtures with a strictly positive minimum lambda also fail for sufficiently small positive effects if every component has nonpositive growth. The superiority null remains mean≤0; choosing a meaningful planning effect does not redefine that null.

The artifact retains five-, ten-, fifteen- and twenty-point alternatives, discordance .2/.4/.6, ICC .25/1, sparse discordance, asymmetric null scores, weak heterogeneous-family nulls, concentrated skew, deterministic offsetting families and adverse missing annotations. Across the simulated null grid, the maximum observed rejection probabilities are .0046 for fixed .25, .0030 for narrow four and .0014 for retained eleven, below nominal .025. These are QA observations; the analytic expectation proof establishes validity. Mapping 10% independently unresolved whole-geometry annotation to adverse score -1 under a ten-point true effect leaves mean -.01. Those geometries stay in N; technical-invalid capture inflation and replication are separate collection requirements.

Any future selection must use a prospective rule based on independent development evidence, rather than confirmation adaptivity:

1. Justify the scientifically useful improvement independently of the largest development effect or comparative p-values. Preserve sensitivity below that improvement.
2. Collect sufficient independent development geometries to estimate geometry-score moments, family heterogeneity, missing-judgment burden and technical invalidity, reporting uncertainty. Do not substitute six answer rows for six geometries.
3. Declare the selection objective and uncertainty envelope. A single lambda may be chosen from independently estimated moments using the justified planning effect and declared growth/power criterion; record the input estimates, conservative uncertainty treatment and algorithm before confirmation.
4. If uncertainty or smaller-effect robustness matters, specify a mixture grid and weights prospectively. Validate every retained candidate over the declared envelope, including null stresses and adverse annotation sensitivity, rather than selecting only favorable scenarios.
5. Freeze the candidate, weights, fixed N or valid stopping rule, endpoint/judging pipeline and population procedure before confirmation. Never maximize bets on confirmation responses or use ordinary repeated significance checks to rescue low power.

No selection in these steps is executed by this report. Further development may motivate other parameter values; their rationale and validation must be recorded before a fresh freeze. Fresh replication identities should be generated in addition to adequately powered confirmation rather than traded against it.

Reproduce the simulation and checks without study inputs:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_fixed_bet_sensitivity_v1.py tests/test_roboboat_cluster_score_design_v1.py tests/test_simulate_roboboat_fixed_n_power_v1.py tests/test_plan_roboboat_population_power.py
OPENBLAS_NUM_THREADS=1 python analysis/roboboat_fixed_bet_sensitivity_v1.py --output docs/roboboat_terminal_evidence/fixed_bet_sensitivity_v1.json --seed 42003 --repetitions 10000
```

Tests independently reconstruct small products, enumerate heterogeneous draws to verify exact expectations under an allocation-weighted weak null, check non-maximized mixture averaging, million-count numerical stability, positive-mean negative-growth failure, complete scenario retention, repeatability and simulated-only input gates. Confirmation/replication N and alpha consumption remain zero.
