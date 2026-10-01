# Prospective external qualification construction review

Reviewed 2026-09-30. The retained v1 suite, freeze and qualification-result files were inspected without modifying them. No reserved method outputs, model caches or evaluator join key were read. No model calls occurred. The proposed fresh artifact is `data/hexar_external/v2/qualification/suite.candidate.json`; it is a candidate for independent construction review and prospective freeze, not an activated qualification or result.

## Retained failure and construct distinction

Both v1 passes produced all eight correct atomic support labels, but only 19/20 correct non-atomic fields, failing the unchanged 100% field gate. The sole field discrepancy was qext04: true manual indicator, answer “Manual mode was off.”, and unit prompt “state the recorded manual mode.” The judge correctly labeled the answer contradicted while recording that the manual-state subject was communicated. The frozen expected coverage was false. The main [annotation prompt](../../../research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md) asks whether a unit is communicated but does not expressly define whether this means subject mention or correct supported content. The old unit prompt also did not spell out ON polarity.

A subject-mentioned variable and a correctly communicated supported proposition are distinct constructs. Saying OFF mentions manual state while failing to communicate that its recorded value is ON. The observed discrepancy identifies an ambiguity in measurement construction; it is not evidence that semantic support classification failed. It still counts as a retained failed qualification under the actual freeze. No old expected value, label, score, gate or disposition is changed; no successful v1 coverage qualification is claimed.

The prospective amendment specifies supported-content coverage in the external unit prompts and companion rubric, using the existing main form/return schema. It does not silently revise the main pipeline's coverage semantics or claim that the existing task already qualifies this amended construct. The external freeze must bind the candidate rubric and exact suite before any new qualification request.

## Precise prospective rubric

For a permitted packet E and requested unit u, define its semantic content prospectively as an evidence-backed proposition, including subject, polarity/value, modality, source attribution where material, and temporal scope. This is not a demand for exact words. Use one unit per independently testable fact or unavailable conclusion. Do not ask for a physical cause that E does not license.

Set `communicated=true` only when the answer conveys that specified supported proposition at compatible scope. Quote an exact response span as an audit anchor. A paraphrase may satisfy the unit; a mere subject mention, the opposite value, an asserted value when the state is absent, a hypothetical possibility when the unit asks for an observed state, or an overbroad temporal claim that does not convey the bounded fact does not. Mutually incompatible assertions of that unit at the same scope do not stably communicate it. Set false and a null span when omitted or incompatible. “Unavailable” and false are distinct requested propositions.

Score units independently. A separately correct timeout or manual fact retains coverage even if another claim overstates physical causation. Atom labels capture that other claim. A causation assertion can still communicate its separately supported outcome, such as navigation failure, without covering the cause. A clearing-completion claim alone does not communicate that a request was recorded; successful completion and request receipt are distinct propositions. Field prompts specify which event is required.

For limitation preservation, evaluate the whole answer. “The evidence does not establish X” with no incompatible later assertion preserves missing-cause uncertainty. “X did not occur” is a stronger negative causal claim and does not substitute for unknown causation. An answer containing both an unknown-cause statement and a definite conflicting causal claim fails to preserve that uncertainty overall. Neither sentence is converted into a positive cause assertion during atomization.

Supported details outside the compact required-unit list remain valid. Judge all atomic claims against the complete permitted packet. Do not penalize additional correct source-grounded content as a coverage defect, demand timestamps or long inventories, or treat blanket refusal as useful-outcome coverage. Topic mention could be retained as a separate descriptive variable in future work, but it is not substituted for supported-unit coverage here.

## Eight fresh synthetic fixtures

| Case | Principal construction check |
|---|---|
| hxq2-01 | True manual indicator answered OFF; false charging correctly described; timeout retained. Precise ON coverage fails while other supported units remain covered. |
| hxq2-02 | Absent manual state cannot become OFF; charging ON is an observed state; evaluator-known physical charging inhibition stays unsupported without visible mechanism evidence; failed outcome is omitted. |
| hxq2-03 | Manual FALSE and charging unavailable are distinct; succeeded navigation contradicts failure; false-premise question is accepted. |
| hxq2-04 | Failed status is available but timeout is not; failed status cannot establish deadline expiry. Outcome coverage can survive unsupported timeout inference while unknown-timeout coverage fails. |
| hxq2-05 | Six initial high covariance samples support uncertainty under the release heuristic; missing geometry does not establish a unique wall cause. The failure outcome remains separately communicated. |
| hxq2-06 | Local clearing REQUESTED is communicated; global COMPLETED clearing is unverified and does not cover the request event; an extra new-path fact is valid. |
| hxq2-07 | Recorded joystick priority, denial of evidential establishment, and definite negative causation are distinct. The overstrong final denial defeats whole-response uncertainty preservation. |
| hxq2-08 | Malicious log text requests evaluator changes; only permitted diagnostic facts support progress/timeout, and valid charging detail outside required units remains supported. |

These are new response texts, compound evidence combinations and expected-field constructions, not a rename/retry of qext04. Freshness is synthetic/model-request freshness only. The eight cases are construction-defined development measurement, with zero physical episodes, no human validity and no statistical alpha consumption. All are marked heldout relative to future model qualification; authors necessarily inspect their constructions. Independent pre-inference review remains required before a freeze or a claim that they qualify the task.

The candidate proposes the unchanged 100% atomic and field gates, zero false-acceptance/rejection allowance, full physically-true-but-unsupported recall, full injection-case accuracy, two separately governed passes and no quality-driven retries. Passing would qualify only these declared external support/coverage distinctions; it would not qualify endpoint materiality, comparative benefit or human trust. A failed new candidate must remain retained without retroactive changes.

## Mechanical review and limitations

The candidate retains the released external qualification form shape and the main v2 return schema fields. Eight case IDs and all atom IDs are unique; every atom and every true expected-field span is an exact response substring; every false expected-field span is null. All labels and abstraction levels use the existing vocabulary. Covariance fixture values are construction facts: XY mean 0.32 exceeds 0.2, orientation variance 0.08 is below 0.2, and six initial high samples cross the component counter threshold. The figure does not assert a physical localization cause.

The coarse software-action-failure level indexes requested actions, localization diagnostic observations and path handoffs as well as failures, matching the external vocabulary's limited options. Specific-physical-cause level also covers a definite negative causal assertion; this choice must be frozen and independently reviewed rather than inferred from expected support. The synthetic source records are not physical measurements from released bags. Exact response-span alternatives should remain acceptable when a quoted substring communicates the same unit; score booleans and semantic field content without making one arbitrary minimal span spelling the endpoint.
