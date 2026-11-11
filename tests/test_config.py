import pytest
from pydantic import ValidationError

from pharma_assist.config import Settings

ENV_VARS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_BASE_UR", "OPENAI_MODEL", "OPENAI_EMBEDDING_MODEL")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_typo_base_url_and_docker_quotes(monkeypatch):
    # Mirrors the provided .env as `docker run --env-file` passes it: typo'd key, quotes kept.
    monkeypatch.setenv("OPENAI_API_KEY", "'sk-test'")
    monkeypatch.setenv("OPENAI_BASE_UR", "'https://proxy.example.com'")
    monkeypatch.setenv("OPENAI_MODEL", '"gpt-x"')

    s = Settings(_env_file=None)

    assert s.openai_base_url == "https://proxy.example.com"
    assert s.openai_model == "gpt-x"
    assert s.openai_api_key.get_secret_value() == "sk-test"


def test_correct_spelling_wins_and_empty_url_is_none(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://right.example.com")
    monkeypatch.setenv("OPENAI_BASE_UR", "https://typo.example.com")
    assert Settings(_env_file=None).openai_base_url == "https://right.example.com"

    monkeypatch.delenv("OPENAI_BASE_URL")
    monkeypatch.setenv("OPENAI_BASE_UR", "''")
    assert Settings(_env_file=None).openai_base_url is None


@pytest.mark.parametrize("key", [None, "", "''"])
def test_missing_api_key_fails(monkeypatch, key):
    if key is not None:
        monkeypatch.setenv("OPENAI_API_KEY", key)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
