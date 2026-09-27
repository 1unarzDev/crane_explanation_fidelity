#!/usr/bin/env python3
"""Run corrected contract-complete Luna qualification v2 without changing judge settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from luna_model_judge import atomic_write_json, digest_path  # noqa:E402
from run_luna_judge_qualification_v8 import wilson_interval  # noqa:E402
from run_luna_v11_qualification import bucket, run_pass, units  # noqa:E402

PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
OUTPUT_SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
BUILDER = ROOT / "analysis/build_contract_complete_luna_qualification_v2.py"


def endpoint(judgment: dict[str, Any]) -> bool:
    return judgment.get("material_error") is False and all(
        units(judgment).get(key) == "covered" for key in ("M", "Q", "O", "L")
    )


def score(suite: dict[str, Any], judgments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(judgments) != {case["case_id"] for case in suite["cases"]}:
        raise ValueError("v2 judgment inventory mismatch")
    endpoints=[]; unit_matches=[]; field_matches=[]; factual=[]; unsupported=[]
    protected=[]; secondary=[]; cases=[]
    for case in suite["cases"]:
        actual=judgments[case["case_id"]]; expected=case["expected"]; actual_units=units(actual)
        if set(actual_units)!={"M","Q","O","L"}: raise ValueError(f"{case['case_id']}: unit inventory mismatch")
        unit={key:actual_units[key]==value for key,value in expected["required_unit_statuses"].items()}
        fields={key:actual.get(key)==expected[key] for key in case["endpoint_scored_fields"]}
        expected_endpoint=expected["material_error"] is False and all(v=="covered" for v in expected["required_unit_statuses"].values())
        endpoint_match=endpoint(actual)==expected_endpoint; endpoints.append(endpoint_match)
        unit_matches.extend(unit.values()); field_matches.extend(fields.values())
        (factual if expected["material_error"] is False else unsupported).append(actual.get("material_error")==expected["material_error"])
        if case["protected_causal"] and not (
            actual.get("material_error")==expected["material_error"]
            and actual.get("causal_overclaim")==expected["causal_overclaim"]
            and actual_units["L"]==expected["required_unit_statuses"]["L"]): protected.append(case["case_id"])
        for field in ("answerability","correct_abstention","material_error_categories"):
            if actual.get(field)!=expected[field]: secondary.append({"case_id":case["case_id"],"field":field,"expected":expected[field],"actual":actual.get(field)})
        cases.append({"case_id":case["case_id"],"variant":case["variant"],"endpoint_match":endpoint_match,"unit_matches":unit,"endpoint_field_matches":fields})
    false_rejections=len(factual)-sum(factual); false_acceptances=len(unsupported)-sum(unsupported); thresholds=suite["thresholds"]
    ep=bucket(endpoints); un=bucket(unit_matches); fi=bucket(field_matches)
    gates={
        "endpoint_accuracy":ep["accuracy"]>=thresholds["minimum_endpoint_accuracy"],
        "required_unit_accuracy":un["accuracy"]>=thresholds["minimum_required_unit_accuracy"],
        "endpoint_field_accuracy":fi["accuracy"]>=thresholds["minimum_endpoint_field_accuracy"],
        "false_rejection_rate":false_rejections/len(factual)<=thresholds["maximum_false_rejection_rate"],
        "false_acceptance_rate":false_acceptances/len(unsupported)<=thresholds["maximum_false_acceptance_rate"],
        "protected_causal_cases":len(protected)<=thresholds["protected_causal_errors_allowed"],
    }
    return {"endpoint":ep,"required_units":un,"endpoint_fields":fi,
            "false_rejections":{**wilson_interval(false_rejections,len(factual)),"errors":false_rejections,"rate":false_rejections/len(factual)},
            "false_acceptances":{**wilson_interval(false_acceptances,len(unsupported)),"errors":false_acceptances,"rate":false_acceptances/len(unsupported)},
            "protected_causal_failures":protected,"secondary_mismatches":secondary,"case_results":cases,
            "gates":gates,"qualified":all(gates.values())}


def validate_freeze(path: Path, suite_path: Path) -> dict[str, Any]:
    freeze=json.loads(path.read_text())
    if freeze.get("schema")!="crane-contract-complete-luna-qualification-freeze/v2" or freeze.get("status")!="FROZEN_BEFORE_ANY_QUALIFICATION_CALL": raise ValueError("v2 freeze mismatch")
    sources={"suite_sha256":suite_path,"prompt_sha256":PROMPT,"output_schema_sha256":OUTPUT_SCHEMA,"caller_source_sha256":CALLER,"runner_source_sha256":Path(__file__),"suite_builder_sha256":BUILDER}
    for field,source in sources.items():
        if freeze.get(field)!=digest_path(source): raise ValueError(f"v2 freeze {field} mismatch")
    return freeze


def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument("--suite",type=Path,required=True);parser.add_argument("--freeze",type=Path,required=True);parser.add_argument("--output-root",type=Path,required=True);args=parser.parse_args()
    suite_path=args.suite.resolve(strict=True);freeze_path=args.freeze.resolve(strict=True);suite=json.loads(suite_path.read_text());validate_freeze(freeze_path,suite_path)
    report_path=args.output_root/"heldout-qualification.json"
    if report_path.exists(): raise FileExistsError("v2 result exists")
    passes={};keys={}
    for pass_id in ("pass-1","pass-2"):
        judgments,keys[pass_id],failures=run_pass(suite["cases"],pass_id,args.output_root)
        if failures: passes[pass_id]={"qualified":False,"call_failures":failures,"call_failure_count":len(failures),"scoring_status":"NOT_SCORED_INCOMPLETE_INVENTORY"}
        else:
            passes[pass_id]={**score(suite,judgments),"call_failures":{},"call_failure_count":0};passes[pass_id]["gates"]["zero_call_failures"]=True;passes[pass_id]["qualified"]=all(passes[pass_id]["gates"].values())
    qualified=all(item["qualified"] for item in passes.values())
    report={"schema":"crane-contract-complete-luna-qualification-result/v2","status":"QUALIFIED" if qualified else "FAILED","suite":suite_path.relative_to(ROOT).as_posix(),"suite_sha256":digest_path(suite_path),"freeze":freeze_path.relative_to(ROOT).as_posix(),"freeze_sha256":digest_path(freeze_path),"passes":passes,"call_cache_keys":keys,"study_scoring_allowed":qualified,"confirmatory_alpha_consumed":0.0}
    atomic_write_json(report_path,report);print(json.dumps({"status":report["status"]}))


if __name__=="__main__":main()
