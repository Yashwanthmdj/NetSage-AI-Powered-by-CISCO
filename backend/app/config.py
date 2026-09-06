from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NetSage AI"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'netsage.db'}"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    cases_csv_path: Path = REPO_ROOT / "data" / "cases.csv"
    auto_seed: bool = True
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 45
    llm_max_tokens: int = 4096
    llm_json_object: bool = True
    llm_enable_thinking: bool = False
    prompts_dir: Path = REPO_ROOT / "prompts"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key.strip())

    def repo_root(self) -> Path:
        return REPO_ROOT


@lru_cache
def get_settings() -> Settings:
    return Settings()
