# Marine terminal evidence: bounded related-work review

Inspection date: 2026-09-30. Scope: the references specified in the RoboBoat research handoff. This review establishes claim boundaries; it is not a systematic literature review or an implementation reproduction of these systems.

The defensible research target is an auditable temporal task-completion certificate, together with evidence-level evaluation of correct and useful docking explanations against an equally informed repository/tool agent. Marine relevance comes from measured post-command motion and sustained berth compliance. Templates, robot experience summaries, explainable docking, and numerical maritime evidence expressed in language already exist. Superiority remains an empirical question, including the possibility of a tie.

## Inspection record

Primary arXiv abstract pages and PDFs were retrieved for all six listed arXiv references. Relevant method/evaluation/limitation portions were inspected using extracted PDF text. The PMLR proceedings page and REFLECT PDF were also retrieved. Fossen's own model page was read for mathematical formulation, kinematics, relative motion, and environmental-force interpretation.

The MDPI landing page for `jmse9111178` returned HTTP 403. The arXiv PDF supplies the journal article, title, author list, and relevant method/discussion/conclusion portions. CORALL's DOI resolved to IEEE document 11617387, but both DOI-following and direct IEEE retrieval returned HTTP 202 with an empty body. Publisher-deposited Crossref metadata confirmed the journal title and linked preprint. The linked preprint's deposited abstract was retrieved through Crossref. CORALL is therefore **abstract/metadata inspected, not full-text or implementation audited**. The preprint abstract must not be silently presented as a new inspection of the final publication abstract.

Retrieval scratch files were stored in `/tmp/boat_reference_review/`; these temporary downloads are not immutable research artifacts. Durable source URLs and inspected portions are recorded below. No controller, simulator, or competing-system replication was performed for this review.

## Explainable docking already exists

