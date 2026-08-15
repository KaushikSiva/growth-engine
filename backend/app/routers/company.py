from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import get_settings
from ..models import Campaign, CEOAction, CompanyEvent, IntegrationStatus, Referral
from ..schemas import CampaignCreate, ReplayQAReport
from .campaigns import campaign_brief
from ..services.events import add_event
from ..services.metrics import business_state, campaign_performance, company_metrics
from ..services.pioneer import run_ceo
from .auth import require_founder

router = APIRouter(prefix="/api/company", tags=["company"])


def action_dict(action: CEOAction | None) -> dict | None:
    if not action: return None
    return {"id": action.id, "summary": action.summary, "decision": action.decision, "target_audience": action.target_audience, "creative_style": action.creative_style, "platform_priority": action.platform_priority, "budget": action.budget, "reasoning_summary": action.reasoning_summary, "next_actions": action.next_actions, "provider": action.provider, "model": action.model, "created_at": action.created_at}


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    current = db.scalar(select(CEOAction).order_by(CEOAction.created_at.desc()).limit(1))
    integrations = {item.name: {"status": item.status, "detail": item.detail, "checked_at": item.checked_at} for item in db.scalars(select(IntegrationStatus)).all()}
    return {"metrics": company_metrics(db), "current_decision": action_dict(current), "campaign_performance": campaign_performance(db), "integrations": integrations}


@router.get("/events")
def events(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.scalars(select(CompanyEvent).order_by(CompanyEvent.created_at.desc()).limit(min(limit, 250))).all()
    return [{"id": item.id, "actor": item.actor, "action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "metadata": item.metadata_json, "created_at": item.created_at} for item in rows]


@router.post("/ceo/run", dependencies=[Depends(require_founder)])
async def run(db: Session = Depends(get_db)):
    state = business_state(db)
    try:
        decision = await run_ceo(state)
    except Exception as error:
        add_event(db, "CEO", f"Pioneer unavailable: {error}", "integration", "pioneer")
        db.commit()
        raise HTTPException(503, str(error)) from error
    action = CEOAction(**decision.model_dump(), input_snapshot=state, provider="pioneer", model=get_settings().pioneer_model)
    db.add(action); db.flush()
    add_event(db, "CEO", f"{decision.decision.replace('_', ' ').title()}: {decision.summary}", "ceo_action", action.id, {"reasoning_summary": decision.reasoning_summary})
    campaign = None
    if decision.decision != "STOP":
        payload = CampaignCreate(
            name=f"{decision.creative_style.replace('_', ' ').title()} — {action.id[-6:]}",
            objective="Turn qualified ReproClip interest into product trials and voluntary $5 open-source support.",
            audience=decision.target_audience,
            creative_style=decision.creative_style,
            hook=next((item.split(":", 1)[1].strip().strip("'\"") for item in decision.next_actions if "hook" in item.lower() and ":" in item), "Stop manually editing screen recordings"),
            platforms=decision.platform_priority,
            budget_usd=decision.budget,
        )
        campaign = Campaign(**payload.model_dump(), brief=campaign_brief(payload), ceo_action_id=action.id, current_decision=decision.decision, status="DRAFT")
        db.add(campaign); db.flush()
        code = __import__("secrets").token_urlsafe(6).replace("-", "").replace("_", "")[:8]
        db.add(Referral(code=code, campaign_id=campaign.id, destination_url=get_settings().product_base_url))
        add_event(db, "CEO", f"Drafted next campaign: {campaign.name}", "campaign", campaign.id, {"budget": campaign.budget_usd, "audience": campaign.audience})
    db.commit(); db.refresh(action)
    return {**action_dict(action), "campaign_id": campaign.id if campaign else None}


@router.post("/qa/replay", dependencies=[Depends(require_founder)])
def ingest_replay(report: ReplayQAReport, db: Session = Depends(get_db)):
    status = "PASS" if report.critical_issues == 0 and all(value != "FAIL" for value in report.checks.values()) else "FAIL"
    item = db.get(IntegrationStatus, "replay") or IntegrationStatus(name="replay")
    item.status = status
    item.detail = f"{report.critical_issues} critical issues · {report.run_url}"
    item.checked_at = datetime.now(timezone.utc)
    db.add(item)
    add_event(db, "Replay", f"UI QA {status}: {report.critical_issues} critical issues", "integration", "replay", {"checks": report.checks, "run_url": str(report.run_url)})
    db.commit()
    return {"status": status, "checks": report.checks, "critical_issues": report.critical_issues}
