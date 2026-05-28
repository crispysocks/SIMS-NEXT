"""
API tests using FastAPI TestClient.

Test the 5 endpoints: question, answer, mastery, progress, reset.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app, _create_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session() -> None:
    """Reset the singleton session before each test."""
    global _session
    from app import main
    main._session = _create_session()


class TestQuestionEndpoint:
    def test_get_question_returns_valid_structure(self):
        resp = client.get("/api/question")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "topic" in data
        assert "difficulty" in data
        assert "question_text" in data
        # answer must NOT be in response
        assert "answer" not in data
        assert "metadata" not in data

    def test_question_topic_is_valid(self):
        resp = client.get("/api/question")
        assert resp.json()["topic"] in (
            "linear_equation", "quadratic_equation", "factoring", "derivative", "integral"
        )

    def test_question_difficulty_is_valid(self):
        resp = client.get("/api/question")
        assert resp.json()["difficulty"] in ("easy", "medium", "hard")

    def test_two_questions_have_different_ids(self):
        q1 = client.get("/api/question").json()
        q2 = client.get("/api/question").json()
        assert q1["id"] != q2["id"]


class TestAnswerEndpoint:
    def test_submit_answer_returns_result(self):
        client.get("/api/question")
        resp = client.post("/api/answer", json={"student_answer": "3"})
        assert resp.status_code == 200
        data = resp.json()
        assert "is_correct" in data
        assert "correct_answer" in data
        assert "student_answer" in data

    def test_submit_without_question_returns_400(self):
        resp = client.post("/api/answer", json={"student_answer": "3"})
        assert resp.status_code == 400
        assert "No active question" in resp.json()["detail"]

    def test_submit_correct_answer(self):
        q = client.get("/api/question").json()
        # We need the correct answer to submit it, but the API doesn't expose it.
        # Use the internal session to get the answer, then submit via API.
        from app.main import _session
        correct = _session._state.current_question.answer
        resp = client.post("/api/answer", json={"student_answer": correct})
        assert resp.status_code == 200
        assert resp.json()["is_correct"] is True

    def test_submit_empty_answer(self):
        client.get("/api/question")
        resp = client.post("/api/answer", json={"student_answer": ""})
        assert resp.status_code == 200
        assert resp.json()["is_correct"] is False

    def test_answer_clears_active_question(self):
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        # Submitting again should be 400 — no active question
        resp = client.post("/api/answer", json={"student_answer": "3"})
        assert resp.status_code == 400


class TestMasteryEndpoint:
    def test_get_mastery_returns_list(self):
        # Asking a question triggers recommender, which populates all 5 topics
        client.get("/api/question")
        resp = client.get("/api/mastery")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_mastery_state_structure(self):
        client.get("/api/question")
        resp = client.get("/api/mastery")
        s = resp.json()[0]
        assert "topic_id" in s
        assert "mastery" in s
        assert "variance" in s
        assert "alpha" in s
        assert "beta" in s
        assert 0.0 <= s["mastery"] <= 1.0
        assert 0.0 <= s["variance"] <= 1.0

    def test_mastery_updates_after_answer(self):
        # Get initial mastery
        before = client.get("/api/mastery").json()
        # Answer a question
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        after = client.get("/api/mastery").json()
        # At least one topic should have changed
        total_attempts_before = sum(s["total_attempts"] for s in before)
        total_attempts_after = sum(s["total_attempts"] for s in after)
        assert total_attempts_after > total_attempts_before


class TestProgressEndpoint:
    def test_get_progress_returns_full_snapshot(self):
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        resp = client.get("/api/progress")
        assert resp.status_code == 200
        data = resp.json()
        assert "mastery_states" in data
        assert "total_questions" in data
        assert "correct_count" in data
        assert "accuracy" in data
        assert "correct_streak" in data
        assert "wrong_streak" in data
        assert data["total_questions"] == 1

    def test_accuracy_calculation(self):
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "correct_answer_1"})
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        p = client.get("/api/progress").json()
        assert p["total_questions"] == 2
        assert 0.0 <= p["accuracy"] <= 1.0


class TestResetEndpoint:
    def test_reset_returns_ok(self):
        resp = client.post("/api/reset")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_reset_clears_history(self):
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        client.post("/api/reset")
        p = client.get("/api/progress").json()
        assert p["total_questions"] == 0
        assert p["accuracy"] == 0.0

    def test_reset_resets_mastery(self):
        client.get("/api/question")
        client.post("/api/answer", json={"student_answer": "3"})
        client.post("/api/reset")
        states = client.get("/api/mastery").json()
        for s in states:
            assert s["alpha"] == 3.0
            assert s["beta"] == 3.0
            assert s["total_attempts"] == 0


class TestFullAPIFlow:
    def test_question_answer_progress_cycle(self):
        # Get question
        q = client.get("/api/question").json()
        assert q["question_text"]
        # Get answer from internal session
        from app.main import _session
        correct = _session._state.current_question.answer
        # Submit correct answer
        r = client.post("/api/answer", json={"student_answer": correct}).json()
        assert r["is_correct"] is True
        # Check progress
        p = client.get("/api/progress").json()
        assert p["total_questions"] == 1

    def test_many_rapid_cycles(self):
        for i in range(30):
            q = client.get("/api/question").json()
            from app.main import _session
            correct = _session._state.current_question.answer
            client.post("/api/answer", json={"student_answer": correct if i % 2 == 0 else "wrong"})
        p = client.get("/api/progress").json()
        assert p["total_questions"] == 30


class TestDeterministicAPI:
    """Same seed + same answer sequence → identical trajectory."""

    def test_deterministic_sessions(self):
        def run_session():
            import app.main as m
            m._session = _create_session()
            results = []
            for _ in range(10):
                q = client.get("/api/question").json()
                from app.main import _session
                correct = _session._state.current_question.answer
                r = client.post("/api/answer", json={"student_answer": correct}).json()
                results.append((q["question_text"], r["is_correct"]))
            return results

        r1 = run_session()
        r2 = run_session()
        assert r1 == r2
