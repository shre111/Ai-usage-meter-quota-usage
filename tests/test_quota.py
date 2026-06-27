import pytest

from app.repositories import get_quota, upsert_quota
from app.services.quota import QuotaExceeded, QuotaNotConfigured, QuotaService


def test_reserve_succeeds_within_allowance(db_session):
    upsert_quota(db_session, "alice", monthly_allowance=100, multiplier=1.0)
    service = QuotaService(db_session)
    service.reserve("alice", 40)
    quota = get_quota(db_session, "alice")
    assert quota.reserved_credits == 40
    assert service.remaining(quota) == 60


def test_reserve_rejected_when_insufficient(db_session):
    upsert_quota(db_session, "alice", monthly_allowance=100, multiplier=1.0)
    service = QuotaService(db_session)
    service.reserve("alice", 80)
    with pytest.raises(QuotaExceeded) as exc:
        service.reserve("alice", 40)
    assert exc.value.remaining == 20
    assert exc.value.required == 40


def test_reserve_unconfigured_user_raises(db_session):
    service = QuotaService(db_session)
    with pytest.raises(QuotaNotConfigured):
        service.reserve("ghost", 10)


def test_commit_moves_reserved_to_used(db_session):
    upsert_quota(db_session, "bob", monthly_allowance=100, multiplier=1.0)
    service = QuotaService(db_session)
    service.reserve("bob", 40)
    service.commit_usage("bob", reserved=40, actual=30)
    quota = get_quota(db_session, "bob")
    assert quota.reserved_credits == 0
    assert quota.used_credits == 30
    assert service.remaining(quota) == 70


def test_release_returns_reserved_credits(db_session):
    upsert_quota(db_session, "carol", monthly_allowance=100, multiplier=1.0)
    service = QuotaService(db_session)
    service.reserve("carol", 40)
    service.release("carol", 40)
    quota = get_quota(db_session, "carol")
    assert quota.reserved_credits == 0
    assert service.remaining(quota) == 100
