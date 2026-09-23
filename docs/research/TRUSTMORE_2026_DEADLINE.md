# TRUSTMORE 2026 submission deadline

Rechecked against first-party sources only: official workshop site retrieved **2026-09-23T08:56:44Z**; official OpenReview submission invitation retrieved **2026-09-23T08:56:46Z**.

## Verified deadline and cutoff

- The official [TRUSTMORE 2026 workshop call](https://trustmoreai.github.io/workshop2026/#cfp) lists the paper submission deadline as **October 4, 2026 (Anywhere on Earth, AoE)** and states that all deadlines are AoE unless otherwise specified.
- The linked official OpenReview portal's [submission-invitation API](https://api2.openreview.net/invitations?id=IEEE.org%2FBigData%2F2026%2FWorkshop%2FTRUSTMORE%2F-%2FSubmission) was accessible and still returned `duedate: 1791183540000`, unchanged from the 2026-09-22 check. This exact portal timestamp converts to **2026-10-05 06:59 UTC** (**2026-10-05 01:59 CDT**, America/Chicago; **2026-10-04 18:59 UTC-12**). It also still returned `expdate: 1791185340000`, or **2026-10-05 07:29 UTC**, 30 minutes later.

These sources are not fully consistent. Conventional end-of-day October 4 AoE would be approximately **2026-10-05 11:59 UTC**, so the portal `duedate` is five hours earlier. The conservative operational cutoff is therefore **2026-10-05 06:59 UTC / 01:59 CDT**; do not rely on the later literal end-of-day AoE interpretation or the separate `expdate`. Recheck the live invitation before submitting because portal dates can change.

## Explicitly stated submission categories

The official call's [submission section](https://trustmoreai.github.io/workshop2026/#submissions) lists:

| Category | Stated length |
|---|---:|
| Full Research Papers | 8–9 pages, including references |
| Short / Work-in-Progress Papers | 4–6 pages, including references |
| System & Demo Papers | 4–6 pages, including references |

The call says to use the IEEE BigData 2026 template. It explicitly includes references in each limit but does **not** state an appendix policy; no stronger interpretation is asserted here.

## Source scope and ambiguity

The workshop site links directly to the cited OpenReview group, and the API invitation is signed by `IEEE.org/BigData/2026/Workshop/TRUSTMORE`. The human-facing portal is JavaScript-driven, and the venue group's generic `date` field was empty; nevertheless, the active public submission invitation exposed the exact `duedate` and `expdate` without sign-in. The source does not explain why its cutoff is earlier than the site's literal AoE interpretation. No submission action or other portal mutation was performed.
