# CRANE Explanation Benchmark

## Episode artifacts

Each opaque episode ID has two separately rooted artifacts:

- robot-visible: evidence records and parity-matched prose;
- evaluator-only: injection, ground truth, expected propositions, answerability, annotations.

The visible schema contains provenance, completeness, decision-time candidates/policy/consumed
inputs when known, BT/action execution events, unique recovery-attempt IDs, and later outcome. It
never labels simulator truth as robot knowledge.

## Scenario taxonomy

Success; contextual recovery→success; repeated recovery; terminal navigation failure; planning
failure; reproducible controller/progress failure; client cancellation (distinct from task/BT
timeout); incomplete/omitted/contradictory evidence; false premise; decision plus unrelated later
failure; equivalent outcomes through different software mechanisms.

## Question taxonomy

Factual execution, contrastive, failure attribution, temporal, alternative status, misleading
premise, insufficient evidence, and unsupported counterfactual. Human-motivated families may be
mapped from Wachowiak et al.; their question corpus is not treated as a fidelity ground truth.

## Gold proposition format

Each proposition records text-independent predicate/arguments, support status, required/forbidden
evidence IDs, derivation, temporal scope, evidence level, assumptions, material-error category,
and answerability. Counts distinguish `at least N recorded` from `exactly N occurred`.

## Mandatory regression suite

- A: Dock selected with no policy/scores → no highest-utility or causal claim.
- B: explicit **synthetic test-only** policy produces 8.3/6.8/7.9 and supports the checked Dock
  versus Slalom contribution comparison.
- C: duplicate messages with one attempt ID count once; two IDs count twice; incomplete history is
  qualified; the premise “both retries” is rejected.
- D: later outcome changes do not alter decision-time rationale.
- E: infeasible, unevaluated, missing-score, tied, near-tied, contradictory-selection cases.

Current executable coverage is in
`packages/astro_dock/src/crane_explain/tests/test_dock_slalom.py`, with its committed fixture at
`configs/fixtures/dock_policy.json`. Near ties preserve exact recorded
scores and are not described as ties; the practical-equivalence threshold remains a pilot design
choice and must be frozen rather than selected from final outcomes.

## Scenario development

The required high-throughput land corridor contract is specified in `ENVIRONMENT_REQUESTS.md`.
The scenario/motif priority is land C/D/F, surface A/B/C/D/E, and optional underwater/aerial B/C/D.
Competition names do not define benchmark units; controlled decision/explanation motifs do.

The first real capture (`nav2-capture-20260919-p03`) is a terminal-success pipeline smoke. Its
single recovery-count question is not a benchmark sample for RQ1/RQ2 because the direct generator
was rule-based and every condition returned the same correct sentence. It demonstrates artifact
flow and information parity while showing that recovery-free factual questions alone are too easy.

The graphics-free land vertical slice now executes a physically constrained Ackermann rover with
odometry, TF, LaserScan, and Nav2. Its successful no-blocker run is infrastructure validation only:
it has no explanation capture or condition outputs, and two preceding client-deadline runs remain
recorded as invalid calibration attempts. Obstacle/recovery episodes must wait until costmap
observation and evaluator-only collision/intervention truth pass the full contract above.
