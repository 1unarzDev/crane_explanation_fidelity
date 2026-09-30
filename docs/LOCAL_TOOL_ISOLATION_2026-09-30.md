# Local primitive-computation isolation — 2026-09-30

`analysis/evidence_calibration_local_tool_sandbox.py` adds a development seam for local Python
computations. It invokes the installed bubblewrap directly, with user/mount/PID/network isolation,
read-only system `/usr` and staged job files, fresh `/proc` and `/dev`, private temporary scratch,
no inherited environment or extra file descriptors, and an isolated standard-library Python entry
point. Workspace inventory is checked before and after. Namespace/runtime failures do not fall
back to execution on the host. Timeouts are bounded to 1–60 seconds.

This seam invokes no model or provider. It is not connected to any method caller. The method
architecture, evidence conditions, prompts, source assets, annotation gates and old runners are
unchanged. It preserves local calculation capability rather than restricting B2 to inventory
summaries. The original staged inventory tool and standard-library arithmetic execute successfully.

## Observed host evidence

Bubblewrap 0.12.0 and unprivileged user namespaces are available on this host. A real subprocess
probe with synthetic job/outside files establishes eight concrete checks: permitted visible reads,
outside-file absence, absence of `/home`, inability to reach the outside path through `/proc/1/root`,
absence of a synthetic inherited environment value, denied visible-file writes, available private
scratch and inability to reach a parent loopback listener. No external network address, provider
credential or actual evaluator artifact is used. The original visible/outside files remain intact.

Nine tests cover that probe, the actual staged primitive tool and arithmetic, runtime failures,
four invalid timeout cases, actual timeout termination and pre-execution workspace tampering. These are environment-specific
local isolation observations, not a general security certification or complete agent confinement.

## Remaining harness boundary

The system `/usr` runtime is exposed and has not been bound as a complete immutable environment.
The binary/interpreter hashes in the observation identify those entry points only; they do not hash
all libraries, executables and runtime content. Future execution must bind and inspect that runtime.
The helper permits subprocess computation inside the isolated namespace; it is not a language-level
Python security boundary or a final allowed-command specification.

The model/provider process needs transport, while primitive tools should use this isolated local
surface. Routing every permitted tool through the seam, disabling alternative file/command/web/
connector routes, binding tool budgets and retaining/auditing every event require a separate
prospective harness integration. A provider process launched outside this seam is not confined by
it. Read-only Codex cwd settings are not evidence that these requirements hold.

B0/B1 must still have their declared no-tool behavior; B2 must retain strong source and primitive
computation access; B3/B4 must receive the same permitted episode evidence. No final harness or
method configuration is frozen here. Actual-route capacity remains unresolved. The failed combined
support canary and unlaunched C remain unchanged, and pilot annotation is closed. No comparative
output, method-key join, episode effect, alpha allocation, fresh physical configuration or P11
authorization follows; independent confirmation/replication N remain zero.
