# Read-only provider binding re-audit

Official OpenAI documentation and local model metadata were rechecked on 2026-10-01 while the predeclared V20 acquisition qualification was running. No qualification-pinned code or source bank was changed. The user-approved development models remain `gpt-6-sol/high` for strengthened HX-PROMPT and `gpt-6-astra/high` for agent assessment.

The local CLI is now **0.160.0**, compared with 0.159.3 in the earlier metadata audit. Read-only app-server calls were restricted to `initialize`, `initialized` and `model/list`. Both requested aliases were returned. Only whitelisted public model metadata and record-field names were retained; no account/authentication/history endpoints were called and no semantic turn was dispatched. The v2 receipt preserves these facts without claiming that local model-list availability identifies an immutable served backend.

Official sources actually fetched:

- [GPT-6 Sol model page](https://developers.openai.com/api/docs/models/gpt-6-sol).
- [GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).
- [Codex configuration reference](https://developers.openai.com/codex/config-reference), which resolves to the official ChatGPT learning site.

The model pages' fetched snapshot sections do not provide a separately dated served-version identifier for the requested aliases. The configuration reference documents requested model/provider/reasoning settings and the model-instruction-file mechanism; it does not certify the complete effective system instructions, sampling/decoding defaults, or hosted backend used by this branch's prior CLI calls. Preserve the requested models rather than replacing them based on documentation. The two new receipts record source URLs, retrieval times, response hashes/excerpts and whitelisted model metadata.

An available CLI alias, executable version/hash, configuration option or successful development response is insufficient to mark provider qualification complete. The actual provider admission still requires supported evidence of a stable served version, a hash-bound complete effective system/request, explicit supported decoding behavior and qualified single-attempt transport. A prospective stability policy would need separate scientific justification and binding; this re-audit does not adopt one or relax admission.

The CLI version change is another reason to capture and qualify the final runtime rather than silently inheriting the development environment. Acquisition engineering can continue independently. No alpha, final N, endpoint, comparator prompt, evaluator prompt or confirmation activation changed.
