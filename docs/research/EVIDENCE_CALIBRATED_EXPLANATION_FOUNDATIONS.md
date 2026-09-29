# Primary-source foundations for evidence-calibrated robot explanations

**Audit date:** 2026-09-28  
**Scope:** Focused primary-source audit for the redirected CRANE thesis: claim-level evidential
support, selective prediction and abstention, controlled evidence interventions, and the closest
robot-explanation evaluations already cited by this repository. This is neither a systematic
review nor empirical evidence for CRANE, and it does not establish literature-wide novelty.

## Bottom line

The redirected thesis has a defensible scientific center, but its individual ingredients have
clear precedents:

- selective prediction already requires risk to be interpreted jointly with coverage;
- atomic factuality and attribution work already separates support by a specified source from
  fluency and completeness;
- rationale and contrast-set work already evaluates behavior under controlled input removal or
  local perturbation;
- robot-explanation work already covers causal models, geometric motion-planning explanations,
  failure summaries, provenance-to-language pipelines, ROS/Nav2 retrieval, hallucination grading,
  multimodal context, and cross-modal entailment/non-entailment.

CRANE should therefore claim exactly the scoped combination it tests: **for the same prospective
robot episode, does the diagnostic specificity of a natural-language explanation track nested,
robot-visible evidence conditions, including when the physically true mechanism is not justified
by the visible evidence?** The strongest distinction is experimental and representational, not a
claim that support checking, abstention, perturbation testing, or robot failure explanation is new.

## Concepts the literature supports—and does not support

