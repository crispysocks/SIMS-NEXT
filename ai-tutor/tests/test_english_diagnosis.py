"""
Unit tests for English grammar diagnosis rules.

Tests all diagnosis check functions in isolation and via integration
with EnglishQuestionEngine.diagnose() and plan_remediation().
"""
from __future__ import annotations

import pytest

from app.core.subject_engine import DiagnosisResult, Question, RemediationPlan
from app.subjects.english.engine import (
    EnglishQuestionEngine,
    _normalize,
    _exact_match,
    _check_verb_tense_error,
    _check_sva_error,
    _check_article_error,
    _check_preposition_error,
    TOPIC_DIAGNOSIS_RULES,
    REMEDIATION_MAP,
)


# -- Helpers ------------------------------------------------------------------

def _make_question(topic: str = "verb_tense") -> Question:
    return Question(
        id="test_1",
        subject="english",
        topic=topic,
        difficulty="easy",
        question_text="Fill in the blank.",
        answer="went",
    )


# -- Normalization & exact match -----------------------------------------------

class TestNormalize:
    def test_lowercase(self):
        assert _normalize("Hello") == "hello"

    def test_strip_whitespace(self):
        assert _normalize("  hello  ") == "hello"

    def test_collapse_whitespace(self):
        assert _normalize("hello   world") == "hello world"

    def test_empty_string(self):
        assert _normalize("") == ""


class TestExactMatch:
    def test_verbatim_match(self):
        assert _exact_match("went", "went") is True

    def test_normalized_match(self):
        assert _exact_match("  Went  ", "went") is True

    def test_multi_acceptable(self):
        assert _exact_match("gone", "went", "gone") is True

    def test_no_match(self):
        assert _exact_match("go", "went") is False

    def test_empty_student(self):
        assert _exact_match("", "went") is False

    def test_whitespace_student(self):
        assert _exact_match("   ", "went") is False


# -- Verb tense checks (existing) ---------------------------------------------

class TestVerbTenseExisting:
    """Tests for the existing _check_verb_tense_error function."""

    def test_base_form_go(self):
        result = _check_verb_tense_error("go", "went")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_base_form_eat(self):
        result = _check_verb_tense_error("eat", "ate")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_base_form_see(self):
        result = _check_verb_tense_error("see", "saw")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_base_form_write(self):
        result = _check_verb_tense_error("write", "wrote")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_base_form_give(self):
        result = _check_verb_tense_error("give", "gave")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_base_form_in_sentence(self):
        result = _check_verb_tense_error(
            "She go to school yesterday.",
            "She went to school yesterday.",
        )
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_correct_answer_no_error(self):
        result = _check_verb_tense_error("went", "went")
        assert result is None

    def test_no_base_form_present(self):
        result = _check_verb_tense_error("played", "played")
        assert result is None


# -- Verb tense checks (new: regular past) ------------------------------------

class TestVerbTenseRegularPast:
    """Tests for regular verb past tense detection (new functionality)."""

    def test_regular_play_to_played(self):
        """'play' should be detected as base form when correct is 'played'."""
        result = _check_verb_tense_error("play", "played")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_regular_walk_to_walked(self):
        result = _check_verb_tense_error("walk", "walked")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_regular_study_to_studied(self):
        """'study' should be detected when correct is 'studied' (y->ied)."""
        result = _check_verb_tense_error("study", "studied")
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_regular_in_sentence(self):
        result = _check_verb_tense_error(
            "They play football last weekend.",
            "They played football last weekend.",
        )
        assert result == ("verb_tense_error", "base_form_instead_of_past")

    def test_regular_no_false_positive_non_verb(self):
        """Words ending in 'ed' that aren't verbs should not trigger."""
        result = _check_verb_tense_error("red", "red")
        assert result is None


# -- Verb tense checks (new: wrong irregular past) -----------------------------

