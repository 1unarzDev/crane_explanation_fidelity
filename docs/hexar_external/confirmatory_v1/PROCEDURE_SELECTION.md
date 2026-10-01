# Paired procedure selection before confirmation

**Candidate design amendment; no freeze or alpha allocation.** No confirmatory outcomes exist.

The initial leading test was exact conditional McNemar. Balanced families are allowed to have different discordance directions; its common conditional-sign assumption is not established for the desired overall average-risk null. Rather than assert that assumption, the proposed primary is a fixed-N paired e-test at fraction λ=.4. It controls the one-sided .01 average-risk null under independent, potentially nonidentical episode distributions. This is a conservative finite-sample test, not exact McNemar. Its rejection probability is calculated exactly for power planning.

| Discordance | Favorable conditional | Recording effect | McNemar power at 72 (its model) | E-test power at 72 | E-test power at 96 | E-test N for 90% |
|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 0.65 | 0.060 | 0.065 | 0.003 | 0.013 | >720 |
| 0.20 | 0.70 | 0.080 | 0.129 | 0.009 | 0.038 | 630 |
| 0.20 | 0.75 | 0.100 | 0.233 | 0.024 | 0.092 | 354 |
| 0.20 | 0.80 | 0.120 | 0.379 | 0.056 | 0.193 | 234 |
| 0.20 | 0.85 | 0.140 | 0.559 | 0.117 | 0.352 | 174 |
| 0.35 | 0.65 | 0.105 | 0.155 | 0.036 | 0.082 | >720 |
| 0.35 | 0.70 | 0.140 | 0.311 | 0.099 | 0.215 | 360 |
| 0.35 | 0.75 | 0.175 | 0.523 | 0.225 | 0.435 | 204 |
| 0.35 | 0.80 | 0.210 | 0.740 | 0.421 | 0.690 | 138 |
| 0.35 | 0.85 | 0.245 | 0.901 | 0.655 | 0.888 | 102 |
| 0.50 | 0.65 | 0.150 | 0.240 | 0.097 | 0.175 | >720 |
| 0.50 | 0.70 | 0.200 | 0.469 | 0.250 | 0.418 | 252 |
| 0.50 | 0.75 | 0.250 | 0.721 | 0.492 | 0.712 | 144 |
| 0.50 | 0.80 | 0.300 | 0.903 | 0.751 | 0.916 | 96 |
| 0.50 | 0.85 | 0.350 | 0.982 | 0.926 | 0.989 | 72 |
| 0.65 | 0.65 | 0.195 | 0.345 | 0.167 | 0.251 | 564 |
| 0.65 | 0.70 | 0.260 | 0.628 | 0.403 | 0.566 | 192 |
| 0.65 | 0.75 | 0.325 | 0.863 | 0.697 | 0.854 | 108 |
| 0.65 | 0.80 | 0.390 | 0.973 | 0.909 | 0.978 | 72 |
| 0.65 | 0.85 | 0.455 | 0.998 | 0.988 | 0.999 | 54 |

At d=.50/q=.80, λ=.4 gives about 75% power at 72 and at least 90% first at balanced N=96. This supplies a 16-valid-episodes-per-family planning example if that regime is accepted; final N remains unset until acquisition qualification. A smaller recording effect can require much larger N; neither 72 nor 96 is automatically adequate. The full JSON also evaluates λ=.3/.5/.6 as prospective design sensitivity, never outcome-dependent tuning. Selecting λ=.4 and N is an a priori decision that must be bound with the protocol; no mixture, maximum over tests, or second confirmatory McNemar test is authorized.

Let Dᵢ = HX-PROMPT failure − HX-CONTRACT failure ∈ {−1,0,1}. For any fixed μ∈[−1,1] define

`E(μ) = ∏ᵢ [1 + λ(Dᵢ − μ)/(1 + |μ|)]`.

Every factor is positive for 0<λ<1. Under H₀: average E[Dᵢ]≤μ and independence, E[E(μ)] equals the product of factor expectations. AM–GM bounds that product by `[1 + λ(average E[Dᵢ] − μ)/(1 + |μ|)]ᴺ ≤ 1`. Markov therefore bounds P(E(μ)≥100) by .01. This proof permits arbitrary fixed-family means, discordance rates and variances. It does not permit dependent episodes. Fixed N and λ are required; no optional stopping claim is made.

Report p=min(1,1/E(0)), both failure rates, the four paired cells and absolute risk difference. Each factor decreases in μ, so invert E(μ)≥100 for a one-sided 99% lower bound. Invert the sign-reversed procedure at .01 for the upper bound; the union bound gives a two-sided interval with at least 98% coverage. The lower bound and the primary test correspond to the same conservative procedure. Full-cohort unresolved outcomes are mapped least favorably; monotonicity prevents missingness from helping CRANE.

The original exact-power report remains available as conditional-model planning, not the new procedure's power. The hypothesis, endpoint, methods and alpha are unchanged. Primary procedure selection is recorded before any confirmation, never chosen from its outcomes.
