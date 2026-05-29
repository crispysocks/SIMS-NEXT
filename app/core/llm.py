from openai import OpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

EMBED_MODEL_PATH = r"D:\model\BAbge-large-zh-v1.5\bge-large-zh-v1.5"


def chat(messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def embed(text: str) -> list[float]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL_PATH)
    embedding = model.encode(text)
    # 手动 L2 归一化
    norm = sum(e * e for e in embedding) ** 0.5
    embedding = embedding / norm
    return embedding.tolist()
