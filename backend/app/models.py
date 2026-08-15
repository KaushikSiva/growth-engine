from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def now() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("campaign"))
    name: Mapped[str] = mapped_column(String(180))
    objective: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(240))
    creative_style: Mapped[str] = mapped_column(String(80))
    hook: Mapped[str] = mapped_column(String(240))
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    brief: Mapped[str] = mapped_column(Text)
    budget_usd: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    current_decision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ceo_action_id: Mapped[str | None] = mapped_column(ForeignKey("ceo_actions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    creators: Mapped[list[Creator]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    studies: Mapped[list[TeracStudy]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    creatives: Mapped[list[Creative]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class Creator(Base):
    __tablename__ = "creators"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("creator"))
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    terac_creator_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    display_name: Mapped[str] = mapped_column(String(140), default="Terac creator")
    referral_code: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: uuid4().hex[:8])
    status: Mapped[str] = mapped_column(String(40), default="INVITED")
    reward_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    campaign: Mapped[Campaign] = relationship(back_populates="creators")
    submissions: Mapped[list[CreatorSubmission]] = relationship(back_populates="creator", cascade="all, delete-orphan")


class CreatorSubmission(Base):
    __tablename__ = "creator_submissions"
    id: Mapped[str] = mapped_column(String(44), primary_key=True, default=lambda: uid("submission"))
    creator_id: Mapped[str] = mapped_column(ForeignKey("creators.id"), index=True)
    terac_submission_id: Mapped[str | None] = mapped_column(String(140), unique=True, nullable=True)
    asset_url: Mapped[str] = mapped_column(Text)
    social_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING_REVIEW")
    automated_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    founder_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    founder_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    creator: Mapped[Creator] = relationship(back_populates="submissions")


class TeracStudy(Base):
    __tablename__ = "terac_studies"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("study"))
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    terac_request_id: Mapped[str | None] = mapped_column(String(140), nullable=True)
    terac_opportunity_id: Mapped[str | None] = mapped_column(String(140), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    requested_count: Mapped[int] = mapped_column(Integer, default=1)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    brief: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    campaign: Mapped[Campaign] = relationship(back_populates="studies")


class Creative(Base):
    __tablename__ = "creatives"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("creative"))
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    submission_id: Mapped[str | None] = mapped_column(ForeignKey("creator_submissions.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    style: Mapped[str] = mapped_column(String(80))
    asset_url: Mapped[str] = mapped_column(Text)
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    click_intent: Mapped[float | None] = mapped_column(Float, nullable=True)
    support_intent: Mapped[float | None] = mapped_column(Float, nullable=True)
    preference_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    campaign: Mapped[Campaign] = relationship(back_populates="creatives")


class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("ref"))
    code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    creator_id: Mapped[str | None] = mapped_column(ForeignKey("creators.id"), nullable=True, index=True)
    destination_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Visit(Base):
    __tablename__ = "visits"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("visit"))
    referral_code: Mapped[str | None] = mapped_column(String(24), nullable=True, index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    creator_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StripePayment(Base):
    __tablename__ = "stripe_payments"
    __table_args__ = (UniqueConstraint("stripe_session_id"), UniqueConstraint("stripe_payment_intent_id"),)
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("payment"))
    stripe_session_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    status: Mapped[str] = mapped_column(String(40))
    customer_email: Mapped[str | None] = mapped_column(String(240), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    creator_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    referral_code: Mapped[str | None] = mapped_column(String(24), nullable=True, index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CEOAction(Base):
    __tablename__ = "ceo_actions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("ceo"))
    summary: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(60))
    target_audience: Mapped[str] = mapped_column(String(240))
    creative_style: Mapped[str] = mapped_column(String(80))
    platform_priority: Mapped[list] = mapped_column(JSON, default=list)
    budget: Mapped[float] = mapped_column(Float, default=0)
    reasoning_summary: Mapped[str] = mapped_column(Text)
    next_actions: Mapped[list] = mapped_column(JSON, default=list)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(40), default="pioneer")
    model: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CompanyEvent(Base):
    __tablename__ = "company_events"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("event"))
    actor: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SocialPost(Base):
    __tablename__ = "social_posts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: uid("post"))
    platform: Mapped[str] = mapped_column(String(40))
    url: Mapped[str] = mapped_column(Text)
    creator_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    campaign_id: Mapped[str] = mapped_column(String(40), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)


class IntegrationStatus(Base):
    __tablename__ = "integration_statuses"
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    status: Mapped[str] = mapped_column(String(40), default="UNAVAILABLE")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
