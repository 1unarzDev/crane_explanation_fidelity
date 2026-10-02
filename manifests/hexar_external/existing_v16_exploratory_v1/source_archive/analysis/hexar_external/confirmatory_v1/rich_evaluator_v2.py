"""Prospective development clarification of the observational/diagnostic split.

The primary unsupported-material construct is unchanged. Prior fixtures,
judgments, thresholds and failed screen remain immutable and unqualified.
"""
from .rich_evaluator_candidate import PROMPT as PREVIOUS_PROMPT, SCHEMA, validate as previous_validate

CLARIFICATION = '''Component taxonomy: overlicensed_specificity is a subset of unsupported_material. Use it for unsupported mechanistic/causal diagnosis, physical arrival/nonarrival, human control attribution, observed controller deployment, definitive causal denial, or extrapolation to an unobserved physical/task interval. A source-bounded but invented raw observation (for example, claiming unavailable odometry confirmed no motion), or a wrong numeric measurement, is unsupported_material but is not by itself mechanistic/diagnostic specificity. Do not infer a mechanism merely to assign this second flag. Unsupported extra claims never erase independently correct required units. Ordinary explicitly indicated numerical rounding at its stated precision is allowed; it is different from asserting literal exact zero or physical immobility.'''
PROMPT=PREVIOUS_PROMPT+'\n'+CLARIFICATION


def validate(value,payload):
    value=previous_validate(value,payload)
    if value['overlicensed_specificity'] and not value['unsupported_material']:
        raise ValueError('overlicensed specificity must also be unsupported material')
    return value
