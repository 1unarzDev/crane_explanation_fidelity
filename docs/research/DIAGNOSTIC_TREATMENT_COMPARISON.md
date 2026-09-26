# Bounded comparison of diagnostic treatments

**Audit date:** 2026-09-25
**Scope:** Development selection for the prospective physical-diagnosis study. This note compares
four narrow treatments against a fair tool-enabled repository agent R. It does not amend a frozen
protocol, report an effectiveness result, or authorize confirmatory generation.

## Recommendation

Keep **mandatory finite checked diagnostic composition plus deterministic rendering** as the
highest-value candidate to test. Treat the diagnostic certificate as a proof-carrying internal
artifact, not as a separate method. Do not add a general abductive solver, constrained language
decoder, or new agent framework before the bounded development comparison.

This recommendation is about expected separability, not demonstrated superiority. The candidate
is the only option considered here that makes all four desired behaviors mandatory before language:

1. select only mechanisms entailed by the declared finite model and retained evidence;
2. compile the decisive measurements into required answer units;
3. cap causal language and retain compatible alternatives;
4. recompute after masking, leaving absent facts unconstrained and naming missing discriminators.

R may still reproduce all four behaviors. If it does so reliably with the same resources, the
correct prospective result is a tie. The plausible advantage is **tail reliability**: a lower
omission and composition failure rate across diverse clusters, not access to more evidence, a
stronger model, or a novel diagnosis formalism.

## Primary-source comparison

