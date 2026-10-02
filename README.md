# CRANE Explain

CRANE Explain studies whether autonomous-robot explanations stay within the evidence available to the robot. The repository is the reproducibility root for the TRUSTMORE 2026 work.

The central problem is **unsupported specificity**: fluent language can claim causes, events, or source details that the runtime evidence does not support.

## Current status (2026-10-01)

The project is running a frozen confirmation study comparing strong tool-enabled **B2** with deterministic checked **B4 v7** on a same-episode land/Nav2 evidence ladder.

- Development is closed at **42 independent primary pairs** (21 persistent command–motion discrepancies and 21 measured recoveries). Both methods had 0/42 primary failures and 0/0 discordances. These are development observations, not a superiority result.
- Confirmation was frozen before semantic outputs were inspected. The prospective declaration fixes the methods, prompts, two blinded annotation passes, episode-level failure definition, one-sided exact paired test (α=.01), and stopping rules.
- The first 600 complete pairs are the first scoring point; collection may continue to 1,200 only under the declared rules. No interim superiority test is allowed.
- The latest retained checkpoint contains **401 complete pairs**, **126 incomplete method pairs** (excluded without retry), and **1,307 technically valid physical records**. Raw outputs and technical failures remain retained. No confirmatory answers, labels, scores, or effects have been inspected.

Start with [the prospective freeze](manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json), [the current state](docs/CURRENT_STATE_2026-09-30.md), and [execution accounting](analysis/results/confirmation/evidence-calibration-b4-b2-confirmation-2026-10-01/execution-accounting-FIRST.json).

## Research scope

The intended method is a pipeline:

```text
robot-visible observations + execution/source evidence
  → validated diagnosis → checked plan → language → final-text verification
```

The primary controlled domain is land/Nav2. RoboBoat is bounded external-validity material. Aerial and underwater environments are validated infrastructure but deferred from the submission study. Evaluator-only truth (fault injection, simulator state, gold labels, and intervention mappings) is never supplied to explanation methods.

The study distinguishes:

- **B0–B4 conditions:** fixed evidence levels used for the evidence-calibration comparison.
- **Primary and secondary arms:** the frozen primary arm determines the main claim; model-family or geometry replications are sensitivity evidence only.
- **Physical model calls and technical records:** failed requests are retained and excluded according to the declaration; they are not silently retried or counted as answers.

The canonical vocabulary is in [CONTEXT.md](CONTEXT.md). Use its terms when adding records or documentation.

## Repository map

| Need | Start here |
|---|---|
| Project orientation and commands | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/BENCHMARK.md](docs/BENCHMARK.md) |
| Script cleanup and modularization | [docs/SCRIPT_MODULARIZATION_PLAN.md](docs/SCRIPT_MODULARIZATION_PLAN.md) |
| Historical scripts | [archive/INDEX.md](archive/INDEX.md) |
| Study design and frozen rules | [docs/STUDY_DESIGN.md](docs/STUDY_DESIGN.md), [docs/EVIDENCE_CALIBRATION_PROTOCOL.md](docs/EVIDENCE_CALIBRATION_PROTOCOL.md) |
| Latest scientific/development history | [docs/EVIDENCE_CALIBRATION_RESPONSE_DEVELOPMENT_2026-09-30.md](docs/archive/2026-09-30/EVIDENCE_CALIBRATION_RESPONSE_DEVELOPMENT_2026-09-30.md), [docs/DECISIONS.md](docs/DECISIONS.md) |
| Diagnostic campaign history | [archived diagnostic campaign history](docs/archive/DIAGNOSTIC_CAMPAIGN_HISTORY.md) |
| Annotation and scoring | [docs/EVIDENCE_CALIBRATION_AGENT_ANNOTATION_RUNBOOK.md](docs/EVIDENCE_CALIBRATION_AGENT_ANNOTATION_RUNBOOK.md), [docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md) |
| Data boundaries and storage | [docs/DATA_STORAGE.md](docs/DATA_STORAGE.md), [data/README.md](data/README.md) |
| Paper traceability | [paper/README.md](paper/README.md), [paper/CLAIM_EVIDENCE_MAP.md](paper/CLAIM_EVIDENCE_MAP.md) |
| Package-specific implementation | [packages/astro_dock/README.md](packages/astro_dock/README.md), [packages/crane_ml/README.md](packages/crane_ml/README.md) |

Detailed dated reports are evidence records. They are intentionally preserved, but they are not the project entry point. Prefer the latest status and decision documents before reading a historical report.

## Historical milestones

- The repository began as a pinned umbrella for CRANE, ROS, Unity, and reproducible reference environments.
- Runtime capture, source provenance, evidence contracts, checked answer plans, deterministic fallback, and final-text verification were implemented and regression-tested.
- Land/Nav2 became the powered primary benchmark; ecological scenario construction and platform expansion were stopped once the study input set was qualified.
- Early F/G/H and diagnostic pilots exposed coverage, provenance, and causal-language failures. Those attempts remain retained as development evidence and are not confirmatory estimates.
- The project redirected its central claim to evidence-calibrated specificity and froze the B2/B4 confirmation protocol.
- The confirmation campaign is now an execution and blinded-scoring task. Do not alter methods, inspect semantic outputs early, or reinterpret incomplete pairs.

For the complete decision trail, use [DECISIONS.md](docs/DECISIONS.md). For the older diagnostic campaign sequence, use [archived diagnostic campaign history](docs/archive/DIAGNOSTIC_CAMPAIGN_HISTORY.md).

## Setup

```bash
git clone --recurse-submodules https://github.com/1unarzDev/crane_explanation_fidelity.git
cd crane_explanation_fidelity
scripts/setup_workspace.sh
```

Pinned component commits and destinations are recorded in `manifests/workspace.lock.json`. Scripts resolve the repository root from their own location; do not add developer-specific absolute paths.

## Working rules for agents

1. Read this file, [CONTEXT.md](CONTEXT.md), and the latest current-state document before acting.
2. Treat the prospective declaration and manifests as authoritative for the frozen confirmation arm.
3. Keep robot-visible evidence separate from evaluator-only truth.
4. Preserve failed calls, technical interruptions, raw outputs, and prior reports; record exclusions rather than deleting history.
5. Do not use development observations as confirmatory results, and do not inspect blinded semantic outputs before the declared scoring point.
6. Add new dated evidence to the relevant report, then update the current-state summary if the project state changes.

## Reproducibility and status language

Use explicit status labels such as `IMPLEMENTED, TESTED`, `DEVELOPMENT ONLY`, `VALIDATED INFRASTRUCTURE`, `DEFERRED_POST_SUBMISSION`, `INCOMPLETE`, and `SEALED`. Every result should identify its episode unit, condition, evidence boundary, source/provenance basis, and whether it is eligible for the primary claim.
