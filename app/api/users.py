from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import get_quota, upsert_quota
from app.schemas import UsageSummary, UserConfigRequest, UserConfigResponse
from app.services.quota import QuotaService

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}/config", response_model=UserConfigResponse)
def configure_user(
    user_id: str, payload: UserConfigRequest, db: Session = Depends(get_db)
) -> UserConfigResponse:
    quota = upsert_quota(
        db,
        user_id,
        monthly_allowance=payload.monthly_allowance,
        multiplier=payload.multiplier,
    )
    return UserConfigResponse(
        user_id=quota.user_id,
        monthly_allowance=quota.monthly_allowance,
        multiplier=quota.multiplier,
    )


@router.get("/{user_id}/usage", response_model=UsageSummary)
def get_usage(user_id: str, db: Session = Depends(get_db)) -> UsageSummary:
    quota = get_quota(db, user_id)
    if quota is None:
        raise HTTPException(status_code=404, detail=f"no quota configured for {user_id}")
    return UsageSummary(
        user_id=quota.user_id,
        monthly_allowance=quota.monthly_allowance,
        multiplier=quota.multiplier,
        used_credits=quota.used_credits,
        reserved_credits=quota.reserved_credits,
        remaining_credits=QuotaService(db).remaining(quota),
    )
