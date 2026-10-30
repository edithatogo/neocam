"""Review-record integrity cannot manufacture independent clinical validation."""
from copy import deepcopy
import pytest

SNAPSHOT='a'*64


def api():
    from quality.clinical_review import review_errors
    return review_errors


def packet():
    from scripts.analyse_refinements import pending_reviews
    p=pending_reviews(SNAPSHOT)
    for i,r in enumerate(p['reviews']):
        r.update(identity=f'Reviewer {i+1}',independent=True,status='approved',
            conflicts='None declared',date='2026-10-29',finding_summary='Assessed declared scope; no unresolved material issues.',
            evidence=['Documented report locator'])
    p['review_type']='external reviewer attestation'
    return p


def test_pending_is_not_validation():
    from scripts.analyse_refinements import pending_reviews
    assert api()(pending_reviews(SNAPSHOT),SNAPSHOT)


def test_valid_attestation_schema_only_not_identity_proof():
    assert api()(packet(),SNAPSHOT)==[]


@pytest.mark.parametrize('field,value',[('identity',''),('independent',False),('independent',1),
 ('status','pending'),('conflicts',''),('date','bad'),('finding_summary',''),('evidence',[]),
 ('snapshot_sha256','b'*64),('role','invented')])
def test_missing_or_false_attestation_fails(field,value):
    p=packet();p['reviews'][0][field]=value
    assert api()(p,SNAPSHOT)


def test_duplicate_role_and_empty_scope_fail():
    p=packet();p['reviews'][1]=p['reviews'][0].copy()
    assert api()(p,SNAPSHOT)
    assert api()({'reviews':[]},SNAPSHOT)


def test_simulated_or_stale_record_fails():
    p=packet();p['review_type']='simulated author roles'
    assert api()(p,SNAPSHOT)
    assert api()(packet(),'b'*64)
    assert api()(packet(),'')


def test_approved_record_with_unresolved_finding_fails():
    p=packet();p['reviews'][0]['findings']=[{'severity':'high','description':'Unknown outcome definition',
        'status':'open','resolution':'','evidence':[]}]
    assert api()(p,SNAPSHOT)
    p['reviews'][0]['findings'][0].update(status='resolved',resolution='Definition reconciled',evidence=['Evidence locator'])
    assert api()(p,SNAPSHOT)==[]


@pytest.mark.parametrize('bad',[None,[],{'reviews':None},{'reviews':[None]},'a'])
def test_malformed_review_fails_without_crash(bad):
    assert api()(bad,SNAPSHOT)


@pytest.mark.parametrize('finding', [None,{'severity':'high'},{'severity':[], 'status':'resolved'}])
def test_malformed_findings_fail_without_exception(finding):
    p=packet();p['reviews'][0]['findings']=[finding]
    assert api()(p,SNAPSHOT)
