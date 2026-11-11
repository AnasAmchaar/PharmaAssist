"""Chat and embedding clients for the OpenAI-compatible endpoint (e.g. LiteLLM proxy)."""

from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from pharma_assist.config import get_settings


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    s = get_settings()
    # temperature=0: grounded, reproducible answers (the proxy model accepts it; probed in Step 1).
    return ChatOpenAI(
        model=s.openai_model,
        api_key=s.openai_api_key,
        base_url=s.openai_base_url,
        temperature=0,
        timeout=120,
        max_retries=2,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    s = get_settings()
    # check_embedding_ctx_length=False: send raw strings; proxies often reject pre-tokenized input.
    # chunk_size=64: one 528-input request (~70k tokens) put the LiteLLM deployment into a 429 cooldown.
    return OpenAIEmbeddings(
        model=s.openai_embedding_model,
        api_key=s.openai_api_key,
        base_url=s.openai_base_url,
        check_embedding_ctx_length=False,
        chunk_size=64,
        timeout=60,
        max_retries=3,
    )
