#!/usr/bin/env python3
"""Same frozen removal/reference rules under a versioned output root."""
import json,sys
from audit_release import ROOT,sha,write
from verify_v3 import V3,study
import build_v2_packets
from build_references_v2 import build

def main():
 study()
 if sys.argv[1:]!=['--cohort','reserved']:raise ValueError('This release only builds the full reserved cohort.')
 build_v2_packets.V2=V3;build_v2_packets.main()
 root=V3/'reserved';rebuilt=build(root);dest=root/'references.json'
 if dest.exists():assert dest.read_bytes()==rebuilt
 else:dest.write_bytes(rebuilt)
 packets=json.loads((root/'packets.json').read_text())['packets']
 assert len(packets)==108 and len({p['recording_id'] for p in packets})==12
 write(root/'reference_release.json',{'schema':'hexar-independent-reference-release/v3','packets_sha256':sha(root/'packets.json'),'references_sha256':sha(dest),'reference_rules_sha256':sha(ROOT/'analysis/hexar_external/build_references_v2.py'),'method_answers_inspected':False,'n_recordings':12,'n_packets':108,'alpha_consumed':0})
 print('ALL_RESERVED_PACKETS_REFERENCES_RELEASED_BEFORE_ANSWERS',flush=True)
if __name__=='__main__':main()