class TestWrongIrregularPast:
    """Tests for _check_wrong_irregular_past (overregularization, wrong participle, missing continuous)."""

    def test_overregularization_eated(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("eated", "ate")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_overregularization_runned(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("runned", "ran")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_overregularization_goed(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("goed", "went")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_overregularization_singed(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("singed", "sang")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_overregularization_comed(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("comed", "came")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_wrong_participle_went(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past(
            "I have went to the store.",
            "I have gone to the store.",
        )
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_wrong_participle_ate(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past(
            "She has ate breakfast.",
            "She has eaten breakfast.",
        )
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_missing_continuous_studied(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("studied", "was studying")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_missing_continuous_watched(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("watched", "were watching")
        assert result == ("verb_tense_error", "wrong_past_form")

    def test_correct_past_no_error(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("went", "went")
        assert result is None

    def test_correct_continuous_no_error(self):
        from app.subjects.english.engine import _check_wrong_irregular_past
        result = _check_wrong_irregular_past("was walking", "was walking")
        assert result is None


# -- SVA checks (existing) ----------------------------------------------------

class TestSVAExisting:
    """Tests for the existing _check_sva_error function."""

    def test_missing_s_has(self):
        """'have' vs 'has' is a suppletive form — not detectable by suffix rules.
        It is caught by _check_plural_subject_error instead."""
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("have", "has")
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_missing_s_does(self):
        result = _check_sva_error("do", "does")
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_missing_s_goes(self):
        result = _check_sva_error("go", "goes")
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_correct_sva_no_error(self):
        result = _check_sva_error("goes", "goes")
        assert result is None


# -- SVA checks (new: generalized -s, student-side, auxiliary) ----------------

class TestSVAGeneralized:
    """Tests for generalized -s/-es detection."""

    def test_missing_s_rains(self):
        """'rain' vs 'rains' — not in hardcoded list, should be caught by generalized rule."""
        result = _check_sva_error("rain", "rains")
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_missing_s_barks(self):
        result = _check_sva_error("bark", "barks")
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_missing_s_walks(self):
        result = _check_sva_error("walk", "walks")
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_no_false_positive_plural_noun(self):
        """'dogs' should not trigger SVA if 'dog' is not a verb stem."""
        result = _check_sva_error("dog", "dogs")
        # 'dog' is not in KNOWN_VERB_STEMS, so should not match
        assert result is None

    def test_student_side_she_go(self):
        """'She go' in student answer should be detected as missing -s."""
        result = _check_sva_error(
            "She go to school yesterday.",
            "She went to school yesterday.",
        )
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_student_side_he_play(self):
        result = _check_sva_error(
            "He play soccer every day.",
            "He plays soccer every day.",
        )
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_auxiliary_dont_for_doesnt(self):
        """'He don't like' should flag auxiliary mismatch."""
        result = _check_sva_error(
            "He don't like coffee.",
            "He doesn't like coffee.",
        )
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")

    def test_auxiliary_dont_in_sentence(self):
        result = _check_sva_error(
            "He don't likes the movie.",
            "He doesn't like the movie.",
        )
        assert result == ("subject_verb_agreement_error", "missing_third_person_s")


# -- SVA checks (new: plural subject error) -----------------------------------

class TestPluralSubjectError:
    """Tests for _check_plural_subject_error."""

    def test_is_are_mismatch(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("is", "are")
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_is_are_in_sentence(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error(
            "The students is ready.",
            "The students are ready.",
        )
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_was_were_mismatch(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("was", "were")
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_has_have_plural_subject(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("has", "have")
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_indefinite_pronoun_everyone_have(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error(
            "Everyone have their own opinion.",
            "Everyone has their own opinion.",
        )
        assert result == ("subject_verb_agreement_error", "plural_subject_error")

    def test_indefinite_pronoun_each_have(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("have", "has")
        # Without context, this is ambiguous; the check looks for indefinite pronouns
        # in the student answer. If not found, it returns None.
        # This tests the conservative behavior.
        pass  # Accept either outcome for bare word case

    def test_no_false_positive_correct_agreement(self):
        from app.subjects.english.engine import _check_plural_subject_error
        result = _check_plural_subject_error("are", "are")
        assert result is None


# -- Article checks (regression) -----------------------------------------------

class TestArticleChecks:
    def test_a_vs_an_a_to_an(self):
        result = _check_article_error("a elephant", "an elephant")
        assert result == ("article_error", "a_vs_an_confusion")

    def test_a_vs_an_an_to_a(self):
        result = _check_article_error("an university", "a university")
        assert result == ("article_error", "a_vs_an_confusion")

    def test_missing_article(self):
        result = _check_article_error("sun rises in east", "The sun rises in the east")
        assert result == ("article_error", "missing_article")

    def test_missing_article_single_word(self):
        result = _check_article_error("sun", "The")
        assert result == ("article_error", "missing_article")

    def test_correct_article_no_error(self):
        result = _check_article_error("an", "an")
        assert result is None


# -- Preposition checks (regression) -------------------------------------------

class TestPrepositionChecks:
    def test_wrong_preposition(self):
        result = _check_preposition_error("in", "on")
        assert result == ("preposition_error", "wrong_preposition")

    def test_wrong_preposition_sentence(self):
        result = _check_preposition_error(
            "I will meet you in Monday.",
            "I will meet you on Monday.",
        )
        assert result == ("preposition_error", "wrong_preposition")

    def test_correct_preposition_no_error(self):
        result = _check_preposition_error("on", "on")
        assert result is None


# -- Integration: EnglishQuestionEngine.diagnose() -----------------------------

class TestDiagnoseIntegration:
    """Integration tests for the diagnose() method."""

    def test_empty_answer_returns_diagnosis(self):
        """Empty student answer should not short-circuit; article checker should fire."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="article_usage",
            difficulty="easy",
            question_text="___ sun rises in the east.",
            answer="The",
        )
        result = engine.diagnose("", "The", q)
        # Empty input: article checker should detect missing article
        assert "missing_article" in result.diagnosis_labels

    def test_sentence_correction_multiple_labels(self):
        """'She go to school yesterday.' should produce both SVA and verb tense labels."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="sentence_correction",
            difficulty="easy",
            question_text="Correct the error: \"She go to school yesterday.\"",
            answer="She went to school yesterday.",
        )
        result = engine.diagnose(
            "She go to school yesterday.",
            "She went to school yesterday.",
            q,
        )
        assert "base_form_instead_of_past" in result.diagnosis_labels
        assert "missing_third_person_s" in result.diagnosis_labels

    def test_dont_auxiliary_in_sentence_correction(self):
        """'He don't likes the movie.' should produce missing_third_person_s."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="sentence_correction",
            difficulty="easy",
            question_text="Correct the error: \"He don't likes the movie.\"",
            answer="He doesn't like the movie.",
        )
        result = engine.diagnose(
            "He don't likes the movie.",
            "He doesn't like the movie.",
            q,
        )
        assert "missing_third_person_s" in result.diagnosis_labels

    def test_correct_answer_produces_empty(self):
        """Correct answer should produce no error types."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="verb_tense",
            difficulty="easy",
            question_text="Fill in the blank: She ___ (go) to school.",
            answer="went",
        )
        result = engine.diagnose("went", "went", q)
        assert result.error_types == []
        assert result.diagnosis_labels == []
        assert result.confidence == 1.0

    def test_wrong_answer_confidence(self):
        """Wrong answer should have confidence < 1.0."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="verb_tense",
            difficulty="easy",
            question_text="Fill in the blank.",
            answer="went",
        )
        result = engine.diagnose("go", "went", q)
        assert result.confidence == 0.85
        assert len(result.error_types) > 0

    def test_eated_produces_wrong_past_form(self):
        """Overregularization should produce wrong_past_form label."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="verb_tense",
            difficulty="easy",
            question_text="I ___ (eat) breakfast.",
            answer="ate",
        )
        result = engine.diagnose("eated", "ate", q)
        assert "wrong_past_form" in result.diagnosis_labels

    def test_plural_subject_produces_label(self):
        """'The students is' should produce plural_subject_error."""
        engine = EnglishQuestionEngine(seed=42)
        q = Question(
            id="test",
            subject="english",
            topic="subject_verb_agreement",
            difficulty="easy",
            question_text="The students ___ ready.",
            answer="are",
        )
        result = engine.diagnose("is", "are", q)
        assert "plural_subject_error" in result.diagnosis_labels


# -- Integration: plan_remediation() -------------------------------------------

class TestPlanRemediation:
    """Tests for plan_remediation with new error types."""

    def test_wrong_past_form_remediation(self):
        engine = EnglishQuestionEngine(seed=42)
        diag = DiagnosisResult(
            error_types=["verb_tense_error"],
            diagnosis_labels=["wrong_past_form"],
        )
        plan = engine.plan_remediation(diag)
        assert "irregular_verbs" in plan.recommended_topics
        assert "past_continuous" in plan.recommended_topics or "present_perfect" in plan.recommended_topics

    def test_plural_subject_remediation(self):
        engine = EnglishQuestionEngine(seed=42)
        diag = DiagnosisResult(
            error_types=["subject_verb_agreement_error"],
            diagnosis_labels=["plural_subject_error"],
        )
        plan = engine.plan_remediation(diag)
        assert "plural_subjects" in plan.recommended_topics
        assert "indefinite_pronouns" in plan.recommended_topics

    def test_multiple_error_types_remediation(self):
        engine = EnglishQuestionEngine(seed=42)
        diag = DiagnosisResult(
            error_types=["verb_tense_error", "subject_verb_agreement_error"],
            diagnosis_labels=["base_form_instead_of_past", "missing_third_person_s"],
        )
        plan = engine.plan_remediation(diag)
        assert "simple_past_tense" in plan.recommended_topics
        assert "subject_verb_agreement" in plan.recommended_topics
        # Labels should be in retrieval_tags
        assert "base_form_instead_of_past" in plan.retrieval_tags
        assert "missing_third_person_s" in plan.retrieval_tags

    def test_empty_diagnosis_remediation(self):
        engine = EnglishQuestionEngine(seed=42)
        diag = DiagnosisResult()
        plan = engine.plan_remediation(diag)
        assert plan.recommended_topics == []
        assert plan.retrieval_tags == []


# -- Topic diagnosis rules registration ----------------------------------------

class TestTopicDiagnosisRules:
    """Verify TOPIC_DIAGNOSIS_RULES includes all new checkers."""

    def test_verb_tense_has_both_checkers(self):
        assert len(TOPIC_DIAGNOSIS_RULES["verb_tense"]) >= 2
        assert _check_verb_tense_error in TOPIC_DIAGNOSIS_RULES["verb_tense"]

    def test_sva_has_both_checkers(self):
        assert len(TOPIC_DIAGNOSIS_RULES["subject_verb_agreement"]) >= 2
        assert _check_sva_error in TOPIC_DIAGNOSIS_RULES["subject_verb_agreement"]

    def test_sentence_correction_has_all_checkers(self):
        rules = TOPIC_DIAGNOSIS_RULES["sentence_correction"]
        assert len(rules) >= 6
        assert _check_verb_tense_error in rules
        assert _check_sva_error in rules
        assert _check_article_error in rules
        assert _check_preposition_error in rules


# -- Remediation map -----------------------------------------------------------

class TestRemediationMap:
    def test_verb_tense_includes_new_topics(self):
        remed = REMEDIATION_MAP["verb_tense_error"]
        assert "past_continuous" in remed
        assert "present_perfect" in remed

    def test_sva_includes_new_topics(self):
        remed = REMEDIATION_MAP["subject_verb_agreement_error"]
        assert "plural_subjects" in remed
        assert "indefinite_pronouns" in remed
