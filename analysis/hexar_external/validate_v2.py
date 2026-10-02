#!/usr/bin/env python3
"""Integrity boundaries for complete or resumable external v2 batches."""
import hashlib,json
from audit_release import ROOT,sha
from study_v2 import V2
from contract_adapter import check_core_pin
from verify_v2 import qualified,study

def main():
 check_core_pin();qualified()
 for cohort in ('development','reserved'):
  base=V2/cohort
  if not (base/'packets.json').exists():continue
  packets=json.loads((base/'packets.json').read_text())['packets'];byid={p['job_id']:p for p in packets}
  refs=json.loads((base/'references.json').read_text())['references'] if (base/'references.json').exists() else []
  if refs:
   assert len(refs)==len(packets)
   for r in refs:assert r['method_packet_sha256']==byid[r['job_id']]['packet_sha256']
  responses=[json.loads(p.read_text()) for p in (base/'responses').glob('*.json')]
  assert len({r['job_id'] for r in responses})==len(responses)
  for r in responses:
   p=byid[r['job_id'].rsplit('-HX-',1)[0]];assert r['packet_sha256']==p['packet_sha256']
   if r['status']=='VALID' and r['method']=='HX-CONTRACT':
    assert r['model_calls']==0;assert r['contract_artifact']['realization']['audit']['missing_required_claim_ids']==[]
  ann=base/'annotation'
  if (ann/'atomic_inventory.json').exists():
   bank={r['response_id']:r for r in json.loads((ann/'blind_bank.json').read_text())['items']};inventory=json.loads((ann/'atomic_inventory.json').read_text())['items']
   assert {r['response_id'] for r in inventory}==set(bank)
   for r in inventory:
    text=bank[r['response_id']]['response_text'];assert r['response_text_sha256']==hashlib.sha256(text.encode()).hexdigest();assert all(a['response_span'] in text for a in r['atoms'])
  if (base/'results.json').exists():
   result=json.loads((base/'results.json').read_text());assert result['alpha_consumed']==0 and result['p_value'] is None and not result['statistically_supported_improvement_claim']
  print(cohort,'packets',len(packets),'responses',len(responses),'references',len(refs))
 if (V2/'study_freeze.json').exists():study()
 print('V2_INTEGRITY_PASS_NO_SHARED_PINS_OR_ALPHA_MUTATION')
if __name__=='__main__':main()
