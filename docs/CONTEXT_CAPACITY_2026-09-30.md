# Context-capacity observation — 2026-09-30

The 120 prospective B0/B1 input candidates contain prompts up to 554,254 and 809,592 UTF-8 bytes.
This offline observation investigates capacity before any model invocation. It changes no provider
authentication, DNS, model configuration, context override, prompt, evidence mask or immutable
study cache. Packages used for tokenizer inspection were isolated under `/tmp`.

## Observed sources

- The fetched [official GPT-6 Sol model page](https://developers.openai.com/api/docs/models/gpt-6-sol)
  advertises a 1,050,000-token context window and 128,000 maximum output tokens.
- `codex debug models` under the installed CLI 0.159.2 reports `gpt-6-sol` with a 272,000-token
  default context, 872,000 catalog maximum and 95% effective-context percentage. The arithmetic
  default is 258,400 tokens before allocating prompt/harness/output budgets. The selected entry
  reports experimental context support false. These are CLI catalog observations, not evidence
  that the configured `codex-lb` provider accepts a particular complete request.
- The existing model cache was fetched by CLI 0.155.1 and has the same smaller default. The current
  CLI query corroborates that observation; its raw catalog hash and a sanitized selected record
  are retained. No model instructions, account identity or credentials are copied into the record.
- Current configuration has no explicit context-window, compaction or model-catalog override.
  [Official configuration documentation](https://learn.chatgpt.com/docs/config-file/config-reference)
  describes these controls. This observation sets none of them. The published API window does not
  automatically establish the configured study route's capacity.
- Exact `tiktoken.encoding_for_model("gpt-6-sol")` lookup fails under both 0.12.0 and the separately
  resolved current package 0.14.0. No alternate model/encoding is substituted. This does not prove
  the model has no tokenizer; it means this lookup did not establish its binding.

## Execution implications

Token fit remains unknown for all baseline requests. Byte size is not a token count, the
published API maximum is not a verified route budget, and a catalog maximum is not the selected
default. The next execution declaration needs an exact model/provider/tokenizer binding,
complete model-visible prompt/schema/harness/tool accounting and a prospective reserve for
output and reasoning. Capacity verification must cover every registered condition without
silent evidence truncation, dropping conditions or weakening B2. No larger override, compression
candidate, new model configuration or schema/model canary is authorized by this observation.

The sanitized snapshot records source URLs/hashes, exact CLI values and failed resolver versions.
`python analysis/audit_evidence_calibration_context_capacity.py` replays it without network access,
reading authentication or refreshing catalogs. It retains `token_fit: null` and execution closed.
Five focused checks reject alternate-encoding substitution, claimed capacity success, context
override, unsanitized model metadata and non-integer limits. Two readiness tests also pass.

This is supporting infrastructure evidence, not a new contribution, model failure, semantic
annotation or episode-level result. No study request, model call or provider canary ran. The
failed combined support gate and unlaunched C remain unchanged. P11, alpha, quarantine and
confirmation/replication N are unchanged; all five-method evaluation and reporting gates remain.
