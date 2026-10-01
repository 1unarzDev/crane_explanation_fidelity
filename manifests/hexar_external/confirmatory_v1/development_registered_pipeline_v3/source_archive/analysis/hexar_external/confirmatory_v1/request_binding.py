"""Pure explicit no-tool request binding for prospective method development.

No ambient environment, repository context or provider call is performed here.
Provider-neutral fields must be implemented and qualified by the selected real
transport; this constructor alone does not assert a pinned hosted backend.
"""
import copy
from .journal import fingerprint
from .blind_bank import PACKET_KEYS

SETTINGS=('provider','model','model_version','temperature','top_p','max_output_tokens',
          'seed','system_instructions','tool_permissions','repository_access','context_access',
          'quality_retries','technical_retries','timeout_seconds','output_schema')


def bind(packet,prompt,settings):
    if set(packet)!=set(PACKET_KEYS):raise ValueError('unapproved packet projection')
    if set(settings)!=set(SETTINGS):raise ValueError('complete explicit runtime settings required')
    for field in SETTINGS:
        if settings[field] is None:raise ValueError('unbound '+field)
    if not isinstance(prompt,str) or not prompt.strip():raise ValueError('strong frozen prompt required')
    if not 0<=settings['temperature']<=2 or not 0<settings['top_p']<=1:
        raise ValueError('invalid decoding settings')
    if settings['tool_permissions']!=[] or settings['repository_access']!='none' or settings['context_access']!='packet_only':
        raise ValueError('tools/repository/unapproved context forbidden')
    if settings['quality_retries']!=0 or settings['technical_retries']!=0:
        raise ValueError('no retries')
    if settings['max_output_tokens']<=0 or settings['timeout_seconds']<=0:
        raise ValueError('invalid resource limits')
    request=dict(schema='hexar-method-request-binding/v1',settings=copy.deepcopy(settings),
                 messages=[dict(role='system',content=settings['system_instructions']),
                           dict(role='developer',content=prompt),
                           dict(role='user',content=copy.deepcopy(packet))])
    return dict(request=request,request_sha256=fingerprint(request),
                packet_sha256=fingerprint(packet),prompt_sha256=fingerprint(prompt),
                transport_qualified=False)


def parse_answer(value):
    if not isinstance(value,dict) or set(value)!={'answer'} or not isinstance(value['answer'],str) or not value['answer'].strip():
        raise ValueError('exact nonempty answer schema required; no repairs or retries')
    return value['answer']
