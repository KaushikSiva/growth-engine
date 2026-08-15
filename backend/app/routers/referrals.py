import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models import Referral, Visit
from ..schemas import VisitCreate
from ..services.events import add_event

router = APIRouter(tags=["referrals"])


@router.get("/r/{code}")
def visit(code: str, request: Request, db: Session = Depends(get_db)):
    referral = db.query(Referral).filter(Referral.code == code).first()
    if not referral: raise HTTPException(404, "Referral not found")
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    salt = get_settings().founder_approval_token or "reproclip"
    ip_hash = hashlib.sha256(f"{salt}:{forwarded}".encode()).hexdigest() if forwarded else None
    row = Visit(referral_code=code, campaign_id=referral.campaign_id, creator_id=referral.creator_id, source="referral", user_agent=request.headers.get("user-agent"), ip_hash=ip_hash)
    db.add(row); add_event(db, "Referral", f"Visitor arrived from {code}", "referral", referral.id, {"campaign_id": referral.campaign_id, "creator_id": referral.creator_id}); db.commit()
    target = referral.destination_url
    separator = "&" if "?" in target else "?"
    return RedirectResponse(f"{target}{separator}ref={code}&campaign={referral.campaign_id}{f'&creator={referral.creator_id}' if referral.creator_id else ''}", status_code=302)


@router.get("/api/referrals/{code}")
def referral(code: str, db: Session = Depends(get_db)):
    item = db.query(Referral).filter(Referral.code == code).first()
    if not item: raise HTTPException(404, "Referral not found")
    return {"code": item.code, "campaign_id": item.campaign_id, "creator_id": item.creator_id, "destination_url": item.destination_url}


@router.post("/api/visits")
def record_visit(body: VisitCreate, request: Request, db: Session = Depends(get_db)):
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    salt = get_settings().founder_approval_token or "reproclip"
    ip_hash = hashlib.sha256(f"{salt}:{forwarded}".encode()).hexdigest() if forwarded else None
    row = Visit(referral_code=body.referral_code, campaign_id=body.campaign_id, creator_id=body.creator_id, source=body.source, user_agent=request.headers.get("user-agent"), ip_hash=ip_hash)
    db.add(row); db.flush(); add_event(db, "Landing", "Product landing page visited", "visit", row.id, {"campaign_id": body.campaign_id, "creator_id": body.creator_id}); db.commit()
    return {"ok": True}
