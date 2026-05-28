import uuid
import random

import pytest
import sympy
from sympy import symbols, expand, diff, integrate, factor

from app.engine import (
    Question,
    QuestionEngine,
    safe_parse,
    safe_compare,
)

x = symbols("x")


# ── Question dataclass ───────────────────────────────────────────────────────

class TestQuestion:
    def test_fields_populated(self):
        q = Question(
            id="abc",
            topic="linear_equation",
            difficulty="easy",
            question_text="Solve: $2x = 6$",
            answer="3",
        )
        assert q.id == "abc"
        assert q.topic == "linear_equation"
        assert q.difficulty == "easy"
        assert q.question_text == "Solve: $2x = 6$"
        assert q.answer == "3"
        assert q.metadata == {}

    def test_metadata_default(self):
        q = Question(id="1", topic="t", difficulty="easy", question_text="?", answer="0")
        assert q.metadata == {}

    def test_metadata_populated(self):
        q = Question(
            id="1", topic="t", difficulty="easy", question_text="?", answer="0",
            metadata={"a": 2, "roots": [1, -1]},
        )
        assert q.metadata["a"] == 2


# ── safe_parse ───────────────────────────────────────────────────────────────

class TestSafeParse:
    def test_empty_string(self):
        assert safe_parse("") is None

    def test_whitespace_only(self):
        assert safe_parse("   ") is None

    def test_none_input(self):
        assert safe_parse(None) is None  # type: ignore

    def test_valid_simple(self):
        expr = safe_parse("2*x + 3")
        assert expr is not None
        assert sympy.simplify(expr - sympy.parse_expr("2*x + 3")) == 0

    def test_valid_power(self):
        expr = safe_parse("x**2")
        assert expr is not None
        assert expr == x**2

    def test_valid_trig(self):
        expr = safe_parse("sin(x)")
        assert expr is not None

    def test_valid_rational(self):
        expr = safe_parse("x/2")
        assert expr is not None

    def test_garbage_symbols(self):
        assert safe_parse("!!!") is None

    def test_chinese_characters(self):
        # SymPy treats unknown tokens as symbol names — this is valid, not an error.
        # safe_parse only returns None on actual parse failures.
        result = safe_parse("你好")
        assert result is not None  # parsed as a symbol named 你好

    def test_sql_injection_like(self):
        assert safe_parse("DROP TABLE students") is None

    def test_empty_parentheses(self):
        # SymPy parses () as an empty tuple — valid Python syntax, not an error.
        result = safe_parse("()")
        assert result is not None  # parsed as Tuple()

    def test_unmatched_parentheses(self):
        assert safe_parse("(x + 1") is None


# ── safe_compare ─────────────────────────────────────────────────────────────

class TestSafeCompare:
    def test_exact_match(self):
        assert safe_compare("2*x + 3", "2*x + 3") is True

    def test_commutative(self):
        assert safe_compare("2*x + 3", "3 + 2*x") is True

    def test_equivalent_expressions(self):
        assert safe_compare("x**2 - 1", "(x-1)*(x+1)") is True

    def test_unequal(self):
        assert safe_compare("2*x + 3", "2*x + 5") is False

    def test_garbage_student(self):
        assert safe_compare("!!!", "2*x + 3") is False

    def test_garbage_correct(self):
        assert safe_compare("2*x + 3", "!!!") is False

    def test_both_garbage(self):
        assert safe_compare("!!!", "???") is False

    def test_empty_student(self):
        assert safe_compare("", "2*x + 3") is False

    def test_numeric_answer(self):
        assert safe_compare("3", "3") is True

    def test_numeric_unequal(self):
        assert safe_compare("3", "4") is False

    def test_rational_equivalent(self):
        assert safe_compare("1/2", "0.5") is True

    def test_factored_equivalent(self):
        """(x+2)(x+3) should equal x**2 + 5*x + 6"""
        assert safe_compare("(x+2)*(x+3)", "x**2 + 5*x + 6") is True

    def test_derivative_comparison(self):
        """Student writes expanded form, answer is factored — both correct."""
        assert safe_compare("6*x + 6", "6*(x + 1)") is True


# ── QuestionEngine ───────────────────────────────────────────────────────────

