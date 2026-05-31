import uuid
import random
from dataclasses import dataclass, field
from math import isclose
from typing import Optional, Callable

import sympy
from sympy import symbols, expand, factor, diff as sym_diff, integrate as sym_integrate
from sympy import sin, cos, exp, sqrt
x = symbols("x")


@dataclass
class Question:
    """A generated math question with its canonical answer."""

    id: str
    topic: str
    difficulty: str
    question_text: str
    answer: str
    metadata: dict = field(default_factory=dict)


# ── Safety wrappers ──────────────────────────────────────────────────────────

def safe_parse(s: str) -> Optional[sympy.Expr]:
    """Parse a user-submitted string into a SymPy expression.

    Returns None on any failure — never raises.
    """
    if not s or not s.strip():
        return None
    try:
        return sympy.parse_expr(s.strip(), evaluate=False)
    except Exception:
        # SymPy may raise SympifyError, SyntaxError, TypeError, ValueError,
        # or Python's tokenize.TokenError. Catch all — contract is "never raise".
        return None


def safe_compare(student: str, correct: str, tolerance: float = 1e-9) -> bool:
    """Compare student answer to correct answer.

    Tries symbolic equality first, falls back to numeric approximation.
    Never raises on malformed input.
    """
    s_expr = safe_parse(student)
    c_expr = safe_parse(correct)
    if s_expr is None or c_expr is None:
        return False

    # Tuple comparison (comma-separated answers like "-1,-4")
    if isinstance(s_expr, tuple) and isinstance(c_expr, tuple):
        if len(s_expr) != len(c_expr):
            return False
        s_items = [sympy.sympify(v) for v in s_expr]
        c_items = [sympy.sympify(v) for v in c_expr]
        try:
            return all(
                sympy.simplify(a - b) == 0 for a, b in zip(s_items, c_items)
            )
        except Exception:
            return False

    try:
        diff = sympy.simplify(s_expr - c_expr)
        if diff == 0:
            return True
    except Exception:
        pass

    # Fallback: numeric evaluation (only for Expr objects, not tuples etc.)
    if not (hasattr(s_expr, "free_symbols") and hasattr(c_expr, "free_symbols")):
        return False

    syms = list(s_expr.free_symbols | c_expr.free_symbols)
    if not syms:
        syms = [x]

    try:
        sub = {s: 3.7 + 0.1 * i for i, s in enumerate(syms)}
        s_val = float(s_expr.evalf(subs=sub))
        c_val = float(c_expr.evalf(subs=sub))
        return isclose(s_val, c_val, rel_tol=tolerance)
    except Exception:
        return False


def _to_str(expr) -> str:
    """Convert a SymPy expression to a parsable string."""
    return str(expr).replace("**", "**")


# ── Engine ───────────────────────────────────────────────────────────────────


