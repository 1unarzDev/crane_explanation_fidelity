"""Fail-closed provider JSON parser candidate; never repairs or retries returns."""
import json
import math


def _pairs(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('duplicate JSON object key: '+key)
        value[key]=item
    return value


def _constant(value):
    raise ValueError('nonstandard JSON numeric constant: '+value)


def _float(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('nonfinite JSON numeric value')
    return result


def load(raw,maximum_bytes=1024*1024):
    if type(maximum_bytes) is not int or maximum_bytes<=0:raise ValueError('positive parser size bound required')
    if type(raw) is bytes:
        if len(raw)>maximum_bytes:raise ValueError('JSON response exceeds frozen size bound')
        text=raw.decode('utf-8',errors='strict')
    elif type(raw) is str:
        if len(raw.encode('utf-8'))>maximum_bytes:raise ValueError('JSON response exceeds frozen size bound')
        text=raw
    else:raise ValueError('raw UTF-8 text/bytes required')
    return json.loads(text,object_pairs_hook=_pairs,parse_constant=_constant,parse_float=_float)
