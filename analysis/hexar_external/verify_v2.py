"""Read-only qualification and prospective execution-pin checks."""
import json
from audit_release import ROOT,sha
from study_v2 import V2

def qualified():
 freeze=json.loads((V2/'qualification/freeze.json').read_text())
 assert sha(ROOT/'docs/hexar_external/v2/annotation_amendment.txt')==freeze['amendment_sha256']
 assert sha(ROOT/'research/explanation_fidelity/prompts/evidence-calibration-agent-annotator-v1.md')==freeze['prompt_sha256']
 assert json.loads((V2/'qualification/qualification-result.json').read_text())['status']=='QUALIFIED'

def study():
 qualified();freeze=json.loads((V2/'study_freeze.json').read_text())
 for f,h in freeze['file_hashes'].items():
  if sha(ROOT/f)!=h:raise ValueError('Frozen file changed: '+f)
 if freeze['alpha_allocated']!=0:raise ValueError('This runner only admits descriptive evaluation.')
