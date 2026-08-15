from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models import Campaign, CEOAction, Creative, Creator, CreatorSubmission, Referral, SocialPost, StripePayment, TeracStudy, Visit
from ..schemas import CampaignCreate, HumanTestIngest, SocialPostCreate, SubmissionIngest, TeracLaunch
from ..services.events import add_event
from ..services.linq import notify_founder
from ..services.metrics import campaign_performance
from ..services.terac import TeracMCP, creative_test_brief, creator_brief
from .auth import require_founder

router = APIRouter(prefix="/api", tags=["campaigns"])


def campaign_brief(payload: CampaignCreate) -> str:
    return "\n".join([
        "Product: ReproClip", f"Target: {payload.audience}", f"Goal: {payload.objective}",
        "Content: 15–30 second short-form promotional video", "Recommended format: Show an ugly/raw screen recording first. Then show the polished ReproClip result.",
        f"Core message: {payload.hook}", "CTA: Try ReproClip. If it saves you time, support the open-source project for $5.",
        "Requirements: Original content; no copyrighted music/assets; no false claims; clear product demonstration; submit final video; submit a social URL only if explicitly permitted.",
    ])


def serialize_campaign(db: Session, campaign: Campaign, detail: bool = False) -> dict:
    performance = next((item for item in campaign_performance(db) if item["campaign_id"] == campaign.id), {})
    referral = db.scalar(select(Referral).where(Referral.campaign_id == campaign.id, Referral.creator_id.is_(None)).limit(1))
    result = {"id": campaign.id, "name": campaign.name, "objective": campaign.objective, "audience": campaign.audience, "creative_style": campaign.creative_style, "hook": campaign.hook, "platforms": campaign.platforms, "brief": campaign.brief, "budget_usd": campaign.budget_usd, "status": campaign.status, "current_decision": campaign.current_decision, "referral_code": referral.code if referral else None, "referral_url": f"{get_settings().app_base_url.rstrip('/')}/r/{referral.code}" if referral else None, "created_at": campaign.created_at, "updated_at": campaign.updated_at, "performance": performance}
    if detail:
        result["creators"] = [creator_stats(db, item) for item in campaign.creators]
        result["studies"] = [{"id": item.id, "kind": item.kind, "terac_request_id": item.terac_request_id, "terac_opportunity_id": item.terac_opportunity_id, "status": item.status, "requested_count": item.requested_count, "response_count": item.response_count, "cost_usd": item.cost_usd, "brief": item.brief, "created_at": item.created_at} for item in campaign.studies]
        result["creatives"] = [{"id": item.id, "name": item.name, "style": item.style, "asset_url": item.asset_url, "clarity_score": item.clarity_score, "click_intent": item.click_intent, "support_intent": item.support_intent, "preference_score": item.preference_score, "response_count": item.response_count} for item in campaign.creatives]
    return result


def creator_stats(db: Session, creator: Creator) -> dict:
    visits = db.scalar(select(func.count(Visit.id)).where(Visit.creator_id == creator.id)) or 0
    payments = db.scalar(select(func.count(StripePayment.id)).where(StripePayment.creator_id == creator.id, StripePayment.status == "paid")) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(StripePayment.creator_id == creator.id, StripePayment.status == "paid")) or 0
    return {"id": creator.id, "display_name": creator.display_name, "terac_creator_id": creator.terac_creator_id, "referral_code": creator.referral_code, "referral_url": f"{get_settings().app_base_url.rstrip('/')}/r/{creator.referral_code}", "status": creator.status, "reward_usd": creator.reward_usd, "visits": int(visits), "supporters": int(payments), "revenue": revenue / 100, "conversion_rate": round(payments / visits, 4) if visits else 0, "submissions": [serialize_submission(item) for item in creator.submissions]}


def serialize_submission(item: CreatorSubmission) -> dict:
    return {"id": item.id, "creator_id": item.creator_id, "terac_submission_id": item.terac_submission_id, "asset_url": item.asset_url, "social_url": item.social_url, "status": item.status, "automated_checks": item.automated_checks, "ai_recommendation": item.ai_recommendation, "quality_score": item.quality_score, "quality_reason": item.quality_reason, "founder_approved": item.founder_approved, "founder_reviewed_at": item.founder_reviewed_at, "submitted_at": item.submitted_at}


@router.post("/campaigns", dependencies=[Depends(require_founder)])
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    latest = db.scalar(select(CEOAction).order_by(CEOAction.created_at.desc()).limit(1))
    campaign = Campaign(**payload.model_dump(), brief=campaign_brief(payload), ceo_action_id=latest.id if latest else None, current_decision=latest.decision if latest else None)
    db.add(campaign); db.flush()
    code = __import__("secrets").token_urlsafe(6).replace("-", "").replace("_", "")[:8]
    db.add(Referral(code=code, campaign_id=campaign.id, destination_url=get_settings().product_base_url))
    add_event(db, "CEO" if latest else "Founder", f"Campaign created: {campaign.name}", "campaign", campaign.id, {"budget": campaign.budget_usd})
    db.commit(); db.refresh(campaign)
    return serialize_campaign(db, campaign, True)


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    return [serialize_campaign(db, item) for item in db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all()]


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    item = db.get(Campaign, campaign_id)
    if not item: raise HTTPException(404, "Campaign not found")
    return serialize_campaign(db, item, True)


