# Technical cohort snapshot

Snapshot: 2026-10-02T00:43:26.316415+00:00 to 2026-10-02T00:43:26.386169+00:00. This is a non-atomic read of a live run. No confirmation answers, annotations, method-key joins, or effects were accessed. Counts refer to unique configuration IDs, checked against unique cluster IDs.

| Technical quantity | Independent configurations |
|---|---:|
| Allocated confirmation candidates | 2,000 |
| Prefreeze-exposed exclusion (0001) | 1 |
| Available frozen candidate cap | 1,999 |
| Operationally scheduled eligible candidates (launch cutoff 1600) | 1599 |
| Reserved candidates not yet scheduled (1601–2000) | 400 |
| Terminal physical-attempt records, eligible pool | 1441 |
| Physical technical admission valid | 1359 |
| Physical technical admission invalid | 80 |
| Capture failures (no admission-validity value) | 2 |
| Scheduled without a terminal physical record | 158 |
| Semantic attempts, including in-flight intent | 554 |
| Complete B2/B4 pairs | 427 |
| Incomplete method pairs with retained technical failures | 126 |
| Method intent in flight | 1 |
| Additional complete pairs required for first look | 173 |
| Additional complete pairs required for 1200 if continuation is prescribed | 773 |

The physical-record denominator closes exactly: 1359 + 80 + 2 = 1441. The prefreeze exclusion has a separate successful physical record and is excluded from all eligible-pool rows above. Terminal records are a lower bound on attempts while capture remains live; the scheduled-without-terminal-record row includes any current capture and future scheduled work, not final missingness.

Current terminal semantic dispositions include 43 physical-invalid no-call records and 8 outside-population no-call records. The former includes capture failure0025; capture failure0692 has no terminal semantic disposition yet. Consequently these disposition counts should not be added to the independent capture/admission counts. Physical-valid configurations awaiting semantic admission number 797; this is a backlog, not a scientifically missing sample. The machine-readable JSON contains the mutually exclusive entire-cap flow; the CSV contains only per-configuration technical fields.

There are501 retained B2 condition technical failures across126 incomplete pairs, and no retained B4 condition technical failures. Conditions are not independent observations. The already reviewed checkpoint attributes500 denied conditions to the125-pair provider outage and one timeout to candidate0416-E2; this snapshot counts statuses only and does not read provider caches or independently reclassify error content. Counterpart outputs and all raw failures remain retained. No semantic retries, duplicate jobs, or exclusions were introduced.

## Missingness and stopping

Physical admission and population exclusions precede method output and remain governed by the freeze. A failed method condition excludes the whole pair from the complete-pair primary analysis; counterpart output remains retained and governed method failures are not retried. An in-flight or not-yet-attempted configuration is pending, not a final missing-pair outcome. Terminal reporting must use the frozen ordered acquisition prefix, so later physical backlog must not inflate the missingness sensitivity denominator.

At600 complete pairs, both blind passes must finish before the registered check. Zero discordances stops for futility with study p=1; otherwise continue to1200 with no interim superiority test. If candidate cap, time, or provider availability prevents the required complete N, retain the shortfall and report administrative stopping without a nominal positive confirmation claim.

At registered release, let n be complete independent pairs, m be primary-eligible method-missing pairs in the frozen acquisition prefix, and d=b-c be signed discordances in favor of B4. Worst-case arbitrary missing-pair bounds are [(d-m)/(n+m), (d+m)/(n+m)]. Neither d nor confirmation labels were inspected here. Do not count technical physical-invalid, outside-population, or prefreeze-exposed configurations as missing eligible pairs. If any annotation pass remains missing, no positive primary claim is permitted; only scoreless technical annotation failures may resume identical requests until the first structurally valid score. Valid scores are never replaced.

The terminal analyzer's current missingness sets are disjoint: METHOD_TECHNICAL_FAILURE dispositions=0; incomplete records with b2_calls=126; intersection=0. No double count is present in the current metadata schema.

## Reproduce the snapshot

From the repository root:

```bash
python3 analysis/preparation/frozen-land-confirmation-2026-10-01/accounting/snapshot_cohort.py --scheduled-through 1600
```

This rewrites only this preparation namespace. The launch cutoff is an explicit operational input, not a new study rule. JSON and CSV contain no response text or semantic labels. No current accounting blocker was identified.
