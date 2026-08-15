from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


Decision = Literal["SCALE_CAMPAIGN", "STOP", "ITERATE", "CHANGE_AUDIENCE", "CHANGE_HOOK", "CHANGE_PLATFORM", "CHANGE_CREATIVE_STYLE", "RUN_NEW_TERAC_STUDY"]


class CEOResponse(BaseModel):
    summary: str = Field(min_length=5, max_length=500)
    decision: Decision
    target_audience: str = Field(min_length=3, max_length=240)
    creative_style: str = Field(min_length=3, max_length=80)
    platform_priority: list[Literal["x", "linkedin", "youtube", "reddit", "other"]] = Field(min_length=1, max_length=4)
    budget: float = Field(ge=0, le=1000)
    reasoning_summary: str = Field(min_length=5, max_length=600)
    next_actions: list[str] = Field(min_length=1, max_length=8)

    @field_validator("next_actions")
    @classmethod
    def concise_actions(cls, values: list[str]) -> list[str]:
        if any(len(item) > 240 for item in values):
            raise ValueError("next actions must be concise")
        return values


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    objective: str = Field(min_length=5, max_length=1000)
    audience: str = Field(min_length=3, max_length=240)
    creative_style: str = Field(default="before_after_demo", max_length=80)
    hook: str = Field(default="Stop manually editing product demos", max_length=240)
    platforms: list[str] = Field(default_factory=lambda: ["x", "linkedin"], max_length=4)
    budget_usd: float = Field(default=0, ge=0, le=1000)


class VisitCreate(BaseModel):
    referral_code: str | None = Field(default=None, max_length=24)
    campaign_id: str | None = Field(default=None, max_length=40)
    creator_id: str | None = Field(default=None, max_length=40)
    source: str | None = Field(default="product", max_length=80)


class SubmissionIngest(BaseModel):
    campaign_id: str
    terac_creator_id: str
    terac_submission_id: str
    asset_url: HttpUrl
    social_url: HttpUrl | None = None
    display_name: str = "Terac creator"
    reward_usd: float | None = Field(default=None, ge=0)
    automated_checks: dict = Field(default_factory=dict)
    ai_recommendation: Literal["APPROVE", "REJECT", "REVIEW"] | None = None
    quality_score: float | None = Field(default=None, ge=0, le=10)
    quality_reason: str | None = Field(default=None, max_length=1000)


class TeracLaunch(BaseModel):
    kind: Literal["CREATOR", "CREATIVE_TEST"]
    count: int = Field(default=3, ge=1, le=100)


class HumanTestResult(BaseModel):
    creative_id: str
    clarity_score: float = Field(ge=0, le=1)
    click_intent: float = Field(ge=0, le=1)
    support_intent: float = Field(ge=0, le=1)
    preference_score: float = Field(ge=0, le=1)
    response_count: int = Field(ge=1)


class HumanTestIngest(BaseModel):
    terac_study_id: str
    results: list[HumanTestResult] = Field(min_length=1)
    raw_result: dict = Field(default_factory=dict)


class SocialPostCreate(BaseModel):
    platform: Literal["x", "linkedin", "youtube", "reddit", "other"]
    url: HttpUrl
    campaign_id: str
    creator_id: str | None = None
    views: int | None = Field(default=None, ge=0)
    clicks: int | None = Field(default=None, ge=0)
    conversions: int | None = Field(default=None, ge=0)
    revenue_cents: int | None = Field(default=None, ge=0)


class ReplayQAReport(BaseModel):
    run_url: HttpUrl
    checks: dict[str, Literal["PASS", "FAIL", "UNAVAILABLE"]]
    critical_issues: int = Field(ge=0)
    detail: str | None = Field(default=None, max_length=1000)
