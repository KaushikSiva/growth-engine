import asyncio
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.database import Base, normalized_database_url
from app.models import Campaign, Creator, CreatorSubmission, StripePayment
from app.routers.campaigns import review_submission
from app.routers.stripe_routes import store_payment
from app.schemas import CEOResponse
from app.services.metrics import company_metrics


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


def test_zero_state_never_fabricates_revenue(db: Session):
    metrics = company_metrics(db)
    assert metrics["revenue"] == 0
    assert metrics["supporters"] == 0
    assert metrics["human_employees"] == 0
    assert metrics["roas"] is None


def test_supabase_urls_use_psycopg_and_ssl():
    value = "postgres://postgres.project:secret@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
    normalized = normalized_database_url(value)
    assert normalized.startswith("postgresql+psycopg://")
    assert "sslmode=require" in normalized


def test_stripe_payment_is_idempotent(db: Session):
    data = dict(session_id="cs_real", payment_intent_id="pi_real", amount=500, currency="usd", status="paid", email="supporter@example.com", metadata={"campaign_id": "campaign_a", "creator_id": "creator_a", "referral_code": "abc123"})
    assert store_payment(db, **data) is True
    assert store_payment(db, **data) is False
    db.commit()
    assert len(db.scalars(select(StripePayment)).all()) == 1
    assert company_metrics(db)["revenue"] == 5


def test_ceo_schema_blocks_unbounded_or_unknown_decisions():
    with pytest.raises(Exception):
        CEOResponse(summary="A valid summary", decision="SPEND_EVERYTHING", target_audience="founders", creative_style="demo", platform_priority=["x"], budget=10, reasoning_summary="Not allowed by schema", next_actions=["do it"])
    with pytest.raises(Exception):
        CEOResponse(summary="A valid summary", decision="ITERATE", target_audience="founders", creative_style="demo", platform_priority=["x"], budget=5000, reasoning_summary="Budget too high", next_actions=["do it"])


def test_creator_submission_requires_explicit_founder_review(db: Session):
    campaign = Campaign(name="Real campaign", objective="Test real creator work", audience="founders", creative_style="before_after_demo", hook="Stop editing", platforms=["x"], brief="brief")
    db.add(campaign); db.flush()
    creator = Creator(campaign_id=campaign.id, display_name="Creator", terac_creator_id="terac_real")
    db.add(creator); db.flush()
    submission = CreatorSubmission(creator_id=creator.id, asset_url="https://example.com/video.mp4", terac_submission_id="sub_real")
    db.add(submission); db.commit()
    assert submission.founder_approved is None
    result = asyncio.run(review_submission(submission.id, True, db))
    assert result["founder_approved"] is True
    assert result["status"] == "FOUNDER_APPROVED"
