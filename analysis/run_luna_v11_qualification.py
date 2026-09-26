#!/usr/bin/env python3
"""Run and score the endpoint-aligned Luna-v11 held-out qualification."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from typing import Any


ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"analysis"))
from luna_model_judge import LunaIsolatedCodexCaller,atomic_write_json,digest_path,qualification_envelope  # noqa:E402
from run_luna_judge_qualification_v8 import wilson_interval  # noqa:E402

PROMPT=ROOT/"research/explanation_fidelity/prompts/luna-model-judge-v5.md"
SCHEMA=ROOT/"research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
BUILDER=ROOT/"analysis/build_luna_v11_qualification_suite.py"


def bucket(matches:list[bool])->dict[str,Any]:
    count=sum(matches); result=wilson_interval(count,len(matches)); result["accuracy"]=count/len(matches)
    return result


def units(judgment:dict[str,Any])->dict[str,str]:
    result={item["unit_id"]:item["status"] for item in judgment["required_units"]}
    if len(result)!=len(judgment["required_units"]): raise ValueError("duplicate unit ID")
    return result


def endpoint_success(case:dict[str,Any],judgment:dict[str,Any])->bool:
    return judgment.get("material_error") is False and units(judgment).get(case["mechanism_unit_id"])=="covered"


def score(suite:dict[str,Any],judgments:dict[str,dict[str,Any]])->dict[str,Any]:
    cases=suite["cases"]
    if set(judgments)!={case["case_id"] for case in cases}: raise ValueError("judgment inventory mismatch")
    primary=[]; all_units=[]; core=[]; factual=[]; unsupported=[]; protected=defaultdict(list); results=[]; pairs=defaultdict(list)
    for case in cases:
        actual=judgments[case["case_id"]]; expected=case["expected"]
        actual_units=units(actual); expected_units=expected["required_unit_statuses"]
        if set(actual_units)!=set(expected_units): raise ValueError(f"{case['case_id']} unit inventory mismatch")
        unit_matches={key:actual_units[key]==value for key,value in expected_units.items()}
        core_matches={field:actual.get(field)==expected[field] for field in case["scored_core_fields"]}
        primary_match=None
        if case["primary_endpoint_eligible"]:
            expected_success=(
                expected["material_error"] is False
                and expected_units[case["mechanism_unit_id"]] == "covered"
            )
            primary_match=endpoint_success(case,actual)==expected_success
        if case["accuracy_eligible"]:
            if primary_match is not None: primary.append(primary_match)
            all_units.extend(unit_matches.values()); core.extend(core_matches.values())
            if expected["material_error"] is False: factual.append(actual.get("material_error") is False)
            else: unsupported.append(actual.get("material_error") is True)
        tags=case["category_tags"]
        if "protected_causal" in tags and not (actual.get("material_error")==expected["material_error"] and actual.get("causal_overclaim")==expected["causal_overclaim"]):
            protected["protected_causal"].append(case["case_id"])
        if "protected_boundary" in tags and not all(unit_matches[key] for key in case.get("protected_unit_ids",[])):
            protected["protected_boundary"].append(case["case_id"])
        if case.get("presentation_pair_id"): pairs[case["presentation_pair_id"]].append(actual)
        results.append({"case_id":case["case_id"],"primary_endpoint_match":primary_match,"required_unit_matches":unit_matches,"core_field_matches":core_matches})
    pair_results=[]
    for identifier,pair in pairs.items():
        fields={field:pair[0].get(field)==pair[1].get(field) for field in ("material_error","disposition","mechanism_identification","causal_overclaim","evidence_problem")}
        invariant=all(fields.values()); pair_results.append({"pair_id":identifier,"invariant":invariant,"fields":fields})
        if not invariant: protected["presentation_invariance"].append(identifier)
    false_rejections=len(factual)-sum(factual); false_acceptances=len(unsupported)-sum(unsupported)
    thresholds=suite["thresholds"]
    primary_result=bucket(primary); unit_result=bucket(all_units); core_result=bucket(core)
    gates={
        "primary_endpoint_accuracy":primary_result["accuracy"]>=thresholds["minimum_primary_endpoint_accuracy"],
        "required_unit_accuracy":unit_result["accuracy"]>=thresholds["minimum_required_unit_accuracy"],
        "scored_core_field_accuracy":core_result["accuracy"]>=thresholds["minimum_scored_core_field_accuracy"],
        "factual_false_rejection_rate":false_rejections/len(factual)<=thresholds["maximum_false_rejection_rate"],
        "unsupported_false_acceptance_rate":false_acceptances/len(unsupported)<=thresholds["maximum_false_acceptance_rate"],
        "protected_tests":not protected,
    }
    return {
        "primary_endpoint":primary_result,"required_units":unit_result,"scored_core_fields":core_result,
        "factual_false_rejections":{**wilson_interval(false_rejections,len(factual)),"errors":false_rejections,"rate":false_rejections/len(factual)},
        "unsupported_false_acceptances":{**wilson_interval(false_acceptances,len(unsupported)),"errors":false_acceptances,"rate":false_acceptances/len(unsupported)},
        "protected_failures":dict(protected),"presentation_pairs":pair_results,"case_results":results,
        "gates":gates,"qualified":all(gates.values()),
    }


def load_suite(path:Path)->dict[str,Any]:
    suite=json.loads(path.read_text())
    if suite.get("schema")!="crane-luna-judge-qualification-suite/v11" or len(suite.get("cases",[]))!=22: raise ValueError("v11 suite mismatch")
    return suite


def validate_freeze(path:Path,suite_path:Path)->dict[str,Any]:
    freeze=json.loads(path.read_text())
    if freeze.get("schema")!="crane-luna-judge-freeze/v11" or freeze.get("status")!="FROZEN_BEFORE_ANY_V11_QUALIFICATION_CALL": raise ValueError("v11 freeze mismatch")
    expected={"suite_sha256":suite_path,"prompt_sha256":PROMPT,"output_schema_sha256":SCHEMA,"caller_source_sha256":ROOT/"analysis/luna_model_judge.py","runner_source_sha256":Path(__file__),"suite_builder_sha256":BUILDER}
    for field,source in expected.items():
        if freeze.get(field)!=digest_path(source): raise ValueError(f"v11 freeze {field} mismatch")
    if freeze.get("passes")!=["pass-1","pass-2"]: raise ValueError("v11 pass inventory mismatch")
    return freeze


def run_pass(cases,pass_id,root):
    caller=LunaIsolatedCodexCaller(cache=root/"calls"/"high"/pass_id,effort="high",prompt_path=PROMPT)
    judgments={}; keys={}; failures={}
    for case in cases:
        try: record=caller.call(qualification_envelope(case,pass_id))
        except RuntimeError as error: failures[case["case_id"]]=str(error); continue
        judgments[case["case_id"]]=record["judgment"]; keys[case["case_id"]]=record["cache_key"]
    return judgments,keys,failures


def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--suite",type=Path,required=True); parser.add_argument("--freeze",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); args=parser.parse_args()
    suite_path=args.suite.resolve(); suite=load_suite(suite_path); validate_freeze(args.freeze.resolve(),suite_path)
    report_path=args.output_root/"heldout-qualification.json"
    if report_path.exists(): raise FileExistsError("v11 report already exists")
    passes={}; keys={}
    for pass_id in ("pass-1","pass-2"):
        judgments,keys[pass_id],failures=run_pass(suite["cases"],pass_id,args.output_root)
        passes[pass_id]={"qualified":False,"call_failures":failures,"call_failure_count":len(failures),"scoring_status":"NOT_SCORED_INCOMPLETE_INVENTORY"} if failures else {**score(suite,judgments),"call_failures":{},"call_failure_count":0}
        if not failures: passes[pass_id]["gates"]["zero_call_failures"]=True
    qualified=all(value["qualified"] for value in passes.values())
    report={"schema":"crane-luna-judge-heldout-qualification/v11","suite":str(suite_path.relative_to(ROOT)),"suite_sha256":digest_path(suite_path),"freeze":str(args.freeze.resolve().relative_to(ROOT)),"freeze_sha256":digest_path(args.freeze.resolve()),"passes":passes,"call_cache_keys":keys,"status":"QUALIFIED" if qualified else "FAILED","study_scoring_allowed":qualified}
    atomic_write_json(report_path,report); print(json.dumps({"status":report["status"]}))


if __name__=="__main__": main()
