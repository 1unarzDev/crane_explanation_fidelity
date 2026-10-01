"""Deterministic decimal-presentation check for a grounded motion measurement.

The caller must separately qualify the claim's quantity, frame, window, scope and
whether it asserts literal exactness. This utility neither locates claims in raw
answers nor supplies physical truth, useful coverage or a no-motion threshold.
"""
from decimal import Decimal, InvalidOperation, localcontext
import math
import re

DECIMAL = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')


def check(reference,reported_decimal,*,literal_exact=False):
    if type(reference) not in (int,float) or not math.isfinite(reference) or reference<0:
        raise ValueError('finite nonnegative grounded distance required')
    if type(reported_decimal) is not str or not DECIMAL.fullmatch(reported_decimal) or len(reported_decimal)>100:
        raise ValueError('one finite decimal measurement literal required')
    if type(literal_exact) is not bool:raise ValueError('explicit exactness disposition required')
    try:
        with localcontext() as context:
            context.prec=110
            actual=Decimal(str(reference));presented=Decimal(reported_decimal)
            exponent=presented.as_tuple().exponent
            if not presented.is_finite() or not -30<=exponent<=30:
                raise ValueError('bounded decimal presentation scale required')
            quantum=Decimal(10)**exponent
            error=abs(actual-presented)
            half_quantum=quantum/2
            matches=actual==presented if literal_exact else error<=half_quantum
            return dict(schema='hexar-grounded-decimal-presentation-candidate/v1',
                        reference_decimal=str(actual),reported_decimal=reported_decimal,
                        literal_exact=literal_exact,decimal_quantum=str(quantum),
                        absolute_error=str(error),maximum_rounding_error='0' if literal_exact else str(half_quantum),
                        numerical_presentation_matches=matches,
                        scope_and_quantity_qualified=False,useful_coverage_decided=False,
                        physical_no_motion_inferred=False,
                        rule='Equality for literal exact assertions; closed half-quantum interval for ordinary decimal presentation. No unreported precision is inferred.')
    except InvalidOperation as failure:raise ValueError('invalid decimal measurement') from failure
