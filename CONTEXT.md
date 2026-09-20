# Explanation Fidelity

This glossary defines the study language used to separate robot evidence, explanation methods,
model execution, and evaluation. It is intentionally independent of any model vendor.

## Evidence and methods

**Robot-visible evidence**:
Episode information an explanation method is allowed to inspect, including retained runtime facts
and explicitly linked source artifacts.
_Avoid_: Robot truth, ground truth

**Evaluator-only truth**:
Fault injection, simulator state, gold labels, and mappings reserved for inclusion checks and
evaluation and unavailable to explanation methods.
_Avoid_: Hidden context, model context

**Runtime presentation**:
A deterministic, traceable projection of robot-visible capture records used to give methods the
same runtime facts in a structured form.
_Avoid_: Ground truth record, enriched evidence

**Provenance link**:
A validated relationship from a runtime event to the exact retained source or configuration
artifact that governed its software behavior.
_Avoid_: Repository match, plausible code

**Checked method**:
An explanation method that constructs supported propositions, realizes them as language, and
verifies the final text with deterministic fallback.
_Avoid_: Checked model, trusted LLM

## Model experiments

**Model configuration**:
The model identifier, reasoning setting, sampling settings, and provider interface fixed for a set
of calls.
_Avoid_: Model, when the interface or settings also differ

**Provider adapter**:
The boundary that turns a provider-neutral model-call request into one concrete CLI or API call and
normalizes its retained result, usage, cost, and integrity attestations.
_Avoid_: Model arm, harness

**Agent harness**:
The provider program, system framing, tool surface, permission enforcement, and repository-access
behavior surrounding a model call.
_Avoid_: Model family

**Study arm**:
A separately declared execution of specified conditions over a fixed episode set under one model
configuration, provider adapter, and agent harness.
_Avoid_: Dataset, independent sample

**Model-family replication arm**:
A secondary study arm that repeats a frozen comparison over the same retained episodes with a
different model family and possibly a different agent harness, reported as sensitivity evidence.
_Avoid_: New cohort, additional episodes, model-only replication

**Primary arm**:
The hash-frozen confirmatory arm whose hypotheses, model configuration, prompts, and stopping rules
govern the main statistical claim.
_Avoid_: GPT arm, Luna arm

**Secondary arm**:
A separately declared sensitivity analysis that cannot replace the primary arm or increase its
independent episode count.
_Avoid_: Extension of the primary sample

**Physical model call**:
One retained provider invocation with its unique request, raw response, latency, usage, and cost
metadata; deterministic envelope entries are not physical calls.
_Avoid_: Output, response
