# Development CLI and prospective runtime binding

Official OpenAI documentation was fetched on 2026-10-01 using the OpenAI Docs skill. The attempted official search URL returned 404; direct official pages were then fetched. No local credential/configuration or model-cache inspection was used to infer hosted model identity.

Sources:

- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) (the developers.openai.com Codex reference redirects here): documents requested model/provider and reasoning-effort settings. It does not establish a returned immutable snapshot for the existing development calls or a complete temperature/decoding/system-instruction binding.
- [Model catalog](https://developers.openai.com/api/docs/models): lists `gpt-6-astra`; the fetched page does not list the exact requested `gpt-6-sol` alias. This does not establish that the alias is unavailable to the authorized development CLI.
- [GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra): describes snapshots as version locks, but its fetched snapshot section lists `gpt-6-astra` without a separately dated snapshot identifier. It does not establish what immutable backend the CLI used.

Preserve the authorized development aliases `gpt-6-sol/high` for HX-PROMPT and `gpt-6-astra/high` for agent evaluation. Do not substitute a different model based on the catalog. Successful CLI calls and a local executable hash do not prove immutable hosted model identity. Current declarations correctly leave model snapshot, decoding defaults, inherited system/context and transport-level tool restrictions unresolved.

Before confirmation, either bind an actual documented immutable runtime with complete effective settings, or prospectively justify a stability policy that includes returned model identity, dispatch-window constraints, drift detection and frozen disposition. Such a policy is not adopted by this note. A drift check cannot retroactively make inspected outputs prospective or authorize outcome-dependent retries. Runtime admission remains fail-closed while development continues using the existing CLI as requested.

The read-only 2026-10-01 app-server audit called only `initialize`, `initialized` and `model/list`, following the [official app-server documentation](https://learn.chatgpt.com/docs/app-server). Both requested aliases were listed by Codex CLI 0.159.3. The returned record fields contained no immutable snapshot/deployment identifier or complete decoding binding. Only whitelisted metadata for those two models was retained in `development_model_metadata_audit_v1.json`; no semantic turn, account/authentication or history endpoint was used. API-key presence was false at this inspection, without inspecting or retaining credential values. This is evidence of current development availability, not stable confirmation binding.

The v12 development unique-method run retained one HX-PROMPT timeout at the declared 360-second limit, with no retry. Runtime transport qualification therefore failed its complete-return criterion. Stable backend identity would not itself repair that failure; the final missing-output disposition must remain prospectively defined and preserve all battery aliases. The pending provider-route choice does not prohibit continued CLI development or authorize freezing a dynamic alias.
