import time
from openai import OpenAI
from app.core.config import EMBED_BASE_URL, EMBED_API_KEY, EMBED_MODEL
from app.core.llm_logger import log_llm

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=EMBED_API_KEY, base_url=EMBED_BASE_URL)
    return _client


def embed(text: str) -> list[float]:
    t0 = time.time()
    response = _get_client().embeddings.create(model=EMBED_MODEL, input=text)
    embedding = response.data[0].embedding
    log_llm({
        "type": "embedding",
        "model": EMBED_MODEL,
        "text_length": len(text),
        "dimensions": len(embedding),
        "latency_ms": int((time.time() - t0) * 1000),
    })
    return embedding
