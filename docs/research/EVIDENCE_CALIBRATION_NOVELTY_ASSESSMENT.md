# Evidence-calibrated robot explanation: novelty assessment

**Audit date:** 2026-09-29  
**Purpose:** Submission-positioning check for TRUSTMORE 2026 / IEEE BigData.  
**Scope:** Primary papers, official proceedings/publisher records, and author-released artifacts
already verified in this repository. This is a focused audit, not a systematic review and not proof
of priority. The more detailed source analysis remains in
[`EVIDENCE_CALIBRATED_EXPLANATION_FOUNDATIONS.md`](EVIDENCE_CALIBRATED_EXPLANATION_FOUNDATIONS.md).

## Conclusion

The defensible contribution is the **scoped combination and its prospective evaluation**:

> Hold a robot episode fixed; deterministically vary only the robot-visible evidence through a
> nested, removal-only ladder; keep evaluator-only physical truth inaccessible to every method;
> and test whether each method emits the deepest diagnosis justified by that evidence without
> sacrificing a prespecified amount of useful supported diagnosis.

This is stronger and safer than claiming that CRANE invents attribution, abstention, atomic
factuality, evidence removal, robot-failure explanation, provenance-to-language generation, or
ROS/Nav2 RAG. All of those have clear precedents. The literature checked here did not expose an
evaluated robot benchmark with the exact combination above, but that remains a **review-scoped
gap**, not a defensible “first” claim.

## What is prior art

