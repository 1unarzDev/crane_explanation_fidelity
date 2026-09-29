# Retrospective run analysis for the evidence-calibration redirect

Status: development and legacy evidence only. Confirmation N = 0; replication N = 0; confirmatory alpha consumed = 0.

## What was audited

The hash-bound inventory in `manifests/study/evidence-calibration-retrospective-run-audit-v1.json` covers 10,168 retained JSON/JSONL artifacts (1,814,108,225 bytes) across analysis results, handoff artifacts, evaluator-only and robot-visible data, manifests, model outputs, and the explanation-fidelity research tree. Generated retrospective outputs and the living P11 file are excluded to avoid self-referential hash cycles.

The audit found:

- 2,443 model-call artifacts;
- 237 response-pair artifacts;
- 386 annotation-packet artifacts;
- 1,811 evaluator/reference artifacts;
- 2,299 robot-visible-evidence artifacts;
- 1,400 summaries or analyses;
- one malformed historical JSONL packet, retained at `model_outputs/annotation_packets/contract-complete-v2-development/cr-pilot-001.jsonl` rather than repaired.

The 386 historical packets are not the new five-way atomic annotation schema. Their original labels remain intact and cannot be silently converted into evidence-calibration labels. The 237 response-pair artifacts are only candidates for a fresh **development-only** atomic audit after per-case robot-visible evidence closure, reference closure, and contamination review. Counts of masks, questions, calls, and annotation passes are never experimental N.

## What the retained runs actually show

The measurement-complete-v2 screen produced an apparently favorable material-error result for P (0/18 versus 14/18) with slightly lower unit coverage (108/126 versus 113/126). It failed its frozen coverage gate. More importantly, the evidence-complete rerun gave the judge the evidence R had been allowed to inspect: material errors became 1/14 for both methods, and no recurring consensus cluster advantage remained. The original large contrast therefore cannot support a method claim.

The contract-complete-v2 pilot reconciled 13 primary clusters and four controls. Its complete-answer P-minus-R contrast was 0.0 under the least-favorable disagreement mapping and +0.0769 under the most favorable mapping; its substantive-error contrast was 0.0 under both. It was correctly not promoted.

The causal-restraint successor initially appeared to find seven prohibited causal statements in six R clusters. Contextual review showed all seven detector findings were false positives, leaving zero confirmed events for both methods. This is direct evidence against brittle lexical causal scoring and supports claim-level semantic scope assessment.

The current evidence-calibration pilot is not analyzable as a method comparison. B4 has 60 deterministic outputs over 16 episodes, but B2 has zero valid outputs. Three B2 logical requests are retained technical failures and must never be retried; 57 were never launched. No B2/B4 semantic effect estimate, confidence interval, p-value, or annotation result exists.

## Consequence for the new study

The historical evidence supports the scientific redirect but not a positive headline result. It suggests three defensible design requirements:

1. judge-evidence closure must include any valid fact either method could establish from permitted evidence;
2. unsupported specificity and useful coverage must be reported together;
3. causal scope must be evaluated at atomic-claim level rather than inferred from keyword patterns.

The exact-task automated-agent qualification is now frozen in `evidence-calibration-agent-exact-task-v1-freeze.json`. It contains four construction-defined development cases and 16 fresh held-out cases covering supported claims, contradiction versus insufficiency, physically true but unsupported claims, partial diagnosis, over-abstention, recovery/outcome causation, false premises, compact-reference omissions, geometry scope, ambiguity, and prompt injection. Two isolated Luna passes must each pass all prospective gates. A failed call or failed gate is retained with no quality-driven retry.

Model calls cannot be executed in the managed shell because its parent disables outbound sockets. The host queue is fully specified in `manifests/operations/evidence-calibration-agent-qualification-host-queue-v1.json`. After qualification, only evidence-closed historical outputs may be annotated, and those results remain development evidence. Fresh confirmation outputs remain prohibited until P11 is frozen.

## Current next action

From a normal network-enabled host, run the transport preflight and the frozen exact-task qualification. If and only if both isolated passes qualify, resume the 57 never-launched B2 development requests without retrying `cm-land-conf-042-E0`, `cm-land-conf-042-E1`, or `cm-land-conf-042-E2`. Then generate blinded atomic packets and run the qualified two-pass annotation/adjudication workflow. Use resulting development discordance to set the coverage floor, practical effect, episode N, and final P11 freeze.
