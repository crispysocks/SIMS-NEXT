"""
Minimal TF-IDF knowledge retriever for English grammar knowledge base.

Indexes markdown files with YAML-like frontmatter. Query by diagnosis
labels, knowledge tags, and topic with weighted ranking.

No external dependencies beyond scikit-learn (TfidfVectorizer).
"""

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.tutor.core.tutoring import KnowledgeSnippet


# -- Frontmatter parser -------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from markdown text.

    Returns (metadata_dict, body_text). Supports simple key: value
    pairs and list items ('  - value'). No PyYAML dependency.
    """
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    frontmatter = parts[1].strip()
    body = parts[2].strip()

    metadata: dict = {}
    current_key: str | None = None

    for line in frontmatter.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        if not line.startswith("  ") and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                metadata[key] = value
            else:
                metadata[key] = []
            current_key = key
        elif line.startswith("  - ") and current_key is not None:
            item = line.strip()[2:]
            if isinstance(metadata.get(current_key), list):
                metadata[current_key].append(item)

    return metadata, body


def _normalize_underscores(text: str) -> str:
    """Replace underscores with spaces so TF-IDF tokenizes tags correctly.

    Tags like 'verb_tense' become 'verb tense', matching body text
    which uses natural language with spaces.
    """
    return text.replace("_", " ")


# -- KnowledgeRetriever -------------------------------------------------------


class KnowledgeRetriever:
    """TF-IDF retriever over a directory of markdown knowledge files.

    Usage:
        retriever = KnowledgeRetriever("app/tutor/subjects/english/knowledge_base")
        snippets = retriever.query(
            labels=["missing_third_person_s"],
            tags=["subject_verb_agreement", "third_person_singular"],
            topic="subject_verb_agreement",
        )
    """

    def __init__(self, kb_path: str) -> None:
        self._snippets: list[KnowledgeSnippet] = []
        # No stop_words — grammar tags contain common English words
        # that would be incorrectly filtered (e.g. "past", "tense").
        self._vectorizer = TfidfVectorizer(
            preprocessor=_normalize_underscores,
            token_pattern=r"(?u)\b\w\w+\b",
        )
        self._matrix = None
        self._load_all(kb_path)
        self._build_index()

    def _load_all(self, kb_path: str) -> None:
        """Walk kb_path, parse all .md files into KnowledgeSnippets."""
        for md_file in Path(kb_path).rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            metadata, body = _parse_frontmatter(text)
            snippet = KnowledgeSnippet(
                id=md_file.stem,
                title=metadata.get("title", md_file.stem),
                topic=metadata.get("topic", ""),
                tags=metadata.get("tags", []),
                diagnosis_labels=metadata.get("diagnosis_labels", []),
                content=body,
            )
            self._snippets.append(snippet)

    def _build_index(self) -> None:
        """Build TF-IDF matrix over (title + body) of all snippets."""
        if not self._snippets:
            self._matrix = None
            return
        docs = [f"{s.title}\n{s.content}" for s in self._snippets]
        self._matrix = self._vectorizer.fit_transform(docs)

    def query(
        self,
        labels: list[str],
        tags: list[str],
        topic: str,
        top_k: int = 3,
    ) -> list[KnowledgeSnippet]:
        """Retrieve top-k snippets with weighted query ranking.

        Weights: diagnosis_labels x3 > knowledge_tags x2 > topic x1
        """
        if self._matrix is None or self._matrix.shape[0] == 0:
            return self._fallback_by_label(labels)

        # Build weighted query string
        query_parts: list[str] = []
        for label in labels:
            query_parts.extend([label] * 3)
        for tag in tags:
            query_parts.extend([tag] * 2)
        query_parts.append(topic)

        query_str = " ".join(query_parts)
        query_vec = self._vectorizer.transform([query_str])
        scores = cosine_similarity(query_vec, self._matrix).flatten()

        top_indices = scores.argsort()[-top_k:][::-1]

        results: list[KnowledgeSnippet] = []
        for idx in top_indices:
            if scores[idx] > 0:
                s = self._snippets[idx]
                results.append(KnowledgeSnippet(
                    id=s.id,
                    title=s.title,
                    topic=s.topic,
                    tags=list(s.tags),
                    diagnosis_labels=list(s.diagnosis_labels),
                    content=s.content,
                    score=float(scores[idx]),
                ))

        if not results:
            return self._fallback_by_label(labels)

        # Label-match boost: if no result matches a diagnosis label,
        # prepend a label-matched fallback snippet so retrieval hits work.
        if labels:
            has_label_match = any(
                any(l in s.diagnosis_labels for l in labels)
                for s in results
            )
            if not has_label_match:
                label_snippet = self._fallback_by_label(labels)
                if label_snippet:
                    results = label_snippet + results[: top_k - 1]

        return results

    def get_by_label(self, label: str) -> KnowledgeSnippet | None:
        """Exact match fallback by diagnosis_label or tag."""
        for s in self._snippets:
            if label in s.diagnosis_labels or label in s.tags:
                return s
        return None

    def _fallback_by_label(self, labels: list[str]) -> list[KnowledgeSnippet]:
        """When TF-IDF returns nothing, match by diagnosis_label exactly."""
        for label in labels:
            snippet = self.get_by_label(label)
            if snippet is not None:
                return [KnowledgeSnippet(
                    id=snippet.id,
                    title=snippet.title,
                    topic=snippet.topic,
                    tags=list(snippet.tags),
                    diagnosis_labels=list(snippet.diagnosis_labels),
                    content=snippet.content,
                    score=1.0,
                )]
        return []
