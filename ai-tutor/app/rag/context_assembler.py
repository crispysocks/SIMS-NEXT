"""Context assembler — deduplicate, truncate, and format retrieved snippets.

Deterministic: same inputs always produce byte-identical output.
Uses character budget (not tokenizer) for simplicity.
"""

from __future__ import annotations

from app.core.tutoring import KnowledgeSnippet

# Character budget
SOFT_LIMIT = 8000   # truncate last snippet to fit
HARD_LIMIT = 12000  # never exceed this


class ContextAssembler:
    """Merge, deduplicate, and truncate snippets into LLM-ready context.

    Usage:
        assembler = ContextAssembler()
        context = assembler.assemble(snippets, question_text, student_answer)
    """

    def __init__(
        self,
        soft_limit: int = SOFT_LIMIT,
        hard_limit: int = HARD_LIMIT,
    ) -> None:
        self._soft_limit = soft_limit
        self._hard_limit = hard_limit

    def assemble(
        self,
        snippets: list[KnowledgeSnippet],
        question_text: str,
        student_answer: str,
    ) -> str:
        """Produce a structured context string.

        Returns a markdown-formatted string with sections:
            ## 知识点
            ## 题目上下文

        Deduplication and truncation are applied before formatting.
        """
        unique = self._deduplicate(snippets)
        unique.sort(key=lambda s: s.score, reverse=True)
        trimmed = self._truncate_to_budget(unique)
        return self._format(trimmed, question_text, student_answer)

    # -- Internal ---------------------------------------------------------------

    @staticmethod
    def _deduplicate(snippets: list[KnowledgeSnippet]) -> list[KnowledgeSnippet]:
        """Remove near-duplicates by (title, content_prefix) hash."""
        seen: set[tuple[str, str]] = set()
        result: list[KnowledgeSnippet] = []
        for s in snippets:
            key = (s.title.strip().lower(), s.content[:100].strip())
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result

    def _truncate_to_budget(
        self,
        snippets: list[KnowledgeSnippet],
    ) -> list[KnowledgeSnippet]:
        """Trim snippet content to fit within character budget.

        Strategy:
        1. Keep all snippets where all content fits within SOFT_LIMIT — no change
        2. If over SOFT_LIMIT: truncate last snippet's content to fit
        3. If over HARD_LIMIT: drop lowest-score snippet and try again
        """
        total_chars = sum(len(s.content) for s in snippets)
        if total_chars <= self._soft_limit:
            return snippets

        # Try truncating the last (lowest-score) snippet
        remaining = self._soft_limit - sum(len(s.content) for s in snippets[:-1])
        if remaining > 100:  # at least some meaningful content
            import copy
            result = [copy.copy(s) for s in snippets[:-1]]
            last = copy.copy(snippets[-1])
            last.content = last.content[:remaining]
            result.append(last)
            total = sum(len(s.content) for s in result)
            if total <= self._hard_limit:
                return result

        # Hard limit: drop lowest-score snippet and re-check
        if len(snippets) > 1:
            return self._truncate_to_budget(snippets[:-1])

        # Only one snippet and still over hard limit — hard truncate
        import copy
        only = copy.copy(snippets[0])
        only.content = only.content[:self._hard_limit]
        return [only]

    @staticmethod
    def _format(
        snippets: list[KnowledgeSnippet],
        question_text: str,
        student_answer: str,
    ) -> str:
        """Format snippets and question context as markdown."""
        parts: list[str] = []
        parts.append("## 知识点\n")

        for i, s in enumerate(snippets, 1):
            source = s.metadata.get("_source_file", s.id)
            parts.append(f"### {i}. {s.title} (相关性: {s.score:.3f})")
            parts.append(f"来源: {source}")
            parts.append(f"主题: {s.topic}")
            if s.tags:
                parts.append(f"标签: {', '.join(s.tags)}")
            if s.diagnosis_labels:
                parts.append(f"诊断标签: {', '.join(s.diagnosis_labels)}")
            parts.append("")
            parts.append(s.content)
            parts.append("")

        parts.append("## 题目上下文\n")
        parts.append(f"题目: {question_text}")
        parts.append(f"学生答案: {student_answer}")

        return "\n".join(parts)
