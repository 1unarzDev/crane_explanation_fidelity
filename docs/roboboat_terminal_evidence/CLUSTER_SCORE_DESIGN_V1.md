# Six-family cluster-score test design — prospective development v1

This additive investigation compares conventional fixed-N tests with the existing finite-sample e-mixture and a Hoeffding bound. It reads no real outcome banks, makes no provider/GPU calls and selects neither a confirmation test nor N. All effects and null stress distributions are hypothetical. The source-bound artifact `cluster_score_design_v1_simulation.json` records seed 42002, NumPy version, runner/dependency SHA256 and 10,000 Monte Carlo repetitions per scenario/N. There are 374 rows and four test candidates per row. Wilson intervals describe Monte Carlo error, not scientific effect uncertainty or joint confidence across the scenario grid.

The provisional endpoint from `COMPLETE_ANSWER_DESIGN_V1.md` is preserved: a geometry score is the equally weighted average of six paired binary complete-supported-answer success differences. Two physical variants, three evidence levels, models and annotation passes add no independent N. The estimand here is the equally weighted mean over six prospectively sampled configuration families. We assume independent geometry draws, iid within each family, deterministic equal family allocation, an unchanged complete-answer instrument and valid method-blind technical admission. The simulator refuses unbalanced allocations rather than quietly substituting sample-frequency weights for equal-family weights. Missing annotation uses explicit adverse geometry bounds; invalid capture exclusions remain separate.

For family j, let `xbar_j` and `s_j²` be the mean and unbiased sample variance of its `n_j` geometry scores. The estimator is `Delta_hat = sum_j xbar_j/6`; its estimated variance is `Vhat = sum_j s_j²/(36*n_j)`. Stratifying the variance avoids adding between-family mean differences to the sampling variance. It does not eliminate skew or low effective information.

The conventional candidates are:

- **Stratified Wald:** reject at the single fixed N when `Delta_hat/sqrt(Vhat) >= z_(1-alpha)`, with one-sided alpha .025.
- **Stratified Welch t:** use the same statistic and Welch-Satterthwaite degrees of freedom `Vhat² / sum_j [(s_j²/(36*n_j))²/(n_j-1)]`. The implementation uses a third-order Cornish-Fisher approximation to the t critical value, explicitly named `stratified_welch_t_cf3`; it is not an exact t CDF. Even the exact t quantile would not make this statistic t-distributed for arbitrary bounded scores.

Both conventional candidates refuse rejection when estimated variance is numerically zero. This prevents spurious certainty from a small sample with no observed variation, but also sacrifices detection in genuinely deterministic positive cases. Neither candidate has distribution-free finite-sample type-I control. Their justification is a stratified CLT and consistent variance estimation as informative within-family sample sizes grow, subject to nondegeneracy/Lindeberg conditions. Large total N alone does not imply adequate effective N when almost all variance resides in one family or rare outcomes are poorly sampled.

The finite-sample candidates are the unchanged prospectively fixed lambda e-mixture and the bounded-mean Hoeffding threshold `sqrt(2*log(1/alpha)/N)`. For balanced allocation the pooled configuration average equals the equal-family estimator. Independent, possibly non-identically distributed scores in [-1,1] with nonpositive average expectation suffice for their fixed-N guarantees. Neither proof licenses optional stopping or family selection based on results. A stratified sign-flip/permutation test would require exchangeability or randomized method assignment beyond the weak mean null; pairing alone does not supply that assumption. Exact McNemar testing of six pooled answers would count dependent questions as independent and would change the endpoint.

The alternative population model exactly convolves six paired question differences and mixes iid-question versus perfectly shared-question configurations. This recovers the declared paired-difference ICC and score moments. Alternatives cover five, ten, fifteen and twenty percentage-point effects, discordance .2/.4/.6 and ICC .25/1. Null stresses add sparse discordance, left/right skew, heterogeneous positive and negative family means, concentrated variance and deterministic family effects offset by another family. The balanced N grid is 60, 120, 150, 240, 420, 600, 840, 1200, 1800, 2400 and 4020; it is a simulation grid, not a sample ceiling or confirmation schedule.

