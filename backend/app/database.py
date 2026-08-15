from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool
from .config import get_settings


class Base(DeclarativeBase):
    pass


def configured_database_url(*, for_migrations: bool = False) -> str:
    settings = get_settings()
    if for_migrations and settings.supabase_migration_url:
        return settings.supabase_migration_url
    return settings.supabase_database_url or settings.database_url


def _is_supabase_url(url: URL) -> bool:
    host = (url.host or "").lower()
    return host.endswith(".supabase.co") or host.endswith(".pooler.supabase.com")


def normalized_database_url(value: str | None = None, *, for_migrations: bool = False) -> str:
    value = value or configured_database_url(for_migrations=for_migrations)
    if value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
        value = value.replace("postgresql://", "postgresql+psycopg://", 1)

    url = make_url(value)
    if _is_supabase_url(url) and "sslmode" not in url.query:
        url = url.update_query_dict({"sslmode": "require"})
    return url.render_as_string(hide_password=False)


def uses_supabase() -> bool:
    return bool(get_settings().supabase_database_url)


def uses_sqlite() -> bool:
    return make_url(normalized_database_url()).get_backend_name() == "sqlite"


def _engine_options() -> dict:
    settings = get_settings()
    url = make_url(normalized_database_url())
    options: dict = {"pool_pre_ping": True}
    if url.get_backend_name() != "postgresql":
        return options

    options["connect_args"] = {"connect_timeout": 8}
    if _is_supabase_url(url):
        options["connect_args"]["sslmode"] = "require"

    # Supavisor transaction mode (6543) cannot retain prepared statements or
    # application-side pooled sessions. Render should normally use Supavisor
    # session mode (5432), but this keeps transaction mode safe if selected.
    if url.port == 6543:
        options["poolclass"] = NullPool
        options["connect_args"]["prepare_threshold"] = None
    else:
        options["pool_size"] = settings.database_pool_size
        options["max_overflow"] = settings.database_max_overflow
        options["pool_recycle"] = 1800
    return options


engine = create_engine(normalized_database_url(), **_engine_options())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