| Topic | Primary-source precedent | Consequence for CRANE |
|---|---|---|
| Support relative to supplied evidence | Attributable to Identified Sources separates whether an utterance is supported by identified sources from source quality and other output properties [Rashkin et al.](https://doi.org/10.1162/coli_a_00486). | Do not claim that source-conditioned evidential support is new. Use it to motivate the distinction between support and world truth. |
| Atomic support | FActScore decomposes generated text into atomic facts and scores support against a designated source; it also warns that factual precision rewards short answers or abstention unless content quantity/response rate is reported [Min et al.](https://doi.org/10.18653/v1/2023.emnlp-main.741). | Pair unsupported-specificity risk with supported diagnostic recall or coverage. Zero claims is not a successful explanation. |
| Abstention and risk--coverage | SelectiveNet optimizes selective risk subject to a target coverage and evaluates risk jointly with coverage [Geifman and El-Yaniv](https://proceedings.mlr.press/v97/geifman19a.html). | Do not claim to introduce selective prediction or risk--coverage. CRANE's narrower distinction is clause-level retention of a supported partial diagnosis rather than rejection of an entire prediction. |
| Controlled evidence removal | ERASER removes or retains rationale spans to measure comprehensiveness and sufficiency [DeYoung et al.](https://doi.org/10.18653/v1/2020.acl-main.408). Contrast sets test local consistency under small, meaningful input changes [Gardner et al.](https://doi.org/10.18653/v1/2020.findings-emnlp.117). | Evidence intervention is not new. CRANE's estimand differs: what the explanation is justified in asserting, not what internally caused a model prediction. |
| Robot failure explanation | Causal contrastive explanations, hierarchical failure summaries, geometry-based planner-failure explanations, and multimodal coherence/non-entailment are already studied by [Diehl and Ramirez-Amaro](https://doi.org/10.1109/LRA.2022.3188889), [Liu et al.](https://proceedings.mlr.press/v229/liu23g.html), [Liu and Brandao](https://doi.org/10.1109/ICRA57147.2024.10611577), and [Pramanick and Rossi](https://doi.org/10.1109/IROS58592.2024.10802671). | Do not claim first robot diagnosis, first natural-language failure explanation, or first entailment-based evaluation. |
| Provenance and robot-record explanation | Explainability-by-Design already connects provenance capture, queries, explanation plans, and realization [Huynh et al.](https://arxiv.org/abs/2206.06251). Fernández-Becerra et al. already provide ROS/Nav2 record retrieval, agentic RAG, calculations, source/event-aware answers, and hallucination grading [ESWA](https://doi.org/10.1016/j.eswa.2026.132631), plus accountable recording and text/visual explanation context [IGPL](https://doi.org/10.1093/jigpal/jzaf016). | Do not claim novelty for black-box recording, source-aware explanation, agentic RAG, VLM context, or hallucination grading. Retrieved-record support is not independent validation of the record's physical causal attribution. |

## TRUSTMORE-safe claims for the three contributions

### C1 — Formalization

Defensible:

- a robot-specific typed relation among evaluator-only physical truth, a robot-visible evidence
  condition, atomic claim requirements, forbidden implications, and maximum justified diagnostic
  depth;
- an operational label for `PHYSICALLY_TRUE_BUT_UNSUPPORTED`, obtained by joining physical truth
  with a separate visible-evidence support judgment; and
- a distinction among supported partial diagnosis, ambiguity, insufficient evidence, false premise,
  and non-triggering.

Risk boundary: this is a domain-specific synthesis and executable formalization, not the invention
of attribution or atomic support. A physically true claim can remain unjustified to the robot; a
claim supported by a log need not be physically or causally correct.

### C2 — Controlled benchmark

Defensible if implemented and frozen as specified:

- same-episode nested evidence conditions with a machine-checked set-inclusion relation;
- deterministic removal-only masks, with physical truth fixed across conditions;
- evaluator-side maximum-defensible-diagnosis references for every condition;
- false-premise and missing-evidence controls that still reward useful lower-level information; and
- episode-clustered inference, so masks, questions, generations, and annotations do not inflate
  independent sample size.

Risk boundary: call these **nested evidence interventions**, not a new theory of contrast sets or a
test of model-internal faithfulness. Evidence monotonicity must be contract-relative: additional
evidence may reveal a contradiction and invalidate an earlier diagnosis, so “more evidence always
means a deeper diagnosis” is false.

### C3 — Contract method and evaluation

Defensible after prospective evidence exists:

- selecting the maximal supported diagnostic node, retaining useful shallower claims, and attaching
  explicit limitations/non-entailments;
- constrained realization and claim-ID-aware verification against approved claims and values; and
- a fair B2/B4 comparison of episode-level evidence-calibration failures while enforcing a
  development-frozen useful-coverage requirement.

Risk boundary: a positive result supports lower calibration risk under the tested contracts and
population. It does not establish better physical-cause discovery, better general reasoning,
human trust, model faithfulness, hardware transfer, or universal safety. If B4 lowers unsupported
specificity but also lowers useful coverage, both results are part of the finding.

## Language to use and avoid

Use:

- “We test whether diagnostic specificity tracks the robot-visible evidence available for the
  same physical episode.”
- “We distinguish physical truth in evaluator-only state from evidential support available to the
  explanation method.”
- “Prior attribution, selective-prediction, and rationale-erasure work motivates our metrics; we
  specialize these ideas to governed robot diagnostics and same-episode evidence ladders.”
- “Our results are episode-clustered and concern evidence calibration at useful coverage.”

Avoid:

- “the first evidence-aware/faithful/abstaining robot explanation system”;
- “evidence monotonicity proves the model used the evidence”;
- “support by a retrieved record proves the physical cause”;
- “a camera-visible obstacle was consumed by Nav2 or caused replanning” without the corresponding
  runtime chain;
- “a blocked direct segment proves global infeasibility”; and
- any superiority statement before the frozen prospective analysis supports it.

## Highest novelty risks before submission

1. **Combination-as-priority risk.** The exact combination appears differentiated in this focused
   audit, but only a broader systematic search could support “first.” State the design directly and
   omit priority language.
2. **Faithfulness conflation.** Evidence sensitivity is not model-internal faithfulness. Reserve
   “faithfulness” for a direct dependence test or use “evidential support/calibration.”
3. **Truth/support collapse.** Gold physical mechanism and method-visible support must remain
   separately stored and annotated. Otherwise the headline distinction becomes circular.
4. **Abstention gaming.** Unsupported-claim reduction without frozen coverage can be obtained by
   silence. Retained supported diagnosis is necessary to interpret any risk reduction.
5. **Robot-causality overreach.** Provenance, VLM observations, planner logs, and retrieved causal
   text do not by themselves demonstrate physical causation or subsystem consumption.
6. **Intervention leakage or pseudoreplication.** Masks must remove rather than rewrite evidence,
   and all conditions from one episode must remain one statistical unit.
7. **Closest-work omission.** The submission must position Fernández-Becerra et al., Huynh et al.,
   REFLECT, causal/geometric robot explanations, and Pramanick--Rossi's robot-failure entailment
   evaluation, not only generic NLG work.

## Source-verification note

The cited claims were cross-checked against the repository's prior primary-source audits, locally
retained primary PDFs for AIS, ERASER, and contrast sets, and official/author records documented in
the linked foundation notes. Live publisher re-checking was unavailable during this pass because
DNS resolution failed. The IGPL article's detailed methods and numerical results remain
full-text-unverified here; only its publisher metadata/abstract and author-released implementation
should support positioning claims until the version of record is checked page by page.
