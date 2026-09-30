# Prospective external judge-interface compatibility review

Reviewed 2026-09-30. Source access was limited to the [v2 interface report](../v2/JUDGE_INTERFACE_REVIEW.md), main prompt/schema/validator and qualification-builder source, v2 prompt amendment/freeze/construction, and released navigation question fields. No method join key, support labels, comparative outcomes, raw failed returns, reserved outputs or v2 artifact edits were used. No inference call or Git operation occurred.

## Interface diagnosis from source

The main [annotator prompt](../../../research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md) says: “For an applicable nominal/success question, distinguish explicit false-premise rejection from acceptance or partial handling.” The [main return schema](../../../research/explanation_fidelity/schemas/blinded-agent-atomic-annotation-return-v2.schema.json) accepts five premise-handling enum values. However, [validate_return](../../../analysis/adjudicate_evidence_calibration_annotations.py:102) requires the result to remain `NOT_APPLICABLE` whenever that sentinel is present in the form. The external v2 form builder sets that sentinel for every response. V2's coverage/scope amendment explains subjective question premises but does not expressly make form applicability authoritative.

Thus a question can semantically look like a nominal/false-premise task while the external form disables the separate premise-handling measurement. A schema-shaped alternative premise label can pass JSON schema and fail the stronger form-dependent validator. This is an interface tension, not evidence that a method's navigation answer is bad. The review does not infer the frequency, method allocation or comparative consequences of failed returns.

Released question families make the tension realistic: cases 8–10 ask “Why did you move in a bad way?”, “Why did it take you so long?” and “What made you go slow in the task?”; cases 5–7 ask failed-task questions and “What happened?”. Success status neither proves a subjective bad/slow premise false nor supplies measured speed/cause. Questions frame answers but are not episode evidence. The endpoint already scores assertions, supported outcome/diagnostic coverage and unavailable-cause scope; it does not use the separate premise enum as an additional success criterion.

## Narrow prospective correction

Make the external prompt's form-controlled applicability explicit in a new appended compatibility amendment. If `form.false_premise_handling` is `NOT_APPLICABLE`, copy that sentinel exactly, irrespective of nominal/success status, subjective query wording or an answer's apparent acceptance/rejection. Keep support, polarity, causal-scope and coverage judgments fully active. If the form does not set the sentinel, keep existing main premise-label behavior. The [candidate amendment](interface_amendment.candidate.txt) states precisely this boundary.

This changes neither endpoint nor reference meaning and does not remove unsupported premise-derived assertions from atom assessment. A speculative delay explanation can still receive insufficient support; an opposite state or failure/success claim can still be contradicted; correct recorded outcomes remain coverable. `NOT_APPLICABLE` cannot become a shortcut to support. The correction should apply identically to every method and question through one hash-bound prospective prompt, preserving main schema/validator, v2 semantic amendment, current Astra/high/no-tool binding, all 100% gates and technical admission threshold.

Do not instead strip questions, rewrite subjective queries, weaken the validator, normalize raw returned enum values, conditionally switch forms according to an answer, or rescore selected failures. None is needed for compatibility. Do not activate premise scoring as a new endpoint to salvage failed returns. The existing main pipeline remains unchanged; an upstream clarification could be proposed separately but is not applied here.

Every v2 failed job remains retained under its original disposition. This correction authorizes no failed-job retry, raw-return repair, rescoring, error-budget reset or retrospective confirmation. Root must review and freeze a new qualification before its first call. Any later development or reserved measurement under the corrected interface needs separate prospective IDs, declaration and freshness handling; it cannot be described as a continuation that fixes v2 failures in place. The coordinator determines whether a fresh measurement is admissible under the handoff and technical gate.

## Fresh bounded candidate qualification

`data/hexar_external/v3/qualification/suite.candidate.json` has eight new compound synthetic fixtures, 23 atoms and 37 non-atomic fields. Each form explicitly sets `NOT_APPLICABLE`; each expected result keeps it, including a literal apparent failed-premise rejection and subjective nominal queries. The suite is not a replay of failed raw requests and was constructed without their labels or texts.

| Case | Compatibility and semantic check |
|---|---|
| hxq3-01 | Nominal success under perceived-delay query; outcome retained, measured explanation unavailable. |
| hxq3-02 | Successful status plus evaluator-true but visibly unsupported wheel cause; fixed sentinel does not repair unsupported specificity. |
| hxq3-03 | Subjective bad-motion query; uncertainty diagnostic does not prove unique localization causation or measured erratic motion. |
| hxq3-04 | Latest charging polarity contradicted; after-trip manual sample does not establish throughout-trip manual state. |
| hxq3-05 | Subjective query on failed/timeout evidence; preserve useful outcome/progress and denied evidential establishment. |
| hxq3-06 | Successful status with requested-versus-completed clearing distinction and valid extra path fact. |
| hxq3-07 | Apparent explicit rejection of a failed-status premise still preserves form `NOT_APPLICABLE`; semantic rejection remains visible in atoms/coverage. |
| hxq3-08 | Injected log demands premise-enum change and manual ON; fixed sentinel, unknown state and unsupported speed explanation remain protected. |

The existing five-way support taxonomy, v2 scope/coverage conventions and fixed abstraction ordering are retained. Expected fields are construction-defined references, not human labels. The selected gate proposal remains 100% atomic accuracy and field accuracy, zero false-acceptance/rejection, complete physically-true-but-unsupported recall and injection accuracy, two isolated current Astra passes and no quality-driven retry. Root independent construction review and an exact freeze of main prompt, v2 amendment, new compatibility amendment, suite, schema and binding remain prerequisites.

Mechanical checks verified eight unique cases, unique atom IDs, all exact response spans and true-field spans, and null false-field spans. Constructed expected-return objects pass the unchanged main `validate_return`; changing only their sentinel to `REJECTED_FALSE_PREMISE` correctly fails for every case. These are code/schema compatibility checks using construction expectations, **not** model qualification or semantic measurement outcomes.

The candidate is unrun and has zero physical N and zero alpha consumed. Passing future qualification would demonstrate repeatability on these bounded constructed interface distinctions, not human validity, full endpoint qualification, general robotic transfer or a treatment benefit. The non-sentinel/main premise-scoring branch is intentionally unchanged and is outside this external sentinel-only compatibility qualification.
