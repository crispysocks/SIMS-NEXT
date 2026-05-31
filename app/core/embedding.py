from openai import OpenAI
from app.core.config import EMBED_BASE_URL, EMBED_API_KEY, EMBED_MODEL

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=EMBED_API_KEY, base_url=EMBED_BASE_URL)
    return _client


def embed(text: str) -> list[float]:
    response = _get_client().embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding
