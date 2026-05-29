from pymilvus import MilvusClient
from app.core.config import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION
import logging

logger = logging.getLogger(__name__)


class MilvusService:
    def __init__(self):
        self.client = MilvusClient(uri=f"http://{MILVUS_HOST}:{MILVUS_PORT}")

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        try:
            results = self.client.search(
                collection_name=MILVUS_COLLECTION,
                data=[query_vector],
                limit=top_k,
                output_fields=["id", "chapter", "speaker", "embedding_text", "metadata"],
            )
            hits = []
            for hit in results[0]:
                hits.append({
                    "id": hit["entity"]["id"],
                    "chapter": hit["entity"].get("chapter"),
                    "speaker": hit["entity"].get("speaker"),
                    "embedding_text": hit["entity"].get("embedding_text"),
                    "distance": hit["distance"],
                })
            return hits
        except Exception as e:
            logger.warning(f"Milvus search failed: {e}")
            return []