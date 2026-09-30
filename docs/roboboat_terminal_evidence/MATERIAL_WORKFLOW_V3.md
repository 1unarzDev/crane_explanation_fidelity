# Prospective marine workflow bridge v3

This additive adapter connects the retained capture/evidence/annotation infrastructure to the proposed materiality endpoint. It is a development readiness component, not a new experiment, population registration or confirmation activation. No old bank is rescored.

`roboboat_material_workflow_v3.prepare` requires exact source-bound project completeness review and both retained extraction returns. It computes public sampled outcome independently, checks production agreement and independently selects the conditional positive sampled-kinematic/hull unit. Synthetic evaluator-only contact completeness is used solely to isolate kinematics in the independent reference; the original evidence, including unavailable/misaligned contact, is preserved byte-for-byte in both judge forms. It supplies the four common units, conditional partial-information unit and the exact two scope/cause limitations plus the bounded materiality limitation. New form identities include this inventory.

`score_return` calls the actual bound validator signature and validates hash/form/source-span identity before decision mapping. `score` rejects missing reviewed claims, unequal evidence/inventories and decisions that do not match the declared forms. Explicit unavailable decisions remain conditional uncertainty rather than silent exclusion. Complete-source semantic citation review remains required; the structural adapter does not establish that arbitrary verbatim text supports its field.

`paired_cluster` feeds the existing fixed six-question adapter (two variants, L0–L2) with proposed-primary success bounds. Definite success/failure becomes Boolean; unresolved answers become adverse/favorable bounds. Both physical variants must satisfy the prospective validity rule. Six question rows supply one independent cluster; duplicates cannot add N. These bounds are conditional missing-judgment bounds, not confidence intervals. Strict all-assertion results and unsupported atoms remain retained separately. Every adapter refuses inference activation.

Twelve targeted tests use independently checked construction fixtures, novel constructed inventory text and simulated labels to verify selection, preservation, provenance, validator signature, source-span/hash rejection, material/strict separation, missing decisions and clustered counting. They establish implementation behavior, not new judge accuracy, physical observations or superiority.

The candidate-binding manifest `material_workflow_candidate_v3.json` locks this bridge and its existing dependencies for prospective development review. It resolves B2, extractor and support bindings from current project manifests, and retains the marine extension disposition. Its registry is empty and activation false. It is intentionally not described as a complete experiment freeze: coordinator allocation/resources, untouched configurations, operational schedule, prospective capture/method/extraction/support declarations, citation review/adjudication procedure and approved analysis release must be bound before confirmation. No physical row becomes untouched merely by inclusion in a new manifest.

Verification:

```bash
cd /home/lunarz/worktrees/roboboat-terminal-evidence
PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_material_workflow_v3.py
PYTHONPATH=analysis python analysis/verify_roboboat_material_qualification_v3.py
python - <<'PYCODE'
import hashlib,json
from pathlib import Path
manifest=json.loads(Path('docs/roboboat_terminal_evidence/material_workflow_candidate_v3.json').read_text())
for b in manifest['dependencies']:
    assert hashlib.sha256(Path(b['path']).read_bytes()).hexdigest()==b['sha256'],b['path']
assert manifest['inference_activation_authorized'] is False
print('prospective development bindings reproduce; no campaign activated')
PYCODE
```

Next decision-ready work is the actual coordinated population/resource/allocation freeze. Retained pilot discordance is zero; no nonzero comparative effect/power estimate may be manufactured from this adapter or construction suite. No provider/GPU queue is started by these commands.
