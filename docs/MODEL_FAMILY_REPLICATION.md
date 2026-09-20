# Model-family replication

This document defines how the frozen F/G/H comparison can be replicated with another model family
without turning the system architecture or scientific claim into a GPT-specific design. The
Claude-family arm is the first worked instance. Its authoritative declaration and amendments are:

- `manifests/study/provenance-claude-replication-arm-v1.json`;
- `manifests/study/provenance-claude-replication-arm-v1-amendment-1.json`;
- `manifests/study/provenance-claude-replication-arm-v1-amendment-2.json`;
- `manifests/study/provenance-claude-replication-arm-v1-amendment-3.json`.

Those immutable records govern where they differ from this living operational document.

## Scientific role

A model-family replication arm asks whether the direction and rough magnitude of the method
contrast survive a different model family and execution harness. It is a separately reported
sensitivity analysis, not an amendment to the primary arm.

An arm must reuse the same retained episodes, questions, condition definitions, prompts, evidence,
repository commit, parity audits, and single-sample/no-retry rule. It must not receive evaluator
truth, stronger evidence, extra repair calls, or post-hoc prompt changes. Its outputs, cache,
manifests, annotations, and analysis results occupy disjoint namespaces.

Reusing an episode with another model does not create another independent episode. Arms must not be
pooled as independent clusters, and a secondary arm cannot repair a shortfall against the primary
arm's collection target. Without a design that separately controls the execution harness, an
across-arm difference is sensitivity to the combined model-family-plus-harness change—not a causal
effect of model weights.

The primary study artifacts are hash-frozen. `analysis/test_freeze_integrity.py` reconstructs the
authoritative hashes from the base freeze and its amendments in amendment order. Replication support
extends the repository by addition: it must not edit the frozen study design, annotation guide,
prompts, or primary runner merely to share code with a new provider.

## Provider-neutral execution contract

Every provider adapter accepts the same logical request:

- role and byte-identical prompt;
- JSON answer schema delivered out of band where the provider supports it;
- model identifier and reasoning/sampling settings;
- optional isolated repository workspace and its declared identity;
- content-addressed cache root.

Every adapter retains a `crane-explain-model-call/v1` record containing the full request, adapter
and provider identities, prompt hash, raw and parsed response, parse status, model settings, CLI/API
version, latency, usage, cost or explicit cost-unavailable status, and workspace-integrity result.
Provider-specific token fields may be retained in addition to the normalized input, cached-input,
output, and reasoning-output totals.

Downstream model manifests, blinding, resource summaries, and scoring consume that normalized
record. Conditions, evidence construction, checked planning, final verification, and template
fallback do not depend on a provider name. A new model family should therefore require a new
adapter and a separately declared arm, not changes to evidence or reasoning semantics.

The current primary runner predates this boundary and is hash-frozen with its Codex caller. The
Claude runner is consequently an additive sibling that imports the frozen condition-building logic
and swaps only the caller and envelope. A future non-frozen runner should receive a caller through
a small protocol (`call(role, prompt, schema, workspace...) -> model-call/v1`) so another adapter
does not require copying orchestration. Do not refactor the frozen runner retroactively just to
make the source tree look generic.

## Capability and integrity requirements

Provider interfaces are not assumed equivalent. Each arm records a capability profile covering:

- schema-delivery mechanism and whether it changes prompt bytes;
- repository/tool access and agent system framing;
- read-only enforcement mechanism;
- network and delegation availability;
- workspace isolation and pre/post integrity checks;
- usage, latency, cost, temperature, and seed observability;
- output parsing and failure behavior.

The strongest available read-only boundary should be used. If a provider lacks a kernel-enforced
sandbox, the adapter must use an isolated disposable checkout, deny mutating/network/delegation
tools, hash the workspace before and after every call, retain violations, and exclude them from
scoring. This is still a weaker guarantee and must be reported.

Schema delivery is part of the request identity. An adapter must not append provider-specific
instructions to a frozen prompt merely to obtain structured output. If no out-of-band schema
facility exists, that difference requires a predeclared amendment and is a validity threat; cached
records from one delivery mechanism cannot be silently reused under another.

## Replication procedure

For each new model family:

1. Declare the arm before its first call, including its purpose, fixed inputs, namespaces,
   capability differences, allowed claims, and prohibited claims.
2. Implement and deterministically test the provider adapter without model calls.
3. Run a development-only model-strength control using the same conditions and matched settings
   within that family. Select before sealed calls; never use the primary model as a cross-family
   equivalence reference.
4. Require the retained runtime-presentation and parity-audit hashes to equal those used by the
   primary arm before every call.
5. Execute one call per declared condition/question with content-addressed caching and no retries.
6. Build hash/usage manifests in an arm-specific namespace.
7. Package and annotate the arm separately if response format would reveal family identity.
8. Report results separately, including harness confounds and identical deterministic G outputs.

