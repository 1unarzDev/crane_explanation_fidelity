# Offline Codex harness prompt inspection — 2026-09-30

This non-study observation uses official OpenAI documentation and the installed CLI's
`codex debug prompt-input`. It submits no model request, reads no study response, stages no episode
and changes no provider authentication, user configuration file or immutable cache.

## Sources and observed behavior

The fetched [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
describes `features.shell_tool`,
`features.unified_exec`, `features.apps`, `web_search`, individual `skills.config` entries and
MCP server `enabled`/`enabled_tools`/`disabled_tools` configuration. The fetched
[MCP documentation](https://learn.chatgpt.com/docs/extend/mcp) describes allowlists and the
`required` startup option. These are configuration interfaces, not proof of actual request tools.

Under CLI 0.159.2, a debug prompt rendered from an empty temporary cwd with `gpt-6-sol` / high,
web search disabled, and shell/unified-exec/apps/plugins/remote-plugin/multi-agent/memories/hooks/
skill-search/view-image flags disabled still included a host skill catalog and host paths.
There were no configured user MCP servers in the inspected configuration. The output was five
messages totaling 22,863 serialized UTF-8 bytes. Disabling skill search did not remove the catalog.

A second debug invocation additionally used the documented per-skill `enabled=false` entries for
all 35 discovered skill paths. The catalog, skill entries and host paths were absent from the
result. It still contained five messages, totaling 6,628 serialized UTF-8 bytes. The decrease is
16,235 bytes, not a token estimate or an effect on answer quality. The difference includes debug
serialization and different temporary cwd strings; it is not an exact instruction-token saving.

Both invocations returned code zero with no stderr. They appended only a non-study inspection
sentence. Source skills were not edited; command-scoped overrides affected only the debug child.
Raw debug output stays under `/tmp` because it contains host instructions and identity/path context.
The repository records hashes and sanitized metadata only, never those instructions or paths.

## What remains unproven

The debug command renders a message list. Neither output contained tool-definition fields;
it does not provide the complete model request or certify that default shell, filesystem,
web, connector, plugin, image or other tool routes are absent. Do not label either profile confined,
freeze it for a study, or use a short debug prompt as capacity certification. Actual tool schema
enumeration and event/permission enforcement require a separate prospective harness check.

The existing local bubblewrap computation seam remains usable, but no MCP route or provider
caller is connected to it. A future harness must route every permitted primitive tool through the
isolated surface, preserve B2's relevant source and calculation access, disable alternative access
routes and bind runtime/budgets/durable execution. B0/B1 no-tool behavior must also be enforced.
Host instructions, skill catalogs and other harness framing must enter exact capacity accounting;
per-skill toggles need reproducible binding rather than dependence on whatever is installed later.

This observation qualifies no annotation configuration. The failed combined support canary and
unlaunched C are unchanged. The measurement reopening proposal still awaits an explicit user
decision. No semantic output, annotation, method-key join, endpoint estimate, physical acquisition,
alpha allocation or P11 authorization occurred. Confirmation/replication independent N remain zero.
