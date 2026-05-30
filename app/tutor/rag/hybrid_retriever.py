"""Hybrid retriever — merges results from primary (embedding) and secondary (TF-IDF).

Thin orchestrator. No caching, retry, telemetry, or logging framework.
Sole job: call retrievers, merge by snippet.id, compute composite score,
return sorted snippets.
"""

from __future__ import annotations

from app.tutor.rag.base_retriever import BaseRetriever
from app.tutor.core.tutoring import KnowledgeSnippet


class HybridRetriever(BaseRetriever):
    """Combine embedding (primary) and TF-IDF (secondary) retrievers.

    Composite scoring:
        final = 0.6 * semantic_score
              + 0.1 * tfidf_score
              + 0.2 * label_match_boost
              + 0.1 * topic_match_boost

    Falls back gracefully when either retriever is unavailable.
    """

    def __init__(
        self,
        primary: BaseRetriever,
        secondary: BaseRetriever,
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    # -- BaseRetriever interface ------------------------------------------------

    def query(
        self,
        labels: list[str],
        tags: list[str],
        topic: str,
        top_k: int = 3,
    ) -> list[KnowledgeSnippet]:
        fetch_k = max(top_k * 2, 6)
        seen: dict[str, KnowledgeSnippet] = {}

        # Primary: embedding retriever
        if self._primary.is_ready():
            for s in self._primary.query(labels, tags, topic, fetch_k):
                seen[s.id] = s

        # Secondary: TF-IDF retriever
        if self._secondary.is_ready():
            for s in self._secondary.query(labels, tags, topic, fetch_k):
                if s.id not in seen:
                    seen[s.id] = s

        # Compute composite scores using raw scores from metadata
        for s in seen.values():
            raw_semantic = s.metadata.get("_raw_semantic_score", 0.0)
            raw_tfidf = s.metadata.get("_raw_tfidf_score", 0.0)
            s.score = self._composite_score(
                semantic_score=raw_semantic,
                tfidf_score=raw_tfidf,
                doc_labels=s.diagnosis_labels,
                doc_topic=s.topic,
                query_labels=labels,
                query_topic=topic,
            )

        sorted_snippets = sorted(seen.values(), key=lambda s: s.score, reverse=True)
        return sorted_snippets[:top_k]

    def is_ready(self) -> bool:
        return self._primary.is_ready() or self._secondary.is_ready()

    # -- Internal ---------------------------------------------------------------

    @staticmethod
    def _composite_score(
        semantic_score: float,
        tfidf_score: float,
        doc_labels: list[str],
        doc_topic: str,
        query_labels: list[str],
        query_topic: str,
    ) -> float:
        """Compute weighted composite score.

        Weights:
            semantic:  0.6
            tfidf:     0.1
            label_match: 0.2 (if any query label overlaps doc labels)
            topic_match: 0.1 (if doc topic == query topic)
        """
        score = 0.6 * semantic_score + 0.1 * tfidf_score

        # Label match boost
        if query_labels:
            overlap = len(set(query_labels) & set(doc_labels))
            if overlap > 0:
                label_boost = min(0.2, 0.1 * overlap)
                score += label_boost

        # Topic match boost
        if doc_topic and query_topic and doc_topic == query_topic:
            score += 0.1

        return score