Condition G is partly deterministic: a failed realization verification produces the checked
template, which is a pure function of the plan. Byte-identical G responses across arms must receive
identical labels. Cross-arm differences in G then concern realization acceptance frequency, not a
different final explanation. In practice, F and H contain most of the model-family sensitivity.

## Claude-family worked arm

The Claude arm was declared after nine primary-arm episodes had been retained. It adds no capture
and no independent episode. It uses:

- adapter: `analysis/claude_cli_caller.py` (`claude-cli-json/v1`);
- runner: `analysis/run_provenance_claude_arm.py`;
- batch driver: `scripts/run_claude_arm_batch.py`;
- development output/cache namespaces under `provenance-model-strength-claude-v1`;
- sealed output/cache namespaces `model_outputs/replication-claude/` and
  `model_cache/claude-replication-v1/`.

The Claude Code CLI supplies `--json-schema`, so current calls preserve frozen prompt bytes. Its
read-only boundary is tool denial plus a disposable checkout and full pre/post workspace hashing,
not a kernel sandbox. F and H use the Claude Code agent harness rather than the Codex harness, so
model family and agent harness remain confounded. Provider monetary cost is available for Claude
calls but not for the primary ChatGPT-login calls; no cross-arm cost comparison is valid.

The Claude models also exhibited a visible response-format difference: some placed a serialized
JSON object inside the schema's `answer` string while the primary model usually emitted prose.
Both satisfy the frozen schema, so this behavior was retained rather than prompt-tuned away. It is
why annotation packets default to one arm per packet; otherwise formatting could reveal arm
identity despite removing explicit model and condition fields.

An early development adapter revision appended schema instructions to the prompt. Sixteen calls
from that revision are retained but excluded. Amendment 1 changed schema delivery to the
out-of-band flag before any sealed Claude call or model selection.

The predeclared development control compared `claude-sonnet-5` and
`claude-haiku-4-5-20251001` at low effort on e019, e021, e037, and e038. Development-only,
single-annotator results were:

| Setting | F errors / 8 | G | H | Specificity | Cost | Input tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-haiku-4-5-20251001` | 7 | 0 | 1 | 117/156 | $2.42 | 8.75M |
| `claude-sonnet-5` | 1 | 0 | 0 | 135/156 | $1.77 | 2.08M |

Coverage was 1.0 for every condition. Haiku failed the predeclared per-condition error margin and
was also slower and more expensive for this agent workload. Amendment 2 therefore selected
`claude-sonnet-5` at low effort before any sealed Claude call. All sixteen G control responses were
byte-identical to the primary arm, so selection discriminated only through F and H. These labels
were unblinded and produced by one automated development annotator; they are configuration-selection
evidence, not an RQ4 result.

The selected sealed Claude replication is **COLLECTED / NOT_ANNOTATED**. Eighteen result
envelopes over `pn-0001`–`pn-0009` hold 54 physical calls with 54 unique cache keys, one per
condition and question, with no retry or resampling. Every envelope reports the required arm status,
single-sample rule, absent evaluator truth, verified read-only workspace, accepted parity, the
selected model and effort, and the pinned commit. Totals are 4,176,634 input tokens, 3,511,517
cached input tokens, 74,953 output tokens, 1,783 reasoning output tokens, 944.116 s aggregate
latency, and $4.1116 provider-reported cost, retained in
`manifests/model_outputs/provenance-claude-replication-arm-v1.json`.

Condition G fell back to its deterministic checked template on 16 of 18 responses, so most G text in
this arm is a pure function of the plan rather than a model realization. Byte-identical G responses
across arms must receive identical labels, which further concentrates the arm's model-family
sensitivity in F and H.

One condition-H call for `pn-0004 failure-cause` first returned a CLI `is_error` envelope carrying
`api_error_status = 429` and an account spend-limit notice. It produced no answer, is retained under
the cache root's `_retained_failed_calls/`, and is excluded from the 54-call shape and every
summary; its $0.0472168 cost is real and reported separately. Amendment 3 records the adapter
correction that keeps such a failure out of the content-addressed answer cache.

No Claude sealed answer has been scored, and no cross-family effect estimate exists.

## Commands

```bash
# Development control for one declared setting
scripts/run_claude_arm_batch.py --batch development \
  --model claude-sonnet-5 \
  --output-root model_outputs/dev/provenance-model-strength-claude-v1/sonnet \
  --cache research/explanation_fidelity/model_cache/provenance-model-strength-claude-v1

# Sealed secondary arm, only after the selected configuration is fixed
scripts/run_claude_arm_batch.py --batch sealed \
  --model claude-sonnet-5 \
  --episodes pn-0001 pn-0002 pn-0003 pn-0004 pn-0005 pn-0006 pn-0007 pn-0008 pn-0009 \
  --output-root model_outputs/replication-claude \
  --cache research/explanation_fidelity/model_cache/claude-replication-v1
```

Existing result files are skipped and calls are content-addressed, so an interrupted batch resumes
without resampling. Never rerun a call to obtain cleaner language.
