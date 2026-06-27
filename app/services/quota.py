from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import UserQuota
from app.repositories import get_quota


class QuotaNotConfigured(Exception):
    pass


class QuotaExceeded(Exception):
    def __init__(self, remaining: int, required: int):
        super().__init__(
            f"quota exceeded: requires {required} credits, {remaining} remaining"
        )
        self.remaining = remaining
        self.required = required


class QuotaService:
    def __init__(self, db: Session):
        self.db = db

    def get_state(self, user_id: str) -> UserQuota:
        quota = get_quota(self.db, user_id)
        if quota is None:
            raise QuotaNotConfigured(f"no quota configured for user {user_id}")
        return quota

    def remaining(self, quota: UserQuota) -> int:
        return quota.monthly_allowance - quota.used_credits - quota.reserved_credits

    def reserve(self, user_id: str, amount: int) -> None:
        stmt = (
            update(UserQuota)
            .where(UserQuota.user_id == user_id)
            .where(
                UserQuota.monthly_allowance
                - UserQuota.used_credits
                - UserQuota.reserved_credits
                >= amount
            )
            .values(reserved_credits=UserQuota.reserved_credits + amount)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        if result.rowcount == 0:
            quota = get_quota(self.db, user_id)
            if quota is None:
                raise QuotaNotConfigured(f"no quota configured for user {user_id}")
            raise QuotaExceeded(remaining=self.remaining(quota), required=amount)

    def commit_usage(self, user_id: str, reserved: int, actual: int) -> None:
        stmt = (
            update(UserQuota)
            .where(UserQuota.user_id == user_id)
            .values(
                reserved_credits=UserQuota.reserved_credits - reserved,
                used_credits=UserQuota.used_credits + actual,
            )
        )
        self.db.execute(stmt)
        self.db.commit()

    def release(self, user_id: str, reserved: int) -> None:
        stmt = (
            update(UserQuota)
            .where(UserQuota.user_id == user_id)
            .values(reserved_credits=UserQuota.reserved_credits - reserved)
        )
        self.db.execute(stmt)
        self.db.commit()
