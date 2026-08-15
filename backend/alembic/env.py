from logging.config import fileConfig
from alembic import context
from app.config import get_settings
from app.database import Base, normalized_database_url
from app import models  # noqa: F401

config = context.config
# ConfigParser treats percent-encoded database passwords as interpolation.
# Escaping here preserves the URL Alembic ultimately passes to SQLAlchemy.
config.set_main_option("sqlalchemy.url", normalized_database_url(for_migrations=True).replace("%", "%%"))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction(): context.run_migrations()


def run_migrations_online():
    from app.database import engine
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
