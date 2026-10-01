# B2/B4 initial paired development results

These are DEVELOPMENT results, not confirmation; no alpha was consumed. Thirty fresh targeted synthetic cases were qualified in two independent automated annotation calls/passes. PrimaryFailure was exact in both passes. The initial24-case suite's sole coverage reference omission was explicitly reviewed; six later cases clarified software recovery versus measured recovery, public Nav2 error-code semantics, and categorical causal negation. No human validation is claimed.

Initial study scoring included114 retained B2/B4 answers plus57 v3 answers, two independent method-blind full-answer passes. The two passes agreed170/171 primary conditions and446/450 required useful units. After development inspection,24 answers with either-pass primary flags or coverage differences were reviewed under the qualified corrected prompt. The corrected prompt avoids overreading “recovered navigation episode” as measured response recovery and recognizes ROS Jazzy code105 as reported controller progress failure. All original scores remain retained as sensitivity; six valid B2 claims initially flagged were corrected. This avoids manufacturing an advantage against the strong B2.

Primary population comprises11 independent complete episodes (persistent discrepancy or discrepancy with measured recovery). Evidence masks are repeated conditions within the same episode; they are never independent N. Four control episodes are reported separately through the all15-episode sensitivity. One additional episode042 has technical B2 missingness in E0–E2; its valid E3 remains descriptive and no poor answer was retried.

| Method | PrimaryFailure /11 | Required units | Mean episode coverage |
|---|---:|---:|---:|
| B2 |0/11|116/116|100%|
| Original B4 |6/11|74/116|63.7%|
| B4 v3 |6/11|110/116|94.8%|
| B4 v4 |0/11|112/116|96.5%|
| B4 v5 |0/11|116/116|100%|

The original/v3 B4 failure mechanism is a categorical limitation: “Measured response recovery does not establish or cause the eventual task outcome.” Lack of causal evidence cannot support a claim that recovery did not cause the outcome. Version4 repairs this local limitation, version5 additionally reconstructs useful delivered-command counts/interval/median rather than merely mentioning a stream. All prior versions/raw answers remain retained.

Current v5 versus B2: discordances0 B2-fails/B4-passes and0 B4-fails/B2-passes; paired risk difference(B2 minus B4)0; conservative95% whole-episode CI[-23.84,+23.84] percentage points; exact one-sided and two-sided descriptive p=1. All15 episodes similarly show0 failures each, v5 required coverage146/146 versus B2 144/146, CI[-18.10,+18.10] percentage points. This provides no observed superiority advantage and does not justify confirmation from a favorable pilot effect.

Intervals avoid the falsely zero-width bootstrap produced by all-zero discordances. With zero discordances, the exact95% upper bound on discordance probability is1−0.05^(1/N); the absolute paired risk difference cannot exceed discordance probability. For nonzero discordances, exact Clopper–Pearson bounds on each direction are projected with Bonferroni coverage. Both use whole episodes as N.

Machine-readable results, decompositions, evidence-level behavior, missingness and individual spans are in initial-paired-development-final-v2.json. v5 completed two independent passes with57/57 answers each,0 primary failures each,150/150 required units each, and no primary/coverage disagreement. Additional12 independent episodes are being collected/scored as DEVELOPMENT before a decision to confirm. Automated same-model agreement does not establish human reliability or eliminate shared annotation bias.
