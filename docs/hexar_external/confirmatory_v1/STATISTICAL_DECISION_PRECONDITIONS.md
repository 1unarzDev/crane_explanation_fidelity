# Preconditions for choosing the paired confirmation procedure

This is a development design audit, not a test/N freeze or alpha allocation. The current whole-recording endpoint and rich motion/source evidence interface remain subject to method and measurement qualification. Nine query/evidence jobs per method produce one binary episode endpoint; they do not supply nine independent units. A neutral query candidate cannot silently replace the registered battery or required information units.

## Target population and null

Let C and P denote whole-episode failure indicators for HX-CONTRACT and strengthened HX-PROMPT. Set D=P−C. Positive D favors CRANE. For six equally weighted families, the intended effect is Δ=(1/6)Σ_h E[D | family h]. Under equal fixed quotas and independently drawn episodes from each frozen family sampling process, Δ equals the average of the N episode expectations. Primary H0 is Δ≤0; H1 is Δ>0. This is an average failure-risk claim, not a requirement that every family improve and not an original HEXAR navigation-accuracy claim.

The composite must protect required coverage and identify unsupported specificity using a qualified, frozen instrument. Whole-episode aggregation makes both the query wording and evidence masks part of the estimand. No answer-level +9.3-point development difference determines this whole-episode Δ. For agent-assessed scoring, the directly observed estimand is failure under that frozen measurement procedure. Qualification and deterministic checks support scientific interpretation but do not turn automated labels into human-validated truth.

## Exact conditional McNemar

The pooled binomial discordance test is justified when, conditional on discordance identities, signs are independent and share a common probability q≤1/2 under H0. Common q across families is sufficient even if their total discordance probabilities differ; independence of episodes alone is insufficient. Under this common-q model, the sign of Δ agrees with the sign of q−1/2.

If families instead have different favorable probabilities q_h, the average null Σ_h d_h(2q_h−1)/6≤0 does not establish that the pooled conditional favorable count is binomial(m,1/2). It does not establish identical pair distributions. A test assuming every pair/family has q_h≤1/2 can be conservative by binomial domination, but that stronger null is not the intended average-risk null; rejecting it can reflect a positive family rather than positive overall Δ. Therefore neither balance nor stratifying descriptive tables repairs pooled McNemar for the intended heterogeneous average null.

Random IID draws from a frozen family mixture could justify an IID marginal pair model, but that is a different acquisition design from fixed balanced quotas. Empirical similarity in a small qualification cohort is not proof of common q. Do not choose a homogeneity assumption because it makes N=72 appear feasible.

## Fixed-N paired e-test

For independent, potentially nonidentical D_i in [−1,1], fixed N and fixed 0<λ<1, the candidate product

`E(μ)=Π_i [1+λ(D_i−μ)/(1+|μ|)]`

has expectation ≤1 under average E[D_i]≤μ by independence and AM–GM. Markov gives a level-.01 test rejecting when E(0)≥100. Thus this procedure matches the balanced heterogeneous average-risk null without common conditional signs. `min(1,1/E(0))` is a conservative marginal p-value; exact enumeration of its power does not make it exact McNemar. The subsequent v2 procedure decision adopts a fixed uniform integral over λ∈[0,1], retaining the same expectation bound by nonnegative integration and resolving the fixed-.4 weak-effect consistency limitation. The old product is historical design sensitivity; neither fraction nor mixing density may be chosen after confirmation.

Shared simulator resets, reused random streams, adaptive scenario choice or outcome-dependent judging can invalidate episode independence. Freeze episode-level randomization and isolated generation/scoring; qualify the acquisition process before accepting this proof's assumptions. Dependence within one episode's nine jobs is allowed. A fixed evaluator shared across episodes is not automatically dependence, but common stochastic batches or adaptive judge state require explicit justification. This test has no optional-stopping guarantee for the average-only null.

## Confidence statements

The candidate e-test lower bound inverts E(μ)≥100 and has at least 99% one-sided coverage for the same average Δ. Applying the sign-reversed bound at .01 gives an upper bound; together they have at least 98% two-sided coverage by union bound. These bounds correspond to the primary e-procedure. They are not exact conditional McNemar confidence limits. At an exact rejection-boundary equality the inverted lower bound may equal zero; distinguish nonnegative from strictly positive bounds and retain the frozen rejection inequality.

The legacy marginal Clopper–Pearson construction bounds favorable probability minus unfavorable probability. Its pooled version requires IID pairs. A family-stratified version is appropriate when episodes are IID within each frozen family: assign each favorable/unfavorable directional tail .005/6 and average the resulting risk-difference bounds at weights 1/6. The lower bound has at least 99% coverage; all 24 tails give at least 98% two-sided coverage. These bounds are conservative and are not inversion of McNemar. A McNemar rejection with a nonpositive such lower bound is possible and must be reported without substituting another interval/test. Nonidentical draws within families invalidate ordinary family binomial coverage even though the e-construction may remain valid under independence.

Unresolved components should retain the declared least-favorable mapping: CRANE failure/HX-PROMPT success unless another observed component resolves failure. This yields D*≤D episode by episode. Monotonicity makes the superiority test and lower bound conservative for the complete-label target. A sign-reversed upper bound calculated on D* is not automatically an upper bound for latent complete-label Δ. Report complete-label identification bounds separately; describe the symmetric interval as referring to the conservatively mapped measured endpoint unless a valid missing-data upper construction is implemented. Mapping must not be described as missingness-free inference.

## Prospective decision

The v2 procedure decision adopts the uniform paired mixture for completing the balanced heterogeneous design. Scientific freeze and N remain incomplete; the selection does not activate confirmation. McNemar and fixed-.4 calculations remain historical sensitivity. Power must model episode pairs, family heterogeneity, invalid acquisition rates and retained semantic failures. Bind N and the fixed mixture before the ordered family starts confirmation. Family sensitivities remain descriptive.

Current code additionally needs care in reporting missingness: its least-favorable mapped point estimate and e-interval should be explicitly labeled, alongside complete-label effect identification bounds. Do not label that symmetric interval as latent true-support uncertainty if labels remain unresolved.
## Latest equal-interface development evidence

The separately declared v13 numerical-policy method run and v4 blinded workflow returned six both-success episode ties, with 100% agent-assessed support/usefulness and required-unit coverage for both methods. No p-value was computed. The complete workflow and tied outcomes remain immutable development evidence. This does not establish an effect of zero in the target population, but it also supplies no empirical support for automatically assuming the older favorable discordance regime repeats under the clarified simulated interface.

Final power planning must distinguish a scientifically meaningful effect worth detecting from a predicted effect. The existing 72/114 and larger-N sensitivities are hypothetical regimes, not observed-power guarantees. Do not weaken the baseline, change the numerical endpoint or select family weights to recover separation. A valid null external confirmation remains an acceptable scientific outcome. N and the accepted degradation regime remain unbound until acquisition and the complete measurement process are qualified.