class TestEngineInit:
    def test_topics_list(self):
        engine = QuestionEngine()
        assert len(engine.TOPICS) == 5
        assert "linear_equation" in engine.TOPICS
        assert "integral" in engine.TOPICS

    def test_difficulties_list(self):
        engine = QuestionEngine()
        assert engine.DIFFICULTIES == ("easy", "medium", "hard")

    def test_all_15_templates_registered(self):
        engine = QuestionEngine()
        assert len(engine._templates) == 15


class TestEngineDeterminism:
    def test_same_seed_same_question(self):
        e1 = QuestionEngine(seed=42)
        e2 = QuestionEngine(seed=42)
        q1 = e1.generate("quadratic_equation", "medium")
        q2 = e2.generate("quadratic_equation", "medium")
        assert q1.question_text == q2.question_text
        assert q1.answer == q2.answer
        assert q1.metadata == q2.metadata

    def test_different_seed_different_question(self):
        e1 = QuestionEngine(seed=42)
        e2 = QuestionEngine(seed=99)
        q1 = e1.generate("linear_equation", "easy")
        q2 = e2.generate("linear_equation", "easy")
        assert q1.question_text != q2.question_text

    def test_default_seed_varies(self):
        """Without seed, engines should produce different sequences."""
        e1 = QuestionEngine()
        e2 = QuestionEngine()
        texts = set()
        for _ in range(5):
            texts.add(e1.generate("factoring", "hard").question_text)
            texts.add(e2.generate("factoring", "hard").question_text)
        # With 2 engines × 5 calls, we should get > 5 unique texts
        assert len(texts) > 5

    def test_unique_ids(self):
        engine = QuestionEngine()
        ids = set()
        for _ in range(30):
            for topic in engine.TOPICS:
                for diff in engine.DIFFICULTIES:
                    q = engine.generate(topic, diff)
                    ids.add(q.id)
        assert len(ids) == 30 * 5 * 3  # no collisions


class TestEngineErrors:
    def test_invalid_topic(self):
        engine = QuestionEngine()
        with pytest.raises(ValueError, match="Unknown topic"):
            engine.generate("calculus", "easy")

    def test_invalid_difficulty(self):
        engine = QuestionEngine()
        with pytest.raises(ValueError, match="Unknown difficulty"):
            engine.generate("linear_equation", "extreme")


# ── Per-topic generation tests ───────────────────────────────────────────────

class TestLinearEquation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = QuestionEngine(seed=1)

    def test_easy_solvable(self):
        q = self.engine.generate("linear_equation", "easy")
        # Answer should be an integer
        sol = int(q.answer)
        # Verify: a * sol == b
        assert q.metadata["a"] * sol == q.metadata["b"]

    def test_medium_solvable(self):
        q = self.engine.generate("linear_equation", "medium")
        sol = int(q.answer)
        a, b, c = q.metadata["a"], q.metadata["b"], q.metadata["c"]
        assert a * sol + b == c

    def test_hard_solvable(self):
        q = self.engine.generate("linear_equation", "hard")
        # The answer string may be a rational like "-4"
        student_parsed = safe_parse(q.answer)
        assert student_parsed is not None
        # Build the equation and verify
        a, b, c, d = q.metadata["a"], q.metadata["b"], q.metadata["c"], q.metadata["d"]
        eq = sympy.Eq(a * x + b, c * x + d)
        sol = sympy.solve(eq, x)[0]
        assert sympy.simplify(student_parsed - sol) == 0


class TestQuadraticEquation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = QuestionEngine(seed=2)

    def test_easy_roots_correct(self):
        q = self.engine.generate("quadratic_equation", "easy")
        roots = [int(r) for r in q.answer.split(",")]
        assert len(roots) == 2
        a_sq = q.metadata["a_sq"]
        for r in roots:
            assert r**2 == a_sq

    def test_medium_roots_correct(self):
        q = self.engine.generate("quadratic_equation", "medium")
        roots = [int(r) for r in q.answer.split(",")]
        b, c = q.metadata["b"], q.metadata["c"]
        for r in roots:
            assert r**2 + b * r + c == 0

    def test_hard_roots_correct(self):
        q = self.engine.generate("quadratic_equation", "hard")
        roots = [int(r) for r in q.answer.split(",")]
        a, b, c = q.metadata["a"], q.metadata["b"], q.metadata["c"]
        for r in roots:
            assert a * r**2 + b * r + c == 0

    def test_hard_two_distinct_roots(self):
        q = self.engine.generate("quadratic_equation", "hard")
        roots = q.answer.split(",")
        assert len(roots) == 2
        assert roots[0] != roots[1]


