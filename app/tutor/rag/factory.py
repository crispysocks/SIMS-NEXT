"""RAG pipeline factory — centralized config loading and construction.

All environment/config reading happens here. No os.getenv scattered
across modules. Factory never crashes — on any failure, returns
the deterministic EnglishTutoringPipeline fallback.

Usage:
    from app.tutor.rag.factory import create_pipeline, RAGConfig

    config = RAGConfig.from_env()
    pipeline = create_pipeline("english", config)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from app.tutor.core.tutoring import TutoringPipeline

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Lightweight RAG configuration — value object, no framework.

    All fields have sensible defaults. Call from_env() to populate
    from environment variables.
    """

    enabled: bool = False
    retriever_mode: str = "hybrid"       # "hybrid" | "embedding" | "tfidf"
    llm_enabled: bool = True
    kb_path: str = "app/tutor/subjects/english/knowledge_base"
    persist_dir: str = "chroma_data"
    model_name: str = "all-MiniLM-L6-v2"
    context_soft_limit: int = 8000
    context_hard_limit: int = 12000
    api_key: str = ""
    base_url: str = ""
    model: str = ""

    @classmethod
    def from_env(cls) -> RAGConfig:
        return cls(
            enabled=_env_bool("RAG_ENABLED", default=False),
            retriever_mode=os.environ.get("RAG_RETRIEVER_MODE", "hybrid"),
            llm_enabled=_env_bool("RAG_LLM_ENABLED", default=True),
            kb_path=os.environ.get("RAG_KB_PATH", "app/tutor/subjects/english/knowledge_base"),
            persist_dir=os.environ.get("RAG_CHROMA_PERSIST_DIR", "chroma_data"),
            model_name=os.environ.get("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            context_soft_limit=_env_int("RAG_CONTEXT_SOFT_LIMIT", default=8000),
            context_hard_limit=_env_int("RAG_CONTEXT_HARD_LIMIT", default=12000),
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", ""),
            model=os.environ.get("LLM_MODEL", ""),
        )


# -- Public factory functions -------------------------------------------------


def create_pipeline(subject: str, config: RAGConfig | None = None) -> TutoringPipeline | None:
    """Create a tutoring pipeline for the given subject.

    Routing:
        RAG_ENABLED=false  -> deterministic template pipeline (no deps needed)
        RAG_ENABLED=true   -> full RAG pipeline (auto-builds vector DB on first run)
                              falls back to TF-IDF if embedding deps missing,
                              falls back to templates if everything fails.

    Args:
        subject: "english" or "math"
        config: RAG config. If None, reads from env via RAGConfig.from_env().

    Returns:
        TutoringPipeline for English (RAG or deterministic), None for math.
        Never raises — returns deterministic fallback on any failure.
    """
    if subject != "english":
        return None  # Math has no tutoring pipeline

    if config is None:
        config = RAGConfig.from_env()

    if not config.enabled:
        logger.info("RAG disabled (RAG_ENABLED=false), using deterministic template pipeline")
        return _build_deterministic(config.kb_path)

    logger.info("RAG enabled, building pipeline (retriever_mode=%s)", config.retriever_mode)
    try:
        pipeline = _build_rag(config)
        logger.info("RAG pipeline ready")
        return pipeline
    except Exception as e:
        logger.warning(
            "RAG pipeline initialization failed (%s), using deterministic fallback",
            e,
        )
        return _build_deterministic(config.kb_path)


# -- Internal builders --------------------------------------------------------


def _build_deterministic(kb_path: str) -> TutoringPipeline:
    """Build the existing template-based EnglishTutoringPipeline."""
    from app.tutor.subjects.english.retrieval import KnowledgeRetriever
    from app.tutor.subjects.english.tutor import EnglishTutoringPipeline

    retriever = KnowledgeRetriever(kb_path)
    return EnglishTutoringPipeline(retriever)


def _build_rag(config: RAGConfig) -> TutoringPipeline:
    from app.tutor.rag.tfidf_retriever import TFIDFRetriever
    from app.tutor.rag.embedding_retriever import EmbeddingRetriever
    from app.tutor.rag.hybrid_retriever import HybridRetriever
    from app.tutor.rag.context_assembler import ContextAssembler
    from app.tutor.rag.llm_explanation_generator import LLMExplanationGenerator
    from app.tutor.rag.rag_tutoring_pipeline import RAGTutoringPipeline

    # Always build TF-IDF retriever (needed for hybrid mode + fallback)
    tfidf_retriever = TFIDFRetriever(config.kb_path)

    # Build primary retriever based on mode
    mode = config.retriever_mode
    if mode == "tfidf":
        retriever = tfidf_retriever
    elif mode == "embedding":
        embedding = EmbeddingRetriever(
            kb_path=config.kb_path,
            persist_dir=config.persist_dir,
            model_name=config.model_name,
        )
        if embedding.is_ready():
            logger.info("Embedding retriever ready")
            retriever = embedding
        else:
            logger.warning("Embedding retriever unavailable, falling back to TF-IDF")
            retriever = tfidf_retriever
    else:  # "hybrid" (default)
        embedding = EmbeddingRetriever(
            kb_path=config.kb_path,
            persist_dir=config.persist_dir,
            model_name=config.model_name,
        )
        if embedding.is_ready():
            logger.info("Hybrid retriever ready (embedding + TF-IDF)")
        else:
            logger.warning("Embedding retriever unavailable, hybrid using TF-IDF only")
        retriever = HybridRetriever(primary=embedding, secondary=tfidf_retriever)

    # Context assembler
    assembler = ContextAssembler(
        soft_limit=config.context_soft_limit,
        hard_limit=config.context_hard_limit,
    )

    # LLM generator (may fail if no API key — handled at generate() time)
    generator = LLMExplanationGenerator(
        api_key=config.api_key or None,
        base_url=config.base_url or None,
        model=config.model or None,
    ) if config.llm_enabled else _DisabledGenerator()

    # Deterministic fallback pipeline
    fallback = _build_deterministic(config.kb_path)

    return RAGTutoringPipeline(
        retriever=retriever,
        assembler=assembler,
        generator=generator,
        fallback_pipeline=fallback,
    )


# -- Helpers ------------------------------------------------------------------


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def _env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


class _DisabledGenerator:
    """No-op generator that always returns None (LLM disabled)."""

    def generate(self, *args, **kwargs) -> None:
        return None
