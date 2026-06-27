from app.models import UsageRecord
from app.repositories import (
    add_usage_record,
    get_quota,
    list_usage_records,
    upsert_quota,
)


def test_upsert_creates_and_updates_quota(db_session):
    created = upsert_quota(db_session, "alice", monthly_allowance=1000, multiplier=1.5)
    assert created.monthly_allowance == 1000
    assert created.multiplier == 1.5
    assert created.used_credits == 0
    assert created.reserved_credits == 0

    updated = upsert_quota(db_session, "alice", multiplier=2.0)
    assert updated.monthly_allowance == 1000
    assert updated.multiplier == 2.0


def test_get_quota_returns_none_when_missing(db_session):
    assert get_quota(db_session, "ghost") is None


def test_usage_records_are_listed_newest_first(db_session):
    upsert_quota(db_session, "bob", monthly_allowance=500, multiplier=1.0)
    add_usage_record(
        db_session,
        UsageRecord(user_id="bob", status="success", actual_credits=10),
    )
    add_usage_record(
        db_session,
        UsageRecord(user_id="bob", status="success", actual_credits=20),
    )
    records = list_usage_records(db_session, "bob")
    assert len(records) == 2
    assert records[0].actual_credits == 20
