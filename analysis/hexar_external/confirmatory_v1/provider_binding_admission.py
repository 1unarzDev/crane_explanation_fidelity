"""Require evidence of a stable served model and full request/system binding.

No provider calls. A CLI executable hash alone cannot satisfy model stability.
"""
import json
from .unique_admission import _pinned


def admission_errors(docs,root):
    targets=(('baseline',docs.get('comparator_freeze.json',{}).get('baseline',{})),
             ('judge',docs.get('annotation_freeze.json',{})))
    errors=[]
    for role,config in targets:
        try:
            pin=config['provider_binding_qualification']
            report=json.loads(_pinned(root,pin).read_text())
            if type(report) is not dict or report.get('schema')!='hexar-provider-binding-qualification/v1' or report.get('status')!='QUALIFIED':
                raise ValueError('qualified provider binding object required')
            if (report.get('role')!=role or type(report.get('confirmatory_outputs_generated')) is not int
                    or report['confirmatory_outputs_generated']!=0):
                raise ValueError('role-specific preconfirmation qualification required')
            expected_model=config.get('model')
            version=config.get('model_version')
            if not isinstance(version,str) or not version.strip() or report.get('requested_model')!=expected_model or report.get('served_model_version')!=version:
                raise ValueError('requested model and observed/attested served version must match freeze')
            if (report.get('immutable_served_version_attested') is not True
                    or report.get('full_system_and_request_binding_verified') is not True
                    or report.get('decoding_binding_verified') is not True
                    or report.get('automatic_retries_disabled') is not True):
                raise ValueError('immutable served version, full system/request/decoding and no-retry evidence required')
            evidence=report.get('evidence')
            names={'version_stability_basis','effective_request_and_system','decoding_behavior','single_attempt_transport'}
            if type(evidence) is not dict or set(evidence)!=names:
                raise ValueError('all four hash-bound evidence categories required')
            for value in evidence.values():_pinned(root,value)
            frozen_decoding=config.get('decoding')
            if type(frozen_decoding) is not dict or not frozen_decoding or report.get('frozen_decoding')!=frozen_decoding:
                raise ValueError('complete explicit decoding configuration must match qualified request')
            if role=='baseline' and report.get('effective_system_sha256')!=config.get('system_instructions_sha256'):
                raise ValueError('effective baseline system binding must match freeze')
            if role=='judge' and report.get('effective_system_sha256')!=config.get('complete_system_instructions_sha256'):
                raise ValueError('effective judge system binding must match freeze')
            if not isinstance(report.get('effective_system_sha256'),str) or len(report['effective_system_sha256'])!=64:
                raise ValueError('full effective system hash required, not user prompt hash alone')
        except (OSError,KeyError,TypeError,ValueError) as exc:
            errors.append('provider '+role+': stable complete binding missing/invalid: '+str(exc))
    return errors
