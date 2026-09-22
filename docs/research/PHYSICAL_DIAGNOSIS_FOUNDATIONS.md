# Physical-diagnosis research foundations

**Audit date:** 2026-09-22

**Scope:** Primary-source check for the prospective physical-diagnosis study. This note is additive and does not amend the frozen provenance study.

## Submission cutoff

The official [TRUSTMORE 2026 call](https://trustmoreai.github.io/workshop2026/#schedule) states **October 4, 2026 (AoE)** and says all deadlines are AoE unless otherwise specified. The live [OpenReview submission invitation](https://api2.openreview.net/invitations?id=IEEE.org%2FBigData%2F2026%2FWorkshop%2FTRUSTMORE%2F-%2FSubmission), checked on 2026-09-22, instead exposes `duedate=1791183540000`: **2026-10-05 06:59 UTC / 01:59 America/Chicago / October 4 18:59 at UTC-12**. That is five hours earlier than the conventional end of October 4 AoE. It exposes `expdate=1791185340000`, **2026-10-05 07:29 UTC / 02:29 America/Chicago**, 30 minutes later. OpenReview's [official documentation](https://docs.openreview.net/getting-started/frequently-asked-questions/what-is-the-difference-between-due-date-duedate-and-expiration-date-expdate) defines `duedate` as the advertised deadline and `expdate` as the hard deadline.

**Project implication:** submit before the portal `duedate`, retain the planned October 3 completion/review buffer, and do not rely on the 30-minute grace period, the site's possible-extension language, or the later conventional AoE interpretation. Recheck the invitation shortly before submission because OpenReview dates are mutable.

## Verified methodological foundations

### Geometric/environment explanations of planning failure

Liu and Brandão formulate an explanation as a small change to selected environment-object poses that makes a previously unsolved motion-planning problem feasible. Their two methods jointly search for an environment change and a feasible trajectory: a planner-agnostic particle-swarm method and a continuous joint trajectory/environment optimization for optimization-based planners. They explicitly preserve robot–environment, self-collision, and environment–environment constraints. In 40 generated infeasible manipulation problems, the evolutionary method found a feasibility-restoring change in all cases but required tens of minutes to hours; the joint method took under a second on average and succeeded on 90% and 95% of the two 20-case scene sets. The paper assumes an oracle identifies which objects may be moved and leaves point-cloud/occupancy-grid scaling and perception of movable objects to future work ([paper](https://www.martimbrandao.com/papers/Liu2024-icra.pdf), [DOI](https://doi.org/10.1109/ICRA57147.2024.10611577)).

**Project implication:** a validated footprint/free-space or controlled obstacle intervention can support a bounded claim about feasibility in the modeled geometry. A local clearance test does not prove global route absence, planner success after a modeled environment change does not prove physical execution success, and evaluator geometry is not robot-visible evidence unless exposed through a declared observation/diagnostic interface.

### Explicit causal models and contrastive failure explanations

Diehl and Ramirez-Amaro learn a discrete Bayesian-network structure and conditional probabilities from randomized simulation executions, then use breadth-first search to find the nearest discretized variable assignment whose predicted success exceeds a threshold. The language explanation names variables changed between the failed state and that contrastive successful assignment. The method requires experimenter-defined variables, treatment/outcome sets, discretization, an a-priori success definition, and the assumption that the learned graph is correct or has been revised with domain knowledge. The authors report 70% and 72% simulation-to-real success-prediction accuracy for cube stacking and sphere dropping, respectively ([RA-L paper/arXiv v2](https://arxiv.org/abs/2204.04483v2), [DOI](https://doi.org/10.1109/LRA.2022.3188889)).

**Project implication:** ordinary event order is not equivalent to this causal basis. CRANE should retain candidate mechanisms, explicit assumptions, contradictory evidence, and unresolved alternatives; causal or counterfactual language requires a declared model or controlled intervention rather than temporal succession alone.

### Hierarchical multisensory histories

REFLECT constructs three linked levels from robot history: sensory-input summaries (task-informed scene graphs, audio, and robot state), event-based summaries of selected key frames, and subgoal-based summaries. Its progressive procedure first tests subgoal completion, then retrieves earlier event/sensory evidence for failure explanation. RoboFail contains simulation and real-robot failure histories, but the simulation evaluation assumes ground-truth object/state detection. The authors explicitly report that their object/state/spatial-relation summary is less effective for low-level control failures and assumes a static environment; their future-work recommendation is richer low-level state perception ([official CoRL/PMLR paper](https://proceedings.mlr.press/v229/liu23g.html), [project](https://robot-reflect.github.io/)).

**Project implication:** retain temporal motion, command, accepted actuation, actuator feedback where available, and independently measured state rather than reducing an episode to scene descriptions or terminal events. REFLECT motivates hierarchical evidence retrieval; it does not establish that an LLM summary is an evidence verifier.

### Specialized explainers and separate correctness axes

HEXAR routes a query to one of several component-specific explainers. Its evaluation separately labels whether an explanation contains the predefined root cause and whether it contains an incorrect fact, then combines those labels into explanation accuracy. The same 60 TIAGo rosbag executions underlie 180 question instances per method; a same-information end-to-end LLM and an all-components aggregation are the baselines. Three coauthor annotators independently labeled blind randomized tables. The paper reports 97% root-cause identification, 7% incorrect facts, and 93% combined accuracy for HEXAR, while explicitly leaving subjective/user effects for future work and warning that results come from one use case and implementation ([arXiv paper](https://arxiv.org/abs/2601.03070), [authors' code/data/results](https://github.com/fgebelli/HEXAR)).

**Project implication:** evaluate diagnostic correctness and unsupported content separately, and evaluate the checked diagnostic result separately from its final-language realization. These labels are not evidence of user trust. Specialized computations may be the contribution, but a repository-aware agent given the same evidence and tools is needed to distinguish tooling from prompting or information advantage.

### Marine disturbance semantics

Fossen's official model writes propulsion/control, current-relative hydrodynamics, wind loads, and wave loads as distinct terms. Ocean current enters through relative velocity, `nu_r = nu - nu_c`; wind and wave loads are added separately as `tau_wind` and `tau_wave` in the relative equations ([official marine-craft model](https://www.fossen.biz/html/marineCraftModel.html)).

**Project implication:** lateral displacement or a lumped motion residual cannot by itself identify waves, current, wind, actuator imbalance, or model error. A boat result should say “uncompensated lateral disturbance” unless retained robot-visible signals and a validated diagnostic discriminate the source. A directly applied force is a synthetic disturbance test, not validated wave physics.

### Nav2 Jazzy `FollowPath` speed feedback

At the audited Jazzy branch commit [`f4108e5b1c2bce804a1aa0c7be6673a8eb4a1501`](https://github.com/ros-navigation/navigation2/tree/f4108e5b1c2bce804a1aa0c7be6673a8eb4a1501), `ControllerServer::computeAndPublishVelocity()` obtains odometry velocity to pass into the controller, asks the controller for `cmd_vel_2d`, and sets `FollowPath` feedback `speed` to the Euclidean norm of that **commanded** linear velocity before publishing the command ([source lines 660–697](https://github.com/ros-navigation/navigation2/blob/f4108e5b1c2bce804a1aa0c7be6673a8eb4a1501/nav2_controller/src/controller_server.cpp#L660-L697)).

**Project implication:** `FollowPath.feedback.speed` is not an independent measurement of robot motion in this source revision. Command-to-motion diagnosis must retain the command plus odometry or another independently measured motion signal, and should record the actually installed Nav2 package/source identity because a moving branch is not a runtime provenance record.

## Evidence boundaries and access limitations

- These papers establish precedents and design constraints, not empirical support for CRANE results. No external experiment was reproduced for this audit.
- Liu and Brandão study manipulation motion planning, not Nav2 execution; feasibility-restoring planner reruns and physical navigation outcomes must remain distinct.
- Diehl and Ramirez-Amaro's causal claim rests on randomized data, the chosen variables, and a learned/revised graph. The reported sim-to-real accuracy is not permission to treat a CRANE residual as a unique cause.
- REFLECT uses simulation ground-truth perception and reports limitations for low-level control. Its metrics cannot be imported as navigation-diagnosis evidence.
- HEXAR is an arXiv/author-release source at the time of this audit; final archival ICRA metadata was not verified. Its coauthor annotation and predefined root-cause labels are not a human-trust study.
- Fossen's page defines a model decomposition; it does not show that CRANE implements, calibrates, senses, or identifies every term.
- The Nav2 statement is verified for the cited Jazzy source commit, not automatically for the frozen or installed binary. Runtime claims require package/version/build provenance or the matching source hash.
- The workshop page and live portal disagree in their effective cutoff. The earlier portal time is the conservative operational authority, but it should be checked again before submission.

## Resulting design rules

1. Diagnose with validated geometric or motion-response computations before language generation.
2. Retain quantities, units, frames, intervals, evidence IDs, computation/version, assumptions, support and conflict, and unresolved alternatives in every diagnostic result.
3. Reserve causal and counterfactual wording for explicit applicable models or executed controlled interventions.
4. Keep robot-visible observations physically separate from evaluator geometry, injected conditions, and simulator force decomposition.
5. Score mechanism identification, unsupported assertions, diagnosis-to-language omissions, qualification on ambiguous cases, and fallback frequency as distinct outcomes.
6. Describe simulation and software evidence at its demonstrated level; do not infer hardware reliability, user trust, globally absent routes, or unique marine disturbance sources.

## Primary sources

- TRUSTMORE 2026 official call and dates: <https://trustmoreai.github.io/workshop2026/#schedule>
- TRUSTMORE live OpenReview invitation API: <https://api2.openreview.net/invitations?id=IEEE.org%2FBigData%2F2026%2FWorkshop%2FTRUSTMORE%2F-%2FSubmission>
- OpenReview due-date/expiration semantics: <https://docs.openreview.net/getting-started/frequently-asked-questions/what-is-the-difference-between-due-date-duedate-and-expiration-date-expdate>
- Q. Liu and M. Brandão, *Generating Environment-based Explanations of Motion Planner Failure*, ICRA 2024: <https://doi.org/10.1109/ICRA57147.2024.10611577>
- M. Diehl and K. Ramirez-Amaro, *Why Did I Fail?*, IEEE RA-L 7(4), 2022: <https://doi.org/10.1109/LRA.2022.3188889>
- Z. Liu, A. Bahety, and S. Song, *REFLECT*, CoRL 2023 / PMLR 229: <https://proceedings.mlr.press/v229/liu23g.html>
- T. Love et al., *HEXAR*: <https://arxiv.org/abs/2601.03070>
- T. I. Fossen, marine-craft model: <https://www.fossen.biz/html/marineCraftModel.html>
- Nav2 Jazzy controller source at the audited commit: <https://github.com/ros-navigation/navigation2/blob/f4108e5b1c2bce804a1aa0c7be6673a8eb4a1501/nav2_controller/src/controller_server.cpp#L660-L697>