class TestFactoring:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = QuestionEngine(seed=3)

    def test_easy_factored_eq_original(self):
        q = self.engine.generate("factoring", "easy")
        factored = sympy.parse_expr(q.answer)
        original = sympy.parse_expr(q.metadata["original"])
        assert expand(factored) == expand(original)

    def test_medium_factored_eq_original(self):
        q = self.engine.generate("factoring", "medium")
        factored = sympy.parse_expr(q.answer)
        original = sympy.parse_expr(q.metadata["original"])
        assert expand(factored) == expand(original)

    def test_hard_factored_eq_original(self):
        q = self.engine.generate("factoring", "hard")
        factored = sympy.parse_expr(q.answer)
        original = sympy.parse_expr(q.metadata["original"])
        assert expand(factored) == expand(original)

    def test_answer_is_factored_form(self):
        """The answer should be a product, not the expanded polynomial."""
        q = self.engine.generate("factoring", "hard")
        expr = sympy.parse_expr(q.answer)
        # A factored expression should be a Mul at the top level
        assert expr.is_Mul or expr.func.__name__ == "Mul"


class TestDerivative:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = QuestionEngine(seed=4)

    def test_easy_matches_sympy(self):
        q = self.engine.generate("derivative", "easy")
        expected = diff(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0

    def test_medium_matches_sympy(self):
        q = self.engine.generate("derivative", "medium")
        expected = diff(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0

    def test_hard_matches_sympy(self):
        q = self.engine.generate("derivative", "hard")
        expected = diff(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0


class TestIntegral:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = QuestionEngine(seed=5)

    def test_easy_matches_sympy(self):
        q = self.engine.generate("integral", "easy")
        expected = integrate(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0

    def test_medium_matches_sympy(self):
        q = self.engine.generate("integral", "medium")
        expected = integrate(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0

    def test_hard_matches_sympy(self):
        q = self.engine.generate("integral", "hard")
        expected = integrate(sympy.parse_expr(q.metadata["expression"]), x)
        actual = sympy.parse_expr(q.answer)
        assert sympy.simplify(actual - expected) == 0

    def test_integral_derivative_roundtrip(self):
        """Differentiating the integral should give back the original integrand."""
        for _ in range(5):
            q = self.engine.generate("integral", "hard")
            integrand = sympy.parse_expr(q.metadata["expression"])
            result = sympy.parse_expr(q.answer)
            deriv = diff(result, x)
            assert sympy.simplify(deriv - integrand) == 0


# ── Cross-topic property tests ───────────────────────────────────────────────

class TestAllTopicsGenerate:
    @pytest.mark.parametrize("topic", QuestionEngine.TOPICS)
    @pytest.mark.parametrize("difficulty", QuestionEngine.DIFFICULTIES)
    def test_generates_without_error(self, topic, difficulty):
        engine = QuestionEngine(seed=0)
        q = engine.generate(topic, difficulty)
        assert isinstance(q, Question)
        assert len(q.id) > 0
        assert q.topic == topic
        assert q.difficulty == difficulty

    @pytest.mark.parametrize("topic", QuestionEngine.TOPICS)
    @pytest.mark.parametrize("difficulty", QuestionEngine.DIFFICULTIES)
    def test_answer_is_parseable(self, topic, difficulty):
        engine = QuestionEngine(seed=0)
        q = engine.generate(topic, difficulty)
        # For quadratic answers with comma-separated roots
        answers = q.answer.split(",")
        for a in answers:
            parsed = safe_parse(a.strip())
            assert parsed is not None, f"Failed to parse answer '{a}' for {topic}/{difficulty}"

    @pytest.mark.parametrize("topic", QuestionEngine.TOPICS)
    @pytest.mark.parametrize("difficulty", QuestionEngine.DIFFICULTIES)
    def test_question_text_not_empty(self, topic, difficulty):
        engine = QuestionEngine(seed=0)
        q = engine.generate(topic, difficulty)
        assert len(q.question_text.strip()) > 0

    @pytest.mark.parametrize("topic", QuestionEngine.TOPICS)
    @pytest.mark.parametrize("difficulty", QuestionEngine.DIFFICULTIES)
    def test_metadata_has_keys(self, topic, difficulty):
        engine = QuestionEngine(seed=0)
        q = engine.generate(topic, difficulty)
        assert isinstance(q.metadata, dict)
        assert len(q.metadata) > 0
