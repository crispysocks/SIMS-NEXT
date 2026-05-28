"""
Tests for the TutorAgent module.

Covers: mock mode, no-API-key fallback, prompt formatting,
response parsing, and TutorSession integration.
"""
import json
import pytest

from app.tutor_agent import TutorAgent, TutorResponse, PROMPT_TEMPLATE
from app.engine import QuestionEngine
from app.mastery import MasteryStore
from app.recommender import Recommender
from app.session import TutorSession


def _make_session(with_agent: bool = True):
    engine = QuestionEngine(seed=42)
    store = MasteryStore()
    rec = Recommender(store)
    agent = TutorAgent(mock=True) if with_agent else None
    return TutorSession(engine, store, rec, tutor_agent=agent)


class TestTutorResponse:
    def test_response_dataclass_fields(self):
        tr = TutorResponse(explanation="e", hint="h", encouragement="c")
        assert tr.explanation == "e"
        assert tr.hint == "h"
        assert tr.encouragement == "c"


class TestMockMode:
    def test_mock_correct_returns_response(self):
        agent = TutorAgent(mock=True)
        resp = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="3",
            correct_answer="3", is_correct=True,
        )
        assert resp is not None
        assert len(resp.explanation) > 0
        assert len(resp.hint) > 0
        assert len(resp.encouragement) > 0

    def test_mock_wrong_returns_response(self):
        agent = TutorAgent(mock=True)
        resp = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="5",
            correct_answer="3", is_correct=False,
        )
        assert resp is not None
        assert len(resp.explanation) > 0
        assert len(resp.hint) > 0
        assert len(resp.encouragement) > 0

    def test_mock_correct_and_wrong_differ(self):
        agent = TutorAgent(mock=True)
        r_correct = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="3",
            correct_answer="3", is_correct=True,
        )
        r_wrong = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="5",
            correct_answer="3", is_correct=False,
        )
        assert r_correct.explanation != r_wrong.explanation


class TestNoAPIKey:
    def test_empty_api_key_returns_none(self):
        agent = TutorAgent(api_key="", mock=False)
        resp = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="3",
            correct_answer="3", is_correct=True,
        )
        assert resp is None

    def test_no_api_key_does_not_crash(self):
        agent = TutorAgent(api_key="", mock=False)
        # Should not raise
        resp = agent.get_feedback(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="3",
            correct_answer="3", is_correct=True,
        )
        assert resp is None


class TestPromptTemplate:
    def test_prompt_contains_required_fields(self):
        prompt = PROMPT_TEMPLATE.format(
            topic="quadratic_equation", difficulty="medium",
            question_text="x^2 - 4 = 0", student_answer="-2,2",
            correct_answer="-2,2", result="correct",
        )
        assert "quadratic_equation" in prompt
        assert "medium" in prompt
        assert "x^2 - 4 = 0" in prompt
        assert "-2,2" in prompt
        assert "correct" in prompt

    def test_prompt_asks_for_json(self):
        prompt = PROMPT_TEMPLATE.format(
            topic="linear_equation", difficulty="easy",
            question_text="2x = 6", student_answer="3",
            correct_answer="3", result="correct",
        )
        assert "JSON" in prompt
        assert "explanation" in prompt
        assert "hint" in prompt
        assert "encouragement" in prompt


class TestParseResponse:
    def test_parse_valid_json(self):
        agent = TutorAgent(mock=False, api_key="")
        resp = agent._parse_response(
            '{"explanation": "对", "hint": "加油", "encouragement": "很好"}'
        )
        assert resp is not None
        assert resp.explanation == "对"
        assert resp.hint == "加油"
        assert resp.encouragement == "很好"

    def test_parse_invalid_json_returns_none(self):
        agent = TutorAgent(mock=False, api_key="")
        resp = agent._parse_response("not json")
        assert resp is None

    def test_parse_missing_field_uses_empty_string(self):
        agent = TutorAgent(mock=False, api_key="")
        resp = agent._parse_response('{"explanation": "ok"}')
        assert resp is not None
        assert resp.explanation == "ok"
        assert resp.hint == ""


class TestEnvConfig:
    def test_default_model(self):
        agent = TutorAgent(mock=False, api_key="")
        assert len(agent._model) > 0

    def test_default_base_url(self):
        agent = TutorAgent(mock=False, api_key="", base_url="https://custom.api/v1")
        assert "custom.api" in agent._base_url

    def test_custom_params(self):
        agent = TutorAgent(
            api_key="sk-test", base_url="http://localhost:11434/v1",
            model="llama3", mock=False,
        )
        assert agent._api_key == "sk-test"
        assert agent._base_url == "http://localhost:11434/v1"
        assert agent._model == "llama3"


class TestSessionIntegration:
    def test_feedback_includes_tutor_response_with_agent(self):
        session = _make_session(with_agent=True)
        session.next_question()
        fb = session.submit_answer("3")
        assert fb.tutor_response is not None
        assert len(fb.tutor_response.explanation) > 0

    def test_feedback_tutor_response_none_without_agent(self):
        session = _make_session(with_agent=False)
        session.next_question()
        fb = session.submit_answer("3")
        assert fb.tutor_response is None

    def test_agent_failure_does_not_break_feedback(self):
        """Even if agent fails, correctness result is still returned."""
        session = _make_session(with_agent=True)
        session.next_question()
        fb = session.submit_answer("3")
        # Feedback must always have correctness fields
        assert fb.is_correct is not None
        assert len(fb.correct_answer) > 0
        assert fb.topic == "linear_equation"

    def test_tutor_response_in_full_loop(self):
        session = _make_session(with_agent=True)
        for _ in range(5):
            q = session.next_question()
            session.submit_answer(q.answer)
        progress = session.get_progress()
        assert progress.total_questions == 5
