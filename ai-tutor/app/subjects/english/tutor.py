"""
English tutoring pipeline — explanation generation and feedback assembly.

Deterministic template-based explanations. No LLM calls.
Diagnosis → retrieval → explanation → feedback.
"""

from app.core.subject_engine import DiagnosisResult, Question
from app.core.tutoring import (
    KnowledgeSnippet,
    TutoringExplanation,
    TutoringFeedback,
    TutoringPipeline,
)
from app.subjects.english.retrieval import KnowledgeRetriever


# -- Explanation templates ----------------------------------------------------

# Each template maps a diagnosis_label to a structured explanation.
# Template variables: {student_form}, {correct_form}, {subject}, {topic_name}
# are filled from question metadata and answer data at runtime.

EXPLANATION_TEMPLATES: dict[str, dict] = {
    "base_form_instead_of_past": {
        "what_is_wrong": (
            "你使用了动词原形 '{student_form}'，但这句话描述的是过去发生的事情，"
            "需要用过去式。"
        ),
        "why_it_is_wrong": (
            "英语中，描述过去发生的动作需要使用动词的过去式形式。"
            "规则动词加 -ed（如 walk → walked），不规则动词有特殊变化"
            "（如 go → went）。中文没有动词时态变化，"
            "所以需要特别注意时间提示词（yesterday, last night 等）。"
        ),
        "how_to_fix": (
            "找到句中的时间线索（如 yesterday, last night, this morning）"
            " → 确定是过去时 → 把动词从 '{student_form}' 改为过去式 "
            "'{correct_form}'。"
        ),
    },
    "missing_third_person_s": {
        "what_is_wrong": (
            "主语是第三人称单数，动词需要加 -s/-es。"
            "你用了 '{student_form}'，正确的形式是 '{correct_form}'。"
        ),
        "why_it_is_wrong": (
            "英语中，当主语是 he/she/it 或单数名词时，"
            "一般现在时的动词要加 -s 或 -es。"
            "这是英语主谓一致的核心规则之一。"
        ),
        "how_to_fix": (
            "第一步：找到主语 → 第二步：判断是否第三人称单数（he/she/it/单数名词）"
            " → 第三步：动词用 '{correct_form}'（原形 + s/es）。"
        ),
    },
    "a_vs_an_confusion": {
        "what_is_wrong": (
            "你用了 '{student_form}'，但这里应该用 '{correct_form}'。"
        ),
        "why_it_is_wrong": (
            "a 和 an 的选择取决于**后面词的发音**，不是拼写字母。"
            "元音音素开头（a, e, i, o, u 的发音）用 an，"
            "辅音音素开头用 a。例如：an hour（h 不发音），"
            "a university（u 发 /juː/，辅音）。"
        ),
        "how_to_fix": (
            "把后面的词读出来——如果第一个音是 a/e/i/o/u 中的一个 → 用 an；"
            "否则 → 用 a。记忆窍门：an + 元音发音。"
        ),
    },
    "missing_article": {
        "what_is_wrong": (
            "这里缺少了冠词。英语中很多名词前面需要 a/an 或 the。"
        ),
        "why_it_is_wrong": (
            "中文没有冠词系统，所以中文学习者经常遗漏冠词。"
            "但英语中，单数可数名词前通常需要冠词——泛指用 a/an，"
            "特指用 the。部分固定表达不需要冠词（如 by bus, have breakfast）。"
        ),
        "how_to_fix": (
            "检查名词：是单数可数名词吗？→ 需要冠词。"
            "是泛指（第一次提到）吗？→ 用 a/an。"
            "是特指（双方都知道）吗？→ 用 the。"
            "是固定表达（交通工具、三餐等）吗？→ 不加冠词。"
        ),
    },
    "wrong_past_form": {
        "what_is_wrong": (
            "你使用了 '{student_form}'，但正确的动词形式是 '{correct_form}'。"
        ),
        "why_it_is_wrong": (
            "不规则动词的过去式和过去分词有特殊形式，不能直接加 -ed。"
            "例如：go → went → gone, eat → ate → eaten。"
            "此外，当句子需要用进行时（was/were + doing）或完成时（have/has + done）时，"
            "动词形式也是固定的，不能用简单过去式替换。"
            "中文没有动词变位和时态助动词，所以需要特别注意这些结构。"
        ),
        "how_to_fix": (
            "1. 记住不规则动词的三个形式：原形 → 过去式 → 过去分词。"
            "2. 识别句中的时间线索和助动词（was/were, have/has），"
            "它们决定了动词该用哪种形式。"
        ),
    },
    "plural_subject_error": {
        "what_is_wrong": (
            "主语与动词在数上不一致。'{student_form}' 在数上与主语不匹配，"
            "正确的形式是 '{correct_form}'。"
        ),
        "why_it_is_wrong": (
            "英语主谓一致的核心规则：单数主语配单数动词，复数主语配复数动词。"
            "特别注意：someone, everyone, each, neither 等不定代词在语法上是单数，"
            "需要用单数动词（加 -s/-es 或用 is/was/has）。"
            "they, we, 复数名词（students, dogs）是复数主语，动词不用加 -s。"
        ),
        "how_to_fix": (
            "第一步：找到主语 → 第二步：判断单复数 → "
            "第三步：选择对应的动词形式。"
            "不定代词（everyone, each...）虽然意思像复数，但语法上算单数。"
        ),
    },
    "wrong_preposition": {
        "what_is_wrong": (
            "你用了介词 '{student_form}'，但正确的介词是 '{correct_form}'。"
        ),
        "why_it_is_wrong": (
            "英语中介词与动词、形容词的搭配是固定的，"
            "不能从中文直接翻译。例如 'good at' 不能说成 'good in'，"
            "'interested in' 不能说成 'interested on'。"
            "这些搭配需要作为整体来记忆。"
        ),
        "how_to_fix": (
            "记住这个固定搭配的正确介词是 '{correct_form}'。"
            "推荐方法：把整个搭配（如 'good at', 'afraid of'）"
            "当作一个词来记，而不是逐字翻译中文。"
        ),
    },
}