@router.post("/campaigns/{campaign_id}/launch-terac", dependencies=[Depends(require_founder)])
async def launch_terac(campaign_id: str, payload: TeracLaunch, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign: raise HTTPException(404, "Campaign not found")
    creatives = [{"id": item.id, "name": item.name, "style": item.style, "asset_url": item.asset_url} for item in campaign.creatives]
    if payload.kind == "CREATIVE_TEST" and len(creatives) < 2:
        raise HTTPException(409, "At least two real approved creatives are required before launching a general-population test.")
    brief = creator_brief(serialize_campaign(db, campaign)) if payload.kind == "CREATOR" else creative_test_brief(serialize_campaign(db, campaign), creatives)
    role = "Short-form product demo creator" if payload.kind == "CREATOR" else "General population research participant"
    task = __import__("json").dumps(brief)
    study = TeracStudy(campaign_id=campaign.id, kind=payload.kind, requested_count=payload.count, brief=brief, status="REQUESTING_FEASIBILITY")
    db.add(study); db.flush(); add_event(db, "Terac", f"{payload.kind.replace('_', ' ').title()} feasibility requested", "terac_study", study.id); db.commit()
    try:
        result = await TeracMCP().request_feasibility(role, task, payload.count)
        request_id = result.get("request_id") or result.get("id")
        study.terac_request_id = request_id
        study.status = str(result.get("status") or "FEASIBILITY_REQUESTED").upper()
        cost = result.get("total_cost_usd") or result.get("cost_usd") or result.get("price_usd")
        study.cost_usd = float(cost) if cost is not None else None
        study.raw_result = result
        campaign.status = "TERAC_ACTIVE"
        add_event(db, "Terac", f"Real feasibility response received: {study.status}", "terac_study", study.id, {"request_id": request_id, "cost_usd": study.cost_usd})
        db.commit(); db.refresh(study)
    except Exception as error:
        study.status = "UNAVAILABLE"; study.raw_result = {"error": str(error)}
        add_event(db, "Terac", f"Integration unavailable: {error}", "terac_study", study.id); db.commit()
        raise HTTPException(503, str(error)) from error
    return {"id": study.id, "status": study.status, "terac_request_id": study.terac_request_id, "cost_usd": study.cost_usd, "raw_result": study.raw_result}


@router.post("/studies/{study_id}/launch", dependencies=[Depends(require_founder)])
async def launch_priced_study(study_id: str, db: Session = Depends(get_db)):
    study = db.get(TeracStudy, study_id)
    if not study: raise HTTPException(404, "Terac study not found")
    if not study.terac_request_id: raise HTTPException(409, "Terac has not returned a request ID yet.")
    try:
        result = await TeracMCP().launch_priced_request(study.terac_request_id)
        study.terac_opportunity_id = result.get("opportunity_id") or result.get("id")
        study.status = str(result.get("status") or "LAUNCHED").upper(); study.raw_result = result
        add_event(db, "Terac", f"{study.kind.replace('_', ' ').title()} launched to real humans", "terac_study", study.id, {"opportunity_id": study.terac_opportunity_id})
        db.commit(); return {"id": study.id, "status": study.status, "terac_opportunity_id": study.terac_opportunity_id, "raw_result": result}
    except Exception as error:
        raise HTTPException(503, str(error)) from error


@router.post("/studies/{study_id}/sync", dependencies=[Depends(require_founder)])
async def sync_study(study_id: str, db: Session = Depends(get_db)):
    study = db.get(TeracStudy, study_id)
    if not study: raise HTTPException(404, "Terac study not found")
    try:
        result = await TeracMCP().submissions(study.terac_opportunity_id)
        study.raw_result = result; study.status = str(result.get("status") or study.status).upper()
        add_event(db, "Terac", "Submission results synchronized from Terac", "terac_study", study.id)
        db.commit(); return {"id": study.id, "status": study.status, "raw_result": result}
    except Exception as error:
        raise HTTPException(503, str(error)) from error


@router.post("/submissions/ingest", dependencies=[Depends(require_founder)])
def ingest_submission(payload: SubmissionIngest, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, payload.campaign_id)
    if not campaign: raise HTTPException(404, "Campaign not found")
    existing = db.scalar(select(CreatorSubmission).where(CreatorSubmission.terac_submission_id == payload.terac_submission_id))
    if existing: return serialize_submission(existing)
    creator = db.scalar(select(Creator).where(Creator.campaign_id == campaign.id, Creator.terac_creator_id == payload.terac_creator_id))
    if not creator:
        creator = Creator(campaign_id=campaign.id, terac_creator_id=payload.terac_creator_id, display_name=payload.display_name, reward_usd=payload.reward_usd, status="SUBMITTED")
        db.add(creator); db.flush(); db.add(Referral(code=creator.referral_code, campaign_id=campaign.id, creator_id=creator.id, destination_url=get_settings().product_base_url))
    submission = CreatorSubmission(creator_id=creator.id, terac_submission_id=payload.terac_submission_id, asset_url=str(payload.asset_url), social_url=str(payload.social_url) if payload.social_url else None, automated_checks=payload.automated_checks, ai_recommendation=payload.ai_recommendation, quality_score=payload.quality_score, quality_reason=payload.quality_reason)
    db.add(submission); db.flush(); add_event(db, "Terac", f"Creator submission received from {creator.display_name}", "submission", submission.id)
    db.commit(); db.refresh(submission)
    return serialize_submission(submission)


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: str, db: Session = Depends(get_db)):
    item = db.get(CreatorSubmission, submission_id)
    if not item: raise HTTPException(404, "Submission not found")
    result = serialize_submission(item); result["creator"] = creator_stats(db, item.creator); result["campaign"] = {"id": item.creator.campaign.id, "name": item.creator.campaign.name}
    return result


