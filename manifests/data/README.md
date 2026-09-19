# Data manifests

Generate robot-visible and evaluator-only manifests separately. A manifest contains hashes and
metadata, not payload content:

```bash
scripts/build_data_manifest.py \
  --root data/robot_visible/RUN_ID \
  --output manifests/data/RUN_ID.robot-visible.json \
  --provenance "CRANE/Nav2 controlled run RUN_ID"
```