# Labels that don't have specific templates — use a generic fallback
_GENERIC_EXPLANATION = {
    "what_is_wrong": "你的答案 '{student_form}' 与正确答案 '{correct_form}' 不一致。",
    "why_it_is_wrong": "请参考下方知识点了解相关语法规则。",
    "how_to_fix": "对比你的答案和正确答案，找出不同之处。阅读下方知识点加深理解。",
}


# -- TutoringPipeline ---------------------------------------------------------


class EnglishTutoringPipeline(TutoringPipeline):
    """English-specific tutoring feedback pipeline.

    Wires: diagnosis -> retrieval -> template explanation.

    Usage:
        retriever = KnowledgeRetriever("app/subjects/english/knowledge_base")
        pipeline = EnglishTutoringPipeline(retriever)
        feedback = pipeline.explain(diagnosis, question, student_answer)
    """

    def __init__(self, retriever: KnowledgeRetriever) -> None:
        self._retriever = retriever

    def explain(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
    ) -> TutoringFeedback:
        """Generate full tutoring feedback for a wrong answer."""
        # Retrieve relevant knowledge snippets
        knowledge_snippets = self._retriever.query(
            labels=diagnosis.diagnosis_labels,
            tags=question.knowledge_tags,
            topic=question.topic,
        )

        # Build explanation from templates
        explanation = self._build_explanation(
            diagnosis=diagnosis,
            question=question,
            student_answer=student_answer,
            knowledge_snippets=knowledge_snippets,
        )

        return TutoringFeedback(
            diagnosis=diagnosis,
            explanation=explanation,
            knowledge_snippets=knowledge_snippets,
        )

    # -- internal ---------------------------------------------------------

    def _build_explanation(
        self,
        diagnosis: DiagnosisResult,
        question: Question,
        student_answer: str,
        knowledge_snippets: list[KnowledgeSnippet],
    ) -> TutoringExplanation:
        """Build a TutoringExplanation from templates and retrieved context."""
        context = self._build_context(question, student_answer)

        # Use the first diagnosis_label that has a template
        template = _GENERIC_EXPLANATION
        for label in diagnosis.diagnosis_labels:
            if label in EXPLANATION_TEMPLATES:
                template = EXPLANATION_TEMPLATES[label]
                break

        # Safely format template values
        what_is_wrong = template["what_is_wrong"].format(**context)
        why_it_is_wrong = template["why_it_is_wrong"].format(**context)
        how_to_fix = template["how_to_fix"].format(**context)

        # Similar examples from knowledge snippets and metadata
        similar_examples = self._extract_examples(knowledge_snippets, question)

        # Retrieved context — join top snippet content
        retrieved_context = ""
        if knowledge_snippets:
            top = knowledge_snippets[0]
            retrieved_context = (
                f"## {top.title}\n\n{top.content}"
            )

        return TutoringExplanation(
            what_is_wrong=what_is_wrong,
            why_it_is_wrong=why_it_is_wrong,
            how_to_fix=how_to_fix,
            similar_examples=similar_examples,
            retrieved_context=retrieved_context,
        )

    def _build_context(
        self,
        question: Question,
        student_answer: str,
    ) -> dict[str, str]:
        """Build template variable context from question and answer data."""
        ctx: dict[str, str] = {
            "student_form": student_answer.strip(),
            "correct_form": question.answer.split("|||")[0].strip(),
            "topic_name": question.topic,
            "subject": question.metadata.get("subject", ""),
        }

        # Enrich from metadata if available
        meta = question.metadata
        if "verb" in meta:
            ctx.setdefault("verb", str(meta["verb"]))
        if "preposition" in meta:
            ctx.setdefault("preposition", str(meta["preposition"]))
        if "error_focus" in meta:
            ctx.setdefault("error_focus", str(meta["error_focus"]))
        if "tense" in meta:
            ctx.setdefault("tense", str(meta["tense"]))
        if "number" in meta:
            ctx.setdefault("number", str(meta["number"]))

        # Fallbacks for missing template variables
        ctx.setdefault("subject", "主语")

        return ctx

    def _extract_examples(
        self,
        snippets: list[KnowledgeSnippet],
        question: Question,
    ) -> list[str]:
        """Extract example sentences from knowledge snippets."""
        examples: list[str] = []
        for snippet in snippets:
            for line in snippet.content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- ✅"):
                    examples.append(stripped[3:].strip())
                elif stripped.startswith("- ❌"):
                    pass  # Skip incorrect examples
        # Deduplicate and limit
        seen: set[str] = set()
        unique: list[str] = []
        for ex in examples:
            if ex not in seen:
                seen.add(ex)
                unique.append(ex)
        return unique[:4]
