import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
B=load("b12",ROOT/"analysis/build_luna_v12_qualification_suite.py");R=load("r12",ROOT/"analysis/run_luna_v12_qualification.py")
def test_suite_denominators_and_fresh_ids():
 s=B.build_suite();B.validate(s);assert len(s["cases"])==18;assert sum(c["accuracy_eligible"] for c in s["cases"])==16;assert sum(c["primary_endpoint_eligible"] for c in s["cases"])==8;assert all(c["case_id"].startswith("Q12") for c in s["cases"])
def test_unit_coverage_collapses_error_subtypes_only():
 assert R.covered("covered");assert not R.covered("incorrect");assert not R.covered("omitted");assert not R.covered("unresolved")
def test_endpoint_still_requires_mechanism_coverage_and_no_material_error():
 c=next(x for x in B.build_suite()["cases"] if x["case_id"]=="Q12H01S");j={"material_error":False,"required_units":[{"unit_id":"u-mechanism","status":"covered"},{"unit_id":"u-limit","status":"covered"}]};assert R.endpoint(c,j);j["material_error"]=True;assert not R.endpoint(c,j)
