"""RAG tutoring pipeline — orchestration only.

No retrieval logic. No prompt logic. No parsing logic. No formatting logic.

Sole responsibility:
  1. Call retriever → get snippets
  2. Assemble context
  3. Call generator → get explanation
  4. Apply fallback chain
  5. Return TutoringFeedback

Fallback chain (explicit, linear):
  try:
      retrieval → assembly → generation
      if success: return with source="rag_llm"
      else: return with source="template_fallback"
  except:
      return fallback_pipeline.explain() with source="deterministic_fallback"
"""

from __future__ import annotations

import logging

from app.core.subject_engine import DiagnosisResult, Question
from app.core.tutoring import (
    TutoringPipeline,
    TutoringFeedback,
    TutoringExplanation,
    KnowledgeSnippet,
)
from app.rag.base_retriever import BaseRetriever
from app.rag.context_assembler import ContextAssembler
from app.rag.llm_explanation_generator import (
    LLMExplanationGenerator,
    SOURCE_RAG_LLM,
    SOURCE_TEMPLATE_FALLBACK,
    SOURCE_DETERMINISTIC_FALLBACK,
)

logger = logging.getLogger(__name__)


class RAGTutoringPipeline(TutoringPipeline):
    """Full RAG tutoring pipeline with graceful degradation.

    Fallback chain:
      1. rag_llm           — retrieval + LLM generation succeeded
      2. template_fallback  — retrieval worked, LLM failed → generic template + context
      3. deterministic_fallback — retrieval failed → existing EnglishTutoringPipeline
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        assembler: ContextAssembler,
        generator: LLMExplanationGenerator,
        fallback_pipeline: TutoringPipeline,
    ) -> None:
        self._retriever = retriever
        self._assembler = assembler
        self._generator = generator
        self._fallback = fallback_pipeline

    # -- TutoringPipeline interface ---------------------------------------------

    def explain(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        """Generate tutoring feedback with fallback chain."""
        try:
            return self._try_rag(diagnosis, question, student_answer)
        except Exception:
            logger.warning("RAG pipeline failed, using deterministic fallback")
            return self._deterministic_fallback(diagnosis, question, student_answer)

    # -- Fallback chain ---------------------------------------------------------

    def _try_rag(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        # Step 1: Retrieve
        snippets = self._retriever.query(
            labels=diagnosis.diagnosis_labels,
            tags=question.knowledge_tags,
            topic=question.topic,
        )

        if not snippets:
            return self._deterministic_fallback(diagnosis, question, student_answer)

        # Step 2: Assemble context
        context = self._assembler.assemble(
            snippets=snippets,
            question_text=question.question_text,
            student_answer=student_answer,
        )

        # Step 3: Generate LLM explanation
        correct_answer = question.answer.split("|||")[0].strip()
        llm_explanation = self._generator.generate(
            question_text=question.question_text,
            student_answer=student_answer,
            correct_answer=correct_answer,
            diagnosis_labels=diagnosis.diagnosis_labels,
            context=context,
        )

        if llm_explanation is not None:
            # Success path
            llm_explanation.retrieved_context = context
            llm_explanation.metadata["source"] = SOURCE_RAG_LLM
            return TutoringFeedback(
                diagnosis=diagnosis,
                explanation=llm_explanation,
                knowledge_snippets=list(snippets),  # defensive copy
            )
        else:
            # LLM failed — template fallback with retrieved context
            logger.warning("LLM generation failed, using template fallback")
            return self._template_fallback(
                diagnosis, student_answer, correct_answer, context, snippets
            )

    def _template_fallback(
        self,
        diagnosis: DiagnosisResult,
        student_answer: str,
        correct_answer: str,
        context: str,
        snippets: list[KnowledgeSnippet],
    ) -> TutoringFeedback:
        """Build a generic template explanation referencing retrieved context."""
        labels_str = ", ".join(diagnosis.diagnosis_labels) if diagnosis.diagnosis_labels else "未知错误"

        explanation = TutoringExplanation(
            what_is_wrong=f"你的答案 '{student_answer}' 不正确，正确答案是 '{correct_answer}'。",
            why_it_is_wrong=f"诊断结果: {labels_str}。请查看下方知识点了解相关语法规则。",
            how_to_fix=f"参考答案: {correct_answer}。请阅读知识点中的规则和例句来理解正确用法。",
            similar_examples=_extract_examples(snippets, max_examples=3),
            retrieved_context=context,
            metadata={"source": SOURCE_TEMPLATE_FALLBACK},
        )
        return TutoringFeedback(
            diagnosis=diagnosis,
            explanation=explanation,
            knowledge_snippets=list(snippets),
        )

    def _deterministic_fallback(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        """Delegate entirely to the existing template-based pipeline."""
        fb = self._fallback.explain(diagnosis, question, student_answer)
        if fb.explanation is not None:
            fb.explanation.metadata["source"] = SOURCE_DETERMINISTIC_FALLBACK
        return fb


def _extract_examples(snippets: list[KnowledgeSnippet], max_examples: int = 3) -> list[str]:
    """Extract example sentences from snippet content.

    Looks for lines starting with '- ✅' (checkmark examples in KB files).
    Deduplicates and caps at max_examples.
    """
    examples: list[str] = []
    seen: set[str] = set()
    for s in snippets:
        for line in s.content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- ✅"):
                example = stripped[3:].strip()
                if example and example not in seen:
                    examples.append(example)
                    seen.add(example)
                    if len(examples) >= max_examples:
                        return examples
    return examples
