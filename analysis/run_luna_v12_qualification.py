#!/usr/bin/env python3
"""Run final endpoint-aligned Luna qualification with binary unit coverage."""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"analysis"))
from luna_model_judge import atomic_write_json,digest_path  # noqa:E402
from run_luna_judge_qualification_v8 import wilson_interval  # noqa:E402
from run_luna_v11_qualification import bucket,run_pass,units  # noqa:E402
PROMPT=ROOT/"research/explanation_fidelity/prompts/luna-model-judge-v5.md";SCHEMA=ROOT/"research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json";BUILDER=ROOT/"analysis/build_luna_v12_qualification_suite.py"

def covered(status): return status=="covered"
def endpoint(case,j): return j.get("material_error") is False and covered(units(j)[case["mechanism_unit_id"]])
def score(suite,judgments):
 cases=suite["cases"]
 if set(judgments)!={c["case_id"] for c in cases}: raise ValueError("inventory mismatch")
 primary=[];unit_matches=[];core=[];factual=[];unsupported=[];protected=defaultdict(list);pairs=defaultdict(list);results=[]
 for c in cases:
  a=judgments[c["case_id"]];e=c["expected"];au=units(a);eu=e["required_unit_statuses"]
  if set(au)!=set(eu): raise ValueError(f"{c['case_id']} units mismatch")
  um={k:covered(au[k])==covered(v) for k,v in eu.items()};cm={k:a.get(k)==e[k] for k in c["scored_core_fields"]};pm=None
  if c["primary_endpoint_eligible"]: pm=endpoint(c,a)==(e["material_error"] is False and covered(eu[c["mechanism_unit_id"]]))
  if c["accuracy_eligible"]:
   if pm is not None: primary.append(pm)
   unit_matches.extend(um.values());core.extend(cm.values());(factual if e["material_error"] is False else unsupported).append(a.get("material_error")==e["material_error"])
  if "protected_causal" in c["category_tags"] and not (a.get("material_error")==e["material_error"] and a.get("causal_overclaim")==e["causal_overclaim"]): protected["causal"].append(c["case_id"])
  if "protected_boundary" in c["category_tags"] and not all(um[x] for x in c.get("protected_unit_ids",[])): protected["boundary"].append(c["case_id"])
  if c.get("presentation_pair_id"): pairs[c["presentation_pair_id"]].append(a)
  results.append({"case_id":c["case_id"],"primary_endpoint_match":pm,"unit_coverage_matches":um,"core_field_matches":cm})
 pair_results=[]
 for pid,pair in pairs.items():
  fields={k:pair[0].get(k)==pair[1].get(k) for k in ("material_error","disposition","mechanism_identification","causal_overclaim","evidence_problem")};ok=all(fields.values());pair_results.append({"pair_id":pid,"invariant":ok,"fields":fields})
  if not ok: protected["invariance"].append(pid)
 fr=len(factual)-sum(factual);fa=len(unsupported)-sum(unsupported);t=suite["thresholds"];pr=bucket(primary);ur=bucket(unit_matches);cr=bucket(core)
 gates={"primary_endpoint_accuracy":pr["accuracy"]>=t["minimum_primary_endpoint_accuracy"],"unit_coverage_accuracy":ur["accuracy"]>=t["minimum_unit_coverage_accuracy"],"core_field_accuracy":cr["accuracy"]>=t["minimum_core_field_accuracy"],"factual_false_rejection_rate":fr/len(factual)<=t["maximum_false_rejection_rate"],"unsupported_false_acceptance_rate":fa/len(unsupported)<=t["maximum_false_acceptance_rate"],"protected_tests":not protected}
 return {"primary_endpoint":pr,"unit_coverage":ur,"core_fields":cr,"factual_false_rejections":{**wilson_interval(fr,len(factual)),"errors":fr,"rate":fr/len(factual)},"unsupported_false_acceptances":{**wilson_interval(fa,len(unsupported)),"errors":fa,"rate":fa/len(unsupported)},"protected_failures":dict(protected),"presentation_pairs":pair_results,"case_results":results,"gates":gates,"qualified":all(gates.values())}
def load_suite(p):
 s=json.loads(p.read_text())
 if s.get("schema")!="crane-luna-judge-qualification-suite/v12" or len(s.get("cases",[]))!=18: raise ValueError("suite mismatch")
 return s
def validate_freeze(p,suite):
 f=json.loads(p.read_text())
 if f.get("schema")!="crane-luna-judge-freeze/v12" or f.get("status")!="FROZEN_BEFORE_ANY_V12_QUALIFICATION_CALL": raise ValueError("freeze mismatch")
 for key,path in {"suite_sha256":suite,"prompt_sha256":PROMPT,"output_schema_sha256":SCHEMA,"caller_source_sha256":ROOT/"analysis/luna_model_judge.py","runner_source_sha256":Path(__file__),"suite_builder_sha256":BUILDER}.items():
  if f.get(key)!=digest_path(path): raise ValueError(f"freeze {key} mismatch")
 return f
def main():
 p=argparse.ArgumentParser();p.add_argument("--suite",type=Path,required=True);p.add_argument("--freeze",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);a=p.parse_args();sp=a.suite.resolve();s=load_suite(sp);validate_freeze(a.freeze.resolve(),sp);rp=a.output_root/"heldout-qualification.json"
 if rp.exists(): raise FileExistsError("v12 report exists")
 passes={};keys={}
 for pid in ("pass-1","pass-2"):
  j,keys[pid],fail=run_pass(s["cases"],pid,a.output_root);passes[pid]={"qualified":False,"call_failures":fail,"call_failure_count":len(fail)} if fail else {**score(s,j),"call_failures":{},"call_failure_count":0}
  if not fail: passes[pid]["gates"]["zero_call_failures"]=True
 ok=all(x["qualified"] for x in passes.values());r={"schema":"crane-luna-judge-heldout-qualification/v12","suite":str(sp.relative_to(ROOT)),"suite_sha256":digest_path(sp),"freeze":str(a.freeze.resolve().relative_to(ROOT)),"freeze_sha256":digest_path(a.freeze.resolve()),"passes":passes,"call_cache_keys":keys,"status":"QUALIFIED" if ok else "FAILED","study_scoring_allowed":ok};atomic_write_json(rp,r);print(json.dumps({"status":r["status"]}))
if __name__=="__main__":main()
