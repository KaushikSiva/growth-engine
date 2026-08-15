from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .config import get_settings
from .database import Base, engine, uses_sqlite, uses_supabase
from .routers import campaigns, company, referrals, stripe_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Alembic exclusively owns the Supabase schema. create_all is deliberately
    # limited to the disposable SQLite developer fallback.
    if uses_sqlite():
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="ReproClip Autonomous Company", version="0.1.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(company.router)
app.include_router(campaigns.router)
app.include_router(stripe_routes.router)
app.include_router(referrals.router)


@app.get("/health")
def health():
    supabase_status = "unavailable"
    if uses_supabase():
        try:
            with engine.connect() as connection:
                connection.execute(text("select 1"))
            supabase_status = "configured"
        except SQLAlchemyError:
            supabase_status = "error"
    return {
        "status": "ok" if supabase_status != "error" else "degraded",
        "integrations": {
            "supabase": supabase_status,
            "stripe": "configured" if settings.stripe_secret_key and settings.stripe_webhook_secret else "unavailable",
            "pioneer": "configured" if settings.pioneer_api_key else "unavailable",
            "terac": "configured" if settings.terac_api_key else "unavailable",
            "linq": "configured" if settings.linq_api_key else "unavailable",
            "replay": "configured" if settings.replay_project_url else "unavailable",
        },
    }
