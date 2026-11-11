"""Runtime settings from the environment / `.env` (graders inject their own `.env`)."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    openai_api_key: SecretStr
    # The provided .env ships the typo `OPENAI_BASE_UR`; accept both spellings.
    openai_base_url: str | None = Field(
        None, validation_alias=AliasChoices("OPENAI_BASE_URL", "OPENAI_BASE_UR")
    )
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    corpus_dir: Path = PROJECT_ROOT / "corpus"
    cache_dir: Path = PROJECT_ROOT / ".cache"
    max_revisions: int = 2

    @field_validator("*", mode="before")
    @classmethod
    def _unquote(cls, v: object) -> object:
        # `docker run --env-file` keeps quotes literally (`OPENAI_MODEL='gpt-x'`); python-dotenv strips them.
        if isinstance(v, str):
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            return v or None
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