For a hypothetical ten-point effect, discordance .4 and maximal difference ICC, the comparison is:

| Valid geometry N | Wald rejection | Welch-CF3 rejection | Fixed lambda mixture rejection | Hoeffding rejection |
|---:|---:|---:|---:|---:|
| 420 | .9052 | .9037 | .5103 | .1435 |
| 600 | .9745 | .9743 | .7492 | .3374 |
| 840 | .9965 | .9965 | .9188 | .6191 |
| 1200 | 1.0000 | 1.0000 | .9893 | .8770 |
| 2400 | 1.0000 | 1.0000 | 1.0000 | .9998 |

At N=420, Wald's 95% Monte Carlo interval is [.8993, .9108], Welch's [.8978, .9093], and the mixture's [.5005, .5201]. Point estimates around 90% are not a demonstrated 90% planning guarantee. With balanced heterogeneous alternative family means [-.15,-.05,.05,.15,.25,.35], discordance .6 and ICC .25, the common ten-point aggregate effect gives N=420 Wald/Welch power .9934 versus mixture .8368. These findings quantify the conventional precision advantage without choosing that test.

The stress tests expose a serious limitation: concentrated left skew produces **8.64%** false rejection for both conventional candidates at N=150, with MC interval [.0811, .0921], despite nominal alpha 2.5%. That scenario has five deterministic-zero families and one zero-mean family with `X=+1/6` with probability 6/7 and `X=-1` with probability 1/7. There are 25 draws in the informative family. The event of exactly one negative draw has probability `25*(1/7)*(6/7)^24 = .088332...`. On that event the studentized statistic is 18/7 ≈2.5714 with Welch df=24, exceeding both the normal and exact 97.5% t critical value (≈2.0639). Thus this specific type-I failure is analytically real, rather than Monte Carlo noise or the CF quantile approximation. The zero-variance no-rejection rule does not repair it.

In the same concentrated-skew scenario, simulated conventional false-rejection rates remain .0471 at N=420, .0529 at N=840 and .0313 at N=4020. With left skew present in every family, N=60 produces .0599 false rejection and N=420 produces .0325. Other null scenarios are nearer nominal, but that cannot justify ignoring these failures. Across the simulated null rows the largest e-mixture rejection rate is .0018; all Hoeffding null rows have zero rejections in these finite simulations. Those observations demonstrate conservatism in this grid; their analytic fixed-N bounds supply validity, rather than the simulations alone.

Ten-percent unresolved whole-geometry annotation under a true ten-point effect maps the adverse-score population mean to -.01. Five-percent unresolved maps it to .045. Neither conventional efficiency nor larger N restores a positive adverse estimand once measurement incompleteness erases it. Resolve instrument and annotation completeness during development, retaining all unresolved observations and their bounds.

A conventional design would require further prospectively documented distributional/measurement checks, sufficient informative sample size within every variance-bearing family and a candid asymptotic claim. It should not be described as exact or distribution-free. The finite-sample mixture offers a defensible alternative at higher N. More efficient finite-sample refinements would need their own mathematical guarantees and prospective power evaluation; this report does not select a refinement or tune a method against real effects. Whatever design is chosen later must bind its fixed N or valid stopping rule before confirmation, preserve the six-family mixture and distinguish population mean superiority from family-specific superiority.

Reproduce without study inputs:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_cluster_score_design_v1.py tests/test_simulate_roboboat_fixed_n_power_v1.py tests/test_plan_roboboat_population_power.py
OPENBLAS_NUM_THREADS=1 python analysis/roboboat_cluster_score_design_v1.py --output docs/roboboat_terminal_evidence/cluster_score_design_v1_simulation.json --seed 42002 --repetitions 10000
```

The 34 passing tests include stratified arithmetic, Welch df, a known t quantile approximation, explicit simulated-only inputs, balanced allocation refusal, zero-variance behavior, reproducibility, adverse missingness, exact moments/log stability from the prior planner and the analytic concentrated-skew rejection event. Confirmation and replication N and alpha consumption remain zero.
