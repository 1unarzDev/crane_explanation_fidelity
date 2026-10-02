# Prospective paired-procedure decision v2

**Adopted for completion of prospective design; not frozen or activated.** The candidate analysis plan now uses one fixed uniform paired-mixture statistic. Final N, model binding, endpoint qualification and the combined H1→H2 scientific freeze remain incomplete. No confirmatory outputs exist; no empirical development p-value selected this procedure.

The original McNemar candidate needs pooled conditional-sign assumptions not established for the equally weighted average-risk null with fixed balanced families. The subsequent fixed fraction λ=.4 candidate permits heterogeneity but has nonpositive expected log evidence for favorable discordance q≤.6028878953, a consistency blind spot for weak positive effects. Integrating a fixed uniform distribution over λ∈[0,1] preserves finite-sample control for independent nonidentical episodes without choosing a fraction from outcomes. This resolves the design limitation at a power cost in some stronger regimes. The earlier [fixed-.4 proposal](PROCEDURE_SELECTION_FIXED_04_HISTORY.md) and original McNemar calculations remain historical design sensitivity.

For Dᵢ = prompt failure − contract failure ∈{−1,0,1}, define

`E(μ) = ∫₀¹ ∏ᵢ [1 + λ(Dᵢ−μ)/(1+|μ|)] dλ`.

For each fixed λ every factor is nonnegative. Independence and AM–GM bound its expected product by `[1+λ(average E[Dᵢ]−μ)/(1+|μ|)]ᴺ≤1` under the average-risk null. Nonnegative integration retains expectation ≤1; Markov bounds P(E(μ)≥100) by .01. This permits arbitrary fixed-family probabilities but requires independent episodes. It is one marginal level-.01 procedure in H2 of the ordered family, not best-p selection, a second alpha allocation or optional stopping. No common conditional favorable probability is required for inference.

At μ=0, with f favorable/u reverse pairs and m=f+u,

`E(0) = [Σⱼ₌₀ᶠ C(m+1,j)] / [(m+1)C(m,f)]`.

The terminal decision uses exact rational E(0)≥100, never a rounded displayed p-value. Report conservative one-sided p=min(1,1/E(0)), both failure rates, all four cells and the paired risk difference. This is not an exact binomial/McNemar p-value. Invert the same μ statistic with directed Decimal bounds for a 99% lower limit; invert the sign-reversed statistic at .01 for the upper limit. Joint coverage is ≥98% by the union bound. Unseparated numerical boundaries cannot earn rejection. The interval targets the least-favorable mapped endpoint. Its lower bound is conservative for latent complete-label effects; its upper bound need not be. Realized-cohort missingness identification bounds remain separate.

The uniform density/support, superiority direction, .01 threshold, implementation and inversion rules must be scientifically bound before H1 confirmation. The analyzer admits the mixture only through that explicit plan. Historical fixed-.4 and McNemar paths remain for offline design tests; the preconfirmation audit requires this adopted configuration. No second confirmatory test is authorized.

Power is not inherited from the earlier 72/96 examples. [Mixture sensitivity](MIXTURE_PROCEDURE_CANDIDATE.md) gives 114 valid episodes for 90% homogeneous power at d=.50/q=.80 and much larger N at weaker effects. [Family/missingness sensitivity](MIXTURE_FAMILY_POWER.md) shows degradation under unfavorable family covariance and unresolved outcomes, with separate invalid-run reserve calculations. Those reports preceded this decision and retain their original unselected status. Final N needs a scientifically accepted degradation regime tied to qualified acquisition and the final endpoint; it remains unset. Increasing N cannot replace measurement qualification or resolve leakage.
