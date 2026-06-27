from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import get_quota, list_usage_records
from app.schemas import UsageRecordOut

router = APIRouter(prefix="/users", tags=["usage"])


@router.get("/{user_id}/usage/records", response_model=list[UsageRecordOut])
def usage_records(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[UsageRecordOut]:
    if get_quota(db, user_id) is None:
        raise HTTPException(status_code=404, detail=f"no quota configured for {user_id}")
    records = list_usage_records(db, user_id, limit=limit)
    return [UsageRecordOut.model_validate(r) for r in records]
