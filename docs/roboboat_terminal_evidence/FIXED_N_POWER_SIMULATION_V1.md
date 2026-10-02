# Prospective fixed-N RoboBoat power simulation v1 — development only

This additive design simulation reads no study recordings, answers, judgments or pilot effects. Every effect and dependence assumption is hypothetical. It neither freezes a confirmation protocol nor selects confirmation N, allocates alpha or activates inference. The source-bound JSON records the simulator SHA256, NumPy version, PCG64 generator, seed 42001 and 10,000 repetitions for each scenario/N combination. Wilson intervals quantify Monte Carlo error only.

The proposed endpoint is the mean of six paired B4-minus-B2 answer-success differences within an independently sampled configuration. Its score is in `{-1,-5/6,...,5/6,1}`. The six questions and two physical variants contribute one independent N. For question difference `Y`, set `P(Y=+1)=(q+delta)/2`, `P(Y=-1)=(q-delta)/2` and `P(Y=0)=1-q`. Six-fold convolution gives the independent-question configuration distribution. Mixing that distribution with probability `1-rho` and a perfectly shared six-question draw with probability `rho` gives paired-difference ICC exactly `rho`, mean `delta` and variance `(q-delta²)*(1+5*rho)/6`. This matches the separate normal planner's moment equation; it does not validate that planner's power for another test.

The candidate fixed-N test uses the equal-weight mixture

`E_N = mean_lambda product_i (1 + lambda*X_i)`

with fixed lambda grid `[.01,.025,.05,.075,.10,.15,.20,.30,.40,.60,.80]`. Reject only at the prospectively fixed N when `E_N >= 1/.025`. Lambda values are never chosen from the observed study scores. Integer multinomial counts on the 13-score support let the simulator evaluate log products and a stable log-sum-exp rather than underflowing or overflowing raw products. Large expectations remain available in log form when exponentiation would overflow.

Validity requires independent configuration scores, but their distributions may differ. Under the weak null `sum_i E[X_i]/N <= 0`, independence gives, for each fixed lambda,

`E[product_i(1+lambda*X_i)] = product_i(1+lambda*E[X_i]) <= (1+lambda*mean_i E[X_i])^N <= 1`.

All factors are positive because `|X_i|<=1` and `0<lambda<1`; the middle inequality is AM-GM. Averaging fixed components preserves expectation at most one, and Markov's inequality gives type-I error at most .025. Positive-mean families are allowed if their predetermined aggregate mean is nonpositive. This is a **fixed-N** argument. No sequential validity or optional stopping is asserted under a weak average null, especially when balanced strata are ordered. Repeated threshold checks cannot replace the single prospectively specified test.

The artifact contains 18 alternative scenarios (`delta=.05,.10,.15`, `q=.2,.4,.6`, `rho=.25,1`) and six stress/sensitivity scenarios at N 50, 100, 150, 250, 410, 620, 800, 1000, 1500, 2000 and 4000. Null checks include symmetric, skewed and balanced heterogeneous-family draws with positive and negative family effects. Remainders are allocated to negative families first so every simulated heterogeneous-null N has nonpositive aggregate expectation. Annotation sensitivity maps an independently unresolved whole configuration to the adverse score -1 and retains it in N; this is distinct from technical capture invalidity.

For a hypothetical ten-percentage-point improvement, the simulated outcomes are:

| Discordance q | Difference ICC rho | Rejection probability at N=410 | First listed N with Wilson lower bound ≥90% | Rejection probability there (95% MC interval) |
|---|---:|---:|---:|---|
| .2 | .25 | .9998 | 250 | .9907 [.9886, .9924] |
| .2 | 1 | .9364 | 410 | .9364 [.9314, .9410] |
| .4 | .25 | .9720 | 410 | .9720 [.9686, .9751] |
| .4 | 1 | .4936 | 1000 | .9694 [.9658, .9726] |
| .6 | .25 | .8476 | 620 | .9770 [.9739, .9798] |
| .6 | 1 | .2711 | 1500 | .9611 [.9571, .9647] |

These are grid observations, not exact minimum sample sizes or a selected study N. They show why normal planning cannot be transferred to this mixture test: the earlier example of N=410, delta=.10, q=.4 and rho=1 yields only about 49% rejection probability here. A scientifically justified test choice and realistic configuration-score variance remain necessary before confirmation.

At the more difficult five-point effect, q=.6 and rho=1, N=4000 gives only .7881 simulated power. Four thousand is therefore not a stopping ceiling. With a ten-point true effect, 5% unresolved whole configurations reduce the adverse-score mean to .045; 10% reduce it to -.01, and rejection at N=4000 is zero in this simulation. More N cannot recover an erased positive adverse-score estimand. Measurement completeness must be addressed during development. Across the simulated null scenarios, the largest observed rejection rate was .0017, consistent with a conservative test; these checks support implementation QA, while the analytic expectation argument establishes the type-I bound.

Reproduce without providers or study inputs:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=analysis python -m pytest -q tests/test_simulate_roboboat_fixed_n_power_v1.py tests/test_plan_roboboat_population_power.py
OPENBLAS_NUM_THREADS=1 python analysis/simulate_roboboat_fixed_n_power_v1.py --output docs/roboboat_terminal_evidence/fixed_n_power_simulation_v1.json --seed 42001 --repetitions 10000
```

The 25 passing tests check exact moments, full-dependence support, direct mixture arithmetic, million-configuration log stability, heterogeneous-family expected-null bounds, reproducibility, explicit simulated-only inputs, adverse missingness and report boundaries. Neither arithmetic QA nor hypothetical Monte Carlo establishes real judge reliability, physical configuration independence or empirical superiority. Technical-invalid inflation, replication identities and any final fixed-N/sequential design remain separate prospective decisions.
