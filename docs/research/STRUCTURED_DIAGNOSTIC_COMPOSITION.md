# Structured diagnostic composition under partial observability

**Audit date:** 2026-09-25  
**Scope:** Development guidance for the prospective physical-diagnosis study. This note neither
amends the frozen F/G/H study nor establishes a CRANE effectiveness result.

## Why another prompt is unlikely to create the needed advantage

The current project already has bounded geometric and command--motion computations, independently
implemented reference calculations, provenance checks, typed answer plans, deterministic
rendering, and fail-closed verification. The retained development comparisons show that a strong
tool-enabled repository agent can usually identify the same central mechanism. The current land
composition code is also case-specific: it accepts exactly a supported command--motion result plus
insufficient geometric evidence and emits one hard-coded plan. It does not yet enumerate every
mechanism compatible with an arbitrary packet or derive which claims survive missing or conflicting
evidence.

The most credible narrow development direction is therefore not more evidence for P, weaker tools
for R, or a more persuasive realization prompt. It is an **executable diagnostic-composition
contract** that turns independently computed observations into a complete set of admissible
diagnostic states, then permits only conclusions common to all admissible states. This targets the
observed gap: reliable composition, preservation, and qualification rather than access to facts.

The accompanying [primary-source audit](DIAGNOSTIC_COMPOSITION_PRIMARY_SOURCE_AUDIT.md) makes the
scope explicit: entailment is relative to the declared finite registry and retained observations.
The certificate must retain the registry hash and an `out_of_model_possible` marker; observation,
chronology, provenance use, or program dependence alone cannot establish physical causal
responsibility. Pearl's structural account supplies the causal-restraint basis: causal and
counterfactual claims require an explicit causal model and its assumptions, not association alone
([Pearl 2009](https://doi.org/10.1017/CBO9780511803161)).

This is established model-based-diagnosis and logic-programming territory, not a claim of a new
reasoning formalism:

- Reiter defines a diagnosis by consistency between a system description, observations, and a set
  of abnormal-component assumptions; minimal diagnoses are characterized through minimal hitting
  sets of conflict sets ([Reiter 1987](https://doi.org/10.1016/0004-3702(87)90062-2)).
- de Kleer's assumption-based truth-maintenance system associates propositions with the
  assumption environments in which they hold and records inconsistent environments as nogoods
  ([de Kleer 1986](https://doi.org/10.1016/0004-3702(86)90080-9)). de Kleer and Williams apply
  conflicts and candidates to multiple-fault diagnosis
  ([de Kleer and Williams 1987](https://doi.org/10.1016/0004-3702(87)90063-4)).
- In answer-set programming, brave consequences are the union and cautious consequences are the
  intersection of all answer sets; `clingo` exposes both modes directly
  ([Potassco Guide 2.2.0, Section 9.1](https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf)).
  CRANE need not adopt ASP to use the corresponding finite-set test.
- Sampath et al. formalize diagnosability for partially observed discrete-event systems, making
  explicit that an observation history may fail to distinguish fault classes
  ([Sampath et al. 1995](https://doi.org/10.1109/9.412626)). CRANE's bounded episode diagnosis is
  not their automaton framework, but the same distinction between an observed symptom and a
  discriminated mechanism is directly relevant.

## Smallest executable proposal: a finite diagnostic lattice

Implement a deterministic Python composer over the current versioned diagnostic JSON, not a new
general framework or knowledge graph. Its finite registry should contain only study mechanisms and
relations already backed by tested computations. A registry entry should declare:

- mechanism identifier and version;
- required positive and negative predicates;
- applicability and completeness predicates;
- incompatible and explicitly coexisting mechanisms;
- measurement and source identifiers that justify each predicate;
- causal-language ceiling;
- observations that would discriminate the remaining candidates.

The composer should enumerate all assignments allowed by those constraints. For every candidate
claim, return one of four statuses:

1. **entailed:** true in every admissible assignment;
2. **excluded:** true in none;
3. **unresolved:** true in some but not all;
4. **evidence problem:** no admissible assignment because retained inputs conflict or violate their
   contract.

These statuses are deliberately not probabilities. `unresolved` must not be converted into the
most plausible mechanism without a prospectively validated probabilistic model. `evidence problem`
must not be converted into an episode diagnosis.

More precisely, let `K = M ∧ E`, where `M` is the versioned mechanism model and `E` is the
retained evidence. Masked or unobserved variables remain unconstrained; they must never be encoded
as false. For candidate claim `h`:

- `K` unsatisfiable means **evidence problem**;
- `K ∧ ¬h` unsatisfiable means **entailed**;
- `K ∧ h` unsatisfiable means **excluded**;
- both satisfiable means **unresolved**, and the composer should retain a witness assignment for
  each side.

This can be implemented by exhaustive enumeration for CRANE's deliberately small finite registry;
it does not require adding a general SAT/ASP dependency. The tests above are the finite equivalent
of cautious versus brave consequence checking.

Each entailed or unresolved claim should have a machine-auditable certificate:

```text
claim ID and semantic type
status and causal-language ceiling
registry/model ID and hash, applicability scope, and `out_of_model_possible`
supporting measurement/source predicate IDs
rule/registry version and input hashes
minimal sufficient support set(s)
contradicting predicates or inconsistent environments
remaining compatible alternatives
missing discriminator(s)
```

A minimal support set is only an audit aid. It does not prove uniqueness, causal responsibility, or
physical truth beyond the declared computation and observation scope.

When a solver is eventually warranted, guard evidence predicates with selectors and minimize an
unsatisfiable core of `M ∧ E ∧ ¬h` to obtain a subset-minimal sufficiency certificate. Retain
a satisfying countermodel when the claim is unresolved, and diagnose an inconsistent packet from
a minimal unsatisfiable subset of `M ∧ E`. Algorithms for minimal unsatisfiable subsets and
conflict explanations are established prior work
([Liffiton and Sakallah 2008](https://doi.org/10.1007/s10817-007-9084-z);
[Junker 2004](https://cdn.aaai.org/AAAI/2004/AAAI04-027.pdf)). “Subset-minimal” does not mean
minimum-cardinality, and the certificate covers only predicates represented in the model. Opaque
numeric calculations still need the project's separate independent reference checks.

### Required rules for the current benchmark

- A supported command--motion computation licenses the bounded execution-response mechanism and
  its checked interval/measurements. It does not select actuator rejection, collision, slip,
  obstruction, or another root cause.
- A geometric restriction requires the relevant footprint/envelope comparison and sufficient
  spatial coverage. A failed planning event or logged obstacle assertion alone does not satisfy
  the rule.
- A visual, scan, or costmap observation can establish a scoped physical condition. “Nav2 acted
  because of that observation” additionally requires the declared runtime-consumption/dependency
  predicate and an applicable mechanism rule.
- Replanning and recovery logs establish execution events, not the physical trigger. The same
  terminal symptom must remain compatible with geometry and execution-response candidates until
  measurements discriminate them.
- Masking a decisive input removes the derived predicate and broadens the admissible set. The
  result must become unresolved or insufficient; it must not reuse a diagnosis computed before
  masking.
- Nominal and false-premise cases remain first-class states. If the asserted mechanism is excluded,
  the response should say so and retain the decisive nominal measurement rather than returning a
  generic nonanswer.

Consumption predicates require positive, completeness-audited lineage. W3C PROV-DM distinguishes
an activity's use of an entity from the entity's mere existence
([PROV-DM 2013](https://www.w3.org/TR/2013/REC-prov-dm-20130430/)); a backward dynamic slice is an
established way to identify statements that affected a value in one execution
([Korel and Laski 1988](https://doi.org/10.1016/0020-0190(88)90054-3)). CRANE need not add a general
provenance store or slicer before submission. The operational rule is narrower: assert consumption
only from an audited runtime dependency already captured for that claim. Missing lineage means
“consumption not established,” not “definitely not consumed.”

For a discretized geometry family, strengthen a disconnection result with a checkable graph-cut
certificate: the reachable free-cell set, the complementary goal set, and the blocked/out-of-scope
frontier separating them. The max-flow/min-cut theorem is established prior work
([Ford and Fulkerson 1956](https://doi.org/10.4153/CJM-1956-045-5)); the allowed CRANE conclusion
must still be only that no connection exists in the audited grid graph under the recorded
footprint/cost policy. It does not establish continuous-world impossibility or physical execution.
Likewise, sampled waypoint clearance is not automatically a swept-body collision certificate.
Continuous collision/distance methods exist—for example GJK for convex distance
([Gilbert, Johnson, and Keerthi 1988](https://doi.org/10.1109/56.2083)) and FCL's collision,
distance, and continuous-collision queries
([Pan, Chitta, and Manocha 2012](https://doi.org/10.1109/ICRA.2012.6225337))—but adding that
dependency is justified only if the active benchmark needs a continuous-envelope claim. Otherwise
the answer must retain the current sampled-grid scope.

## Certificate-to-language interface

The answer-plan compiler should consume only the composition certificate and should be total over
the four statuses. It should not ask a model to decide which mechanism or limitation to mention.
For each question it should deterministically select:

1. the deepest entailed mechanism at the allowed causal level;
2. the measurements in its minimal support certificate, including units and interval/frame;
3. the supported execution chain, without silently promoting chronology to cause;
4. every question-relevant unresolved alternative and the scope limitation that keeps it open;
5. one fixed-menu measurement that distinguishes the largest declared subset of remaining states.

The existing model realizer may paraphrase this plan, and the existing verifier/fallback may check
it. The required-unit inventory should be generated from the same certificate IDs, not authored as
a second free-text summary. This provides one concrete way to reduce required-unit and semantic-
field mismatch in downstream judging, although Luna qualification must still be demonstrated
independently; a cleaner packet does not validate the judge.

The implementation now separates a valid mechanism certificate from a language-ready answer plan.
If any registered unit required by the selected mechanism is absent, the certificate records
`language_ready=false` and the renderer refuses to emit an answer. This prevents a valid lattice
classification from silently becoming a response that drops the decisive comparison or limit.
Packets also declare an outcome-independent applicability scope. This prevents a command--motion
answer from dumping missing geometry, perception, or map-consistency predicates merely because
those mechanisms exist in the global registry. The registry-wide `out_of_model_possible` boundary
still applies.

Strict adapters now compile the retained command--motion v3 and newer geometric v1/v2 diagnostic
schemas into predicates and answer units. Real-fixture tests cover persistent discrepancy,
measured response recovery, nominal false-premise rejection, missing odometry, route change with an
unresolved trigger, nominal geometry, and nonterminal geometry insufficiency. Older positive
geometry exports lack structured action status and are deliberately rejected rather than repaired
from prose; use fresh complete captures for that family.

Moryossef, Goldberg, and Dagan's plan-first data-to-text method and Dušek and Kasner's bidirectional
semantic checking are already audited in
[`DIAGNOSIS_LANGUAGE_POSITIONING.md`](DIAGNOSIS_LANGUAGE_POSITIONING.md). They support separating
content planning from realization, but neither validates the diagnostic inputs. CRANE should not
claim novelty for that separation.

## Fair comparison with tool-enabled R

R must retain the same robot-visible packet, exact relevant source/configuration, retrieval,
primitive geometric and motion calculators, source-inspection tools, model/settings, and comparable
call/token/time budget. The composition rules and implementation may be inspectable repository
source, and R may receive the same generic constraint-calculation capability, but R must not receive
P's episode-specific checked composition result, support certificate, or answer plan. Log every
tool invocation and returned value.

The treatment is then a frozen, mandatory orchestration policy:

- P always validates primitive results, exhausts the finite candidate set, compiles the certificate,
  and verifies realization against it;
- R decides how to use the same permitted calculations and sources within the matched budget.

If R is instead given P's completed episode certificate, the diagnostic treatment has been removed
and the comparison becomes language realization only. Conversely, withholding lower-level tools or
material evidence from R would make any P advantage an information/tool-access effect. Report both
tool invocation and total resource use so the interpretation remains honest.

## Development experiments before another confirmatory campaign

Do not reopen confirmation merely because this composer runs. First require development evidence
that it addresses the failures that matter.

### 1. Deterministic composition conformance

Build reference-authored cases before executing the composer. Include:

- replanning recorded with no physical restriction established;
- an obstacle assertion in a log with no supporting physical predicate;
- matched terminal symptoms from geometric restriction and command--motion discrepancy;
- a visible obstacle with and without a proved Nav2-consumption/dependency link;
- every decisive measurement present versus one masked;
- persistent discrepancy, later measured compensation, and nominal response;
- jointly possible mechanisms, mutually incompatible mechanisms, contradictory evidence, and an
  out-of-model case.

Require exact status, required-unit IDs, limits, and support certificates. Mutation tests should
remove or contradict one decisive predicate at a time and verify monotonic narrowing: removing
evidence may change entailed to unresolved, but may not create a stronger mechanism claim.

### 2. End-to-end language preservation

On development-only packets, check exact machine predicates before any model judge:

- the required mechanism is present when entailed;
- every decisive quantity, unit, interval, and evidence ID survives;
- no observation-to-consumption or chronology-to-cause promotion appears;
- masked cases name the missing discriminator and preserve supported execution facts;
- false premises are rejected without discarding useful nominal evidence.

Report raw realization, verifier decision, repair/fallback, and final answer separately. A method
whose apparent gain comes entirely from deterministic fallback must be described that way.

### 3. Fresh development P--R comparison

Use independent scenario configurations across the campaign's declared families; question variants,
masks, repeated generations, and judge passes remain within-cluster measurements. Freeze P's
registry and templates before generating each bounded development batch. Retain every R and P
output without resampling. Compare supported diagnostic success, material error, required-unit
coverage, ambiguity handling, and resource use at the cluster level.

Advance a candidate only if the advantage appears across more than one mechanism family and comes
from the declared composition behavior—not prompt leakage, extra evidence, repeated attempts, or a
single easy template. The project should predeclare the development promotion rule and maximum
candidate count before inspecting the next batch. Development performance selects a candidate; it
is not confirmatory evidence and must not consume or be pooled with the fresh confirmation or
replication reserves.

## Alternatives considered for this deadline

| Direction | Expected value now | Decision |
|---|---|---|
| More prompt engineering or a larger realizer | Low: R already finds most central mechanisms, while the retained P failures concern composition, omitted units, and fallback | Do not make this the principal intervention |
| Learned Bayesian/causal diagnosis | Potentially valuable, but current clusters do not calibrate a causal graph, priors, or conditional likelihoods; introducing one now would create a larger validation burden | Defer unless an already validated model exists for a narrowly measured family |
| Full ASP/ATMS platform | The formal semantics fit, but a new dependency and general rule language are unnecessary for two or three bounded mechanism families | Implement finite enumeration and certificates in ordinary Python; cite the established formal basis |
| Environment-changing counterfactual search | Useful for modeled feasibility when actual controlled reruns are executed, but it cannot recover evidence absent from a retained episode and may be too expensive for each answer | Keep as a separately labeled intervention test, not the default composer |
| New VLM/perception stack | It would change both the evidence and engineering scope; visual presence still would not prove Nav2 consumption or causation | Do not pursue before submission |
| Finite checked composition over existing diagnostics | Directly targets mechanism selection, decisive-unit preservation, causal restraint, and masked-evidence qualification while keeping primitive evidence/tools matched | Highest-value bounded development candidate |

## What this can and cannot support

If the experiments succeed, the defensible method claim is narrow: mandatory, checked composition
of independently computed diagnostic predicates improves preservation and qualification relative
to an equally informed tool-enabled agent on the tested navigation families. It is not a claim of
universal root-cause discovery, novel model-based diagnosis, complete causal inference, or an
architecture-independent ontology.

If R invokes the tools and matches the certificate reliably, that is a valid negative result: the
structured composer may still improve auditability or deterministic rendering, but it does not
justify a semantic-performance advantage claim. If both methods remain ambiguous, the next action
is better discriminating instrumentation or a narrower question, not stronger causal wording.

## Primary sources

- R. Reiter, “A Theory of Diagnosis from First Principles,” *Artificial Intelligence* 32(1),
  1987: <https://doi.org/10.1016/0004-3702(87)90062-2>
- J. de Kleer, “An Assumption-Based TMS,” *Artificial Intelligence* 28(2), 1986:
  <https://doi.org/10.1016/0004-3702(86)90080-9>
- J. de Kleer and B. C. Williams, “Diagnosing Multiple Faults,” *Artificial Intelligence* 32(1),
  1987: <https://doi.org/10.1016/0004-3702(87)90063-4>
- Potassco, *A User's Guide to gringo, clasp, clingo, and iclingo*, version 2.2.0:
  <https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf>
- M. Sampath et al., “Diagnosability of Discrete-Event Systems,” *IEEE Transactions on Automatic
  Control* 40(9), 1995: <https://doi.org/10.1109/9.412626>
- L. R. Ford Jr. and D. R. Fulkerson, “Maximal Flow Through a Network,” *Canadian Journal of
  Mathematics* 8, 1956: <https://doi.org/10.4153/CJM-1956-045-5>
- M. H. Liffiton and K. A. Sakallah, “Algorithms for Computing Minimal Unsatisfiable Subsets of
  Constraints,” *Journal of Automated Reasoning* 40(1), 2008:
  <https://doi.org/10.1007/s10817-007-9084-z>
- U. Junker, “QUICKXPLAIN: Preferred Explanations and Relaxations for Over-Constrained Problems,”
  AAAI 2004: <https://cdn.aaai.org/AAAI/2004/AAAI04-027.pdf>
- L. Moreau and P. Missier, eds., *PROV-DM: The PROV Data Model*, W3C Recommendation, 2013:
  <https://www.w3.org/TR/2013/REC-prov-dm-20130430/>
- B. Korel and J. Laski, “Dynamic Program Slicing,” *Information Processing Letters* 29(3), 1988:
  <https://doi.org/10.1016/0020-0190(88)90054-3>
- E. G. Gilbert, D. W. Johnson, and S. S. Keerthi, “A Fast Procedure for Computing the Distance
  Between Complex Objects in Three-Dimensional Space,” *IEEE Journal on Robotics and Automation*
  4(2), 1988: <https://doi.org/10.1109/56.2083>
- J. Pan, S. Chitta, and D. Manocha, “FCL: A General Purpose Library for Collision and Proximity
  Queries,” ICRA 2012: <https://doi.org/10.1109/ICRA.2012.6225337>