| CRANE term | Closest audited precedent | Safe interpretation for this project | Boundary that must remain explicit |
|---|---|---|---|
| **Evidential support** | Attributable to Identified Sources (AIS) asks whether all information conveyed by an interpretable output is supported by identified sources; source quality and relevance are separate evaluations [Rashkin et al. 2023](https://doi.org/10.1162/coli_a_00486). | Judge each atomic claim against the permitted robot-visible evidence named by its contract. | Support by the supplied record is not proof that the record is physically true, causally complete, or actually used by another subsystem. |
| **Unsupported specificity** | AIS counts even partially unsupported information as not fully attributable; FActScore scores the fraction of atomic facts supported by a designated source [Rashkin et al. 2023](https://arxiv.org/abs/2112.12870v2), [Min et al. 2023](https://doi.org/10.18653/v1/2023.emnlp-main.741). | A deeper mechanistic claim fails when its required visible evidence is absent, even if evaluator-only state shows that it happened. | This is an epistemic error, not necessarily a physical-factual error. |
| **Useful partial diagnosis / over-abstention** | FActScore explicitly warns that factual precision alone rewards saying fewer facts or abstaining, and recommends reporting response rate and fact count; SelectiveNet optimizes selective risk subject to coverage [Min et al. 2023](https://aclanthology.org/2023.emnlp-main.741/), [Geifman and El-Yaniv 2019](https://proceedings.mlr.press/v97/geifman19a.html). | Report unsupported-claim risk together with supported diagnostic recall and retained coverage. | A silent system can have zero unsupported claims and still be diagnostically useless. |
| **Evidence intervention** | ERASER removes or retains rationale spans to measure comprehensiveness and sufficiency; contrast sets make small, meaningful input changes and score consistency [DeYoung et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.408), [Gardner et al. 2020](https://doi.org/10.18653/v1/2020.findings-emnlp.117). | Apply deterministic, removal-only masks to a fixed episode and test whether permitted specificity changes at the declared boundary. | ERASER's intervention tests whether a model relied on a rationale; CRANE's intervention tests what an explanation is justified in asserting. These are not the same notion of faithfulness. |
| **Evidence monotonicity** | Contrast-set consistency tests local stability under expert-authored perturbations, while ERASER measures prediction change after evidence removal [Gardner et al. 2020](https://aclanthology.org/2020.findings-emnlp.117/), [DeYoung et al. 2020](https://aclanthology.org/2020.acl-main.408/). | A weaker evidence packet must not retain claims whose declared requirements occur only in a stronger packet. | Monotonicity is contract-relative: adding genuinely conflicting evidence may invalidate a previously supported claim, so the formalism must allow contradiction and ambiguity rather than demand only deeper diagnoses. |
| **Physically true but unsupported** | AIS deliberately evaluates attribution to the supplied source separately from source quality and other response properties [Rashkin et al. 2023](https://arxiv.org/pdf/2112.12870v2). | Evaluator truth and visible-evidence support are two separately stored labels. A true hidden intervention can remain impermissible in method output. | The phrase is CRANE's robot-specific evaluation distinction, not a claim that AIS introduced evaluator-only robot truth. |
| **Model faithfulness** | ERASER defines faithful rationales in terms of what influenced a model's prediction and uses input erasure to test that relation [DeYoung et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.408). | Reserve the term for a direct test of dependence on a model's internal decision process. | Nested robot-evidence masks establish evidence sensitivity or calibration, not internal model faithfulness. |

## Primary methodological precedents

### 1. Attribution is support by an identified source, not world truth

Rashkin et al. formalize **Attributable to Identified Sources (AIS)** around the information an
utterance conveys in context. Their annotation procedure first checks interpretability and then
asks whether *all* conveyed information is supported by the supplied source. It treats missing
context or a small meaning-changing detail as an attribution failure. Crucially, the protocol
separates attribution from source quality, relevance, and fluency
([formalism and annotation guidelines](https://arxiv.org/pdf/2112.12870v2),
[version-of-record DOI](https://doi.org/10.1162/coli_a_00486)).

This is the cleanest primary-source basis for CRANE's epistemic boundary. An utterance can be true
in the world yet not attributable to the evidence supplied to the method; conversely, faithful
repetition of a faulty log can be attributable without being physically correct. CRANE adds a
robot-specific evaluator plane and typed evidence requirements, but should not claim to originate
source-conditioned attribution.

AIS evaluates the whole informative utterance rather than required-content recall. CRANE therefore
still needs a separate supported-diagnostic-recall measure and required-unit inventory.

### 2. Atomic factual precision cannot stand alone

FActScore decomposes a response into atomic facts and measures the fraction supported by a chosen
knowledge source. Its authors explicitly identify missing recall as a limitation: abstention or
shorter responses can increase factual precision, so response rate and the number of facts should
also be reported. They also warn that the method assumes facts are equally weighted and support is
unambiguous, assumptions that do not hold for every causal robot claim
([paper and metadata](https://aclanthology.org/2023.emnlp-main.741/),
[DOI](https://doi.org/10.18653/v1/2023.emnlp-main.741)).

For CRANE, atomic claims are the appropriate scoring granularity, but materiality, required-unit
coverage, diagnostic depth, and causal scope must remain explicit. A safe one-clause answer cannot
receive scientific credit equivalent to a complete supported partial diagnosis merely because
both contain no unsupported facts.

### 3. Selective prediction motivates risk--coverage, not an explanation policy

SelectiveNet defines a prediction function and selection function, minimizes loss on covered
examples subject to target coverage, and evaluates risk--coverage behavior. The authors also
calibrate selection on an independent validation set because achieved coverage can miss the target
([PMLR paper and proceedings record](https://proceedings.mlr.press/v97/geifman19a.html)).

CRANE can legitimately inherit the principle that withholding and error must be evaluated jointly.
It does not implement SelectiveNet merely because a claim contract withholds a mechanism.
SelectiveNet rejects whole supervised predictions; CRANE may retain shallower supported claims
while withholding only an unsupported causal refinement. Consequently, USR and supported
diagnostic recall should be reported at claim level, and the confirmatory calibration failure and
coverage requirement should be reported at episode level.

### 4. Controlled erasure is precedent, but the estimand differs

ERASER packages inputs, labels, and human-marked rationales and distinguishes rationale
**comprehensiveness** from **sufficiency**. Its comprehensiveness intervention removes a predicted
rationale and measures the resulting change in model confidence; sufficiency retains the rationale
and tests whether it is adequate for the prediction. The paper explicitly distinguishes a
plausible human-facing rationale from evidence the model actually used
([paper](https://aclanthology.org/2020.acl-main.408/),
[DOI](https://doi.org/10.18653/v1/2020.acl-main.408)).

This supports deterministic evidence-removal experiments and the requirement to test both removal
and retention of decisive information. It does **not** authorize CRANE to call its result model
faithfulness: the proposed benchmark asks whether an emitted claim is licensed by the evidence
condition, not whether a neural model internally used that evidence.

Gardner et al.'s contrast sets are complementary precedent: dataset authors make small,
meaningful perturbations to test a model's local decision boundary and measure contrast
consistency. Their experiments span ten NLP datasets and report substantial performance drops on
the perturbed examples
([paper](https://aclanthology.org/2020.findings-emnlp.117/),
[DOI](https://doi.org/10.18653/v1/2020.findings-emnlp.117)).

CRANE's masks should be described more narrowly as **nested evidence interventions**, not generic
contrast sets: they leave the physical episode fixed, only remove permitted evidence, and keep all
conditions from one episode inside one statistical cluster. A mask must never rewrite an event to
manufacture a different world state.

### 5. Entailment/non-entailment is useful but not a sufficient robot gold standard

Pramanick and Rossi formulate coherence between a robot-failure explanation and graphical, plan,
or observation evidence as contradiction, entailment, or non-entailment. On their RoboFail-derived
data, generic NLI checkpoints performed poorly until robotics-domain fine-tuning; performance also
dropped on unseen task types. Their released evaluation therefore directly cautions against
treating generic NLI as a validated semantic judge for CRANE
([DOI](https://doi.org/10.1109/IROS58592.2024.10802671),
[author repository](https://github.com/pradippramanick/coexp-iros24),
[author preprint](https://arxiv.org/abs/2410.00659)).

Their three-way labels are useful semantic precedent, but cross-modal coherence does not establish
that the evidence was available to the explanation method, that a planner consumed an observation,
or that a physical mechanism caused an outcome. CRANE's `PHYSICALLY_TRUE_BUT_UNSUPPORTED` label
must be generated by joining separately governed evaluator truth and visible-evidence support—not
by renaming generic NLI neutrality.

## Closest robot-explanation evaluation precedents already in CRANE

| Work | What it establishes | What the evidence-calibration study must add or keep separate |
|---|---|---|
| Fernández-Becerra et al., ESWA 2026 [DOI](https://doi.org/10.1016/j.eswa.2026.132631), [author repository copy](https://hdl.handle.net/10612/28306) | Close ROS 2/Nav2 precedent for structured records, source/event-aware agentic RAG, calculations over retrieved records, hallucination grading, and natural-language evaluation. | A grader that checks traceability to retrieved records does not independently validate the record's physical causal attribution. CRANE must claim no novelty for ROS-log RAG, source-aware explanation, or hallucination grading. |
| Fernández-Becerra et al., IGPL [DOI](https://doi.org/10.1093/jigpal/jzaf016), [author code](https://github.com/laurafbec/nav2_accountability_explainability_vlms) | Precedent for accountable robot recording, replay/privacy/authenticity concerns, and textual plus visual/VLM explanation context. | Seeing an obstacle does not establish that Nav2 received, represented, consumed, or acted on it. Do not add a VLM workstream for this paper. |
| Huynh et al., Explainability-by-Design [preprint](https://arxiv.org/abs/2206.06251), [artifacts](https://github.com/plead-project/EbD-artefacts) | Provenance capture, explanation queries, explicit explanation plans, and realization are established architectural patterns. | Provenance of a modeled decision is not independent physical-cause evidence. CRANE's contract and evaluator planes must preserve that distinction. |
| Liu, Bahety, and Song, REFLECT [PMLR record](https://proceedings.mlr.press/v229/liu23g.html), [project](https://robot-reflect.github.io/) | Robot-failure summaries, hierarchical analysis, correction plans, and human judgments of whether explanations are correct and informative over simulated and real manipulation failures. | Human “correct and informative” judgments do not isolate whether specificity contracts as decisive robot-visible evidence is removed. Ground-truth simulator perception must not leak into CRANE method packets. |
| Diehl and Ramirez-Amaro [DOI](https://doi.org/10.1109/LRA.2022.3188889), [author preprint](https://arxiv.org/abs/2204.04483) | A learned causal Bayesian network and search for a nearby successful contrast produce contrastive failure explanations in manipulation tasks. | A learned causal model is itself part of the evidence/model contract. Its output must not be equated with a directly observed physical cause, and CRANE does not need a new causal-learning workstream. |
| Liu and Brandão [DOI](https://doi.org/10.1109/ICRA57147.2024.10611577) | Environment-based explanations for motion-planner failures establish nearby geometric-planning explanation work. | A restricted direct segment is not global infeasibility. CRANE's geometry contracts need independent connectivity/coverage evidence and explicit non-entailments. |
| Wachowiak et al., explanation selection [DOI](https://doi.org/10.1145/3776734.3794387), [evaluation repository](https://github.com/lwachowiak/explanation-selection-eval) | Selecting plan steps and heterogeneous XAI artifacts relevant to robot questions, plus a preliminary helpfulness comparison. | Retrieval correctness and helpfulness are not claim support under nested evidence, calibrated abstention, or explanation accuracy. |

These works are closer robot-domain precedents than generic NLG evaluation, but none should be
described as deficient merely because it studies a different estimand. This focused audit found no
evaluated robot benchmark among them whose primary manipulation is a deterministic nested ladder
of method-visible evidence for the same physical episode and whose target is maximum justified
diagnostic specificity. That is a **review-scoped gap**, not proof of priority; novelty language
must remain bounded unless a systematic review confirms it.

## Consequences for the three contributions

### C1 — Formalization

The defensible addition is a robot-specific typed relation among:

1. evaluator-only physical truth;
2. robot-visible evidence condition;
3. an atomic claim's `RequiredEvidence` contract;
4. the highest justified diagnostic abstraction node; and
5. forbidden implications/non-entailments.

Reuse attribution and atomic-support terminology, but keep these separations:

- `SUPPORTED_BY_ROBOT_EVIDENCE` is source-conditioned;
- `PHYSICALLY_TRUE_BUT_UNSUPPORTED` joins evaluator truth with failed visible-evidence support;
- `AMBIGUOUS` means multiple supported alternatives remain;
- `INSUFFICIENT_EVIDENCE` means no stronger contracted claim is licensed;
- `FALSE_PREMISE` concerns the question relative to the recorded outcome;
- `model faithfulness` is reserved for internal-decision dependence and is not a synonym for any of
  the above.

Evidence monotonicity should be stated as a requirement on **evidence-dependent claims**, with an
exception for claims invalidated by newly revealed contradiction. It is not simply “more evidence
always means a deeper answer.”

### C2 — Controlled benchmark

The benchmark's scientific leverage comes from holding the episode fixed while changing only the
permitted evidence. To separate it from ordinary perturbation testing:

- masks must only remove declared evidence;
- the evidence-set inclusion relation must be machine-checked;
- the maximum defensible diagnosis and unsupported claims must be recomputed for every condition;
- evaluator truth must remain constant and inaccessible to methods;
- all masks, questions, generations, and annotations for an episode remain one experimental
  cluster;
- both removal and restoration of decisive evidence should cross the relevant claim boundary;
- false-premise and missing-evidence controls must retain useful lower-level facts rather than
  reward blanket refusal.

This supports evidence calibration and sensitivity claims. It does not by itself establish human
trust, model faithfulness, or physical-world transfer.

### C3 — Contract method and comparative evaluation

The method's appropriate goal is not raw diagnostic superiority over a strong tool-enabled agent.
It is to select and realize the maximal supported claim set, preserving partial diagnosis and
explicit non-entailments. The evaluation should therefore pair:

- unsupported-specificity risk with supported-diagnostic recall;
- highest-level calibration with over- and under-specific decomposition;
- appropriate abstention with over-abstention;
- evidence monotonicity with claim-level evidence references;
- primary episode-level calibration failures with raw claim numerators/denominators.

B2 and B4 require the same visible evidence and permitted primitive computations. B4 may be more
conservative, so a useful-coverage floor must be frozen from development evidence before
confirmation. A positive result would support safer **evidence calibration under the tested
contracts**, not better physical discovery, general reasoning, trust, or deployment safety.

## Manuscript-safe statements

- “Prior work provides atomic source-attribution metrics, risk--coverage analysis, and controlled
  input-removal evaluations; we specialize these ideas to typed diagnostic claims over governed
  robot evidence.”
- “We distinguish whether a claim is physically true in evaluator state from whether it is
  supported by evidence available to the explanation method.”
- “Our evidence interventions hold the robot episode fixed and deterministically remove declared
  evidence, allowing explanation specificity to be audited at known diagnostic boundaries.”
- “The study evaluates evidence calibration and useful retained diagnosis, not model-internal
  faithfulness or universal root-cause discovery.”
- “ROS/Nav2 retrieval, accountable recording, source-aware explanation, hallucination grading,
  provenance-to-language planning, and multimodal context are established prior art.”

## Claims to avoid

- “CRANE is the first system to abstain, use risk--coverage, atomize claims, remove evidence, or
  verify generated explanations.”
- “A supported claim is physically true” or “a physically true claim was justified to the robot.”
- “Evidence monotonicity proves the model used the evidence internally.”
- “NLI entailment establishes physical causation or planner/controller consumption.”
- “A camera-visible obstacle caused replanning.”
- “A blocked direct route proves no feasible path exists.”
- “A provenance or retrieved log statement independently proves a physical mechanism.”
- “Repeated masks, questions, generations, or annotations are independent robot episodes.”

## Audited primary sources

1. Hannah Rashkin et al. “Measuring Attribution in Natural Language Generation Models.”
   *Computational Linguistics* 49(4):777–840, 2023. DOI
   [10.1162/coli_a_00486](https://doi.org/10.1162/coli_a_00486); author preprint
   [arXiv:2112.12870v2](https://arxiv.org/abs/2112.12870v2).
2. Sewon Min et al. “FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form
   Text Generation.” *EMNLP 2023*, pp. 12076–12100. DOI
   [10.18653/v1/2023.emnlp-main.741](https://doi.org/10.18653/v1/2023.emnlp-main.741).
3. Yonatan Geifman and Ran El-Yaniv. “SelectiveNet: A Deep Neural Network with an Integrated Reject
   Option.” *ICML 2019*, PMLR 97:2151–2159.
   [Official proceedings record](https://proceedings.mlr.press/v97/geifman19a.html).
4. Jay DeYoung et al. “ERASER: A Benchmark to Evaluate Rationalized NLP Models.” *ACL 2020*,
   pp. 4443–4458. DOI
   [10.18653/v1/2020.acl-main.408](https://doi.org/10.18653/v1/2020.acl-main.408).
5. Matt Gardner et al. “Evaluating Models' Local Decision Boundaries via Contrast Sets.” *Findings
   of EMNLP 2020*, pp. 1307–1323. DOI
   [10.18653/v1/2020.findings-emnlp.117](https://doi.org/10.18653/v1/2020.findings-emnlp.117).
6. Pradip Pramanick and Silvia Rossi. “Multimodal Coherent Explanation Generation of Robot
   Failures.” *IROS 2024*, pp. 2487–2493. DOI
   [10.1109/IROS58592.2024.10802671](https://doi.org/10.1109/IROS58592.2024.10802671).

The robot-domain sources in the preceding table were also checked against their official
publisher/proceedings records and author-released papers, data, or code. Detailed audits of the
Fernández-Becerra papers and the earlier diagnosis-to-language literature remain in
[`FERNANDEZ_BECERRA_PRIOR_WORK.md`](FERNANDEZ_BECERRA_PRIOR_WORK.md) and
[`DIAGNOSIS_LANGUAGE_POSITIONING.md`](DIAGNOSIS_LANGUAGE_POSITIONING.md).
