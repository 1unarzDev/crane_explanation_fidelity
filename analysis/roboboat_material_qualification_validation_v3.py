"""Corrected local adapter for the two-argument bound annotation validator."""
from adjudicate_evidence_calibration_annotations import validate_return


def validate(packet,returned,response_text):
    checked=validate_return(packet,returned)
    if not isinstance(response_text,str) or not response_text.strip():raise ValueError('qualification source text required')
    for category,field in (('required_unit_coverage','communicated'),('limitation_preservation','preserved')):
        for row in returned[category]:
            span=row['response_span']
            if row[field] and (not isinstance(span,str) or not span or span not in response_text):
                raise ValueError('positive annotation citation is not verbatim source text')
            if not row[field] and span is not None and (not isinstance(span,str) or not span or span not in response_text):
                raise ValueError('negative annotation citation is not verbatim source text')
    return checked
