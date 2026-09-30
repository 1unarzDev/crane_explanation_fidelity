#!/usr/bin/env python3
"""Independent mechanical span/hash/coverage audit, not semantic qualification."""
import argparse,hashlib,json,re
from audit_release import ROOT,sha,write
from study_v2 import V2
STOP={'i','me','my','the','a','an','and','or','but','however','so','because','therefore','to','of','in','on','at','for','with','from','that','this','it','its','is','are','was','were','been','be','being','as','by','then','also','only','we','our','your','you','not','no','can','could','did','do','have','has','had'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args();out=V2/a.cohort/'annotation'
 bank={r['response_id']:r for r in json.loads((out/'blind_bank.json').read_text())['items']};inv=json.loads((out/'atomic_inventory.json').read_text());rows=[];seen=set()
 for r in inv['items']:
  text=bank[r['response_id']]['response_text'];assert r['response_text_sha256']==hashlib.sha256(text.encode()).hexdigest();covered=set()
  for atom in r['atoms']:
   assert atom['item_id'] not in seen;seen.add(atom['item_id']);assert atom['response_span'] in text;assert atom['statement'].strip()
   for match in re.finditer(re.escape(atom['response_span']),text):covered.update(range(match.start(),match.end()))
  words=[m for m in re.finditer(r"[\w]+(?:['’][\w]+)?",text) if m.group().lower() not in STOP]
  missing=[m.group() for m in words if not all(i in covered for i in range(m.start(),m.end()))]
  rows.append({'response_id':r['response_id'],'atoms':len(r['atoms']),'substantive_token_span_coverage':1-len(missing)/len(words) if words else 1,'uncovered_tokens':missing})
 assert {r['response_id'] for r in inv['items']}==set(bank)
 write(out/'mechanical_inventory_audit.json',{'schema':'hexar-blind-inventory-audit/v2','bank_sha256':sha(out/'blind_bank.json'),'inventory_sha256':sha(out/'atomic_inventory.json'),'hashes_exact_spans_unique_items_complete_answers':True,'semantic_completeness_established':False,'human_or_model_extractor_qualified':False,'records':rows,'low_token_coverage_review_required':[r for r in rows if r['substantive_token_span_coverage']<.9]})
 print(json.dumps({'responses':len(rows),'atoms':len(seen),'low_coverage':sum(r['substantive_token_span_coverage']<.9 for r in rows)}))
if __name__=='__main__':main()
