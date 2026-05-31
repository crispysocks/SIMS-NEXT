from openai import OpenAI
from app.core.config import EMBED_BASE_URL, EMBED_API_KEY, EMBED_MODEL

_client = OpenAI(api_key=EMBED_API_KEY, base_url=EMBED_BASE_URL)


def embed(text: str) -> list[float]:
    response = _client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding
