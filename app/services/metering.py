from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai.base import AIGenerationError, AIProvider
from app.config import Settings, get_settings
from app.models import UsageRecord
from app.repositories import add_usage_record
from app.services.credits import billable_credits, estimate_credits
from app.services.quota import QuotaService


@dataclass
class GenerationOutcome:
    text: str
    record: UsageRecord
    remaining_credits: int


class GenerationService:
    def __init__(
        self,
        db: Session,
        provider: AIProvider,
        settings: Settings | None = None,
    ):
        self.db = db
        self.provider = provider
        self.settings = settings or get_settings()
        self.quota = QuotaService(db)

    def generate(
        self, user_id: str, prompt: str, max_tokens: int | None = None
    ) -> GenerationOutcome:
        quota = self.quota.get_state(user_id)
        multiplier = quota.multiplier
        estimated = estimate_credits(prompt, multiplier, max_tokens, self.settings)

        try:
            self.quota.reserve(user_id, estimated)
        except Exception:
            self._record(user_id, "rejected", None, estimated, 0, multiplier)
            raise

        try:
            result = self.provider.generate(prompt, max_tokens)
        except AIGenerationError as exc:
            self._handle_failure(user_id, estimated, multiplier, exc)
            raise

        actual = billable_credits(
            result.prompt_tokens, result.completion_tokens, multiplier, self.settings
        )
        self.quota.commit_usage(user_id, reserved=estimated, actual=actual)
        record = self._record(
            user_id, "success", result, estimated, actual, multiplier
        )
        return GenerationOutcome(
            text=result.text,
            record=record,
            remaining_credits=self.quota.remaining(self.quota.get_state(user_id)),
        )

    def _handle_failure(
        self, user_id: str, estimated: int, multiplier: float, exc: AIGenerationError
    ) -> None:
        partial = exc.partial_usage
        if partial is not None:
            actual = billable_credits(
                partial.prompt_tokens,
                partial.completion_tokens,
                multiplier,
                self.settings,
            )
            self.quota.commit_usage(user_id, reserved=estimated, actual=actual)
            self._record(user_id, "failed", partial, estimated, actual, multiplier)
        else:
            self.quota.release(user_id, estimated)
            self._record(user_id, "failed", None, estimated, 0, multiplier)

    def _record(
        self, user_id, status, usage, estimated, actual, multiplier
    ) -> UsageRecord:
        record = UsageRecord(
            user_id=user_id,
            status=status,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            estimated_credits=estimated,
            actual_credits=actual,
            multiplier_at_time=multiplier,
        )
        return add_usage_record(self.db, record)
