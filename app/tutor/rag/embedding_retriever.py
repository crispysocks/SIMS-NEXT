"""Semantic retriever using sentence-transformers + ChromaDB.

Self-contained — no dependency on existing KnowledgeRetriever or TF-IDF code.

Key properties:
- Constructor never throws — load failures set is_ready() = False
- Incremental indexing via per-file SHA256 hash in ChromaDB metadata
- Synchronous retrieval only (async not needed at this scale)
- Each retrieved snippet preserves source file path and match metadata
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from app.tutor.rag.base_retriever import BaseRetriever
from app.tutor.core.tutoring import KnowledgeSnippet

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2
_COLLECTION_NAME = "english_knowledge_base"


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
    """Replace underscores with spaces for natural-language embedding."""
    return text.replace("_", " ")


def _file_hash(path: Path) -> str:
    """SHA256 hex digest of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EmbeddingRetriever(BaseRetriever):
    """Semantic retriever backed by sentence-transformers + ChromaDB.

    Usage:
        retriever = EmbeddingRetriever(
            kb_path="app/tutor/subjects/english/knowledge_base",
            persist_dir="chroma_data",
            model_name="all-MiniLM-L6-v2",
        )
        if retriever.is_ready():
            snippets = retriever.query(labels, tags, topic)
    """

    def __init__(
        self,
        kb_path: str,
        persist_dir: str = "chroma_data",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self._kb_path = kb_path
        self._persist_dir = persist_dir
        self._ready = False
        self._model = None
        self._collection = None
        self._doc_meta: dict[str, dict] = {}  # doc_id -> parsed frontmatter

        # Load embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers  "
                "EmbeddingRetriever disabled, falling back to TF-IDF."
            )
            return
        except Exception as e:
            logger.warning(
                "Failed to load embedding model '%s': %s. "
                "EmbeddingRetriever.is_ready() = False.",
                model_name, e,
            )
            return

        # Connect to ChromaDB
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except ImportError:
            logger.warning(
                "chromadb not installed. "
                "Run: pip install chromadb  "
                "EmbeddingRetriever disabled, falling back to TF-IDF."
            )
            return
        except Exception as e:
            logger.warning(
                "Failed to connect to ChromaDB at '%s': %s. "
                "EmbeddingRetriever.is_ready() = False.",
                persist_dir, e,
            )
            return

        # Index knowledge base (auto-builds vector DB on first run)
        try:
            self._index_kb(kb_path)
        except Exception as e:
            logger.warning(
                "Failed to index knowledge base at '%s': %s. "
                "EmbeddingRetriever.is_ready() = False.",
                kb_path, e,
            )
            return

        self._ready = True

    # -- BaseRetriever interface ------------------------------------------------

    def query(
        self,
        labels: list[str],
        tags: list[str],
        topic: str,
        top_k: int = 3,
    ) -> list[KnowledgeSnippet]:
        if not self._ready:
            return []

        query_text = self._build_query_text(labels, tags, topic)
        query_embedding = self._model.encode(
            [query_text], convert_to_numpy=True
        ).tolist()[0]

        # Fetch extra candidates for metadata re-ranking
        fetch_k = max(top_k * 3, 9)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(fetch_k, self._collection.count()),
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        snippets: list[KnowledgeSnippet] = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            document = results["documents"][0][i] if results["documents"] else ""
            distance = results["distances"][0][i] if results["distances"] else 0.0

            # Cosine distance → similarity
            semantic_score = 1.0 - distance

            # Compute composite score with metadata boosts
            composite = self._compute_score(
                semantic_score=semantic_score,
                doc_labels=_split_meta(meta.get("diagnosis_labels", "")),
                doc_topic=meta.get("topic", ""),
                query_labels=labels,
                query_topic=topic,
            )

            snippets.append(KnowledgeSnippet(
                id=doc_id,
                title=meta.get("title", doc_id),
                topic=meta.get("topic", ""),
                tags=_split_meta(meta.get("tags", "")),
                diagnosis_labels=_split_meta(meta.get("diagnosis_labels", "")),
                content=document,
                score=composite,
                metadata={
                    "_raw_semantic_score": round(semantic_score, 4),
                    "_source_file": doc_id,
                },
            ))

        snippets.sort(key=lambda s: s.score, reverse=True)
        return snippets[:top_k]

    def is_ready(self) -> bool:
        return self._ready

    # -- Internal ---------------------------------------------------------------

    @staticmethod
    def _build_query_text(labels: list[str], tags: list[str], topic: str) -> str:
        """Build a natural-language query from structured labels/tags/topic."""
        parts: list[str] = []
        parts.extend(labels)
        parts.extend(tags)
        parts.append(topic)
        return _normalize_underscores(" ".join(parts))

    @staticmethod
    def _compute_score(
        semantic_score: float,
        doc_labels: list[str],
        doc_topic: str,
        query_labels: list[str],
        query_topic: str,
    ) -> float:
        """Composite score: 0.8 * semantic + 0.1 * label_match + 0.1 * topic_match."""
        score = 0.8 * semantic_score

        # Label match boost
        if query_labels:
            overlap = len(set(query_labels) & set(doc_labels))
            if overlap > 0:
                # Score proportional to overlap count, capped at 0.1
                label_boost = min(0.1, 0.05 * overlap)
                score += label_boost

        # Topic match boost
        if doc_topic and query_topic and doc_topic == query_topic:
            score += 0.1

        return score

    def _index_kb(self, kb_path: str) -> None:
        """Incremental index: only embed new or changed markdown files."""
        kb_dir = Path(kb_path)
        if not kb_dir.is_dir():
            logger.warning("Knowledge base directory not found: %s", kb_path)
            return

        # Scan current files
        current_files: dict[str, dict] = {}  # doc_id -> {path, hash}
        for md_file in sorted(kb_dir.rglob("*.md")):
            doc_id = str(md_file.relative_to(kb_dir).with_suffix("")).replace("\\", "/")
            current_files[doc_id] = {
                "path": md_file,
                "hash": _file_hash(md_file),
            }

        # Get stored documents from ChromaDB
        try:
            stored = self._collection.get()
        except Exception:
            stored = {"ids": [], "metadatas": []}

        stored_ids = set(stored["ids"]) if stored["ids"] else set()
        stored_metas = {}
        if stored["ids"] and stored["metadatas"]:
            for i, doc_id in enumerate(stored["ids"]):
                stored_metas[doc_id] = stored["metadatas"][i] or {}

        current_ids = set(current_files.keys())

        # Determine what changed
        to_add: dict[str, dict] = {}      # doc_id -> {path, hash}
        to_delete: list[str] = []

        for doc_id, info in current_files.items():
            if doc_id not in stored_ids:
                to_add[doc_id] = info
            elif stored_metas.get(doc_id, {}).get("file_hash") != info["hash"]:
                to_add[doc_id] = info

        for doc_id in stored_ids - current_ids:
            to_delete.append(doc_id)

        # Delete removed files
        if to_delete:
            self._collection.delete(ids=to_delete)
            logger.info("Removed %d deleted docs from vector DB", len(to_delete))

        # Embed and add new/changed files
        if to_add:
            if not stored_ids:
                logger.info(
                    "First run: building vector DB from %d knowledge base files...",
                    len(to_add),
                )
            else:
                logger.info("Incremental update: embedding %d changed files", len(to_add))
            ids: list[str] = []
            embeddings: list[list[float]] = []
            metadatas: list[dict] = []
            documents: list[str] = []

            for doc_id, info in to_add.items():
                text = info["path"].read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(text)
                doc_text = f"{meta.get('title', '')}\n{body}"

                ids.append(doc_id)
                embedding = self._model.encode(
                    [_normalize_underscores(doc_text)],
                    convert_to_numpy=True,
                ).tolist()[0]
                embeddings.append(embedding)
                metadatas.append({
                    "title": meta.get("title", doc_id),
                    "topic": meta.get("topic", ""),
                    "tags": ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else meta.get("tags", ""),
                    "diagnosis_labels": ", ".join(meta.get("diagnosis_labels", [])) if isinstance(meta.get("diagnosis_labels"), list) else meta.get("diagnosis_labels", ""),
                    "remediation": ", ".join(meta.get("remediation", [])) if isinstance(meta.get("remediation"), list) else meta.get("remediation", ""),
                    "file_hash": info["hash"],
                })
                documents.append(doc_text)

            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )


def _split_meta(value: str) -> list[str]:
    """Split a comma-joined metadata string back into a list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
