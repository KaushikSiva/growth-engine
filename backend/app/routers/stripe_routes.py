from datetime import datetime, timezone
import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import SessionLocal, get_db
from ..models import Campaign, CEOAction, Referral, StripePayment
from ..schemas import CampaignCreate, CheckoutCreate
from ..services.events import add_event
from ..services.metrics import business_state
from ..services.pioneer import run_ceo
from .campaigns import campaign_brief

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


@router.post("/create-checkout")
def create_checkout(body: CheckoutCreate, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(503, "STRIPE_SECRET_KEY is not configured. No Checkout session was created.")
    stripe.api_key = settings.stripe_secret_key
    metadata = {key: value for key, value in {"campaign_id": body.campaign_id, "creator_id": body.creator_id, "referral_code": body.referral_code, "source": body.source or "direct"}.items() if value}
    line_item = {"price": settings.stripe_price_id, "quantity": 1} if settings.stripe_price_id else {"price_data": {"currency": "usd", "unit_amount": 500, "product_data": {"name": "Support ReproClip", "description": "Voluntary support for the open-source ReproClip project"}}, "quantity": 1}
    try:
        session = stripe.checkout.Session.create(
            mode="payment", line_items=[line_item], metadata=metadata,
            payment_intent_data={"metadata": metadata},
            success_url=f"{settings.app_base_url.rstrip('/')}/thanks?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_base_url.rstrip('/')}/support?cancelled=1",
            client_reference_id=body.referral_code,
            allow_promotion_codes=False,
        )
    except stripe.StripeError as error:
        raise HTTPException(502, f"Stripe Checkout failed: {error.user_message or str(error)}") from error
    add_event(db, "Stripe", "Checkout opened for voluntary $5 support", "checkout", session.id, metadata)
    db.commit()
    return {"checkout_url": session.url, "session_id": session.id}


def store_payment(db: Session, *, session_id: str | None, payment_intent_id: str | None, amount: int, currency: str, status: str, email: str | None, metadata: dict) -> bool:
    existing = db.scalar(select(StripePayment).where(or_(StripePayment.stripe_session_id == session_id if session_id else False, StripePayment.stripe_payment_intent_id == payment_intent_id if payment_intent_id else False)))
    if existing:
        existing.status = status
        if session_id: existing.stripe_session_id = session_id
        if payment_intent_id: existing.stripe_payment_intent_id = payment_intent_id
        return False
    payment = StripePayment(stripe_session_id=session_id, stripe_payment_intent_id=payment_intent_id, amount_cents=amount, currency=currency, status=status, customer_email=email, campaign_id=metadata.get("campaign_id"), creator_id=metadata.get("creator_id"), referral_code=metadata.get("referral_code"), paid_at=datetime.now(timezone.utc))
    db.add(payment); db.flush()
    add_event(db, "Stripe", f"${amount / 100:.2f} support payment received", "payment", payment.id, {"campaign_id": payment.campaign_id, "creator_id": payment.creator_id, "referral_code": payment.referral_code})
    return True


async def ceo_review_after_payment() -> None:
    with SessionLocal() as db:
        try:
            state = business_state(db)
            decision = await run_ceo(state)
            settings = get_settings()
            action = CEOAction(**decision.model_dump(), input_snapshot=state, provider="pioneer", model=settings.pioneer_model)
            db.add(action); db.flush()
            add_event(db, "CEO", f"Revenue review: {decision.decision.replace('_', ' ').title()}", "ceo_action", action.id, {"reasoning_summary": decision.reasoning_summary})
            if decision.decision != "STOP":
                payload = CampaignCreate(name=f"{decision.creative_style.replace('_', ' ').title()} — {action.id[-6:]}", objective="Turn qualified ReproClip interest into product trials and voluntary $5 open-source support.", audience=decision.target_audience, creative_style=decision.creative_style, hook=next((item.split(":", 1)[1].strip().strip("'\"") for item in decision.next_actions if "hook" in item.lower() and ":" in item), "Stop manually editing screen recordings"), platforms=decision.platform_priority, budget_usd=decision.budget)
                campaign = Campaign(**payload.model_dump(), brief=campaign_brief(payload), ceo_action_id=action.id, current_decision=decision.decision, status="DRAFT")
                db.add(campaign); db.flush()
                code = __import__("secrets").token_urlsafe(6).replace("-", "").replace("_", "")[:8]
                db.add(Referral(code=code, campaign_id=campaign.id, destination_url=settings.product_base_url))
                add_event(db, "CEO", f"Drafted next campaign after revenue: {campaign.name}", "campaign", campaign.id, {"budget": campaign.budget_usd})
            db.commit()
        except Exception as error:
            add_event(db, "CEO", f"Revenue changed; Pioneer review unavailable: {error}", "integration", "pioneer")
            db.commit()


@router.post("/webhook")
async def webhook(request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "STRIPE_WEBHOOK_SECRET is not configured.")
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as error:
        raise HTTPException(400, "Invalid Stripe webhook signature") from error
    created = False
    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        if obj.get("payment_status") == "paid":
            created = store_payment(db, session_id=obj.get("id"), payment_intent_id=obj.get("payment_intent"), amount=int(obj.get("amount_total") or 0), currency=obj.get("currency") or "usd", status="paid", email=(obj.get("customer_details") or {}).get("email"), metadata=dict(obj.get("metadata") or {}))
    elif event["type"] == "payment_intent.succeeded":
        obj = event["data"]["object"]
        created = store_payment(db, session_id=None, payment_intent_id=obj.get("id"), amount=int(obj.get("amount_received") or 0), currency=obj.get("currency") or "usd", status="paid", email=obj.get("receipt_email"), metadata=dict(obj.get("metadata") or {}))
    db.commit()
    if created: background.add_task(ceo_review_after_payment)
    return {"received": True, "stored": created}


@router.get("/session/{session_id}")
def session_status(session_id: str, db: Session = Depends(get_db)):
    payment = db.scalar(select(StripePayment).where(StripePayment.stripe_session_id == session_id))
    return {"paid": bool(payment and payment.status == "paid"), "amount": payment.amount_cents / 100 if payment else None}
