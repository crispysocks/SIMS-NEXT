"""
RAG English Tutor — Evaluation Harness

Runs a standardised eval dataset across multiple pipeline variants and
produces JSON + markdown reports.

Usage:
    uv run python evaluation/english_rag_eval.py

Environment:
    RAG_LLM_ENABLED=true|false     enable LLM for full_rag variant
    OPENAI_API_KEY=...             required only for full_rag variant
    OPENAI_BASE_URL=...            optional custom endpoint
    LLM_MODEL=...                  optional model name

Does NOT import app.main or streamlit. Constructs pipeline instances directly.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# -- Path setup ---------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.core.subject_engine import DiagnosisResult, Question
from app.core.tutoring import TutoringFeedback
from app.rag.factory import RAGConfig, create_pipeline
from app.rag.llm_explanation_generator import (
    SOURCE_RAG_LLM,
    SOURCE_TEMPLATE_FALLBACK,
    SOURCE_DETERMINISTIC_FALLBACK,
)

# -- Constants ----------------------------------------------------------------

SEED = 42
KB_PATH = "app/subjects/english/knowledge_base"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Knowledge tags per topic (derived from EnglishQuestionEngine templates)
TOPIC_TAGS: dict[str, list[str]] = {
    "verb_tense": ["verb_tense", "past_tense", "irregular_verbs", "past_continuous"],
    "subject_verb_agreement": ["subject_verb_agreement", "third_person_singular", "plural_subjects", "indefinite_pronouns"],
    "article_usage": ["article_usage", "indefinite_article", "definite_article", "a_vs_an", "zero_article"],
    "preposition_usage": ["preposition_usage", "time_prepositions", "place_prepositions", "dependent_prepositions"],
    "sentence_correction": ["sentence_correction", "subject_verb_agreement", "verb_tense", "article_usage", "preposition_usage"],
}

# -- Pipeline variants --------------------------------------------------------

PIPELINE_VARIANTS = {
    "deterministic": RAGConfig(enabled=False, kb_path=KB_PATH),
    "tfidf": RAGConfig(enabled=True, retriever_mode="tfidf", llm_enabled=False, kb_path=KB_PATH),
    "hybrid": RAGConfig(enabled=True, retriever_mode="hybrid", llm_enabled=False, kb_path=KB_PATH),
    "full_rag": RAGConfig(enabled=True, retriever_mode="hybrid", llm_enabled=True, kb_path=KB_PATH),
}


# -- Data structures ----------------------------------------------------------

@dataclass
class CaseResult:
    case_index: int
    topic: str
    student_answer: str
    correct_answer: str
    expected_labels: list[str]
    expected_remediation: list[str]
    # Diagnosis
    diagnosis_labels: list[str] = field(default_factory=list)
    diagnosis_match: bool = False
    # Retrieval
    retrieved_ids: list[str] = field(default_factory=list)
    retrieval_hit: bool = False
    retrieval_count: int = 0
    # Remediation
    remediation_topics: list[str] = field(default_factory=list)
    remediation_overlap: int = 0
    remediation_total: int = 0
    # Explanation
    generation_source: str = ""
    latency_ms: float = 0.0


@dataclass
class EvalMetrics:
    variant: str
    total_cases: int = 0
    diagnosis_accuracy: float = 0.0
    retrieval_hit_rate: float = 0.0
    remediation_recall: float = 0.0
    llm_success_rate: float = 0.0
    fallback_rate: float = 0.0
    avg_latency_ms: float = 0.0
    results: list[CaseResult] = field(default_factory=list)


# -- Engine helpers -----------------------------------------------------------

def _create_engine():
    from app.subjects.english.engine import EnglishQuestionEngine
    return EnglishQuestionEngine(seed=SEED)


def _build_question(case: dict, idx: int) -> Question:
    topic = case["topic"]
    return Question(
        id=f"eval_{idx}",
        subject="english",
        topic=topic,
        difficulty="easy",
        question_text=case["question"],
        answer=case["correct_answer"],
        knowledge_tags=TOPIC_TAGS.get(topic, [topic]),
    )


# -- Main eval loop -----------------------------------------------------------

def load_dataset(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_eval(variant_name: str, config: RAGConfig, cases: list[dict]) -> EvalMetrics:
    engine = _create_engine()
    pipeline = create_pipeline("english", config)

    metrics = EvalMetrics(variant=variant_name, total_cases=len(cases))

    for idx, case in enumerate(cases):
        question = _build_question(case, idx)
        student_answer = case["student_answer"]
        correct_answer_first = case["correct_answer"].split("|||")[0].strip()

        # Diagnosis (rule-based, same for all variants)
        diagnosis = engine.diagnose(student_answer, correct_answer_first, question)

        # Tutoring pipeline
        t0 = time.perf_counter()
        feedback = pipeline.explain(diagnosis, question, student_answer) if pipeline else None

        # Fallback: if no pipeline, construct minimal feedback
        if feedback is None:
            latency = 0.0
            explanation_labels = diagnosis.diagnosis_labels
            retrieved_ids = []
            generation_source = ""
            remediation_topics = []
            knowledge_snippets = []
        else:
            latency = (time.perf_counter() - t0) * 1000
            explanation_labels = diagnosis.diagnosis_labels
            knowledge_snippets = feedback.knowledge_snippets
            retrieved_ids = [s.id for s in knowledge_snippets]
            remediation_topics = feedback.diagnosis.error_types if feedback.diagnosis else []
            if feedback.explanation is not None:
                generation_source = feedback.explanation.metadata.get("source", "")
            else:
                generation_source = ""

        # Actual remediation from engine
        remediation = engine.plan_remediation(diagnosis)
        actual_remediation = remediation.recommended_topics

        # Compute per-case metrics
        expected_labels = case.get("expected_labels", [])
        expected_remediation = case.get("expected_remediation", [])

        # Diagnosis match: exact set match
        diagnosis_match = set(diagnosis.diagnosis_labels) == set(expected_labels)

        # Retrieval hit: any expected label appears in retrieved snippet tags or labels
        retrieval_hit = False
        for ks in knowledge_snippets:
            ks_labels = set(ks.diagnosis_labels) | set(ks.tags)
            if ks_labels & set(expected_labels):
                retrieval_hit = True
                break

        # Remediation overlap
        rem_overlap = len(set(actual_remediation) & set(expected_remediation))
        rem_total = len(expected_remediation)

        cr = CaseResult(
            case_index=idx,
            topic=case["topic"],
            student_answer=student_answer,
            correct_answer=correct_answer_first,
            expected_labels=expected_labels,
            expected_remediation=expected_remediation,
            diagnosis_labels=diagnosis.diagnosis_labels,
            diagnosis_match=diagnosis_match,
            retrieved_ids=retrieved_ids,
            retrieval_hit=retrieval_hit,
            retrieval_count=len(knowledge_snippets),
            remediation_topics=actual_remediation,
            remediation_overlap=rem_overlap,
            remediation_total=rem_total,
            generation_source=generation_source,
            latency_ms=latency,
        )
        metrics.results.append(cr)

    # Aggregate
    n = metrics.total_cases
    if n > 0:
        metrics.diagnosis_accuracy = sum(1 for r in metrics.results if r.diagnosis_match) / n
        metrics.retrieval_hit_rate = sum(1 for r in metrics.results if r.retrieval_hit) / n
        metrics.remediation_recall = (
            sum(r.remediation_overlap for r in metrics.results) /
            max(sum(r.remediation_total for r in metrics.results), 1)
        )
        metrics.llm_success_rate = sum(
            1 for r in metrics.results if r.generation_source == SOURCE_RAG_LLM
        ) / n
        metrics.fallback_rate = sum(
            1 for r in metrics.results
            if r.generation_source in (SOURCE_TEMPLATE_FALLBACK, SOURCE_DETERMINISTIC_FALLBACK)
        ) / n
        metrics.avg_latency_ms = sum(r.latency_ms for r in metrics.results) / n

    return metrics


# -- Output -------------------------------------------------------------------

def write_json_report(all_metrics: list[EvalMetrics], path: str) -> None:
    output = {}
    for m in all_metrics:
        output[m.variant] = {
            "total_cases": m.total_cases,
            "diagnosis_accuracy": round(m.diagnosis_accuracy, 4),
            "retrieval_hit_rate": round(m.retrieval_hit_rate, 4),
            "remediation_recall": round(m.remediation_recall, 4),
            "llm_success_rate": round(m.llm_success_rate, 4),
            "fallback_rate": round(m.fallback_rate, 4),
            "avg_latency_ms": round(m.avg_latency_ms, 1),
            "per_case": [
                {
                    "index": r.case_index,
                    "topic": r.topic,
                    "student_answer": r.student_answer,
                    "correct_answer": r.correct_answer,
                    "diagnosis_labels": r.diagnosis_labels,
                    "diagnosis_match": r.diagnosis_match,
                    "retrieval_hit": r.retrieval_hit,
                    "retrieved_ids": r.retrieved_ids,
                    "remediation_overlap": f"{r.remediation_overlap}/{r.remediation_total}",
                    "generation_source": r.generation_source,
                    "latency_ms": round(r.latency_ms, 1),
                }
                for r in m.results
            ],
        }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def _pct(v: float) -> str:
    return f"{v:.0%}"


def _ms(v: float) -> str:
    return f"{v:.0f}ms"


def write_markdown_report(all_metrics: list[EvalMetrics], path: str) -> None:
    lines: list[str] = []
    lines.append("# RAG Evaluation Summary")
    lines.append("")
    lines.append(f"**Dataset**: {all_metrics[0].total_cases} cases")
    lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append("| Pipeline | Diagnosis | Retrieval | Remediation | LLM Success | Fallback | Avg Latency |")
    lines.append("|----------|-----------|-----------|-------------|-------------|----------|-------------|")

    for m in all_metrics:
        lines.append(
            f"| {m.variant:13s} "
            f"| {_pct(m.diagnosis_accuracy):9s} "
            f"| {_pct(m.retrieval_hit_rate):9s} "
            f"| {_pct(m.remediation_recall):11s} "
            f"| {_pct(m.llm_success_rate):11s} "
            f"| {_pct(m.fallback_rate):8s} "
            f"| {_ms(m.avg_latency_ms):11s} |"
        )

    lines.append("")
    lines.append("## Per-Case Breakdown")
    lines.append("")

    for m in all_metrics:
        lines.append(f"### {m.variant}")
        lines.append("")
        lines.append("| # | Topic | Student | Correct | Diagnosis | Labels | Retrieval | Remediation | Source | Latency |")
        lines.append("|---|-------|---------|---------|-----------|--------|-----------|-------------|--------|---------|")

        for r in m.results:
            diag = "✓" if r.diagnosis_match else "✗"
            retr = "✓" if r.retrieval_hit else "✗"
            labels_short = ", ".join(r.diagnosis_labels)[:40]
            rem = f"{r.remediation_overlap}/{r.remediation_total}"
            src = r.generation_source.replace("_", " ")[:20] if r.generation_source else "—"
            lines.append(
                f"| {r.case_index:2d} "
                f"| {r.topic[:20]:21s} "
                f"| {r.student_answer[:15]:15s} "
                f"| {r.correct_answer[:15]:15s} "
                f"| {diag:9s} "
                f"| {labels_short:30s} "
                f"| {retr:9s} "
                f"| {rem:11s} "
                f"| {src:20s} "
                f"| {_ms(r.latency_ms):7s} |"
            )
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# -- Main ---------------------------------------------------------------------

def main() -> None:
    dataset_path = Path(__file__).resolve().parent / "datasets" / "grammar_eval_set.json"
    print(f"Loading dataset: {dataset_path}")
    cases = load_dataset(str(dataset_path))
    print(f"Loaded {len(cases)} cases across {len(set(c['topic'] for c in cases))} topics")

    # Detect LLM availability
    api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_available = bool(api_key)
    if not llm_available:
        print("Note: OPENAI_API_KEY not set — full_rag will use template fallback (slow due to timeouts)")
        print("Set OPENAI_API_KEY for faster full_rag evaluation with real LLM generation")

    variants = dict(PIPELINE_VARIANTS)
    # If no API key, skip full_rag to avoid long network timeouts
    if not llm_available:
        del variants["full_rag"]
        print("Skipping full_rag variant (no API key)")

    print(f"\n{'='*60}")
    print(f"Running evaluation across {len(variants)} pipeline variants")
    print(f"{'='*60}")

    all_metrics: list[EvalMetrics] = []
    for variant_name, config in variants.items():
        label = f"{variant_name} (rag={config.enabled}, mode={config.retriever_mode}, llm={config.llm_enabled})"
        print(f"\n--- {label} ---")
        metrics = run_eval(variant_name, config, cases)
        all_metrics.append(metrics)
        print(f"  diagnosis_accuracy:  {metrics.diagnosis_accuracy:.2%}")
        print(f"  retrieval_hit_rate:  {metrics.retrieval_hit_rate:.2%}")
        print(f"  remediation_recall:  {metrics.remediation_recall:.2%}")
        print(f"  llm_success_rate:    {metrics.llm_success_rate:.2%}")
        print(f"  fallback_rate:       {metrics.fallback_rate:.2%}")
        print(f"  avg_latency_ms:      {metrics.avg_latency_ms:.1f}")

    # Write reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "eval_results.json"
    md_path = REPORTS_DIR / "eval_summary.md"

    print(f"\nWriting JSON report: {json_path}")
    write_json_report(all_metrics, str(json_path))

    print(f"Writing markdown report: {md_path}")
    write_markdown_report(all_metrics, str(md_path))

    print(f"\n{'='*60}")
    print("Evaluation complete.")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
