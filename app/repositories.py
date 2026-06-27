from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UsageRecord, UserQuota


def get_quota(db: Session, user_id: str) -> UserQuota | None:
    return db.get(UserQuota, user_id)


def upsert_quota(
    db: Session,
    user_id: str,
    monthly_allowance: int | None = None,
    multiplier: float | None = None,
) -> UserQuota:
    quota = db.get(UserQuota, user_id)
    if quota is None:
        quota = UserQuota(
            user_id=user_id,
            monthly_allowance=monthly_allowance if monthly_allowance is not None else 0,
            multiplier=multiplier if multiplier is not None else 1.0,
        )
        db.add(quota)
    else:
        if monthly_allowance is not None:
            quota.monthly_allowance = monthly_allowance
        if multiplier is not None:
            quota.multiplier = multiplier
    db.commit()
    db.refresh(quota)
    return quota


def add_usage_record(db: Session, record: UsageRecord) -> UsageRecord:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_usage_records(
    db: Session, user_id: str, limit: int = 100
) -> list[UsageRecord]:
    stmt = (
        select(UsageRecord)
        .where(UsageRecord.user_id == user_id)
        .order_by(UsageRecord.created_at.desc(), UsageRecord.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
