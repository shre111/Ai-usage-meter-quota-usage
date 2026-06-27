from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIGenerationError, AIProvider
from app.ai.factory import get_provider
from app.db import get_db
from app.schemas import GenerateRequest, GenerateResponse, GenerationUsage
from app.services.metering import GenerationService
from app.services.quota import QuotaExceeded, QuotaNotConfigured

router = APIRouter(prefix="/users", tags=["generation"])


@router.post("/{user_id}/generate", response_model=GenerateResponse)
def generate(
    user_id: str,
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_provider),
) -> GenerateResponse:
    service = GenerationService(db, provider)
    try:
        outcome = service.generate(user_id, payload.prompt, payload.max_tokens)
    except QuotaNotConfigured:
        raise HTTPException(status_code=404, detail=f"no quota configured for {user_id}")
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "quota_exceeded",
                "remaining_credits": exc.remaining,
                "required_credits": exc.required,
            },
        )
    except AIGenerationError as exc:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}")

    record = outcome.record
    return GenerateResponse(
        user_id=user_id,
        record_id=record.id,
        text=outcome.text,
        usage=GenerationUsage(
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            total_tokens=record.total_tokens,
            estimated_credits=record.estimated_credits,
            actual_credits=record.actual_credits,
        ),
        remaining_credits=outcome.remaining_credits,
    )
