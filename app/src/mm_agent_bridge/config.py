from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "mm-agent-bridge"
    database_url: str = "sqlite+pysqlite:///./mm_agent_bridge.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MM_BRIDGE_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
