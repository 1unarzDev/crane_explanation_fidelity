"""Prospective sentinel compatibility, no semantic-core or schema fork."""
import json
from audit_release import ROOT,sha
from study_v2 import V2
from evidence_calibration_io import canonical_sha256
from verify_v2 import qualified as v2_qualified
V3=ROOT/'data/hexar_external/v3'
def qualified():
 v2_qualified();f=json.loads((V3/'qualification/freeze.json').read_text())
 result=json.loads((V3/'qualification/qualification-result.json').read_text())
 assert result['status']=='QUALIFIED'
 assert result['freeze_sha256']==canonical_sha256(f)
 assert result['suite_sha256']==f['qualification_suite_sha256']==canonical_sha256(json.loads((V3/'qualification/suite.candidate.json').read_text()))
 assert f['amendment_sha256']==sha(ROOT/'docs/hexar_external/v3/sentinel_clarification.txt')
 assert f['base_external_v2_amendment_sha256']==sha(ROOT/'docs/hexar_external/v2/annotation_amendment.txt')
 assert f['prompt_sha256']==sha(ROOT/'research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md')
 assert f['schema_sha256']==sha(ROOT/'research/explanation_fidelity/schemas/blinded-agent-atomic-annotation-return-v2.schema.json')
