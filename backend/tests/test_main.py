"""
Unit Tests — Online Exam Proctoring System
Covers: API endpoints, proctoring engine, edge cases
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base
from models import Exam, Submission

# ── Test DB setup ──────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_proctoring.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


from main import get_db
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ── Exam Endpoints ─────────────────────────────────────────────────────────────

class TestCreateExam:
    def test_create_exam_success(self):
        r = client.post("/exams/", json={"title": "Python 101", "duration": 60})
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Python 101"
        assert data["duration"] == 60
        assert "id" in data

    def test_create_exam_zero_duration(self):
        r = client.post("/exams/", json={"title": "Bad Exam", "duration": 0})
        assert r.status_code == 422

    def test_create_exam_negative_duration(self):
        r = client.post("/exams/", json={"title": "Bad Exam", "duration": -5})
        assert r.status_code == 422

    def test_create_exam_empty_title(self):
        r = client.post("/exams/", json={"title": "", "duration": 30})
        assert r.status_code == 422

    def test_list_exams_empty(self):
        r = client.get("/exams/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_exams_populated(self):
        client.post("/exams/", json={"title": "Exam A", "duration": 30})
        client.post("/exams/", json={"title": "Exam B", "duration": 45})
        r = client.get("/exams/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_exam_not_found(self):
        r = client.get("/exams/999")
        assert r.status_code == 404


# ── Submission Endpoints ───────────────────────────────────────────────────────

class TestSubmissions:
    def _create_exam(self, duration=60):
        r = client.post("/exams/", json={"title": "Test Exam", "duration": duration})
        return r.json()["id"]

    def test_clean_submission(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "alice",
            "answers": {"q1": "def foo(): pass", "q2": "return 42"},
            "time_taken_seconds": 2000,
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is False
        assert data["flag_reasons"] == []

    def test_copy_paste_frontend_flag(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "bob",
            "answers": {"q1": "some answer", "q2": "another answer"},
            "time_taken_seconds": 1800,
            "paste_detected": True
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert "COPY_PASTE_DETECTED" in data["flag_reasons"]

    def test_copy_paste_identical_answers(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "charlie",
            "answers": {"q1": "def add(a,b): return a+b", "q2": "def add(a,b): return a+b"},
            "time_taken_seconds": 1800,
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert "COPY_PASTE_DETECTED" in data["flag_reasons"]

    def test_fast_submission_flagged(self):
        eid = self._create_exam(duration=60)  # 3600s
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "diana",
            "answers": {"q1": "quick guess"},
            "time_taken_seconds": 30,  # way too fast
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert any("FAST" in f for f in data["flag_reasons"])

    def test_overtime_flagged(self):
        eid = self._create_exam(duration=60)
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "eve",
            "answers": {"q1": "answer"},
            "time_taken_seconds": 4000,  # > 60min * 110%
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert any("OVERTIME" in f or "INACTIVITY" in f for f in data["flag_reasons"])

    def test_blank_submission_flagged(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "frank",
            "answers": {"q1": "", "q2": "   "},
            "time_taken_seconds": 1000,
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert "BLANK_SUBMISSION" in data["flag_reasons"]

    def test_submit_nonexistent_exam(self):
        r = client.post("/exams/9999/submit", json={
            "user_name": "ghost",
            "answers": {"q1": "answer"},
        })
        assert r.status_code == 404

    def test_submit_empty_username(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "",
            "answers": {"q1": "answer"},
        })
        assert r.status_code == 422

    def test_list_flagged_only(self):
        eid = self._create_exam()
        # Clean submission
        client.post(f"/exams/{eid}/submit", json={
            "user_name": "clean",
            "answers": {"q1": "unique answer 1", "q2": "unique answer 2"},
            "time_taken_seconds": 2000,
            "paste_detected": False
        })
        # Flagged submission
        client.post(f"/exams/{eid}/submit", json={
            "user_name": "cheat",
            "answers": {"q1": "same", "q2": "same"},
            "time_taken_seconds": 2000,
            "paste_detected": True
        })
        r = client.get("/submissions/?flagged_only=true")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["user_name"] == "cheat"


# ── Health Check ───────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ── Tab-switch Detection ───────────────────────────────────────────────────────

class TestTabSwitchDetection:
    def _create_exam(self):
        r = client.post("/exams/", json={"title": "Tab Test Exam", "duration": 60})
        return r.json()["id"]

    def test_few_tab_switches_not_flagged(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "careful_user",
            "answers": {"q1": "unique answer here"},
            "time_taken_seconds": 2000,
            "paste_detected": False,
            "tab_switch_count": 2   # below threshold of 3
        })
        assert r.status_code == 201
        data = r.json()
        assert not any("FOCUS_LOSS" in f for f in data["flag_reasons"])

    def test_many_tab_switches_flagged(self):
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "suspicious_user",
            "answers": {"q1": "answer"},
            "time_taken_seconds": 2000,
            "paste_detected": False,
            "tab_switch_count": 5   # above threshold
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert any("FOCUS_LOSS" in f for f in data["flag_reasons"])

    def test_exactly_three_tab_switches_flagged(self):
        """Boundary test: exactly 3 switches should trigger flag"""
        eid = self._create_exam()
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "boundary_user",
            "answers": {"q1": "some answer"},
            "time_taken_seconds": 2000,
            "paste_detected": False,
            "tab_switch_count": 3
        })
        assert r.status_code == 201
        data = r.json()
        assert data["suspicious"] is True
        assert any("FOCUS_LOSS" in f for f in data["flag_reasons"])


# ── Submission Response Schema ─────────────────────────────────────────────────

class TestResponseSchema:
    def test_clean_submission_has_no_audit_log(self):
        r = client.post("/exams/", json={"title": "Schema Exam", "duration": 60})
        eid = r.json()["id"]
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "clean_schema_user",
            "answers": {"q1": "good unique answer", "q2": "another unique answer"},
            "time_taken_seconds": 2000,
            "paste_detected": False,
            "tab_switch_count": 0
        })
        assert r.status_code == 201
        data = r.json()
        assert "audit_log" in data
        assert data["audit_log"] is None  # no audit log for clean submissions

    def test_submission_response_includes_all_fields(self):
        r = client.post("/exams/", json={"title": "Fields Exam", "duration": 30})
        eid = r.json()["id"]
        r = client.post(f"/exams/{eid}/submit", json={
            "user_name": "field_tester",
            "answers": {"q1": "my answer"},
            "time_taken_seconds": 800,
            "paste_detected": False
        })
        assert r.status_code == 201
        data = r.json()
        for field in ["id", "exam_id", "user_name", "suspicious", "flag_reasons", "time_taken_seconds", "audit_log"]:
            assert field in data, f"Missing field: {field}"
