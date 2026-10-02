# Evidence-calibration handoff results — 2026-09-30

Development now has a real paired result: **B2 0/22 PrimaryFailures; repaired B4 v5 0/22; discordances 0 versus 0.** No superiority advantage is observed. The absolute paired risk difference (B2 minus B4) is 0, with a conservative whole-episode 95% interval of **[−12.73, +12.73] percentage points** and exact descriptive one-sided/two-sided p=1. This is not confirmation or evidence of equivalence.

## Independent units and retained data

The 22 complete primary configurations comprise 11 persistent discrepancies and 11 discrepancy/recovery episodes. Each has four removal-only evidence conditions. Masks, annotations, and multiple B4 versions do not increase N. Four old controls remain separately reported; they do not rescue the primary result.

The original pilot contributed 11 complete primary episodes and four controls. A source-order, outcome-independent extension attempted 12 additional development configurations, retaining 47/48 valid unchanged strong B2 calls and all B4 outputs. One B2 timeout excludes configuration 061 as a whole, without retry or replacement. Original configuration 042 retains its three technical failures and descriptive valid E3 answer. Thus 24 scheduled primary episodes yield 22 complete pairs. Allowing either discordant direction arbitrarily on the two missing pairs gives full-scheduled-sample point-identification bounds of [−8.33,+8.33] points; these are missingness bounds, not confidence intervals.

| Primary measure | B2 | B4 v5 |
|---|---:|---:|
| Episode PrimaryFailure |0/22|0/22|
| Useful required units |229/231 (99.13%)|231/231 (100%)|
| Mean episode coverage |99.17%|100%|
| Unsupported mechanism/deeper diagnostic assertions |0|0|

The small coverage difference is secondary and does not establish primary superiority. Per-level behavior, both discordant directions, source bindings and full episode records are in the [result manifest](../manifests/analysis/evidence-calibration-handoff-paired-development-result-v1.json). Two extension annotation passes agree on all 88 answers' primary and coverage labels. Initial current-v5 passes similarly agree on all 57 answers/150 units. All annotation is automated and same-model agreement does not prove human validity or eliminate shared judge error.

## Measurement and B4 development

Thirty fresh targeted synthetic cases received two independent annotation passes. The historical failed combined canary remains unchanged. Development revisions clarified mentioning versus communicating a diagnosis, measured versus software recovery, qualified favored causes versus unendorsed alternatives, explicit negation versus omission, and public Nav2 code 105 software semantics. The initial scoring passes and all corrected reviews remain retained. In particular, legitimate B2 software diagnoses/recovered navigation episodes were not allowed to become artificial B2 failures.

On the initial 11 primary episodes, old B4 failed 6 times and retained 74/116 required units. Its causal limitation said measured recovery “does not establish or cause” the task outcome. That improperly denies a causal contribution rather than withholding a causal conclusion. B4 v3 restored supported software failures and trace details but retained that flaw; v4 repaired it locally; v5 added supported delivered-command counts, span and median. Current v5 retains all supported units while withholding physical cause. Original answers, contracts and algorithm versions are preserved. B2's model, high reasoning, prompt, permitted evidence, source/configuration and primitive tools remain unchanged.

Independent reference checks reproduced 192 selected discrepancy numeric slots across 216 retained v4/v5 outputs, with no mismatch or unsupported motion admission. Thirteen relevant algorithm tests passed. These checks do not substitute for answer annotation.

Secondary factual/numeric annotation has additional limitations. Six primary B2 conditions were initially flagged, versus none for B4. Full permitted raw sample computations vindicate three exact B2 command counts that the compressed scoring summary could not determine. All original flags and deterministic corrections are retained. The three remaining flags concern two overstatements of zero motion throughout median-defined intervals and one direction-specific statement. These secondary labels are not a primary effect; future scoring should supply deterministic exact value counts instead of asking a judge to reconstruct omitted statistics.

## Power, alpha and prospective allocation

The alpha audit confirms .02 already consumed, .01 candidate alpha available and .02 protected replication alpha. A prospective one-sided exact paired superiority test at .01 is compatible with this unfrozen redirect and improves power, but no test or alpha was bound here.

Exact prospective calculations include technical thinning, both discordant directions, sidedness and sensitivity around small effects. With 10% invalidity, 80% power requires approximately 211 acquired primary configurations for b/c=.10/.02,423 for .05/.01,633 for .03/.005 and1273 for .02/.005. A favorable .25/.05 scenario needs 84, but that large effect is unsupported by this pilot. At the observed b=c=0 plug-in estimate, accumulating N creates no discordant-pair power. These are planning scenarios, not claims that the true effect is zero. The interval still permits scientifically meaningful effects.

The 100 formerly unmaterialized v6 layouts were prospectively reassigned, independently of method outcomes: 80 physical confirmation candidates and 20 protected fresh replication configurations. Four new candidates have completed valid recording and independent preprocessing, with no B2/B4 outputs or development use. They remain eligible candidates only, not confirmatory semantic N. Legacy dev filesystem storage does not change this reservation. The other 96 remain uncollected; the replication 20 remain untouched. This bank is insufficient for realistic small effects, and further genuinely new configurations would be necessary for an adequately powered modest-effect confirmation.

A useful future coverage requirement would be B4 mean episode required-unit coverage ≥95% and coverage loss versus B2 ≤5 percentage points, chosen for scientific usefulness. It remains a candidate requirement; no confirmatory freeze exists.

## Scientific disposition

**Do not launch an underpowered nominal confirmation to satisfy a milestone.** The current method repairs succeed, but unchanged strong B2 is at an observed failure floor on this population. Improving B4 cannot create a superiority discordance when B2 already passes. No confirmatory outputs were generated, no alpha was spent, and no replication was started. B0/B1/B3 were not allowed to delay paired B2/B4 scoring.

Further work should first establish a credible effect under a defensible, outcome-independent primary population sampling design, or report this development floor candidly. Do not weaken B2, promote numeric secondary labels into a new primary endpoint after seeing them, count masks as independent episodes, or borrow replication alpha. Any later confirmatory design must bind the minimum 16 scientific fields before generating its method outputs. Historical platform gates no longer govern development under the handoff authorization.

## Reproduction and retention

Run `python analysis/summarize_handoff_development_results.py` for paired results; `python analysis/power_evidence_calibration_handoff.py` for the general power grid; `python analysis/check_handoff_b4_reference_fidelity.py` for deterministic reference fidelity. Measurement prompts, qualification references, raw calls, blind cases, separate development joins and disagreement records are retained under `analysis/results/evidence-calibration-handoff-development/` and `analysis/results/development/evidence-calibration-extension-v1/`.

Model outputs and physical/reference captures are indexed by the updated DVC pointers and retained in the existing shared local cache. No DVC remote is configured, so external durability is not claimed. No Git push was performed.
