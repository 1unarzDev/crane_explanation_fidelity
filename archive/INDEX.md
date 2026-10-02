# Historical script policy

Superseded analysis and test scripts are intentionally absent from the working tree. Their exact contents remain available in Git history under their original paths, so they do not need to remain in a new agent's context or active import/test surface.

## Removed family: installed-client observers

The following historical families were removed after the v9 implementation became canonical:

- `evidence_calibration_local_tool_sandbox_v2.py` through `v8.py`
- `evidence_calibration_mcp_stdio_v2.py` and `v3.py`
- `evidence_calibration_tool_broker_v2.py` and `v3.py`
- `observe_evidence_calibration_app_server_mcp_v2.py` through `v8.py`
- matching `tests/test_*` files for those versions

To recover an exact historical implementation, use Git history:

```bash
git log --all -- analysis/observe_evidence_calibration_app_server_mcp_v8.py
git show <commit>:analysis/observe_evidence_calibration_app_server_mcp_v8.py
```

Do not reintroduce a superseded copy for current work. Extend the canonical v9 path or extract shared behavior into `analysis/crane_explain_core/`.
