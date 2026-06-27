from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserConfigRequest(BaseModel):
    monthly_allowance: int | None = Field(default=None, ge=0)
    multiplier: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserConfigRequest":
        if self.monthly_allowance is None and self.multiplier is None:
            raise ValueError("provide monthly_allowance and/or multiplier")
        return self


class UserConfigResponse(BaseModel):
    user_id: str
    monthly_allowance: int
    multiplier: float


class UsageSummary(BaseModel):
    user_id: str
    monthly_allowance: int
    multiplier: float
    used_credits: int
    reserved_credits: int
    remaining_credits: int


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_tokens: int | None = Field(default=None, gt=0)


class GenerationUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_credits: int
    actual_credits: int


class GenerateResponse(BaseModel):
    user_id: str
    record_id: int
    text: str
    usage: GenerationUsage
    remaining_credits: int


class UsageRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    status: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_credits: int
    actual_credits: int
    multiplier_at_time: float