Vilde B. Gjærum, Inga Strümke, Ole Andreas Alsos, and Anastasios M. Lekkas, *Explaining a Deep Reinforcement Learning Docking Agent Using Linear Model Trees with User Adapted Visualization* ([journal DOI](https://doi.org/10.3390/jmse9111178), [arXiv abstract](https://arxiv.org/abs/2203.00368), [PDF](https://arxiv.org/pdf/2203.00368)). Inspected: abstract, linear model tree approach, discussion, Section 7 conclusions.

The work approximates a neural docking policy with linear model trees in a simulated ASV environment. The surrogate runs alongside the policy and provides feature attributions with proposed presentations adapted to developers and operators. Its discussion explicitly acknowledges approximation error, tree-size transparency limits, and regions where constant predictions prevent feature-attribution explanations. These facts establish substantive explainable-docking prior art; they do not establish a temporal task-completion certificate or the correctness of sustained docking assertions.

**Constraint:** Do not claim first explainable ASV or first explainable docking. Describe our question as whether explanations distinguish navigation termination from independently declared, sustained physical task requirements. Do not claim that this prior work universally fails to distinguish those propositions: this review inspected relevant paper portions rather than exhaustively auditing every implementation.

## Planner cost and physical-measure explanations already exist

Joel Jose et al., *“Why This Avoidance Maneuver?” Contrastive Explanations in Human-Supervised Maritime Autonomous Navigation* ([abstract](https://arxiv.org/abs/2604.08032), [PDF](https://arxiv.org/pdf/2604.08032)). Inspected: Sections II–III, cost-measure mapping, Section IV user-study setup, results and conclusion.

The method selects contrastive features from an additive collision-avoidance cost function, relates costs to meaningful measures such as closest point of approach, and populates a predefined text template. It also describes forward simulation for ahead-of-time explanations. The exploratory study involved four experienced marine officers; simulated scenarios assumed perfect target-position knowledge and calm conditions. Reported feedback supports usefulness in some complex encounters while acknowledging workload and novelty effects.

**Constraint:** Recorded costs, physical measures, and textual templates are established maritime explanation machinery. Our target is retrospective physical completion and evidence sufficiency, rather than introducing another cost-comparison interface. Preserve the distinction between a predicted future maneuver and an observed trajectory. Do not borrow this small exploratory study as evidence of our user benefit or deployability. Its workload findings motivate concise answers and explicit tradeoffs.

## Explained LLM maritime navigation already exists

Klinsmann Agyei, Pouria Sarhadi, and Wasif Naeem, *CORALL: A COLREGs-Guided Risk-Aware LLM for Decision-Making in Maritime Autonomous Surface Ships* ([journal DOI](https://doi.org/10.1109/JOE.2026.3703695), [IEEE record](https://ieeexplore.ieee.org/document/11617387/), [linked preprint](https://doi.org/10.36227/techrxiv.173834815.58607693/v1)). Inspected: journal bibliographic metadata and linked-preprint abstract only. Metadata sources: [journal deposit](https://api.crossref.org/works/10.1109/JOE.2026.3703695), [preprint deposit containing abstract](https://api.crossref.org/works/10.36227/techrxiv.173834815.58607693/v1).

The deposited preprint abstract describes a risk-aware high-level decision-maker, an execution layer for tracking/collision avoidance, navigation outputs and risk indices supplied to an LLM, and decisions with accompanying explanations. It reports testing on 22 Imazu benchmark problems using a high-speed ship model. These are abstract-level descriptions and reported results, not independently verified implementation facts.

**Constraint:** Do not claim first natural-language maritime navigation or imply that LLM maritime decision explanations are absent. Do not infer whether CORALL implements or lacks our exact temporal support states from this abstract. Do not claim a full publication/implementation audit or hardware validation. This source establishes an existing research direction, not a head-to-head comparison.

## Numerical maritime evidence converted to language already exists

*AIS-LLM: A Unified Framework for Maritime Trajectory Prediction, Anomaly Detection, and Collision Risk Assessment with Explainable Forecasting* ([abstract](https://arxiv.org/abs/2508.07668), [PDF](https://arxiv.org/pdf/2508.07668)). Inspected: abstract, architecture, LLM-based prompt encoding, explanation-generation training/inference, qualitative output discussion.

AIS-LLM integrates AIS sequences, a time-series encoder, an LLM prompt encoder, cross-modal alignment, and a multitask decoder. The method converts positional/motion/temporal information to prompts and describes inference-time briefings generated from numerical prediction results. Its qualitative figure includes trajectory, anomaly, and risk narratives.

**Constraint:** Do not claim that numerical maritime evidence becomes natural language for the first time here. Distinguish our retrospective execution measurements and support/coverage contract from predictive traffic summaries. Forecasting accuracy and plausible narrative examples do not substitute for independent docking-completion references or evidence-level annotation.

## Navigation reasoning benchmarks are relevant but distinct

*Exploring LLM Capabilities for Situational Understanding and COLREG compliance on real-world maritime navigation scenarios* ([abstract](https://arxiv.org/abs/2608.08281), [PDF](https://arxiv.org/pdf/2608.08281)). Inspected: abstract, dataset construction, scenario representation, evaluation/discussion.

The study constructs 50 diverse real-world scenarios from AIS data, with applicable rules, recommended actions, and action reasoning, and evaluates LLM navigation reasoning. Its reference task concerns situational understanding and recommended navigational decisions.

**Constraint:** A relevant navigation-reasoning benchmark does not establish observed docking execution ground truth. Our evidence ladders require event times, measured trajectories, fixed physical requirements, and independent interval references. Do not imply these 50 scenarios validate our simulator, sensor capture, or docking outcomes.

## Evidence-grounded risk narratives already exist; directional consistency is narrower than correctness

*LLM-Grounded Explainable AI for Supply Chain Risk Early Warning via Temporal Graph Attention Networks* ([abstract](https://arxiv.org/abs/2603.04818), [PDF](https://arxiv.org/pdf/2603.04818)). Inspected: attention evidence extraction and Section V structured prompts, six-section report structure, directional-consistency validation.

The method uses maritime hubs as supply-chain nodes. Its evidence record retains feature z-scores, correlation directions, and attention-proxy neighbor weights. The LLM report schema includes drivers, neighbors, summary, counterfactuals, confidence/uncertainty, and limitations. The paper reports 498 consistent feature-direction judgments out of 500 across 100 reports (99.6%). Its operational check verifies whether a driver's stated direction agrees with the directional label explicitly supplied in the prompt.

**Constraint:** Do not claim first evidence-grounded maritime explanation or first explicit evidence-limit section. Directional consistency checks a bounded relation, not full report correctness, physical causality, counterfactual validity, temporal task completion, or usefulness. Our semantic endpoint must preserve negation/modality/time scope and combine supported outcome with decisive evidence and absence of material unsupported claims; merely matching a sign is insufficient. Attention/correlation evidence must not become an identified environmental cause.

## General robot explanations and experience summaries are established

Tamlin Love et al., *HEXAR: a Hierarchical Explainability Architecture for Robots* ([abstract](https://arxiv.org/abs/2601.03070), [PDF](https://arxiv.org/pdf/2601.03070)). Inspected: architecture, evaluation metrics/baselines/setup, annotation/results, and discussion.

HEXAR orchestrates specialized component explainers for robot modules. It tests end-to-end and all-component baselines against the same 60 recorded executions and obtains 180 query instances per method. Combined explanation accuracy requires identifying the specified root cause and excluding incorrect facts. Three coauthor annotators label blind randomized outputs. The discussion limits conclusions to one use case and implementation and leaves subjective/user effects for future work.

**Constraint:** Modularity, tailored component explanations, same-recording comparisons, and correctness-without-false-facts metrics are existing ideas. Same recording does not imply independent queries: our ladder levels, questions and repeated generations must remain within configuration clusters. This source's human coauthor annotation is not our annotation status; report our authorized automated judgments as agent-assessed. Specific induced failures with predefined root causes do not authorize our universal physical-cause diagnosis.

Zeyi Liu, Arpit Bahety, and Shuran Song, *REFLECT: Summarizing Robot Experiences for Failure Explanation and Correction*, CoRL 2023, PMLR 229:3468–3484 ([proceedings](https://proceedings.mlr.press/v229/liu23g.html), [PDF](https://proceedings.mlr.press/v229/liu23g/liu23g.pdf)). Inspected: Section 3 hierarchical/progressive explanation, evaluation metrics, limitations, and appendix evaluation instructions.

REFLECT forms sensory-input, event-based, and subgoal-based summaries from multisensory observations, checks subgoal satisfaction, explains failures, and guides correction plans. The paper evaluates informative/correct explanations, localization and executed correction success. It acknowledges limitations from scene-graph heuristics, object-state assumptions, static-environment assumptions, and reduced effectiveness for low-level control failures given its retained information.

**Constraint:** Robot evidence summaries, plan-versus-observation checks, progressive explanation, and useful correction are prior art. Our candidate contribution is narrowly the auditable physical completion interval contract and evidence-sufficiency evaluation. Do not manufacture novelty by claiming all prior robot explanations ignore task outcomes.

## Marine motion observations do not identify a unique disturbance cause

Thor I. Fossen, [*Fossen's Marine Craft Model*](https://fossen.biz/html/marineCraftModel.html). Inspected: mathematical formulation, body/NED kinematics, relative-motion equations and wind/wave/current terms.

The model relates pose rates to body velocities through a coordinate transformation and relates acceleration to inertia, Coriolis effects, hydrodynamic damping, hydrostatics, and generalized forces. The relative-motion formulation represents currents through relative velocity and adds wind/wave loads. It distinguishes propulsion from environmental forces and body-frame quantities from navigation-frame quantities.

**Constraint:** A recorded trajectory can establish displacement and threshold crossings; it does not uniquely invert these dynamics into a wind/current/wave cause. Retain frame identity and transformation provenance, measured versus commanded velocity, and limitations of measurement. “The boat continued moving after action return” is an observation; “waves caused the drift” needs additional identifiable evidence. A stopping prediction requires a separately justified/calibrated model and must remain distinct from retrospective measurements. Do not add path arclength to radial target error as if all motion pointed away from the dock.

## Integration-ready scoped manuscript language

Prior work explains simulated ASV docking policies through surrogate feature attribution (Gjærum et al.) and avoidance choices through contrastive costs, physical measures, and templated text (Jose et al.). Explained LLM maritime navigation (CORALL), numerical AIS briefings (AIS-LLM), and structured evidence-grounded port-risk narratives are also established directions. General robot systems such as REFLECT and HEXAR organize execution evidence for task or component explanations. We study a narrower question: whether a declared temporal docking contract improves correct and useful explanations when reported navigation success differs from sustained physical compliance, compared with an agent receiving the same primitive evidence and public requirements.

The proposed certificate records measured margins, interval witnesses, observation coverage, and unavailable components. It supports reported action status, sampled physical compliance or violation, and limits on what the evidence establishes. It does not identify a unique physical disturbance from drift alone, prove continuous-time compliance without justified intersample bounds, or validate hardware. Comparative benefit, answer coverage, abstention, cost, and language tradeoffs require the separately declared marine experiment; no superiority or significance is established by this review.
