# Positioning CRANE's diagnosis-to-language pipeline

**Audit date:** 2026-09-22; ROS/Nav2 prior-work addendum 2026-09-24
**Scope:** The detailed primary-source reading below is limited to five language-planning and
evaluation works. It must be read with the separate
[`FERNANDEZ_BECERRA_PRIOR_WORK.md`](FERNANDEZ_BECERRA_PRIOR_WORK.md) audit of close ROS/Nav2
accountability, agentic-RAG, and multimodal explanation precedents. Neither note provides empirical
evidence for CRANE or establishes literature-wide novelty.

## Bottom line

CRANE should be presented as a **robot-navigation-specific synthesis and evaluation** of several
established ideas, with a task-specific diagnostic layer between evidence and language:

> retained physical/execution and runtime/source evidence → validated, bounded diagnosis → checked
> answer plan → language realization → final claim check or deterministic fallback

The safe distinction is not simply “planning before realization,” “checking factuality,”
“abstaining,” or “using provenance.” Each already has a clear precedent in the audited sources.
CRANE's narrower contribution is to make a versioned physical or execution diagnosis—with
measurements, evidence identifiers, conflicts, unresolved alternatives, and permitted causal
language—the object that planning and final verification must preserve, then test diagnostic
correctness separately from language faithfulness under evidence- and tool-matched robot
navigation baselines. Even that wording should be called the paper's **method/contribution**, not
the first such system, unless a broader systematic review supports priority.

## Source-by-source positioning

| Source | Exact methodological precedent | What CRANE can legitimately say is additional | Important non-equivalence |
|---|---|---|---|
| Moryossef, Goldberg, and Dagan (2019) | An explicit symbolic text plan separates input structuring from neural realization. For WebNLG RDF triples, the plan fixes sentence grouping, fact and sentence order, and relation direction; its symbolic construction is faithful and complete with respect to the input facts. | CRANE's checked plan is downstream of a validated diagnostic computation and carries evidential support, conflicts, applicability limits, unresolved alternatives, and causal-language permissions rather than merely arranging given facts. CRANE also checks the final realized text. | Separating plan and realization is prior art. The 2019 planner's guarantee applies to the symbolic plan, not to every neural realization: the authors measured omissions, wrong lexicalizations, and over-generation, and reported weaker entity coverage on unseen plans. Their low-level plan construction is explicitly WebNLG-specific and may not generalize as-is. |
| Min et al. (2023), FActScore | Decompose long-form output into atomic facts and score the fraction supported by a specified reliable knowledge source; the automated estimator combines retrieval with a language model (and, in some variants, a nonparametric score). | CRANE can cite atomic/claim-level support checking as evaluation precedent, while using episode evidence and exact source/configuration as the claim-specific authority and separately testing whether required diagnostic content was omitted. | FActScore is factual **precision**, not recall or diagnosis correctness. Its main experiments are people biographies against Wikipedia; it assumes support is unambiguous, facts are equally weighted, and the source does not conflict. The authors warn that abstention or saying fewer facts can inflate the score and recommend reporting response rate and fact count. Its automated estimator is imperfect and retrieval-dependent. It neither validates robot measurements nor establishes causal mechanisms. |
| Dušek and Kasner (2020) | A pretrained NLI model checks data-to-text semantic accuracy in two directions: generated text as premise against each templated input fact to detect omissions, and concatenated input facts as premise against generated text to detect hallucinations. It can yield four-way error labels or filter/rerank any non-OK output. | CRANE can position its final check as the same broad kind of bidirectional semantic-accounting problem, but against a typed diagnostic plan and evidence contract, with deterministic fallback after bounded repair. | NLI-based semantic verification is prior art. The method converts RDF-like triples with hand-built or extracted templates, uses off-the-shelf `roberta-large-mnli`, and was tested on E2E and WebNLG. It does not validate the truth of input data or the diagnostic computation. Template imprecision and linguistic variability caused errors; long text and content-selection tasks were left for future work. When content selection is intended, the paper says omission checking must use the explicitly selected facts or be disabled. |
| Geifman and El-Yaniv (2019), SelectiveNet | Jointly train prediction and selection heads to minimize selective risk subject to target coverage; evaluate the risk–coverage trade-off. An auxiliary prediction head prevents the shared representation from focusing too early on the selected subset. | CRANE may use risk–coverage analysis and the general principle that withholding can reduce error, while defining coverage over answerable diagnostic claim families and measuring unnecessary abstention/fallback explicitly. | SelectiveNet is supervised classification/regression with an integrated learned reject option, not a claim-level language verifier, missing-evidence rule, or deterministic fallback system. CRANE does not implement SelectiveNet merely because it withholds unsupported clauses. Its target coverage can be violated and is calibrated post-training on an independent validation set; its experiments do not establish safety, causal validity, or generative factuality. |
| Huynh et al. (arXiv:2206.06251v2) | Explainability-by-Design's technical phase models application logs as decision provenance, builds graph queries to retrieve explanation-relevant data, turns exemplar narratives into configurable NLG syntax-tree plans, and deploys a reusable Explanation Assistant. The provenance requirements include tracing outcomes to influencers, attribution, activities, timing, and contribution to outcomes. | CRANE can distinguish exact robot runtime/source linkage plus validated physical/execution diagnostics from provenance-backed narration of an application decision. Its prospective evaluation tests diagnostic correctness and realization faithfulness rather than assuming a trace is itself an adequate explanation. | Provenance-to-query-to-plan-to-language is prior art, as is a separate explanation service. Huynh et al. focus on the engineering phase, use designed provenance patterns and exemplar narratives, and simulate two decision pipelines. Requirements elicitation and stakeholder validation are outside the paper's scope; integration cost is excluded, development time is estimated retrospectively, and the authors assume explanations are separately validated. A provenance edge records the modeled decision history; it does not by itself prove a physical cause or counterfactual. |