class QuestionEngine:
    """Deterministic math question generator backed by SymPy.

    Usage:
        engine = QuestionEngine(seed=42)
        q = engine.generate("linear_equation", "easy")
    """

    TOPICS = ("linear_equation", "quadratic_equation", "factoring", "derivative", "integral")
    DIFFICULTIES = ("easy", "medium", "hard")

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self._templates: dict[tuple[str, str], Callable[[], Question]] = {}
        self._register_all()

    def generate(self, topic: str, difficulty: str) -> Question:
        if topic not in self.TOPICS:
            raise ValueError(f"Unknown topic: {topic}. Valid: {self.TOPICS}")
        if difficulty not in self.DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {difficulty}. Valid: {self.DIFFICULTIES}")
        return self._templates[(topic, difficulty)]()

    def _register_all(self) -> None:
        """Register all 15 template methods (5 topics × 3 difficulties)."""
        self._templates[("linear_equation", "easy")] = self._linear_easy
        self._templates[("linear_equation", "medium")] = self._linear_medium
        self._templates[("linear_equation", "hard")] = self._linear_hard
        self._templates[("quadratic_equation", "easy")] = self._quadratic_easy
        self._templates[("quadratic_equation", "medium")] = self._quadratic_medium
        self._templates[("quadratic_equation", "hard")] = self._quadratic_hard
        self._templates[("factoring", "easy")] = self._factoring_easy
        self._templates[("factoring", "medium")] = self._factoring_medium
        self._templates[("factoring", "hard")] = self._factoring_hard
        self._templates[("derivative", "easy")] = self._derivative_easy
        self._templates[("derivative", "medium")] = self._derivative_medium
        self._templates[("derivative", "hard")] = self._derivative_hard
        self._templates[("integral", "easy")] = self._integral_easy
        self._templates[("integral", "medium")] = self._integral_medium
        self._templates[("integral", "hard")] = self._integral_hard

    # ── linear_equation ──────────────────────────────────────────────────

    def _linear_easy(self) -> Question:
        a = self.rng.randint(2, 9)
        sol = self.rng.randint(-10, 10)
        if sol == 0:
            sol = 1
        b = a * sol
        return Question(
            id=str(uuid.uuid4()),
            topic="linear_equation",
            difficulty="easy",
            question_text=f"Solve: ${a}x = {b}$",
            answer=str(sol),
            metadata={"a": a, "b": b, "solution": sol},
        )

    def _linear_medium(self) -> Question:
        a = self.rng.randint(2, 8)
        sol = self.rng.randint(-8, 8)
        b = self.rng.randint(1, 10)
        c = a * sol + b
        sign = "+" if b >= 0 else "-"
        return Question(
            id=str(uuid.uuid4()),
            topic="linear_equation",
            difficulty="medium",
            question_text=f"Solve: ${a}x {sign} {abs(b)} = {c}$",
            answer=str(sol),
            metadata={"a": a, "b": b, "c": c, "solution": sol},
        )

    def _linear_hard(self) -> Question:
        a = self.rng.randint(2, 8)
        c = self.rng.choice([v for v in range(2, 9) if v != a])
        sol = self.rng.randint(-5, 5)
        b = self.rng.randint(1, 9)
        d = (a - c) * sol + b
        sign_b = "+" if b >= 0 else "-"
        sign_cx = "+" if c >= 0 else "-"
        cx_part = f"{sign_cx} {abs(c)}x" if c != 1 else f"{sign_cx} x"
        return Question(
            id=str(uuid.uuid4()),
            topic="linear_equation",
            difficulty="hard",
            question_text=f"Solve: ${a}x {sign_b} {abs(b)} = {cx_part} + {abs(d)}$" if d >= 0
            else f"Solve: ${a}x {sign_b} {abs(b)} = {cx_part} - {abs(d)}$",
            answer=_to_str(sympy.Rational((d - b), (a - c))),
            metadata={"a": a, "b": b, "c": c, "d": d, "solution_sym": str(sympy.Rational((d - b), (a - c)))},
        )

    # ── quadratic_equation ───────────────────────────────────────────────

    def _quadratic_easy(self) -> Question:
        sqrt_n = self.rng.randint(2, 10)
        a_sq = sqrt_n ** 2
        return Question(
            id=str(uuid.uuid4()),
            topic="quadratic_equation",
            difficulty="easy",
            question_text=f"Solve: $x^2 = {a_sq}$",
            answer=f"{-sqrt_n},{sqrt_n}",
            metadata={"a_sq": a_sq, "roots": [-sqrt_n, sqrt_n], "format": "comma_separated"},
        )

    def _quadratic_medium(self) -> Question:
        r1 = self.rng.randint(-8, 8)
        r2 = self.rng.choice([v for v in range(-8, 9) if v != r1])
        b = -(r1 + r2)
        c = r1 * r2
        sign_b = f"+ {abs(b)}" if b >= 0 else f"- {abs(b)}"
        sign_c = f"+ {abs(c)}" if c >= 0 else f"- {abs(c)}"
        return Question(
            id=str(uuid.uuid4()),
            topic="quadratic_equation",
            difficulty="medium",
            question_text=f"Solve: $x^2 {sign_b}x {sign_c} = 0$",
            answer=f"{r1},{r2}",
            metadata={"b": b, "c": c, "roots": [r1, r2], "format": "comma_separated"},
        )

    def _quadratic_hard(self) -> Question:
        a = self.rng.randint(2, 5)
        r1 = self.rng.randint(-5, 5)
        r2 = self.rng.choice([v for v in range(-5, 6) if v != r1])
        b = -a * (r1 + r2)
        c = a * r1 * r2
        sign_b = f"+ {abs(b)}" if b >= 0 else f"- {abs(b)}"
        sign_c = f"+ {abs(c)}" if c >= 0 else f"- {abs(c)}"
        a_prefix = "" if a == 1 else str(a)
        roots_str = f"{r1},{r2}"
        return Question(
            id=str(uuid.uuid4()),
            topic="quadratic_equation",
            difficulty="hard",
            question_text=f"Solve: ${a_prefix}x^2 {sign_b}x {sign_c} = 0$",
            answer=roots_str,
            metadata={"a": a, "b": b, "c": c, "roots": [r1, r2], "format": "comma_separated"},
        )

    # ── factoring ────────────────────────────────────────────────────────

    def _factoring_easy(self) -> Question:
        a = self.rng.randint(2, 9)
        expr = a * x + a * self.rng.randint(1, 9)
        factored = factor(expr)
        return Question(
            id=str(uuid.uuid4()),
            topic="factoring",
            difficulty="easy",
            question_text=f"Factor: ${_to_str(expr)}$",
            answer=_to_str(factored),
            metadata={"original": _to_str(expr), "factored": _to_str(factored)},
        )

    def _factoring_medium(self) -> Question:
        a = self.rng.randint(1, 10)
        expr = x**2 - a**2
        factored = (x - a) * (x + a)
        return Question(
            id=str(uuid.uuid4()),
            topic="factoring",
            difficulty="medium",
            question_text=f"Factor: $x^2 - {a**2}$",
            answer=_to_str(factored),
            metadata={"a": a, "original": f"x**2 - {a**2}", "factored": _to_str(factored)},
        )

    def _factoring_hard(self) -> Question:
        p = self.rng.randint(-6, 6)
        q = self.rng.choice([v for v in range(-6, 7) if v != p])
        b = p + q
        c = p * q
        expr = x**2 + b * x + c
        factored = factor(expr)
        sign_b = f"+ {abs(b)}" if b >= 0 else f"- {abs(b)}"
        sign_c = f"+ {abs(c)}" if c >= 0 else f"- {abs(c)}"
        return Question(
            id=str(uuid.uuid4()),
            topic="factoring",
            difficulty="hard",
            question_text=f"Factor: $x^2 {sign_b}x {sign_c}$",
            answer=_to_str(factored),
            metadata={"p": p, "q": q, "b": b, "c": c, "original": _to_str(expr), "factored": _to_str(factored)},
        )

    # ── derivative ───────────────────────────────────────────────────────

    def _derivative_easy(self) -> Question:
        n = self.rng.randint(2, 6)
        expr = x**n
        result = sym_diff(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="derivative",
            difficulty="easy",
            question_text=f"Find $d/dx$ of $x^{{{n}}}$",
            answer=_to_str(result),
            metadata={"expression": _to_str(expr), "derivative": _to_str(result)},
        )

    def _derivative_medium(self) -> Question:
        a = self.rng.randint(2, 5)
        n = self.rng.randint(2, 5)
        b = self.rng.randint(1, 4)
        m = self.rng.choice([v for v in range(1, 5) if v != n])
        expr = a * x**n + b * x**m
        result = sym_diff(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="derivative",
            difficulty="medium",
            question_text=f"Find $d/dx$ of ${_to_str(expr)}$",
            answer=_to_str(result),
            metadata={"a": a, "n": n, "b": b, "m": m, "expression": _to_str(expr), "derivative": _to_str(result)},
        )

    def _derivative_hard(self) -> Question:
        a = self.rng.randint(2, 4)
        b = self.rng.randint(1, 5)
        n = self.rng.randint(2, 4)
        expr = (a * x + b) ** n
        result = sym_diff(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="derivative",
            difficulty="hard",
            question_text=f"Find $d/dx$ of $({a}x + {b})^{{{n}}}$",
            answer=_to_str(result),
            metadata={"a": a, "b": b, "n": n, "expression": _to_str(expr), "derivative": _to_str(result)},
        )

    # ── integral ─────────────────────────────────────────────────────────

    def _integral_easy(self) -> Question:
        n = self.rng.randint(1, 5)
        expr = x**n
        result = sym_integrate(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="integral",
            difficulty="easy",
            question_text=f"Integrate: $\\int {_to_str(expr)} \\, dx$",
            answer=_to_str(result),
            metadata={"expression": _to_str(expr), "integral": _to_str(result)},
        )

    def _integral_medium(self) -> Question:
        a = self.rng.randint(2, 5)
        n = self.rng.randint(1, 4)
        b = self.rng.randint(1, 4)
        m = self.rng.choice([v for v in range(1, 5) if v != n])
        expr = a * x**n + b * x**m
        result = sym_integrate(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="integral",
            difficulty="medium",
            question_text=f"Integrate: $\\int ({_to_str(expr)}) \\, dx$",
            answer=_to_str(result),
            metadata={"a": a, "n": n, "b": b, "m": m, "expression": _to_str(expr), "integral": _to_str(result)},
        )

    def _integral_hard(self) -> Question:
        a = self.rng.randint(2, 4)
        b = self.rng.randint(1, 5)
        n = self.rng.randint(2, 4)
        expr = (a * x + b) ** n
        result = sym_integrate(expr, x)
        return Question(
            id=str(uuid.uuid4()),
            topic="integral",
            difficulty="hard",
            question_text=f"Integrate: $\\int ({a}x + {b})^{{{n}}} \\, dx$",
            answer=_to_str(result),
            metadata={"a": a, "b": b, "n": n, "expression": _to_str(expr), "integral": _to_str(result)},
        )
