# Exploratory evaluation on existing simulated HEXAR episodes

The retained V16 bank contains 144 independently seeded TIAGo/Nav2-compatible simulated episodes, 24 per navigation family. We selected an outcome-independent balanced subset of 36 episodes (six per family) before generating new explanations, and applied the unchanged strengthened HX-PROMPT and current HX-CONTRACT to identical visible evidence and public useful-information requirements. The fixed battery contains three questions and three evidence conditions, with identical-request aliases yielding six unique generations per method per episode. Independent statistical N is 36, not the answer or judge-call count.

Support and coverage were agent-assessed using blinded separate A/B calls and disagreement-only C adjudication. Deterministic checks authenticate inputs, contract approved numeric bindings, output schemas and literal quotations; semantic support/coverage, including baseline numerical wording, remains agent-assessed. A whole-episode explanation-battery failure occurs when any battery cell contains unsupported material, overlicensed specificity or a mandatory useful-information omission. Unresolved labels and unfinished scheduled episodes remain unknown. This is exploratory development analysis; no confirmatory alpha was allocated or consumed.

| Family | Collected | Eligible | Scheduled | Both methods generated | Scoring closed | Complete paired endpoint | Missing/unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| charging | 24 | 24 | 6 | 5 | 5 | 5 | 1 |
| dynamic_env | 24 | 24 | 6 | 5 | 5 | 5 | 1 |
| localization | 24 | 24 | 6 | 5 | 5 | 5 | 1 |
| manual_joystick | 24 | 24 | 6 | 5 | 5 | 5 | 1 |
| obstacle | 24 | 24 | 6 | 5 | 5 | 5 | 1 |
| success | 24 | 24 | 6 | 5 | 4 | 4 | 2 |

| Outcome | HX-CONTRACT | Strengthened HX-PROMPT |
|---|---:|---:|
| Explanation-battery failure, complete pairs | 0.0% | 10.3% |
| Useful supported answer cells | 261/324 scheduled | 256/324 scheduled |
| Unsupported-material answer cells | 0/324 scheduled | 5/324 scheduled |
| Overlicensed-specificity answer cells | 0/324 scheduled | 1/324 scheduled |
| Required-unit omission cells | 0/324 scheduled | 0/324 scheduled |
| Mean episode required-unit recall (scored coverage) | 100.0% (N=29) | 100.0% (N=29) |
| Mean words per unique valid answer | 34.6 | 52.4 |
| Within-episode distinct answer-text fraction | 33.3% | 100.0% |

Complete paired endpoints were available for 29/36 scheduled episodes. The four paired cells were 3 contract-success/prompt-failure, 0 prompt-success/contract-failure, 26 both-success and 0 both-failure. The complete-case prompt-minus-contract failure difference was +10.3 percentage points; its fixed-family stratified descriptive bootstrap interval was [+3.4, +20.7] pp. Full-scheduled missingness bounds were [-11.1, +27.8] pp.

The predeclared heterogeneous-episode paired e-mixture, applied conservatively to all scheduled episodes, returned one-sided exploratory e-value-derived p=1. Its independent-episode uncertainty interval with the unknown-label envelope was [-41.2, +58.4] pp. This procedure tests a mean-effect null under independent paired episode outcomes; it does not assume pooled IID discordant signs. Secondary metrics, family summaries and evidence-condition analyses are descriptive, with no additional inferential p-values.

| Family sensitivity | Complete episodes | Contract net wins | Failure difference |
|---|---:|---:|---:|
| charging | 5 | 0 | +0.0 percentage points |
| dynamic_env | 5 | 0 | +0.0 percentage points |
| localization | 5 | 0 | +0.0 percentage points |
| manual_joystick | 5 | 1 | +20.0 percentage points |
| obstacle | 5 | 0 | +0.0 percentage points |
| success | 4 | 2 | +50.0 percentage points |

Retained closed stages contain 880 provider attempts, with token-usage receipts for 880. Reported totals are 18,096,816 input tokens (including 12,239,104 cached input tokens) and 198,403 output tokens. Stable provider latency and monetary cost are unavailable; no assumed pricing is substituted.

The comparison is limited to existing, development-exposed episodes in a restricted adapted simulated HEXAR domain and a small fixed-family sample. Randomized subset selection reduces outcome-based selection but does not establish broad robot-domain representativeness. Hosted model aliases and inherited CLI defaults do not identify immutable served model/system/decoding versions. Automated same-model judges may share errors or infer style despite hidden method IDs; no blinded human validation was performed. Unresolved labels and technical missingness limit precision and may be informative. Within-family bootstrap intervals can be optimistic with only six scheduled episodes per family; the independent-episode interval and missingness envelope are therefore also reported.

HX-CONTRACT uses deterministic constrained realization and can trade stylistic flexibility and optional detail for support discipline. Answer length and useful-unit coverage are reported so brevity cannot silently substitute for useful communication. No specific physical cause is established merely by controller configuration, boundary snapshots, commands or odometry; software success is not independently measured physical arrival.

The released physical-recording development comparison remains separate: twelve recordings, 324 generated answers, useful supported answer rates 100% versus 90.7%, descriptive +9.26 percentage points, seven contract-better recordings and five ties. The original-task navigation subgroup recalculated from Love et al.’s released labels is 49/54 (90.7%) across eighteen physical recordings; it is not a separately reported paper-wide accuracy. Neither value is a confirmatory p-value or an estimate of this simulated whole-episode endpoint. No universal superiority over HEXAR or improvement of its original published accuracy is claimed.

Artifact status: PARTIAL_SNAPSHOT. Raw returns, source/request hashes, immutable selected schedule and the full scheduled denominator are retained. Reproduce with `uv run --no-project --with numpy --with pyyaml python -m analysis.hexar_external.existing_v16_exploratory_v1.analyze --output <new-directory>`; render this section/figure using `uv run --no-project --with matplotlib --with numpy python -m analysis.hexar_external.existing_v16_exploratory_v1.paper --results <results.json> --output <new-directory>`. No provider calls occur during reproduction.
