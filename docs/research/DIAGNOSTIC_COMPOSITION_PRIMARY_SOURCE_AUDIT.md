# Primary-source audit of finite diagnostic composition

**Audit date:** 2026-09-25  
**Scope:** Narrow review of the executable finite-composition candidate in
[`STRUCTURED_DIAGNOSTIC_COMPOSITION.md`](STRUCTURED_DIAGNOSTIC_COMPOSITION.md), its prospective
study design, benchmark, and claim-to-evidence boundary. This is development guidance, not an
amendment to a frozen protocol and not evidence that CRANE outperforms baseline R.

## Bottom line

The current primary-source basis is adequate for testing a small, deterministic composition
layer. Reiter/de Kleer support consistency-based diagnosis and explicit assumption environments;
cautious versus brave consequences support the finite all-model/some-model test; and Sampath et
al. support treating observationally indistinguishable mechanisms as unresolved. None of those
sources establishes that CRANE's registry is complete, that its observations are physically
correct, or that an entailed registry predicate is a real-world physical cause.

The method is therefore scientifically defensible only as **checked consequence over a declared,
bounded mechanism model**. Its prospective value must come from measured improvements in mechanism
identification, decisive-unit preservation, and qualification under masking—not from presenting
finite enumeration as a new diagnosis or causal-inference formalism.

## Proposition-by-proposition assessment

