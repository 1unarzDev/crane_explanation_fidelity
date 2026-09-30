# HEXAR primary-source audit

Audited 2026-09-30. This document records primary-source facts and constraints; it contains no new model comparison or evidence-calibration effect. Upstream revision: `f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc`. Primary paper: Tamlin Love, Ferran Gebellí, Pradip Pramanick, Antonio Andriella, Guillem Alenyà, Anais Garrell, Raquel Ros and Silvia Rossi, *HEXAR: a Hierarchical Explainability Architecture for Robots*, arXiv:2601.03070v1, 2026-01-06 ([abstract](https://arxiv.org/abs/2601.03070), [versioned full text](https://arxiv.org/html/2601.03070v1)). Cached HTML is under `data/hexar_external/primary_sources/`.

## What the paper establishes

HEXAR composes specialized component explainers with a selector. Its evaluated TIAGo implementation has navigation, planning, asking humans for help, text-to-speech and pizza-recommendation components. The navigation component uses an LLM with filtered Nav2 logs and examples; other components use different explanation mechanisms. The empirical claim is for this physical robot/home-assistance implementation, not universal architecture effectiveness ([paper §§III–IV](https://arxiv.org/html/2601.03070v1#S3)).

The authors declare 20 scenario families, three task-instruction variations per scenario and three queries per execution: 60 recorded physical executions and 180 answers per method, 540 answers overall. The methods reuse the same recorded executions. Repetition of queries is not independent execution replication. The study used an i5-11400H, 16 GB RAM and an RTX 3080 with 12 GB VRAM ([§V-C](https://arxiv.org/html/2601.03070v1#S5.SS3)).

Navigation is the complete scenario set 5–10: static obstacles, enabled joystick manual control, charger override, poor localization, moving obstacles/replanning and nominal navigation. Its declared sample is 18 executions and 54 queries per method. Use this set for accounting and eligibility, never as method-visible hidden-cause information ([Table I and §V-C](https://arxiv.org/html/2601.03070v1#S5.T1)).

The paper says all application/explanation LLMs were phi4, 14B parameters, with temperature zero/greedy decoding. Temperature zero alone does not supply artifact identity or guarantee output reproduction across runtimes ([§V](https://arxiv.org/html/2601.03070v1#S5)).

## Historical metrics and immutable labels

The historical root-cause-identification metric is one when an answer includes the scenario ground-truth root cause. Incorrect-facts presence is one when it includes false information about the task/failure. Combined explanation accuracy is one when root-cause identification is one and incorrect-facts presence is zero. Selection accuracy is the proportion of correct component selections; runtime is elapsed explanation computation on common hardware ([§V-A](https://arxiv.org/html/2601.03070v1#S5.SS1)). These are historical truth-based definitions, not our permitted-packet support endpoint.

Three co-author human annotators independently reviewed blinded, randomized rows containing description, instruction, query, ground truth and answer. The paper reports majority aggregation, 0.93% root-cause disagreement and 1.30% incorrect-fact disagreement ([§V-D](https://arxiv.org/html/2601.03070v1#S5.SS4)). Preserve all released columns and recompute both majority primitive labels and the conjunction. Separately compare the released `accuracy_majority` to majority of the three annotators' conjunctions and to conjunction of the two primitive majorities; these aggregation orders are not generally identical.

Paper-reported rounded outcomes are:

| Method | Root cause identified | Incorrect facts present | Combined accuracy | Mean runtime |
|---|---:|---:|---:|---:|
| HEXAR | 97% | 7% | 93% | 1.73 s |
| End-to-end | 73% | 28% | 66% | 7.86 s |
| All components | 92% | 32% | 67% | 10.05 s |

The paper reports Cochran Q omnibus tests followed by pairwise McNemar tests with Holm correction and 179/180 correct HEXAR selections ([§V-E](https://arxiv.org/html/2601.03070v1#S5.SS5)). These claims require comparison to actual released counts; do not silently replace the paper values with our new support scores. The released CSV presently contains 540 rows, 180 each under `explanation`, `explanation_no_components` and `explanation_trigger_all`; the driver uses `explanation_end_to_end` and `explanation_all_components` when preparing fresh rows. Record this name mapping explicitly ([released CSV](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/detailed_results.csv), [driver](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/run_experiments.py)).

## Pinned implementation evidence and replay hazards

The following observations come from the pinned [navigation implementation](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/component_explain_navigation/component_explain_navigation/component_explainer_impl.py), [selector/task implementation](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/skill_explain/skill_explain/skill_impl.py), and [driver](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/run_experiments.py). They identify tests to perform; they do not establish an observed comparative failure.

- Navigation already includes an insufficient-information answer. Its one-sentence prompt also maps missing-path symptoms to obstacles, replanning/costmap clearing to moving obstacles, and nominal logs to safety-limited speed. Such examples do not supply episode-specific physical-cause evidence. Correct unjustified generalizations prospectively in HX-PROMPT and share that strengthened prompt with HX-CONTRACT.
- Logs are accepted by a fixed logger-name list, filtered by substring and deduplicated against each logger's last accepted message. Repetition and skipped-message effects must be tested using real recordings; discarded scan-buffer warnings do not prove scans were recorded.
- Stored log times use node callback clock time, not the source log header. They are serialized as unpadded `sec.nanosec` strings and then converted to floats. An offline replay must match native prompt input or declare a common infrastructure patch; padding timestamps changes behavior.
- The covariance heuristic increments on XY mean variance or orientation variance above 0.2, emits a derived message when the counter exceeds five, and decrements without a lower bound on lower-variance observations. It is not simply six consecutive high-variance messages.
- Manual and charging states initialize as `None`, update on callbacks, and are injected from final cached state outside the time-window-filtered log loop. Missing state must remain unknown. Do not relabel missing state as false or rely on a remembered removed state.
- The selector currently chooses latest task information rather than its commented question-based task-selection call. Failed skills use previous-skill/current-skill update times; other branches use task creation/update times. Task bookkeeping also uses callback clock times. Preserve these branches and windows in all methods.
- The driver replays at rate 1.0 and restarts/replays when the question changes. `last_question` persists across bag iteration, so state/replay skipping across an adjacent repeated question is a hypothesis requiring an actual ordering check. Clean per-recording/mask replay is required for the removal experiment; any fresh-state infrastructure correction is common to methods and separated from treatment.

Sample metadata for `bagfile_6_1.bag` lists `/rosout`, `/task_info`, `/joy_priority`, `/power/is_charging` and `/amcl_pose`, plus speech and empty auxiliary topics. It does not list raw scans, paths or costmaps. Full navigation metadata/database inventory remains the authoritative eligibility audit ([sample metadata](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/bagfiles/bagfile_6_1.bag/metadata.yaml)).

A genuine decisive-removal intervention must precede callback replay and remove relevant duplicate representations, task error strings and resulting diagnostics/caches. The public scenario truth is an evaluator-only source. Conditional source-code rules can establish program semantics, but not that their predicates occurred during an episode.

## Model and dependency identity limitations

The release [launch](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/launch_explainability.launch.py) and driver set `phi4:latest`; implementation defaults independently use `gpt-4.1-mini` with OpenAI. Thus launching the Python component without release parameter overrides is not the declared phi4 experiment. The driver names an Ollama server but publishes no immutable Ollama manifest, GGUF hash, quantization identity, tokenizer hash or server/runtime version. No exact historical model artifact was found in inspected release entry points. Obtain and retain these identifiers for any available fresh model; run all fresh conditions on that same pinned model. Historical phi4 answers remain category A and cannot be a matched-model treatment comparison.

The [README](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/README.md) prescribes ROS 2 Humble via `osrf/ros:humble-desktop` and colcon. Its sample container uses host network/IPC and privileged flags; these are instructions in the source, not demonstrated requirements. Native replay must use isolated ROS domain/ports and an audited minimum environment. Pin image digest rather than its moving tag.

The [requirements](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/requirements.txt) list numpy 1.22.0, lime 0.2.0.1, scikit-learn 1.7.0, pandas 1.3.5, networkx 3.4.2 and openai 1.62.0. This list is not an environment lock: Python version, ROS packages, transitive versions and external `launch_pal` remain separate dependencies. Resolve compatibility in isolation and record any patch rather than pretending an unavailable environment reproduced the release.

## Code and data licenses are separate

The navigation and skill packages each carry Apache License 2.0 text and declare `Apache-2.0` in `package.xml` and `setup.py`; the pinned tree contains package-local LICENSE files for the other components and ROS interfaces too ([navigation metadata](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/component_explain_navigation/package.xml), [navigation license](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/component_explain_navigation/LICENSE), [skill license](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/skill_explain/LICENSE)). Preserve notices, license text, modifications and source attribution when redistributing adapted code. The navigation copyright test is skipped because generated source has no copyright header; do not invent an author header.

No root-level or dataset-specific LICENSE/NOTICE was found among inspected tracked paths. README publicly releases bags and CSV results but does not separately grant dataset/asset redistribution terms. Package declarations therefore do not resolve bag, speech, environmental asset or CSV redistribution rights. Local read-only analysis and reporting provenance can proceed; do not relicense or bundle recordings as Apache-2.0 without an applicable explicit grant. This is a redistribution uncertainty, not a finding that data are prohibited for analysis.

## Current CRANE bindings and bounded blockers

The [2026-09-30 checkpoint](../CURRENT_STATE_2026-09-30.md) governs over older P/R and Luna text. It centers evidence calibration and B0–B4, with B2 versus B4 sole main discovery candidate, P11 closed and confirmatory N=0. Its later five-method update reports 19 open gates. The statistical ledger remains globally owned: 0.02 consumed, at most 0.01 for future discovery, 0.02 protected replication. This external checkout creates no allocation.

The active [annotation disposition](../../manifests/study/evidence-calibration-agent-qualification-disposition-v1.json) binds `gpt-6-astra`, high reasoning, ephemeral login-backed Codex CLI, no tools, two isolated passes, v2 return/adjudication schemas and no quality-driven retries. Its qualification is for agent-assessed atomic evidence support. Navigation-specific new semantic categories require bounded additional qualification; the authors' human annotations do not qualify our mask scoring. See the [active runbook](../EVIDENCE_CALIBRATION_AGENT_ANNOTATION_RUNBOOK.md). The newer checkpoint supersedes the runbook's historical managed-shell transport limitation for the current host, but does not waive canary/declaration gates.

Open dependencies for new claims are native/offline input-state-prompt parity, all-source removal closure, available-model immutable identity, fair shared evidence exports, external reference/judge qualification, prospective endpoint/split freeze and explicit coordinated inferential allocation. Until those are resolved, report category A recalculation and category B/C development or descriptive evidence separately. Public-data familiarity remains a model limitation even after opaque naming.

## Core source hashes

SHA-256, upstream paths relative to the pinned repository:

| File | SHA-256 |
|---|---|
| `README.md` | `f21917adae707e663aab6cc452cf0a8941743d7af3467389db33dbf2f7fb1188` |
| `experiments.csv` | `c21833211c28667c83ad0e074d94cc9a2dd6c64281ace981e747bd1c556422cf` |
| `detailed_results.csv` | `8a441ef1601be34cbf3be6b13ab78df8421a0973320a5ad1c3e41bca95ffcb7b` |
| `run_experiments.py` | `be9c8aad61a103e256cc77310f6e9d1d82305fbd5b35bfc9ac946d9a7c9e2baf` |
| `launch_explainability.launch.py` | `f003857977d19b8000f2715c056fdacae2bac7647d1f59faeb18d62a1fa945b7` |
| `requirements.txt` | `053fc1f667c6712d662e6bd626a67733b914603f5533940c240d96a64b578375` |
| `component_explain_navigation/component_explain_navigation/component_explainer_impl.py` | `cf8ba279c6d962ed3c5a619bdcd871531a5d07d6943fbcbe8290c0e39b64ba07` |
| `skill_explain/skill_explain/skill_impl.py` | `247cc8e16101f047a15601f30f859ff8a14bd46dc5650e561d5c88443411b1c5` |