Fernández-Becerra et al. add closer robot-domain precedent than this five-source table: their ESWA
work covers ROS 2/Nav2 records, agentic and source-aware retrieval, model-performed aggregation and
distance calculations, hallucination grading, and natural-language log explanations; their IGPL
work covers accountable black-box recording and textual-plus-visual LLM/VLM context. CRANE
therefore claims none of those
capabilities as novel. Its prospective distinction is the independently checked physical or
execution mechanism and its evidence-sufficiency limits, and any advantage claim depends on fresh
scenario-clustered results.

## Detailed methodological reading

### 1. Explicit planning before realization

Moryossef, Goldberg, and Dagan split data-to-text generation into a non-neural symbolic planner and
an NMT realizer. Their WebNLG plan is an ordered sequence of sentence-plan trees. It specifies how
input RDF facts are split across sentences, the sentence order, fact order inside a sentence, and
the direction in which a relation is expressed. The precise relationship between an input graph
and a symbolic plan makes the plan checkable for completeness and faithfulness
([paper, Sections 2–3](https://aclanthology.org/N19-1236.pdf)).

Within the five language-method sources analyzed in this note, this is the most direct precedent
for CRANE's narrow “checked plan → language” separation. It is not a claim that Moryossef et al. are
the closest prior work to the complete robot system. CRANE should not claim that inserting a
symbolic/structured intermediate representation before neural realization is novel. The defensible
distinction is the **semantics of the
intermediate record**: CRANE first computes a bounded robot diagnosis and requires its answer plan
to preserve support, contradiction, uncertainty, and limits on causal wording.

The distinction must not be overstated. The 2019 work already targets adequacy and semantic
faithfulness, not just style. Conversely, its plan-level guarantee is not an end-to-end guarantee:
the authors manually observed omissions, wrong lexicalizations, and over-generation, and separately
measured whether the realizer covered and ordered planned entities. They also state that their
low-level plan representation and construction are dataset-dependent and may be insufficient for
more demanding tasks ([paper, Sections 2 and 6.3–8](https://aclanthology.org/N19-1236.pdf)). This
supports CRANE's final-text check, but does not prove that CRANE's checker is correct.

### 2. Atomic support is necessary but not sufficient

FActScore defines an atomic fact as a short sentence conveying one piece of information. For a
response, its score is the proportion of atomic facts supported by a chosen knowledge source; the
model-level score averages over responses conditional on the model responding. The paper's main
human study uses biographies as prompts and Wikipedia as the source, and its automated estimator
uses retrieval plus an evaluator LM, with optional nonparametric scoring
([paper, Sections 3–4](https://aclanthology.org/2023.emnlp-main.741.pdf)).

CRANE can use this work to motivate clause/claim-level evaluation instead of a single holistic
“factual” label. However, supported diagnostic success cannot be replaced by FActScore. A response
could state one safe detail, omit the decisive mechanism and limitations, and receive perfect
precision. The FActScore authors explicitly say the metric omits recall, does not penalize frequent
abstention or fewer generated facts, assumes equal fact importance, and is unsuitable where claims
or sources are disputed or nuanced ([paper, Section 3.1 and Limitations](https://aclanthology.org/2023.emnlp-main.741.pdf)).
CRANE therefore needs separate labels for required-mechanism coverage, decisive evidence,
limitations, unsupported claims, and abstention/fallback. Material claims should not be treated as
exchangeable with cosmetic facts.

### 3. Bidirectional semantic checking after generation

Dušek and Kasner verbalize each RDF-like input fact with a simple template and apply a pretrained
NLI model in both directions. To detect omissions, generated text is the premise and each fact is a
hypothesis. To detect hallucination, the concatenated facts are the premise and the generated text
is the hypothesis. Their output can distinguish OK, omission, hallucination, and both, or collapse
all errors into a filter/reranker decision
([paper, Sections 3.2–3.3](https://aclanthology.org/2020.inlg-1.19.pdf)).

That method is direct precedent for verifying realization against planned content, including both
missing and added meaning. CRANE's appropriate distinction is a stricter, application-specific
contract: claims are checked against a typed diagnostic plan and retained evidence, and failed
language falls back to a deterministic rendering. CRANE should describe any exact/string checker
as conservative contract checking, not as equivalent to learned NLI.

The 2020 paper also fixes a crucial scope condition. Two-way completeness checking assumes that all
input facts should be expressed. For tasks with content selection, the authors recommend checking
omissions only against the explicitly selected facts, or checking hallucination alone. CRANE's
checker should therefore compare final language with the **checked selected answer plan**, not
demand that every item in the episode packet be verbalized. The paper reports errors from
imprecise templates and greater variability in human text, and leaves long-form generation and
content-selection experiments to future work ([paper, Sections 5–6](https://aclanthology.org/2020.inlg-1.19.pdf)).

### 4. Selectivity and the risk–coverage trade-off

SelectiveNet formalizes a selective model as a prediction function plus a selection function that
either predicts or returns “don't know.” It minimizes loss over the covered region subject to a
user-specified minimum coverage, using prediction, selection, and auxiliary prediction heads. The
paper evaluates the resulting risk–coverage curves on classification and regression datasets
([paper, Sections 2 and 4](https://proceedings.mlr.press/v97/geifman19a/geifman19a.pdf)).

This supports reporting CRANE's error–coverage trade-off rather than treating maximum answer rate
as inherently desirable. It does **not** make CRANE an instance of SelectiveNet. CRANE uses
engineered evidence-sufficiency and verification rules to narrow or withhold claims and may fall
back to deterministic text; SelectiveNet jointly learns whole-example acceptance for supervised
classification/regression at a requested coverage. “Selective diagnosis” should be defined in the
paper in this ordinary operational sense and not presented as algorithmic equivalence.

SelectiveNet also shows why achieved coverage must be measured rather than assumed: the authors
observe target-coverage violations and calibrate the selection threshold with an independent
unlabeled validation set ([paper, Section 5](https://proceedings.mlr.press/v97/geifman19a/geifman19a.pdf)).
For CRANE, report useful coverage, material-error risk, unnecessary abstention, and fallback
frequency together, preferably as risk–coverage curves over predeclared claim families.

### 5. Provenance-driven explanation construction by design

Huynh et al.'s Explainability-by-Design methodology contains three phases: requirements analysis,
technical design, and validation. The paper develops the technical phase. Engineers (1) define
provenance patterns that let application logs record entities, activities, agents, timing, and
influence; (2) construct graph queries that retrieve data needed by each explanation; (3) turn
exemplar narratives into NLG syntax-tree explanation plans whose variables bind query results; and
(4) configure a reusable Explanation Assistant that constructs traces, executes queries, fills
plans, and realizes text
([paper, Sections 4–6](https://arxiv.org/pdf/2206.06251v2)).

This is strong prior art for “provenance → query → explanation plan → language,” including
explainability as an architectural requirement rather than an after-the-fact prompt. CRANE should
credit that architecture-level precedent. Its narrower difference is the robot evidence boundary:
runtime/source provenance is combined with independently validated geometric or command-to-motion
diagnostics, and provenance is not treated as proof of a physical cause.

The 2023 arXiv revision evaluates engineering effort in two simulated application scenarios, not
the factual or diagnostic accuracy of robot explanations. Its case study covers only the technical
design phase; application integration and the reusable service's implementation cost are excluded;
development time is estimated retrospectively from repository history; three authors performed the
engineering; and explanation suitability/validation is assumed outside the study
([paper, Sections 8–9](https://arxiv.org/pdf/2206.06251v2)). The reported “as low as two hours per
sentence” is therefore not a transferable cost estimate for CRANE.

## Manuscript-safe claims

- “Following explicit plan-before-realization work in data-to-text generation, CRANE separates a
  checked answer plan from language realization; unlike an RDF text plan, its plan is derived from
  a versioned robot diagnostic result and retains evidence and applicability limits.”
- “Following atomic factual-precision evaluation and bidirectional NLI checking, CRANE scores
  unsupported additions separately from omissions of required diagnostic content and evaluates the
  final language separately from the diagnostic result.”
- “CRANE treats evidence sufficiency as a selective-prediction problem at evaluation time and
  reports risk against useful coverage, without claiming to implement SelectiveNet.”
- “Explainability-by-Design establishes provenance-driven querying and explanation planning as
  prior art; CRANE specializes this pattern to retained robot runtime/source evidence plus validated
  physical or execution diagnostics.”
- “The contribution claimed here is the scoped method and its robot-navigation evaluation, not the
  individual ideas of structured plans, atomic support checks, semantic verification, abstention,
  or provenance-backed explanation.”

## Claims to avoid

- “CRANE is the first system to separate reasoning/planning from realization.”
- “FActScore verifies diagnostic correctness” or “a high factual-precision score proves the answer
  is complete.”
- “NLI entailment proves that the underlying robot evidence or causal diagnosis is true.”
- “CRANE implements SelectiveNet” or “SelectiveNet validates CRANE's rule-based abstention.”
- “Provenance proves causation,” “source access proves runtime execution,” or “a provenance trace
  proves that the physical mechanism occurred.”
- “The five sources establish novelty for CRANE's combination.” They establish nearby precedents
  and design constraints; priority would require a broader search than this deliberately narrow
  audit.

## Verified bibliographic metadata and primary sources

1. Amit Moryossef, Yoav Goldberg, and Ido Dagan. “Step-by-Step: Separating Planning from
   Realization in Neural Data-to-Text Generation.” *Proceedings of NAACL-HLT 2019, Volume 1*,
   pages 2267–2277, Minneapolis, June 2019. ACL. DOI
   [10.18653/v1/N19-1236](https://doi.org/10.18653/v1/N19-1236). arXiv
   [1904.03396v2](https://arxiv.org/abs/1904.03396v2). [ACL record](https://aclanthology.org/N19-1236/).
2. Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke
   Zettlemoyer, and Hannaneh Hajishirzi. “FActScore: Fine-grained Atomic Evaluation of Factual
   Precision in Long Form Text Generation.” *Proceedings of EMNLP 2023*, pages 12076–12100,
   Singapore, December 2023. ACL. DOI
   [10.18653/v1/2023.emnlp-main.741](https://doi.org/10.18653/v1/2023.emnlp-main.741). arXiv
   [2305.14251v2](https://arxiv.org/abs/2305.14251v2). [ACL record](https://aclanthology.org/2023.emnlp-main.741/).
3. Ondřej Dušek and Zdeněk Kasner. “Evaluating Semantic Accuracy of Data-to-Text Generation with
   Natural Language Inference.” *Proceedings of the 13th International Conference on Natural
   Language Generation*, pages 131–137, Dublin, December 2020. ACL. DOI
   [10.18653/v1/2020.inlg-1.19](https://doi.org/10.18653/v1/2020.inlg-1.19).
   [ACL record](https://aclanthology.org/2020.inlg-1.19/).
4. Yonatan Geifman and Ran El-Yaniv. “SelectiveNet: A Deep Neural Network with an Integrated Reject
   Option.” *Proceedings of the 36th International Conference on Machine Learning*, PMLR
   97:2151–2159, Long Beach, 9–15 June 2019.
   [PMLR record and paper](https://proceedings.mlr.press/v97/geifman19a.html).
5. Trung Dong Huynh, Niko Tsakalakis, Ayah Helal, Sophie Stalla-Bourdillon, and Luc Moreau. “A
   Methodology and Software Architecture to Support Explainability-by-Design.” arXiv
   [2206.06251v2](https://arxiv.org/abs/2206.06251v2), revised 25 May 2023. The audited source is the
   cited arXiv revision; no archival venue is asserted here.