| CRANE proposition | Primary-source basis | What the source does not license | Project implication |
| --- | --- | --- | --- |
| Candidate mechanism states may be represented as consistency-preserving assignments under a system description and observations. | Reiter defines diagnosis relative to a system description, observed behavior, and abnormality assumptions; de Kleer and Williams develop conflict/candidate reasoning for multiple faults ([Reiter 1987](https://doi.org/10.1016/0004-3702(87)90062-2); [de Kleer and Williams 1987](https://doi.org/10.1016/0004-3702(87)90063-4)). | A consistency diagnosis need not be the actual physical cause. The cited theory does not validate CRANE's predicates, thresholds, observation quality, or registry completeness. | Say “entailed by registry version X and evidence packet Y,” not “proved root cause,” unless a separately valid causal/physical test supports that stronger claim. |
| An assumption environment and its inconsistent combinations can be retained as an auditable explanation of a derived proposition. | The ATMS associates propositions with the assumption environments in which they hold and records inconsistent environments as nogoods ([de Kleer 1986](https://doi.org/10.1016/0004-3702(86)90080-9)). | An ATMS label is a symbolic dependency record, not proof that an input measurement is true or that the relationship is causal. | Support sets and conflict sets are useful audit certificates, but they must retain the input/model hashes and their scope limitations. |
| A finite composer can distinguish claims true in all admissible states, some states, or no states. | The Potassco guide defines cautious consequences over all answer sets and brave consequences over some answer set; `clingo` exposes both enumeration modes ([Potassco Guide 2.2.0, section 9.1](https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf)). | This semantic analogy does not make CRANE's hand-authored model complete or its predicates causal. | The current exhaustive-enumeration implementation is sufficient for a deliberately small registry. A general ASP dependency is not required for the study claim. |
| Mechanisms that cannot be distinguished from the retained observation history must remain unresolved. | Sampath et al. define diagnosability relative to a discrete-event system and its observable-event projection, explicitly exposing fault classes that cannot be distinguished from observation histories ([Sampath et al. 1995](https://doi.org/10.1109/9.412626)). | Their theorem applies to their modeled discrete-event setting; it does not prove that a bounded CRANE episode is diagnosable or that CRANE has captured every discriminator. | Treat the source as the basis for the distinction, not as a theorem already satisfied by CRANE. Each study family still needs declared discriminators and masking tests. |
| Recorded use or execution dependence may be distinguished from mere availability of an observation. | PROV-DM defines `used` as an activity beginning to utilize an entity; backward dynamic slicing identifies executed statements that affected a selected value ([W3C PROV-DM 2013](https://www.w3.org/TR/2013/REC-prov-dm-20130430/); [Korel and Laski 1988](https://doi.org/10.1016/0020-0190(88)90054-3)). | Provenance use and program dependence do not by themselves establish physical causal responsibility, sufficiency, or the counterfactual claim that the decision would have differed without the observation. | Preserve separate predicates for observation presence, runtime delivery/use, decision dependence, and physical mechanism. Never promote one to another implicitly. |
| A grid disconnection can have a checkable separating-cut certificate. | The max-flow/min-cut result establishes a cut certificate in the represented graph ([Ford and Fulkerson 1956](https://doi.org/10.4153/CJM-1956-045-5)). | The certificate does not establish continuous-space infeasibility, physical obstruction, or failure for a different footprint/cost policy. | State the grid, footprint/cost policy, and coverage boundary in both certificate and language. |

## Missing foundation worth adding

The present note correctly restricts causal language, but its formal citations principally cover
diagnosis, logical consequence, provenance, and observability. Pearl's structural account is a
useful primary foundation for the missing boundary between observational association and causal or
counterfactual claims: causal conclusions require an explicit causal model and assumptions that
connect observations or interventions to that model ([Pearl, *Causality: Models, Reasoning, and
Inference*, 2nd ed., 2009](https://doi.org/10.1017/CBO9780511803161)).

This source supports a restraint rule, not a new workstream:

- temporal order, co-occurrence, a log assertion, provenance `used`, or a dynamic dependency is
  insufficient on its own for a physical-cause or counterfactual conclusion;
- controlled reruns may support a bounded intervention claim only when the intervention, restored
  initial state, relevant assumptions, and remaining nondeterminism are recorded;
- a registry constraint may limit the language to a mechanism-level observation without licensing
  a unique latent cause such as collision, actuator rejection, slip, current, or waves.

No broad structural-causal-model implementation is needed before submission. The smallest useful
change is to cite this boundary wherever the composer assigns a causal-language ceiling and to
test that observation, lineage, and chronology predicates cannot alone unlock a causal claim.

## Challenge to the candidate method

The main validity threat is **model-relative overconfidence**. Exhaustive enumeration can be
complete over the implemented Boolean registry while the registry omits a physically possible
mechanism, an observation is stale or misframed, or a numeric diagnostic is inapplicable. In those
cases an `entailed` predicate is only a consequence of the encoded model. The certificate should
therefore retain, and final language should expose when relevant:

1. registry/model identifier and hash;
2. applicability and evidence-completeness predicates;
3. measurement interval, unit, frame, and source identity;
4. explicitly modeled alternatives and missing discriminators;
5. an `out_of_model_possible` or equivalent scope marker that prevents “only possible cause”
   wording unless the candidate set's completeness has independent support.

This limitation should also shape reference labels. A reference inventory may require the deepest
mechanism entailed within a declared diagnostic contract, but it must not label a unique physical
root cause merely because no other registry entry remains.

## Fair comparison with tool-enabled R

No additional foundational citation is required to justify the current R comparison. It is an
experimental contrast, not a theorem from the diagnosis literature. Its interpretation depends on
enforcing and retaining the parity conditions already stated in the study:

- identical robot-visible evidence and relevant source/configuration access;
- identical primitive diagnostic and deterministic calculation tools and descriptions;
- comparable model, call, token, wall-time, and retry budgets;
- no access by R to P's episode-specific certificate, checked plan, verifier state, or fallback;
- complete tool-call/result and resource-use logs for both conditions.

Under that contrast, a positive result would support mandatory checked composition as an
orchestration policy. It would not isolate a novel reasoning formalism. If R voluntarily executes
the generic composer or otherwise reproduces the same certificate within its matched budget, a tie
is the scientifically correct outcome. Withholding primitive tools, source, or material evidence
from R would instead test information/tool advantage and should not be used for the primary claim.

## Minimum prospective checks implied by this audit

Before freezing another candidate, retain deterministic tests showing that:

- removing evidence can weaken `entailed` to `unresolved` but cannot create a stronger conclusion;
- contradictory inputs produce `evidence_problem`, not an arbitrary diagnosis;
- visible obstacle, logged obstacle wording, replanning, and recovery chronology cannot unlock a
  physical-cause claim without the separately required physical and consumption/dependence facts;
- matched terminal symptoms remain distinguishable only when the declared geometry or
  command-to-motion discriminator is present;
- out-of-model and masked-evidence cases keep supported execution facts while qualifying the
  unresolved mechanism;
- answer-plan required units are compiled from certificate identifiers so the mechanism,
  decisive measurements, and limitations cannot silently disappear in realization.

These checks support development promotion only. Statistical advantage still requires fresh
independent scenario configurations, held-out-qualified semantic evaluation, the frozen fair R
comparison, prospective guardrails, and replication.

## Sources checked

- R. Reiter, “A Theory of Diagnosis from First Principles,” *Artificial Intelligence* 32(1),
  1987. <https://doi.org/10.1016/0004-3702(87)90062-2>
- J. de Kleer, “An Assumption-Based TMS,” *Artificial Intelligence* 28(2), 1986.
  <https://doi.org/10.1016/0004-3702(86)90080-9>
- J. de Kleer and B. C. Williams, “Diagnosing Multiple Faults,” *Artificial Intelligence* 32(1),
  1987. <https://doi.org/10.1016/0004-3702(87)90063-4>
- Potassco, *A Guide to the `gringo` Grounder and `clingo` Solver*, version 2.2.0, section 9.1.
  <https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf>
- M. Sampath et al., “Diagnosability of Discrete-Event Systems,” *IEEE Transactions on Automatic
  Control* 40(9), 1995. <https://doi.org/10.1109/9.412626>
- W3C, *PROV-DM: The PROV Data Model*, Recommendation, 2013.
  <https://www.w3.org/TR/2013/REC-prov-dm-20130430/>
- B. Korel and J. Laski, “Dynamic Program Slicing,” *Information Processing Letters* 29(3), 1988.
  <https://doi.org/10.1016/0020-0190(88)90054-3>
- L. R. Ford Jr. and D. R. Fulkerson, “Maximal Flow Through a Network,” *Canadian Journal of
  Mathematics* 8, 1956. <https://doi.org/10.4153/CJM-1956-045-5>
- J. Pearl, *Causality: Models, Reasoning, and Inference*, 2nd ed., Cambridge University Press,
  2009. <https://doi.org/10.1017/CBO9780511803161>

