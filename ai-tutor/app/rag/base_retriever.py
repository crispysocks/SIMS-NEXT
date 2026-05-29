"""Base retriever interface for knowledge base document retrieval."""

from abc import ABC, abstractmethod

from app.core.tutoring import KnowledgeSnippet


class BaseRetriever(ABC):
    """Abstract retriever for knowledge base documents.

    All retrievers (TF-IDF, embedding, hybrid) implement this
    interface so the pipeline can swap them polymorphically.
    """

    @abstractmethod
    def query(
        self,
        labels: list[str],
        tags: list[str],
        topic: str,
        top_k: int = 3,
    ) -> list[KnowledgeSnippet]:
        """Retrieve top-k relevant knowledge snippets.

        Args:
            labels: diagnosis labels from DiagnosisResult
            tags: knowledge tags from the Question
            topic: topic string from the Question
            top_k: max number of snippets to return

        Returns:
            Ranked list of KnowledgeSnippet with populated scores.
        """
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Check whether the retriever is initialized and healthy.

        Returns False when the retriever failed to load (e.g., missing
        model, inaccessible storage). Callers use this to decide
        fallback behavior.
        """
        ...
