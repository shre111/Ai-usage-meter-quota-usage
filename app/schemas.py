from pydantic import BaseModel, Field, model_validator


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
