Reproducible commands (from repository root)

These are preparation instructions, not authorization to duplicate live jobs. The existing queued FIRST launcher owns first-look case construction, annotation and analysis. Do not run the FIRST block while that launcher is live. No confirmation output inspection before the registered release.

```bash
export LAND_FREEZE=manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json
export LAND_STUDY=analysis/results/confirmation/evidence-calibration-b4-b2-confirmation-2026-10-01
export LAND_PREP=analysis/preparation/frozen-land-confirmation-2026-10-01/analysis
export LAND_SCORER=analysis/results/evidence-calibration-handoff-development/run_measurement.py
export LAND_PROMPT=analysis/results/evidence-calibration-handoff-development/annotation-prompt-v5.md
python3 "$LAND_PREP/synthetic_review.py"
```

At exactly 600 complete ordered pairs, the sole first-look launcher executes:

```bash
python3 analysis/build_handoff_confirmation_scoring_cases.py --freeze "$LAND_FREEZE" --look FIRST
python3 "$LAND_SCORER" --cases "$LAND_STUDY/look-600/blind-cases-v1.json" --output "$LAND_STUDY/look-600/blind-returns-v1" --slot A --workers 2 --prompt "$LAND_PROMPT" --group-by-episode --scope CONFIRMATION --timeout-seconds 900 --reasoning-effort high
python3 "$LAND_SCORER" --cases "$LAND_STUDY/look-600/blind-cases-v1.json" --output "$LAND_STUDY/look-600/blind-returns-v1" --slot B --workers 2 --prompt "$LAND_PROMPT" --group-by-episode --scope CONFIRMATION --timeout-seconds 900 --reasoning-effort high
python3 analysis/analyze_handoff_frozen_confirmation.py --freeze "$LAND_FREEZE" --annotations "$LAND_STUDY/look-600/blind-returns-v1" --look FIRST
```

A/B can run concurrently with two workers each as already queued. Successful subprocess return codes do not imply structurally complete annotation; the frozen analyzer checks exact case coverage. If any scoreless failures remain, follow the procedure below before analysis. If zero discordance terminates the study, export only that terminal result. Otherwise launch the sole FINAL generation driver after FIRST has exited and its continuation-only artifact is retained:

```bash
python3 analysis/resume_handoff_confirmation_when_available.py --freeze "$LAND_FREEZE" --look FINAL --follow-collection
```

After 1,200 complete ordered pairs, build final blind cases and preserve first600 valid annotations unchanged:

```bash
python3 analysis/build_handoff_confirmation_scoring_cases.py --freeze "$LAND_FREEZE" --look FINAL
python3 "$LAND_PREP/prepare_continuation.py" --first-cases "$LAND_STUDY/look-600/blind-cases-v1.json" --final-cases "$LAND_STUDY/look-1200/blind-cases-v1.json" --output "$LAND_PREP/release/continuation-cases.json"
python3 "$LAND_SCORER" --cases "$LAND_PREP/release/continuation-cases.json" --output "$LAND_PREP/release/new600-returns" --slot A --workers 2 --prompt "$LAND_PROMPT" --group-by-episode --scope CONFIRMATION --timeout-seconds 900 --reasoning-effort high
python3 "$LAND_SCORER" --cases "$LAND_PREP/release/continuation-cases.json" --output "$LAND_PREP/release/new600-returns" --slot B --workers 2 --prompt "$LAND_PROMPT" --group-by-episode --scope CONFIRMATION --timeout-seconds 900 --reasoning-effort high
```

`prepare_continuation.py` asserts all old blinded payloads and source assets identical, and exactly 600 disjoint new episode identities. Use a reviewed `selected-valid-paths.txt`, one original valid return path per episode/pass (or its first valid scoreless technical replacement), combining first600 and new600. This list must be based only on technical status and case identity. Retain every original failure outside the assembly; never include multiple valid scores for one case.

```bash
python3 "$LAND_PREP/assemble_valid_returns.py" --selected-paths "$LAND_PREP/release/selected-valid-paths.txt" --cases "$LAND_STUDY/look-1200/blind-cases-v1.json" --output "$LAND_PREP/release/assembled1200"
python3 analysis/analyze_handoff_frozen_confirmation.py --freeze "$LAND_FREEZE" --annotations "$LAND_PREP/release/assembled1200" --look FINAL
python3 "$LAND_PREP/export_terminal.py" --result "$LAND_STUDY/look-1200/primary-analysis-v1.json" --output "$LAND_PREP/release/terminal-tables-figures"
```

For zero-discordance FIRST termination, replace the export input with `look-600/primary-analysis-v1.json`. The exporter rejects continuation-only artifacts and refuses overwrite. It writes raw failure/coverage CSV, paired-effect CSV, evidence-level descriptive CSV, and standalone SVG RD/CI plot. Any administrative shortfall has no nominal terminal p-value; use manuscript shortfall text instead.

Scoreless technical annotation resumption (only after registered annotation has begun)

Confirm the original request process is terminal and not still in flight. Never retry method generation. Inspect only annotation technical status, not endpoint labels or answer quality. For a terminal annotation record with `FAILED_NO_RETRY` and no `parsed_final`, prepare its original request in an unused attempt directory:

```bash
python3 "$LAND_PREP/prepare_scoreless_resume.py" --failed-record ORIGINAL_FAILED_RECORD --request ORIGINAL_BATCH_REQUEST --output "$LAND_PREP/release/retry-001/cases.json"
python3 "$LAND_SCORER" --cases "$LAND_PREP/release/retry-001/cases.json" --output "$LAND_PREP/release/retry-001/returns" --slot ORIGINAL_SLOT --workers 1 --prompt "$LAND_PROMPT" --group-by-episode --preserve-episode-order --scope CONFIRMATION --timeout-seconds 900 --reasoning-effort high
```

Replace uppercase placeholders with the original technical record, matching request and A/B slot. `--preserve-episode-order` is essential to reproduce the exact original case order. Same source assets, prompt, schema, model, effort and timeout are required; compare request identity with the retained original before accepting. Do not resume an unresolved in-flight intent or replace a valid score. Use a fresh attempt directory for every scoreless retry; retain all attempts. For FIRST technical replacements, assemble valid scores exactly as above using FIRST cases, then rerun FIRST analyzer on that assembly. No added judge passes.
