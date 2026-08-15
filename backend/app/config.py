from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase is the production system of record. SQLite remains available only
    # for keyless local development and the isolated test suite.
    supabase_database_url: str = ""
    supabase_migration_url: str = ""
    database_url: str = "sqlite:///./reproclip_company.db"
    database_pool_size: int = 5
    database_max_overflow: int = 5
    app_base_url: str = "http://localhost:3001"
    product_base_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3001,http://localhost:3000"
    founder_approval_token: str = ""

    pioneer_api_key: str = ""
    pioneer_model: str = "Qwen/Qwen3-8B"
    pioneer_base_url: str = "https://api.pioneer.ai/v1"

    terac_api_key: str = ""
    terac_mcp_url: str = "https://terac.com/api/mcp"
    terac_project_id: str = ""
    terac_budget_usd: float = 0

    linq_api_key: str = ""
    linq_from_number: str = ""
    linq_to_number: str = ""

    replay_project_url: str = ""
    infrastructure_cost_usd: float | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
