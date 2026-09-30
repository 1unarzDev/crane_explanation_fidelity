# Five-method packet candidate — 2026-09-30

The existing B0–B4 packet builder now has an offline integration over the original pilot's fixed
sixteen inspected development episodes: six persistent discrepancies, six measured recoveries,
two missing-odometry controls and two nominal controls. It keeps every selected episode, including
the one with retained B2 transport failures. No selection uses method outcomes. These recordings
are development material, not fresh acquisition or confirmation. The pilot's older human/judge
annotation wording remains historical; the newer governed automated annotation protocol applies
to future measurement.

## Packet construction

The integration reuses the normalizer, nested removal-only builder, catalog validator and
five-method packet builder. Non-nominal question text is unchanged. Nominal source projection
and the exact registered-discrepancy question use the separately audited nominal adapter,
including removal of duplicated trace counts and their assumption. All families use the existing
catalog ladder IDs and a separate `five-method-aligned-v1` condition namespace. Old packet hashes
are reproduced and preserved; no historical response is rescored.

All sixty conditions have five candidate method packets, for three hundred packets total.
The same question and robot-visible inventory bind each five-method set. B2/B3/B4 retain exact
behavior-tree, Nav2 and diagnostic configuration assets, with their actual file hashes checked
against the retained diagnostic. They receive the same primitive inventory tool. The v2 contract
asset is method-defining input for B3/B4; B2 receives no evaluator reference or contract diagnosis.
B3's final-verification flag is false and B4's is true, as in the existing builder. These flags
are packet specifications, not executed ablations or proof of implementation behavior.

B0's ordinary presentation here is a lossless serialized raw JSON record; B1's is the structured
object. Parsing the former must reproduce the latter exactly. This is an infrastructure
presentation candidate, with the actual raw-summary/structured method prompts and model choices
still unbound. It does not establish a meaningful prompt distinction or a completed baseline
implementation. A future execution declaration must specify those choices explicitly for all
five methods, without weakening B2, adding private evidence or selecting variants by outcomes.

The audit counts unique episode/configuration pairs rather than adding the existing builder's
per-condition `independent_episode_increment` metadata. Masks and methods add no independent N.
Primary effects would use the twelve primary-family episodes; controls must remain separate.
All recordings remain inspected development data and all confirmation/replication counts are zero.

## Retention, verification and open gates

Only a compact snapshot of condition/method/source/tool hashes is retained. Candidate packets
are reconstructed in memory; no method prose, model output or new DVC pointer is written.
`python analysis/build_evidence_calibration_five_method_packet_candidate.py` reproduces this
snapshot read-only. Tests cover full fixed-selection reconstruction, information/source/tool
parity, verification flags, nominal question/role boundaries and complete missing-odometry
removal. Existing source packets, outputs, unknown intents and failures remain unchanged.

This prepares aligned packet inputs only. It authorizes zero model calls, no annotation calls,
no physical acquisition and no P11 freeze. The failed combined support canary remains closed,
with C never launched. Exact model configurations/prompts/tool budgets, durable execution and
technical-failure rules, qualified claim attachment/support/adjudication, and eventual coverage
and episode discordances remain necessary before power and P11 decisions. B2/B4 remains primary;
B0/B1/B3 versus B4 must all be prospectively evaluated with episode effects, intervals and
Holm-corrected paired p-values, including inconclusive and unfavorable outcomes.
