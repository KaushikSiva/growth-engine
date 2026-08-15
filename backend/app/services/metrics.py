from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import Campaign, CEOAction, Creator, Creative, SocialPost, StripePayment, TeracStudy, Visit


def money(value: float | int) -> float:
    return round(float(value), 2)


def company_metrics(db: Session) -> dict:
    revenue_cents = db.scalar(select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(StripePayment.status == "paid")) or 0
    supporters = db.scalar(select(func.count(StripePayment.id)).where(StripePayment.status == "paid")) or 0
    visits = db.scalar(select(func.count(Visit.id))) or 0
    campaigns = db.scalar(select(func.count(Campaign.id))) or 0
    creators = db.scalar(select(func.count(Creator.id))) or 0
    humans_surveyed = db.scalar(select(func.coalesce(func.sum(TeracStudy.response_count), 0)).where(TeracStudy.kind == "CREATIVE_TEST")) or 0
    social_posts = db.scalar(select(func.count(SocialPost.id))) or 0
    terac_spend = db.scalar(select(func.coalesce(func.sum(TeracStudy.cost_usd), 0)).where(TeracStudy.cost_usd.is_not(None))) or 0
    settings = get_settings()
    infrastructure = settings.infrastructure_cost_usd
    gross = money(revenue_cents / 100 - float(terac_spend) - (infrastructure or 0)) if infrastructure is not None else None
    return {
        "revenue": money(revenue_cents / 100),
        "supporters": int(supporters),
        "campaigns": int(campaigns),
        "human_creators": int(creators),
        "humans_surveyed": int(humans_surveyed),
        "social_posts": int(social_posts),
        "landing_visits": int(visits),
        "conversion_rate": round(supporters / visits, 4) if visits else 0,
        "human_employees": 0,
        "terac_spend": money(terac_spend),
        "infrastructure_cost": money(infrastructure) if infrastructure is not None else None,
        "gross_contribution": gross,
        "roas": round((revenue_cents / 100) / float(terac_spend), 2) if terac_spend else None,
        "cac": round(float(terac_spend) / supporters, 2) if supporters and terac_spend else None,
    }


def campaign_performance(db: Session) -> list[dict]:
    rows = []
    for campaign in db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all():
        visits = db.scalar(select(func.count(Visit.id)).where(Visit.campaign_id == campaign.id)) or 0
        payments = db.scalar(select(func.count(StripePayment.id)).where(StripePayment.campaign_id == campaign.id, StripePayment.status == "paid")) or 0
        revenue_cents = db.scalar(select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(StripePayment.campaign_id == campaign.id, StripePayment.status == "paid")) or 0
        cost = db.scalar(select(func.coalesce(func.sum(TeracStudy.cost_usd), 0)).where(TeracStudy.campaign_id == campaign.id)) or 0
        preferred = db.scalar(select(func.max(Creative.preference_score)).where(Creative.campaign_id == campaign.id))
        rows.append({
            "campaign_id": campaign.id, "campaign": campaign.name, "status": campaign.status,
            "creative_style": campaign.creative_style, "audience": campaign.audience,
            "human_preference_score": preferred,
            "visits": int(visits), "stripe_conversions": int(payments), "revenue": money(revenue_cents / 100),
            "conversion_rate": round(payments / visits, 4) if visits else 0,
            "terac_cost": money(cost), "gross_contribution": money(revenue_cents / 100 - float(cost)),
        })
    return rows


def business_state(db: Session) -> dict:
    metrics = company_metrics(db)
    history = [{"decision": item.decision, "summary": item.summary, "reasoning_summary": item.reasoning_summary, "created_at": item.created_at.isoformat()} for item in db.scalars(select(CEOAction).order_by(CEOAction.created_at.desc()).limit(20)).all()]
    creator_performance = []
    for creator in db.scalars(select(Creator)).all():
        visits = db.scalar(select(func.count(Visit.id)).where(Visit.creator_id == creator.id)) or 0
        conversions = db.scalar(select(func.count(StripePayment.id)).where(StripePayment.creator_id == creator.id, StripePayment.status == "paid")) or 0
        revenue = db.scalar(select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(StripePayment.creator_id == creator.id, StripePayment.status == "paid")) or 0
        creator_performance.append({"creator_id": creator.id, "campaign_id": creator.campaign_id, "status": creator.status, "visits": int(visits), "stripe_conversions": int(conversions), "revenue": money(revenue / 100), "conversion_rate": round(conversions / visits, 4) if visits else 0})
    human_feedback = [{"creative_id": item.id, "campaign_id": item.campaign_id, "style": item.style, "clarity": item.clarity_score, "click_intent": item.click_intent, "support_intent": item.support_intent, "preference": item.preference_score, "responses": item.response_count} for item in db.scalars(select(Creative)).all()]
    social_performance = [{"platform": item.platform, "campaign_id": item.campaign_id, "creator_id": item.creator_id, "views": item.views, "clicks": item.clicks, "conversions": item.conversions, "revenue_cents": item.revenue_cents} for item in db.scalars(select(SocialPost)).all()]
    return {
        "objective": "Generate real revenue while growing ReproClip using an on-demand human marketing workforce.",
        "metrics": metrics,
        "campaign_performance": campaign_performance(db),
        "creator_performance": creator_performance,
        "terac_human_feedback": human_feedback,
        "content_performance": social_performance,
        "current_terac_budget": get_settings().terac_budget_usd,
        "historical_ceo_decisions": history,
        "data_policy": "Missing values are null or zero. Never infer revenue, study outcomes, or social performance.",
    }