async def review_submission(submission_id: str, approved: bool, db: Session) -> dict:
    item = db.get(CreatorSubmission, submission_id)
    if not item: raise HTTPException(404, "Submission not found")
    item.founder_approved = approved; item.founder_reviewed_at = datetime.now(timezone.utc); item.status = "FOUNDER_APPROVED" if approved else "FOUNDER_REJECTED"; item.creator.status = "APPROVED" if approved else "REVISION_REQUIRED"
    if approved:
        creative = db.scalar(select(Creative).where(Creative.submission_id == item.id))
        if not creative:
            db.add(Creative(campaign_id=item.creator.campaign_id, submission_id=item.id, name=f"{item.creator.display_name} creative", style=item.creator.campaign.creative_style, asset_url=item.asset_url))
    add_event(db, "Founder", f"{'Approved' if approved else 'Rejected'} creator submission — Financial Human Approval Required", "submission", item.id)
    db.commit()
    try: await notify_founder(f"ReproClip: submission {item.id} was {'approved' if approved else 'rejected'}. No automated payout approval was performed.")
    except Exception: pass
    return serialize_submission(item)


@router.post("/submissions/{submission_id}/approve", dependencies=[Depends(require_founder)])
async def approve_submission(submission_id: str, db: Session = Depends(get_db)):
    return await review_submission(submission_id, True, db)


@router.post("/submissions/{submission_id}/reject", dependencies=[Depends(require_founder)])
async def reject_submission(submission_id: str, db: Session = Depends(get_db)):
    return await review_submission(submission_id, False, db)


@router.post("/human-tests/ingest", dependencies=[Depends(require_founder)])
def ingest_human_test(payload: HumanTestIngest, db: Session = Depends(get_db)):
    study = db.get(TeracStudy, payload.terac_study_id)
    if not study or study.kind != "CREATIVE_TEST": raise HTTPException(404, "Creative test study not found")
    for result in payload.results:
        creative = db.get(Creative, result.creative_id)
        if not creative or creative.campaign_id != study.campaign_id: raise HTTPException(409, f"Creative {result.creative_id} is not part of this campaign")
        creative.clarity_score = result.clarity_score; creative.click_intent = result.click_intent; creative.support_intent = result.support_intent; creative.preference_score = result.preference_score; creative.response_count = result.response_count
    study.raw_result = payload.raw_result; study.status = "RESULTS_INGESTED"
    study.response_count = max(item.response_count for item in payload.results)
    winner = max(payload.results, key=lambda item: item.preference_score)
    add_event(db, "Research", f"Human creative test completed; {winner.creative_id} won with {winner.preference_score:.0%} preference", "terac_study", study.id, {"responses": sum(item.response_count for item in payload.results)})
    db.commit(); return {"ok": True, "winner_creative_id": winner.creative_id}


@router.post("/social-posts", dependencies=[Depends(require_founder)])
def create_social_post(payload: SocialPostCreate, db: Session = Depends(get_db)):
    if not db.get(Campaign, payload.campaign_id): raise HTTPException(404, "Campaign not found")
    if payload.creator_id and not db.get(Creator, payload.creator_id): raise HTTPException(404, "Creator not found")
    item = SocialPost(**payload.model_dump(exclude={"url"}), url=str(payload.url))
    db.add(item); db.flush()
    add_event(db, "Distribution", f"Published campaign creative on {payload.platform}", "social_post", item.id, {"url": str(payload.url)})
    db.commit()
    return {"id": item.id, "platform": item.platform, "url": item.url, "campaign_id": item.campaign_id, "creator_id": item.creator_id, "published_at": item.published_at, "views": item.views, "clicks": item.clicks, "conversions": item.conversions, "revenue_cents": item.revenue_cents}