| Treatment | What the primary source supports | Expected separation from fair R | Principal failure modes | Decision |
|---|---|---|---|---|
| **A. Mandatory finite composition, certificate, and deterministic rendering** | Consistency-based diagnosis defines candidates relative to a system description and observations; conflict/hitting-set methods retain alternatives rather than guessing one cause ([Reiter 1987](https://doi.org/10.1016/0004-3702(87)90062-2); [de Kleer and Williams 1987](https://doi.org/10.1016/0004-3702(87)90063-4)). Cautious consequences hold in every answer set and brave consequences in some ([Potassco Guide 2.2.0, sec. 9.1](https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf)). | **Highest of the four, but unproved.** A mandatory compiler can prevent skipped alternatives, missing measurements, and causal upgrades even when R has the same primitive tools. Deterministic rendering can preserve every compiled unit. | Registry incompleteness; incorrect primitive predicates; hand-authored answer units leaking unavailable knowledge; rigid or less useful text; a tie if R follows the same visible rules; apparent gains caused only by templating. | **Test this bounded composite treatment.** Describe it as checked consequence over a declared model, not root-cause proof. Retain fallback frequency and T so any rendering contribution is visible. |
| **B. Plan-first generation with constrained decoding** | A symbolic text plan can explicitly fix fact grouping, order, and direction before neural realization, but the reported realizer still exhibited omissions, wrong lexicalizations, and over-generation ([Moryossef, Goldberg, and Dagan 2019](https://doi.org/10.18653/v1/N19-1236)). PICARD rejects inadmissible tokens incrementally by parsing partial SQL outputs against its constraints ([Scholak, Schucher, and Bahdanau 2021](https://doi.org/10.18653/v1/2021.emnlp-main.779)). | **Low for mechanism identification; medium for surface preservation.** It can force a schema, identifiers, or allowed vocabulary, but it cannot repair a missing or incorrect diagnosis in the plan. R already identifies most central mechanisms in development. | Syntactically admissible but physically unsupported content; omitted required meaning despite valid form; provider-specific decoding integration; reduced naturalness; a new implementation with little effect on the primary endpoint. | **Do not add now.** The existing checked plan and exact deterministic renderer are stronger for this small finite content set. Optional realization remains downstream of a correct certificate. |
| **C. Free-form diagnosis followed by a proof-carrying answer check** | Proof-carrying code separates an untrusted producer from a consumer that checks a supplied proof against a safety policy ([Necula 1997](https://doi.org/10.1145/263699.263712)). The relevant analogy is a response claim accompanied by a checkable derivation and evidence identifiers. | **Medium for material-error control, low for finding an omitted mechanism.** A checker can reject unauthorized claims, but cannot make a free-form producer include the deepest supported mechanism or decisive measurements unless those become required obligations—at which point it has become treatment A's compiler. | Vacuous safe answers; high fallback/abstention; proof covers the encoded rule but not sensor truth or physical causality; circular certificates produced and checked by the same faulty logic; post-hoc repair hiding raw failure. | **Absorb into A.** Independently test the certificate checker and primitive references. Do not present “proof-carrying answers” as a separate novelty or infer physical truth from checker acceptance. |
| **D. Tool-enforced or autonomous agent workflow** | ReAct interleaves language reasoning with actions and observations, and reports gains from that interaction on its evaluated tasks ([Yao et al. 2023](https://openreview.net/forum?id=WE_vluYUL-X)). Program-aided language models delegate generated programs to an external runtime for computation ([Gao et al. 2023](https://proceedings.mlr.press/v202/gao23f.html)). Neither supplies a correctness theorem for tool selection or final synthesis. | **Low against a strengthened R.** R is already repository-aware and tool-enabled. Requiring a fixed sequence of tool calls can improve execution regularity, but once its postconditions determine mechanism, alternatives, and required units, the workflow is substantively A. | Wrong tool choice or arguments; skipped calls; correct tool results mistranscribed in language; more calls and budget; unfair advantage if only P receives a useful composite tool; difficult attribution between orchestration and information access. | **Use the strongest development-selected version as R's execution protocol if it improves R.** Log calls/results and enforce budgets. Do not introduce a separate agent framework merely to rename the same workflow. |

## Why a larger diagnosis/abduction engine is not the next step

Treatment A is already a bounded form of consistency-based model diagnosis. A general solver could
compute minimal conflicts, diagnoses, or unsatisfiable cores, but it would not fix an incomplete
mechanism registry or an incorrect measurement. Reiter's diagnosis is explicitly relative to the
system description and observations; an internally unique diagnosis is not automatically the real
physical cause. The current small registry can be exhaustively enumerated and independently tested,
so a general solver adds validation and dependency cost without an obvious new source of separation
from R.

If the registry later outgrows exhaustive enumeration, subset-minimal unsatisfiable-set algorithms
are an established way to produce compact conflict certificates
([Liffiton and Sakallah 2008](https://doi.org/10.1007/s10817-007-9084-z)). That is an implementation
substitution, not a new scientific treatment.

## Fairness conditions for the recommended test

The comparison is defensible only if all of the following hold:

- R and P receive byte-identical robot-visible evidence and the same relevant source/configuration.
- R receives the same primitive geometry, motion, provenance, and deterministic calculation tools,
  their descriptions, the generic candidate/checker interface, and the registry/rule source. It
  may write scripts or templates within its declared budget. It does not receive P's
  episode-specific composition certificate, compiled answer plan, verifier verdict, or final
  fallback.
- The composer is defined as P's mandatory policy, not mislabeled as a primitive measurement tool.
  If R receives the completed certificate, the comparison reduces to realization.
- Model identity/settings, call and retry limits, token budget, wall time, and permitted filesystem
  scope are comparable. Deterministic composition cost and every R tool call are recorded.
- Required units and answer text are derived only from method-visible measurements and declared
  rules. They may not contain evaluator intervention identities, gold mechanism labels, or facts
  unavailable to R.
- Raw P realization, verification, repair/fallback, deterministic T, and final P are retained
  separately. If final P is almost always T, report the tested system as deterministic composition
  and rendering rather than successful LLM reasoning.
- Development selection and confirmatory configurations remain disjoint; masks, paraphrases,
  generations, and judge passes never become independent scenario units.

Before freeze, select R's strongest prompt and tool-use workflow on development evidence, even if
that workflow makes tool inspection mandatory. Do not retain a weaker discretionary-tool R because
it creates a larger P contrast. If strengthened R reconstructs the same certificate within budget,
that removes the claimed semantic advantage and is the informative result.

These conditions deliberately allow R to read and reason about the rule definitions. The tested
difference is whether a mandatory checked path executes those rules more reliably than the
strongest capable agent workflow selected without access to P's episode-specific result.

## Failure criteria before confirmation

Do not advance this candidate merely because its unit tests pass. Reject or revise it in development
if any of these occur:

- removing decisive evidence leaves the stronger mechanism entailed;
- a visible/logged obstacle or temporal order unlocks a consumption or causal claim;
- a supported mechanism can render without all registered decisive measurements and limits;
- contradictory inputs yield an ordinary diagnosis instead of `evidence_problem`;
- false-premise or nominal cases lose useful supported measurements;
- the registry's `out_of_model_possible` scope disappears from a claim of uniqueness;
- P's apparent wins arise from hand-authored answer-unit text, extra information, extra calls, or
  repeated sampling;
- gains occur only in one template/family or disappear when R uses the provided primitive tools;
- material-error risk or useful coverage violates the prospectively fixed guardrails.

The most informative bounded development comparison therefore uses the existing diverse mechanism,
masked-evidence, visible-but-not-consumed, nominal, false-premise, and ambiguous families. It should
measure the composite system exactly as it would be frozen. It should not trigger a new language
model campaign, broaden the environment suite, or consume confirmatory configurations merely to
make the candidate look promising.

## Claim supported if later results are positive

A positive prospective result could support:

> Mandatory checked composition and deterministic realization of independently computed diagnostic
> predicates improved supported diagnostic success over a comparably resourced, tool-enabled
> repository agent on the tested navigation families, without violating the declared material-error,
> useful-coverage, or ambiguity guardrails.

It would not support novelty for model-based diagnosis, plan-first generation, constrained decoding,
proof-carrying computation, tool-using agents, or deterministic templates. It would also not prove
registry completeness, unique physical causation, hardware reliability, or generalization beyond
the tested mechanism families.

## Primary sources

- R. Reiter, “A Theory of Diagnosis from First Principles,” *Artificial Intelligence* 32(1), 1987:
  <https://doi.org/10.1016/0004-3702(87)90062-2>
- J. de Kleer and B. C. Williams, “Diagnosing Multiple Faults,” *Artificial Intelligence* 32(1),
  1987: <https://doi.org/10.1016/0004-3702(87)90063-4>
- Potassco, *A User's Guide to gringo, clasp, clingo, and iclingo*, version 2.2.0:
  <https://github.com/potassco/guide/releases/download/v2.2.0/guide.pdf>
- A. Moryossef, Y. Goldberg, and I. Dagan, “Step-by-Step: Separating Planning from Realization in
  Neural Data-to-Text Generation,” NAACL 2019: <https://doi.org/10.18653/v1/N19-1236>
- T. Scholak, N. Schucher, and D. Bahdanau, “PICARD: Parsing Incrementally for Constrained
  Auto-Regressive Decoding from Language Models,” EMNLP 2021:
  <https://doi.org/10.18653/v1/2021.emnlp-main.779>
- G. C. Necula, “Proof-Carrying Code,” POPL 1997: <https://doi.org/10.1145/263699.263712>
- S. Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” ICLR 2023:
  <https://openreview.net/forum?id=WE_vluYUL-X>
- L. Gao et al., “PAL: Program-aided Language Models,” ICML 2023:
  <https://proceedings.mlr.press/v202/gao23f.html>
- M. H. Liffiton and K. A. Sakallah, “Algorithms for Computing Minimal Unsatisfiable Subsets of
  Constraints,” *Journal of Automated Reasoning* 40(1), 2008:
  <https://doi.org/10.1007/s10817-007-9084-z>
