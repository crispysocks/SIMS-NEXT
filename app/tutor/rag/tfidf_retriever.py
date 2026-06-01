"""TF-IDF retriever adapter — wraps existing KnowledgeRetriever."""

from app.tutor.rag.base_retriever import BaseRetriever
from app.tutor.core.tutoring import KnowledgeSnippet


class TFIDFRetriever(BaseRetriever):
    """Adapter wrapping the existing KnowledgeRetriever to conform to BaseRetriever.

    Zero logic change to the underlying retriever — enriches returned
    snippets with raw score and source file metadata for transparency.
    """

    def __init__(self, kb_path: str) -> None:
        from app.tutor.subjects.english.retrieval import KnowledgeRetriever

        self._kb_path = kb_path
        self._retriever = KnowledgeRetriever(kb_path)

    def query(
        self,
        labels: list[str],
        tags: list[str],
        topic: str,
        top_k: int = 3,
    ) -> list[KnowledgeSnippet]:
        snippets = self._retriever.query(labels, tags, topic, top_k)
        for s in snippets:
            s.metadata.setdefault("_raw_tfidf_score", s.score)
            s.metadata.setdefault("_source_file", s.id)
        return snippets

    def is_ready(self) -> bool:
        return self._retriever._matrix is not None and self._retriever._matrix.shape[0] > 0
