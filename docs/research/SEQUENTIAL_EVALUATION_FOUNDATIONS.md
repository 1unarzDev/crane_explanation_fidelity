# Sequential evaluation foundations for new diagnostic campaigns

**Audit date:** 2026-09-23
**Scope:** Prospective diagnostic-study campaigns only. This note does not amend, reanalyse, or
retrofit the frozen F/G/H study or any already inspected diagnostic-development outcome.

## What the confirmatory quantity is

For each independently sampled scenario cluster $i$, let $Y_{Pi}$ and $Y_{Ri}$ be binary
supported-diagnostic-success outcomes for the frozen proposed method $P$ and the frozen strongest
development-selected baseline $R$. A success means that the **final response identifies the
required supported physical/execution mechanism and contains no material unsupported or
contradicted assertion**. Both methods must receive the same allowed robot-visible evidence,
relevant source/configuration, diagnostic tools and descriptions, model strength, and declared
resource ceiling. Calls, latency, and actual resource use remain measured treatment properties.

Define the paired cluster difference

\[
D_i = Y_{Pi}-Y_{Ri}\in\{-1,0,1\},\qquad
\Delta = \mathbb{E}(D_i)=p_{10}-p_{01}.
\]

Here $p_{10}$ is the probability that only $P$ succeeds and $p_{01}$ the probability that only
$R$ succeeds under the frozen target scenario distribution. Pairing is essential: it removes
between-scenario difficulty from the within-cluster comparison. The response, not a question
paraphrase or a judge pass, is the observational item; the scenario cluster is the independent
statistical unit. McNemar's original matched-pair statistic likewise uses only the two discordant
cells, although the proposed sequential estimand is the **marginal risk difference** $p_{10}-p_{01}$,
not merely equality of discordant probabilities ([McNemar, 1947](https://doi.org/10.1007/BF02295996)).

Use exactly one predeclared primary diagnosable response per cluster. If a future campaign genuinely
needs several primary responses, freeze a cluster-level rule such as “all required responses
succeed” before collection; never count the responses as independent. Diagnostic computations and
their independently checked numeric predicates are reported separately from the Luna-derived
semantic outcome.

## Estimand and sampling assumptions

A confidence sequence does not repair a moving target distribution. Before collection, freeze:

- scenario families and their target weights;
- the configuration generator or finite catalog and exclusion/admission rules;
- the paired execution and evidence-mask relationships;
- one statistical cluster ID covering shared layouts, controlled interventions, evidence masks,
  question variants, and reruns that share the same underlying scenario;
- the method versions and primary response selection rule.

The simplest valid design draws each new independent configuration from the frozen target mixture.
Then, conditional on the past, a fresh cluster has the same mean difference $\Delta$. If fixed
family quotas are used instead, construct simultaneous family-specific sequences for
$\Delta_h$ and combine them with the frozen weights, $\Delta=\sum_h w_h\Delta_h$; a quota-ordered
sequence is not automatically iid from the target mixture. An especially clear alternative is a
predeclared balanced block containing one independent draw from each family, with block score
$B_b=\sum_h w_hD_{bh}\in[-1,1]$; update the sequential analysis only after a complete independent
block. Sampling without replacement from a
finite catalog needs a finite-population confidence sequence, not the with-replacement formula
below. Waudby-Smith and Ramdas give distinct betting constructions for sampling with and without
replacement, which is why the sampling contract must be explicit
([JRSS B paper](https://doi.org/10.1093/jrsssb/qkad009),
[author manuscript](https://arxiv.org/abs/2010.09686)).

Independence means independence between scenario clusters, not merely distinct filenames or seeds.
Multiple observations inside one cluster may be arbitrarily dependent because they are reduced by
the frozen cluster rule. A simple paired-cluster analysis is invalid if configurations are selected
after viewing method differences, if variants of an easy family are promoted to independent units,
or if a later cluster inherits simulator/controller state from an earlier run. Unexpected outcomes
remain in the intended-to-evaluate cohort when the recording is valid; fault-induction success is a
separate descriptive measure.

An adaptive sampler may still be scientifically useful, but the ordinary $\Delta$ above then refers
to the actual adaptive sequence only under a suitable conditional-mean model. It no longer estimates
the originally advertised fixed scenario mixture. Avoid that ambiguity: use frozen sampling, or
predeclare an appropriate stratified/inverse-probability estimand and its valid sequential method.

## A theorem-backed anytime-valid construction

A confidence sequence (CS) covers its target simultaneously at all times, so inspecting it after
every completed independent cluster and stopping at a boundary does not create the repeated-peeking
error of ordinary fixed-time intervals. Howard et al. define this time-uniform coverage and derive
CSs by nonnegative supermartingales and Ville's inequality
([Annals of Statistics, 2021](https://doi.org/10.1214/20-AOS1991),
[author manuscript](https://arxiv.org/abs/1810.08240)). Waudby-Smith and Ramdas give a four-step
test-supermartingale inversion and tighter betting CSs specifically for bounded means
([JRSS B, 2024](https://doi.org/10.1093/jrsssb/qkad009)).

For an especially auditable reference implementation, suppose the fresh-cluster contract ensures

\[
\mathbb{E}[D_i\mid\mathcal F_{i-1}]=\Delta,\quad -1\le D_i\le1.
\]

For a one-sided null $H_m:\Delta\le m$, Hoeffding's lemma gives, for any nonnegative predictable
$\lambda_i$, the test supermartingale

\[
E_t(m)=\exp\left\{\sum_{i=1}^t \lambda_i(D_i-m)
                  -\frac12\sum_{i=1}^t\lambda_i^2\right\}.
\]

The $1/2$ penalty follows from the range width two: $(b-a)^2/8=4/8$. Predictable means that
$\lambda_i$ is fixed or depends only on data through cluster $i-1$. Ville's inequality gives

\[
\Pr_{H_m}\{\exists t:E_t(m)\ge1/\alpha\}\le\alpha.
\]

Inverting the tests yields the lower CS

\[
L_t=
\frac{\sum_{i=1}^t\lambda_iD_i-\tfrac12\sum_{i=1}^t\lambda_i^2
      -\log(1/\alpha)}{\sum_{i=1}^t\lambda_i},
\]

clipped to $[-1,1]$. An upper sequence follows by applying the same construction to $-D_i$.
A deterministic diminishing schedule, frozen with the protocol, is predictable and makes this a
direct theorem-to-code implementation. A published betting or mixture CS will usually be tighter
and is preferable if implemented exactly against its theorem and regression-tested. Do **not**
choose among CS variants after seeing confirmatory differences. Simulation can test calibration
bugs and budget expected stopping time, but is not the proof of coverage; the proof is the
supermartingale theorem plus verified correspondence between the frozen code and formula.

For the preferred bounded-mean betting implementation, transform
$X_i=(D_i+1)/2\in[0,1]$. Proposition 2 of Waudby-Smith and Ramdas constructs the capital process
$K_t(m)=\prod_{i\le t}[1+\lambda_i(m)(X_i-m)]$ with a predictable admissible bet; their Theorems 1
and 3 invert test supermartingales, including a hedged two-sided construction, into confidence
sequences. Transform its bounds back as
$[L_t^{(\Delta)},U_t^{(\Delta)}]=[2L_t^{(X)}-1,2U_t^{(X)}-1]$. The implementation must use the
paper's admissible-bet constraints and running-intersection rule rather than reconstructing them
from this summary.

The construction above tests a conditional-mean null. It is valid for iid paired clusters from the
frozen distribution and for some martingale models, but not for arbitrary dependent clusters,
post-outcome exclusions, or an outcome-adaptive shift in the estimand. A naive bootstrap interval
recomputed at every look is not anytime-valid. Nor does optional stopping make a fixed-sample exact
McNemar interval time-uniform.

### The actual success boundary

Let $\delta>0$ be the minimum worthwhile improvement fixed before confirmation. Evidence of a
meaningful advantage requires

\[
L_t^{(\Delta)}>\delta,
\]

not merely $L_t^{(\Delta)}>0$, a point estimate above $\delta$, or a $p$-value below .05 for
equality. The current development sensitivity calculation's +15-point alternative was used to plan
a test against zero. It therefore cannot justify power to show a lower bound above +15 points. If
the prospective protocol retains $\delta=0.15$, it must plan under scientifically plausible true
effects **larger than 0.15** and use the corrected sequential boundary. If that budget is
impractical, the honest result is that the desired advantage cannot be established at the planned
precision—not a reduced post-outcome $\delta$.

## Guardrails as simultaneous noninferiority claims

Define paired, cluster-level guardrail differences with “larger is worse for $P$” orientation:

- $G_E=\Pr(\text{material error}_P)-\Pr(\text{material error}_R)$;
- $G_C=\Pr(\text{useful coverage}_R)-\Pr(\text{useful coverage}_P)$, the coverage loss;
- $G_A=\Pr(\text{appropriate ambiguity handling}_R)-
  \Pr(\text{appropriate ambiguity handling}_P)$.

Freeze scientifically unacceptable degradation margins $m_E,m_C,m_A\ge0$ from development
considerations before confirmation. A positive overall claim requires corrected upper confidence
bounds

\[
U_t^{(G_E)}<m_E,\qquad U_t^{(G_C)}<m_C,\qquad U_t^{(G_A)}<m_A
\]

as well as $L_t^{(\Delta)}>\delta$. This is the confidence-bound form of a noninferiority rule:
the FDA's primary-source guidance likewise describes specifying a margin in advance and requiring
the upper confidence bound on loss to fall below it
([FDA Non-Inferiority Clinical Trials Guidance, 2016](https://www.fda.gov/media/78504/download)).
The clinical margin derivation in that guidance does not transfer to robotics; only the logic of a
prespecified unacceptable loss and an upper bound is used here.

Zero degradation is usually not a practical noninferiority margin and can make a modest study
incapable of claiming success. Conversely, a generous margin can make the guardrail meaningless.
The protocol must state why each chosen loss would still leave the system scientifically useful.
Do not replace an upper-bound requirement with “no significant difference,” which confuses absence
of evidence with evidence that unacceptable harm is excluded.

ICH E9 independently states the general design principle used here: declare noninferiority intent
in the protocol, define the largest acceptable difference in advance, justify it substantively, and
use confidence intervals relative to that margin rather than failure to reject a difference
([ICH E9, Section 3.3.2](https://database.ich.org/sites/default/files/E9_Guideline.pdf)). Its
clinical-trial terminology is not a source for CRANE's numerical margins.

Ambiguous cases should be a separately frozen stratum or guardrail inventory rather than mixed
opportunistically into the diagnosable primary endpoint. This makes “diagnose when supported” and
“qualify when underdetermined” separately auditable.

## Multiplicity and the cumulative error-budget ledger

Anytime validity handles repeated looks **within one frozen hypothesis**. It does not license trying
unlimited method versions, baselines, endpoints, margins, scenario mixtures, or replications at the
same nominal alpha. Maintain a prospective familywise error budget across the entire research
program.

The most assumption-light ledger is online Bonferroni/alpha spending. Before campaign $j$, assign
an $\alpha_j\ge0$ measurable from the prior ledger, with

\[
\sum_{j=1}^{\infty}\alpha_j\le\alpha_{\mathrm{program}}.
\]

Give that campaign's primary and guardrail CSs allocations whose sum is at most $\alpha_j$.
The union bound then controls the probability of any false confirmatory crossing by the total
budget even under arbitrary dependence, provided each campaign's test remains conditionally valid
given the history that selected it. Operationally, freeze the candidate and its hypotheses before
collecting that campaign's fresh configurations. Tian and Ramdas describe this method as online
Bonferroni/Alpha-Spending and distinguish it from more powerful online-FWER rules whose gains
require independence or local-dependence assumptions
([Statistical Methods in Medical Research, 2021](https://doi.org/10.1177/0962280220983381),
[author manuscript](https://arxiv.org/abs/1910.04900)). Use the simple ledger unless stronger
assumptions are explicitly justified.

The machine-readable ledger should retain, without deletion:

| Field | Meaning |
|---|---|
| campaign/method/baseline IDs and hashes | exactly what was tested |
| estimand, $\delta$, guardrails and margins | frozen scientific success claim |
| target distribution/split | population to which the claim applies |
| allocated alpha by bound | corrected crossing thresholds |
| first/last cluster and look | audit of chronological eligibility |
| spent, crossed, stopped, unresolved | immutable disposition |
| development lineage | why this candidate entered confirmation |
| reserved replication alpha | cannot be consumed by discovery |

For example, a program-level one-sided budget could reserve fixed portions for the first selected
candidate, all later candidate versions through a summable sequence, and one fresh replication.
The exact fractions are a scientific design decision and must be frozen before the first campaign;
the important invariants are that the allocations sum to the program budget, every guardrail has a
corrected bound, and failed candidates remain debited. Do not recycle a failed candidate's alpha or
use false-discovery-rate procedures when the intended guarantee is “no false confirmatory claim.”

Requiring efficacy and every guardrail is a conjunctive claim, but simultaneous corrected bounds
are still appropriate because the project reports the individual claims and may carry them across
candidate campaigns. A ledger is clearer and more conservative than relying on an unstated
intersection-union exception.

## Planned group-sequential alternative

If a vetted anytime CS is unavailable, use a finite group-sequential design rather than ordinary
confidence intervals at repeated looks. Freeze a maximum cluster count, number and approximate
timing of looks, information measure, efficacy boundaries, guardrails, and futility rules. The
Lan-DeMets approach specifies cumulative alpha spending as a function of information fraction and
chooses boundaries so the probability of crossing by each look equals that spend
([Lan and DeMets, 1983](https://doi.org/10.1093/biomet/70.3.659)). FDA's official adaptive-design
guidance confirms that conventional testing at every interim look inflates Type-I error, explains
Lan-DeMets spending, and warns that choosing look times based on comparative interim results can
itself inflate error
([FDA Adaptive Designs Guidance, 2019](https://www.fda.gov/media/78495/download)).

Standard group-sequential software often assumes a canonical asymptotic joint-normal score process.
With few clusters, rare discordances, or a custom weighted cluster endpoint, that approximation may
be poor. The protocol must identify the statistic and information fraction, derive or cite its joint
null law, and test code against known boundary cases. Merely simulating apparently acceptable Type-I
error is useful QA, not mathematical justification. This consideration favors the bounded-mean
supermartingale construction for the small paired binary campaign.

## Precision planning and futility

Use development data only to estimate plausible paired discordance, judge-unresolved rates,
recording yield, and collection cost. Plan across a range of true effects and discordance structures:

- probability of crossing $L_t>\delta$ by the maximum budget;
- simultaneous probability of satisfying every guardrail;
- expected and upper-quantile stopping cluster counts;
- precision if collection reaches the resource deadline without crossing;
- sensitivity to the worst permitted judge-unresolved assignments.

These simulations budget the campaign; they do not make the eventual inference valid and do not
promise that continued sampling must win. In particular, power must be computed under an
alternative separated from $\delta$, not at $\Delta=\delta$.

Freeze a maximum sample/resource cutoff and review points. Sound futility options include:

1. stop when the corrected upper CS for $\Delta$ falls below $\delta$, which is direct evidence
   against a worthwhile effect under the model;
2. a predeclared nonbinding conditional-power or probability-of-success threshold computed under
   stated alternatives; or
3. stop at the resource/deadline maximum without a positive conclusion.

FDA's guidance notes that a preplanned **nonbinding** futility guideline added to a valid efficacy
design does not increase Type-I error, whereas binding rules must be incorporated into the design
([FDA Adaptive Designs Guidance, 2019](https://www.fda.gov/media/78495/download)). Continuing after
a nonbinding futility review may consume resources but cannot change the positive efficacy boundary.
After futility, freeze and retain the campaign. Any improved method returns to development and gets
a new version, fresh configurations, and a new ledger allocation; it does not overwrite or continue
the failed candidate under a new name.

## Luna validity is a prerequisite, not something sample size fixes

The semantic endpoint is interpretable only if the frozen Luna judge has passed a genuinely held-out
qualification for the intended rubric and response distribution. Freeze before that qualification:

- rubric, prompt, reference-construction rules, schema, model/interface/settings;
- category-specific false-acceptance, false-rejection, unresolved, evidence-unit-coverage, and
  presentation-invariance gates;
- two-pass isolation, cache, retry, disagreement, and deterministic-resolution rules;
- how judge-uncertain outcomes enter the confirmatory analysis.

Prompt/model selection belongs only on judge-development cases. Run the held-out qualification once
after freeze and do not tune on its detailed results while continuing to call it held out. Dwork et
al. show formally that repeated adaptive reuse can overfit a holdout; their reusable-holdout
mechanism is specialized and is not implemented here
([Science, 2015](https://doi.org/10.1126/science.aaa9375),
[author manuscript](https://arxiv.org/abs/1506.02629)). A failed qualification blocks confirmatory
Luna semantic claims until a prospectively versioned judge is developed and tested on new held-out
reference cases.

Cawley and Talbot show the corresponding selection-bias problem directly for model-selection
criteria: using performance estimates to choose a model can overfit the selection criterion, so an
outer, independent evaluation is required
([JMLR, 2010](https://jmlr.org/papers/v11/cawley10a.html)). Here, prompt and reasoning-effort
selection are model selection; the untouched qualification cases are the outer evaluation.

LLM judging also has known construct-specific biases. Zheng et al. document position, verbosity,
limited-reasoning, and self-enhancement effects and validate agreement only for their particular
preference benchmarks
([NeurIPS 2023 paper](https://arxiv.org/abs/2306.05685)). Panickssery et al. experimentally find
self-preference when an LLM evaluates outputs from the same underlying model
([NeurIPS 2024 paper](https://arxiv.org/abs/2404.13076)). These studies do not quantify Luna's error
on CRANE evidence auditing; they justify blinding, presentation-invariance tests, category-specific
qualification, and an explicit same-family limitation.

Two Luna passes are repeated measurements, not independent annotators. If a disagreement is not
settled by a predeclared deterministic fact, keep it unresolved. Never remove unresolved clusters
from the denominator. A conservative confirmatory sensitivity can assign unresolved $P$ outcomes
to failure and unresolved $R$ outcomes to success for the lower efficacy bound, with the reverse
worst case for each guardrail. A positive claim should survive that assignment, or the protocol must
predeclare another mathematically justified partial-identification rule. More robot responses make
the conditional Luna-labeled CS narrower; they do not reduce unknown systematic judge bias.

All manuscript wording must therefore say **Luna-assessed semantic performance**, alongside
independently checkable diagnostic measurements. It must not say human agreement, human trust, or
unqualified semantic truth.

## Fresh replication

After one frozen candidate satisfies discovery/confirmation boundaries, lock its code, prompts,
thresholds, baseline, and resources. Evaluate it on fresh scenario configurations drawn from the
same frozen target distribution—or on a separately named transport distribution if that is the
intended claim. Development episodes, discovery clusters, evidence masks, paraphrases, reruns, and
additional judge calls are not replication.

This follows Nosek and Errington's operational definition: a replication is a new study for which
any outcome would be diagnostic evidence about the prior claim. A repetition whose design can only
be interpreted as support is not a diagnostic replication
([PLOS Biology, 2020](https://doi.org/10.1371/journal.pbio.3000691)).

Specify the replication criterion before collecting it. A defensible strict criterion is the same
directional efficacy claim and all guardrails under the replication's reserved corrected bounds;
if the budget cannot support $L>\delta$ twice, prospectively define a weaker but still meaningful
replication threshold rather than weakening it after seeing results. Report discovery and
replication separately and together only under a predeclared combination rule. Failure to replicate
is retained as a result, not folded back into development.

## Minimum reproducible progress report

At every allowed look, write an immutable report containing:

1. eligible independent clusters overall and by frozen scenario family;
2. invalid recordings and fault-induction outcomes, with predeclared reasons;
3. paired $2\times2$ counts, point estimate $\widehat\Delta$, corrected anytime bounds, and the
   worthwhile threshold $\delta$;
4. each guardrail estimate, margin, corrected bound, and pass/fail/open status;
5. judge qualification identity, valid/unresolved/failed-call counts, pass agreement, and
   worst/best-case sensitivity;
6. deterministic diagnostic-predicate correctness and traceability;
7. program/campaign alpha allocated and cumulatively debited;
8. model/tool calls, tokens, latency, cost, fallback frequency, and collection resource use;
9. boundary/futility/resource status and the single next action allowed by the protocol.

The report must retain unsuccessful candidates and unresolved results. It must not expose interim
comparative results to scenario selection or method development personnel if those personnel can
change the active confirmatory campaign. If a boundary does not establish the meaningful advantage,
the campaign remains negative or unresolved under its registered rules.

## Required implementation verification

Before the first new confirmatory cluster:

1. translate the selected published theorem and its assumptions into a versioned analysis spec;
2. unit-test $D=-1,0,1$, clipping, sign/orientation, alpha allocation, root/boundary calculation,
   missing and unresolved labels, and family-weight combination;
3. verify that every reported look uses only clusters chronologically eligible at that look;
4. compare the simple Hoeffding e-process against hand-calculated prefixes;
5. simulate null and alternative sequences as QA, including dependence violations that should be
   rejected by admission checks, while stating that simulation is not the coverage proof;
6. freeze hashes for the baseline, proposed method, sampler, Luna arm, references, analysis code,
   delta, guardrails, ledger, and replication criterion;
7. demonstrate end-to-end reproduction from retained inputs without condition leakage.

No current Luna arm has passed its declared held-out qualification, so this note supports design and
implementation only. It does not authorize bulk semantic annotation or convert existing development
responses into prospective confirmation.

## Primary sources

- Q. McNemar, “Note on the Sampling Error of the Difference between Correlated Proportions or
  Percentages,” *Psychometrika* 12, 1947: <https://doi.org/10.1007/BF02295996>
- S. R. Howard et al., “Time-uniform, nonparametric, nonasymptotic confidence sequences,”
  *Annals of Statistics* 49(2), 2021: <https://doi.org/10.1214/20-AOS1991>
- I. Waudby-Smith and A. Ramdas, “Estimating means of bounded random variables by betting,”
  *JRSS B* 86(1), 2024: <https://doi.org/10.1093/jrsssb/qkad009>
- K. K. G. Lan and D. L. DeMets, “Discrete sequential boundaries for clinical trials,”
  *Biometrika* 70(3), 1983: <https://doi.org/10.1093/biomet/70.3.659>
- J. Tian and A. Ramdas, “Online control of the familywise error rate,” *Statistical Methods in
  Medical Research* 30(4), 2021: <https://doi.org/10.1177/0962280220983381>
- U.S. FDA, *Adaptive Designs for Clinical Trials of Drugs and Biologics: Guidance for Industry*,
  2019: <https://www.fda.gov/media/78495/download>
- U.S. FDA, *Non-Inferiority Clinical Trials to Establish Effectiveness: Guidance for Industry*,
  2016: <https://www.fda.gov/media/78504/download>
- International Council for Harmonisation, *E9 Statistical Principles for Clinical Trials*, 1998:
  <https://database.ich.org/sites/default/files/E9_Guideline.pdf>
- C. Dwork et al., “The reusable holdout: Preserving validity in adaptive data analysis,”
  *Science* 349(6248), 2015: <https://doi.org/10.1126/science.aaa9375>
- G. C. Cawley and N. L. C. Talbot, “On Over-fitting in Model Selection and Subsequent Selection
  Bias in Performance Evaluation,” *JMLR* 11, 2010: <https://jmlr.org/papers/v11/cawley10a.html>
- L. Zheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” NeurIPS 2023:
  <https://arxiv.org/abs/2306.05685>
- A. Panickssery et al., “LLM Evaluators Recognize and Favor Their Own Generations,” NeurIPS 2024:
  <https://arxiv.org/abs/2404.13076>
- B. A. Nosek and T. M. Errington, “What is replication?” *PLOS Biology* 18(3), 2020:
  <https://doi.org/10.1371/journal.pbio.3000691>
