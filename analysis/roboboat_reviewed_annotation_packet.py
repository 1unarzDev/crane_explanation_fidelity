"""Construct support packets only after explicit response-level inventory review."""
import hashlib
import json
from run_roboboat_terminal_comparison import annotation_packet


def validate_review_provenance(answer, review, returns):
    """Bind the project review to both retained, structurally valid extractions.

    Returns are raw file bytes, so this checks the exact audited artifacts rather
    than trusting a claimed status or silently recanonicalizing their contents.
    It checks provenance, not semantic completeness or physical support.
    """
    answer_hash=hashlib.sha256(answer.encode()).hexdigest()
    if review.get('source_text_sha256')!=answer_hash or review.get('opaque_response_id')!=answer_hash:
        raise ValueError('review source binding mismatch')
    for key in ('project_review_not_human_validation','abstraction_tags_discarded',
                'source_assertion_completeness_reviewed'):
        if review.get(key) is not True:
            raise ValueError('explicit project completeness review required')
    if set(returns)!={'A','B'} or set(review.get('extractor_returns_sha256',{}))!={'A','B'}:
        raise ValueError('both extraction passes required')
    for slot, raw in returns.items():
        if hashlib.sha256(raw).hexdigest()!=review['extractor_returns_sha256'][slot]:
            raise ValueError('audited extraction bytes changed')
        retained=json.loads(raw)
        if (retained.get('case_id')!=answer_hash or retained.get('slot')!=slot
            or retained.get('entry',{}).get('response_text')!=answer
            or retained.get('validation',{}).get('status')!='STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'):
            raise ValueError('extraction source or structural gate mismatch')


def build_reviewed_packet(evidence,answer,reference,review):
    if review['status']!='COMPLETE_FAITHFUL_PROJECT_REVIEW':
        raise ValueError('inventory completeness review gate closed')
    if hashlib.sha256(answer.encode()).hexdigest()!=review['opaque_response_id']:
        raise ValueError('review binds a different answer')
    claims=review['claims']
    if not claims:raise ValueError('empty reviewed inventory')
    seen=set()
    for c in claims:
        if set(c)!={'response_span','claim_text'} or c['response_span'] not in answer:
            raise ValueError('invalid reviewed claim or non-verbatim span')
        if not c['response_span'].strip() or not c['claim_text'].strip():
            raise ValueError('empty reviewed claim')
        pair=(c['response_span'],c['claim_text'])
        if pair in seen:raise ValueError('duplicate reviewed claim')
        seen.add(pair)
    inventory_hash=hashlib.sha256(json.dumps(claims,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    opaque=hashlib.sha256((evidence['packet_id']+review['opaque_response_id']+inventory_hash).encode()).hexdigest()[:24]
    result=annotation_packet(evidence,answer,reference,opaque)
    for form in result['forms']:
        form['atomic_statements']=[{
            'item_id':f'claim-{i+1:03d}','statement':c['claim_text'],
            'response_span':c['response_span'],'asserted_abstraction_level':None,
            'label':None,'annotation_notes':None,'visible_support_references':[]}
            for i,c in enumerate(claims)]
    result['inventory_origin']='marine-project-reviewed-two-pass-atomic-inventory-development'
    result['abstraction_tags_qualified']=False
    result['endpoint_status']='development reassessment only; confirmatory endpoint mapping unfrozen'
    return result
