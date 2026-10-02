"""Prospective candidate numeric usefulness for separately grounded odometry.

No answer parsing, claim detection, physical truth or runtime admission. The
caller must qualify quantity/source/window and literal exactness separately.
"""
from decimal import Decimal, localcontext

from .measurement_rounding import check, DECIMAL

MAX_WIDTH_M=Decimal('0.1')
PUBLIC_REQUIREMENT=(
    'When sampled odometry is visible, report its estimated XY travel and sampled '
    'odometry scope quantitatively: a supported approximate distance at 0.1 m or '
    'finer expressed resolution, or a supported bound/range no wider than 0.1 m '
    '(equivalent metric units are acceptable). Approximate rounded zero is not '
    'literal zero, physical immobility or physical goal attainment. Unquantified '
    'phrases such as some/little travel do not supply this required observation. '
    'Do not invent a measurement when this evidence is absent or masked.')


def _literal(text):
    if type(text) is not str or len(text)>100 or not DECIMAL.fullmatch(text):
        raise ValueError('bounded nonnegative decimal distance literal required')
    value=Decimal(text)
    if not value.is_finite() or value<0 or not -30<=value.as_tuple().exponent<=30:
        raise ValueError('bounded nonnegative decimal distance literal required')
    return value


def scalar(reference,reported_m,*,source_window_qualified,literal_exact=False):
    if type(source_window_qualified) is not bool:
        raise ValueError('explicit independently qualified source/window disposition required')
    _literal(reported_m)
    value=check(reference,reported_m,literal_exact=literal_exact)
    precision_ok=literal_exact or Decimal(value['decimal_quantum'])<=MAX_WIDTH_M
    return dict(value,useful_coverage_decided=True,
                source_window_qualified=source_window_qualified,
                substantive_precision_matches=precision_ok,
                useful_motion_coverage=source_window_qualified and precision_ok and value['numerical_presentation_matches'],
                policy='hexar-motion-usefulness-candidate/v1')


def interval(reference,lower_m,upper_m,*,source_window_qualified,lower_closed=True,upper_closed=True):
    if any(type(flag) is not bool for flag in (source_window_qualified,lower_closed,upper_closed)):
        raise ValueError('explicit source/window and interval-boundary dispositions required')
    # Reuse independently tested reference validation; exact string irrelevant.
    check(reference,'0')
    with localcontext() as context:
        context.prec=110
        low,high=_literal(lower_m),_literal(upper_m)
        if low>high or (low==high and not (lower_closed and upper_closed)):
            raise ValueError('nonempty ordered nonnegative measurement interval required')
        actual=Decimal(str(reference));width=high-low
        supported=(actual>=low if lower_closed else actual>low) and (actual<=high if upper_closed else actual<high)
        precise=width<=MAX_WIDTH_M
    return dict(policy='hexar-motion-usefulness-candidate/v1',numerical_presentation_matches=supported,
        substantive_precision_matches=precise,source_window_qualified=source_window_qualified,
        useful_motion_coverage=source_window_qualified and precise and supported,
        interval_width_m=str(width),physical_no_motion_inferred=False,
        physical_goal_attainment_inferred=False,useful_coverage_decided=True)
