# Fixed-N mean-difference interval candidate

Development-only `roboboat_fixed_n_interval_design_v1.py` provides interpretable effect uncertainty for the existing bounded independent-geometry score design. No real outcomes are read, no final test/N/weights are selected, and `origin` other than SIMULATED is refused. It is an analysis-tool candidate to be frozen prospectively with the eventual primary protocol.

Let each paired geometry score D_i lie in [-1,1], and let the estimand be the fixed allocation average of its expectations. For any proposed mean m in (-1,1], set Y_i=(D_i-m)/(1+m). For a prospectively fixed lambda in (0,1), each factor 1+lambda Y_i is positive. Independence yields

E[product_i(1+lambda Y_i)] = product_i(1+lambda(E[D_i]-m)/(1+m)) <= (1+lambda(mean_i E[D_i]-m)/(1+m))^N <= 1

under the fixed-N average null mean_i E[D_i] <= m. The AM-GM bound allows heterogeneous configuration families with fixed estimand-compatible allocations; conditional per-family nulls are not required. A prospectively fixed positive-weight mixture preserves the bound, and Markov gives a valid one-sided alpha test for each m. This is finite-N validity, not anytime validity or permission for optional stopping under a weak average null.

The observed e-value decreases with m because every factor equals 1-lambda + lambda(D_i+1)/(1+m). Inverting its rejection boundary supplies a one-sided lower confidence bound. Apply the same construction to -D for an upper bound; union bound gives coverage at least1-2alpha. Alpha=.025 per tail therefore gives a95% two-sided interval compatible with the primary one-sided.025 test at m=0. Endpoint cases use the known [-1,1] support; numerical inversion returns the lower bracket to avoid narrowing the confidence set through rounding.

Five tests check reproduction of the existing zero-null statistic, exact enumerated heterogeneous-average-null expectation, monotone inversion and endpoints, adverse missing-score monotonicity, and refusal of real-study origins/invalid settings. These are proof/implementation checks, not an empirical coverage estimate or selected confirmatory procedure. Fresh stress simulations and independent mathematical review remain necessary before final selection. A lower score replacing unavailable judgments cannot increase the positive-lambda statistic; analogous upper scores can conservatively bound unresolved outcomes. No missing-data mechanism independence is asserted or needed for that pointwise comparison. All physical and judging failures must remain visible.
