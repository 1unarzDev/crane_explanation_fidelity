# Fixed uniform paired-mixture procedure candidate

Prospective theoretical design sensitivity only; no procedure or N is frozen. No semantic study data enter these calculations, and no primary p-value is computed for development episodes.

The six-unique-request sensitivity exposes a limitation of fixed fraction λ=.4: its expected conditional log evidence is nonpositive when favorable discordance q≤0.6028878953. Increasing N alone cannot give consistent detection throughout that degraded-positive-effect region. This is an overbetting limitation of that particular statistic, not evidence that CRANE lacks a benefit. It must be resolved before selecting the final power assumptions and procedure.

A candidate single fixed statistic integrates rather than selects fractions:

`E(μ) = ∫₀¹ ∏ᵢ [1 + λ(Dᵢ−μ)/(1+|μ|)] dλ`.

For every fixed λ, independence of episode pairs and AM–GM give expectation ≤1 under the null that the average episode mean is ≤μ. Every factor is nonnegative, so integration preserves this inequality. Markov yields `P(E(μ)≥100)≤.01`. This is one prospectively specified marginal test, not taking the best p-value, optional stopping, or a second alpha allocation. It permits nonidentical family distributions; it does not repair dependence or leakage. The uniform mixing distribution must be frozen. The method is not exact McNemar and no conditional-sign common-q model is asserted for inference.

For f favorable and u unfavorable discordances, m=f+u, ties contribute one at μ=0. Beta-integral algebra gives

`E(0) = [Σⱼ₌₀ᶠ C(m+1,j)] / [(m+1)C(m,f)]`.

The primary comparison with 100 uses exact integers/rationals. Report `p=min(1,1/E(0))` as a conservative marginal one-sided p-value, not an exact binomial p-value. For the corresponding lower bound, invert the same μ-integral using nonnegative Bernstein coefficients with directed floor/ceiling decimal arithmetic. Inversion retains a certified rejected point; uncertain numerical boundaries never earn rejection. A sign-reversed upper bound gives joint coverage at least 98%. As in the fixed-fraction candidate, the symmetric interval refers to the measured/conservatively mapped endpoint; latent complete-label identification bounds remain separate.

Tests compare the algebraic integral with exact small polynomials, verify expectation and nontrivial rejection size under opposing heterogeneous family means, bracket exact rational μ-integrals, and check direction/interval inversion. The proof supplies general control; finite tests illustrate rather than prove every population. An initial implementation error in negative-μ tie factors was caught by exact rational tests and corrected before any study analysis. No empirical result used that version.

`mixture_design_sensitivity_v1.json` enumerates planning power across 20 homogeneous paired regimes and balanced N up to 1,920. Examples: d=.50/q=.80 needs balanced N=114 for 90% power, compared with the fixed-.4 planning example of 96; d=.50/q=.60 needs 1,236; d=.20/q=.80 needs 276; d=.20/q=.65 needs 1,296. At weak effects, large required N is an honest limitation. This is planning under explicit assumptions, not proof that any particular cohort has those probabilities. Family heterogeneity, missingness and acquisition validity still require prospective sensitivity before final selection.

The subsequent v2 procedure decision adopts this single uniform mixture for completion of the prospective design. The candidate analyzer now supports an explicitly bound mixture configuration and the candidate analysis plan records it. This is not a freeze, alpha binding or activation: endpoint/runtime qualification and the power decision remain incomplete. Complete scientific binding must still precede H1 confirmation. Do not select between fixed, mixture or McNemar tests after confirmatory outcomes. This document and its immutable sensitivity report preserve the pre-adoption theoretical investigation.
