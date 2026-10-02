# Existing V16 exploratory evaluation

This is the paper-analysis route authorized by the [October 1 handoff](../../research/HEXAR_EXISTING_EPISODES_ANALYSIS_HANDOFF_2026-10-01.md). Additional acquisition and confirmation activation are outside this work. The [bound plan](PLAN.md) selects 36 of 144 retained simulated episodes, six per family, independently of semantic outcomes. The pre-generation declaration was committed in `d88fb2b9`.

The statistical unit is the independently generated episode. Nine battery cells and six unique method requests per episode do not increase N. Both methods receive the same legitimate evidence, source/configuration context, and public useful-information requirements. HX-PROMPT remains the unchanged strengthened comparator; HX-CONTRACT uses the pinned constrained realization pipeline. Support and coverage are agent-assessed with blinded A/B calls and disagreement-only C adjudication.

The [results JSON](../../../manifests/hexar_external/existing_v16_exploratory_v1/analysis_results_v1/results.json), [cohort flow](../../../manifests/hexar_external/existing_v16_exploratory_v1/analysis_results_v1/cohort_flow.csv), [episode outcomes](../../../manifests/hexar_external/existing_v16_exploratory_v1/analysis_results_v1/episode_outcomes.csv), and [evidence conditions](../../../manifests/hexar_external/existing_v16_exploratory_v1/analysis_results_v1/evidence_conditions.csv) retain scheduled-denominator accounting. The [manuscript section](report/manuscript_section.md), [figure](report/evidence_conditions.png), [caption](report/figure_caption.md), and [claim map](report/claim_language.json) provide paper-ready reporting.

Reproduce from retained artifacts, without provider calls, into new directories:

```bash
uv run --no-project --with numpy --with pyyaml python -m analysis.hexar_external.existing_v16_exploratory_v1.analyze --output /tmp/hexar-v16-reproduction
uv run --no-project --with matplotlib --with numpy python -m analysis.hexar_external.existing_v16_exploratory_v1.paper --results /tmp/hexar-v16-reproduction/results.json --output /tmp/hexar-v16-paper
```

The sole exploratory inferential procedure is the predeclared heterogeneous independent-episode paired e-mixture. Family and component analyses are descriptive; pooled IID McNemar is not used. Preserve unknown labels and technical failures. Results do not allocate or consume confirmatory alpha and cannot support confirmatory external-superiority wording.

The twelve-recording physical study, V15, and V20 remain separate development banks. Original HEXAR navigation accuracy is separately recalculated as 49/54 from released navigation-subgroup labels; it is a reference on the original task, not this explanation-calibration endpoint or a separately reported paper-wide accuracy.
