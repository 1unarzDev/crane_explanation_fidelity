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
recorded as invalid calibration attempts.

The subsequent opaque `land-nav-20260919-e001` development pilot validates a different motif: an
explicit harness deadline and client cancellation under a full-width blocker. Its capture contains
223 BT transitions and 2,341 feedback records but zero recoveries before cancellation. It is not a
Nav2 terminal-failure or obstacle-causality example. Its terminal-status A/B/C/D/E parity smoke is
useful for selective explanation because the supported answer must withhold both BT-timeout and
physical-cause claims. Independent multi-seed recovery variants remain required before design freeze.

`land-nav-20260919-e019` supplies the first included recovery-followed-by-success mechanism. A
predeclared evaluator-only planar mobility hold caused FollowPath to return FAILURE; the recorded
controller-recovery guard returned SUCCESS, one unique Wait attempt completed, and the later
NavigateToPose result succeeded after mobility was released. The robot-visible record contains no
fault identity or intervention timing, so explanations may describe the software recovery sequence
but must withhold the physical reason for lost progress. e018 used the same seed/configuration but
is excluded because volatile harness QoS lost its accepted-goal record; e019 is the sole countable
instance after the reliable transient-local capture repair.

The predeclared e020–e023 batch varies seed, corridor width, goal distance, and mobility-hold
timing without changing that mechanism. e021–e023 each captured one FollowPath failure, one
successful recovery guard, exactly one successful Wait attempt, and a successful terminal action;
all 18 A/B parity audits pass. e020 succeeded with zero recoveries and is retained as an excluded
expected-outcome mismatch rather than relabeled as another success-family episode. These three
additional clusters improve sample size but must not be described as three new failure mechanisms.

The predeclared e024–e027 balanced batch adds e024 as a second TurtleBot3 unblocked-success instance
and e027 as an Ackermann client-deadline/cancellation instance. E025 is retained/excluded because it
reached the client deadline instead of the predeclared terminal abort; e026 is retained/excluded
because its immediate planning abort had no costmap observation and failed the capture-quality gate.
Neither excluded run is rerun, tuned, or relabeled. All 12 A/B parity audits for e024/e027 pass.

`land-nav-20260919-e004` is the first included recovery-bearing model pilot. It terminated with a
real NavigateToPose `aborted` result before the client deadline and recorded two completed `Wait`
recoveries. Because the BT topic lacks the terminal transition for a third `FollowPath` start, its
history is deliberately marked incomplete. Six questions cover count, misleading count premise,
software recovery mechanism, terminal status, physical-cause insufficiency, and unsupported
counterfactual. The A/B inputs use a dedicated parity-controlled structured presentation rather
than exposing native timestamps only to B; D alone consumes the native record to exercise checked
planning. The first unequal-information attempt is retained but excluded.

The single-episode development result falsified the assumption that checked output is automatically
more informative: C/D/E omitted the supported `Wait`-success fact on the misleading-premise
question, while B covered all 16 provisional gold information units. This is a design signal to
improve plan content before freeze, not permission to tune against final-test answers.

The corrected three-episode pilot adds e007 unblocked success and e009 independently configured
partial-blocker terminal exhaustion. It also separates exact recovery-count completeness from
whole-BT transition completeness because the Nav2 topic stream omitted final node transitions on
both success and abort. The provisional result remains mixed: A made one unsupported false-premise
classification, while checked methods made no material errors but falsely abstained when complete
e007 evidence established that recovery never occurred. Risk must therefore remain paired with
coverage; zero observed checked errors is not yet evidence that D dominates B or E.

The fourth evaluated episode reuses e001's deliberate client cancellation. Its parity inventory
keeps deadline and cancellation request as separate facts. Direct prose A introduced an unsupported
“because” relationship; B and checked methods did not. This supplies a concrete explanatory-
relationship error without exposing evaluator truth. It also leaves RQ1 unresolved/negative in
development: strong prose B-equivalent content was sufficient for the direct structured condition
to avoid all observed errors.
