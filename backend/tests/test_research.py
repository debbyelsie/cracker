# pyrefly: ignore[missing-import]
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    assert client.get("/api/health").json()["status"] == "ok"


def test_research_returns_labelled_structured_demo():
    response = client.post("/api/research", json={"question": "What affects small business AI adoption?", "scope": "Africa"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert len(data["findings"]) == 3
    assert data["findings"][0]["evidence"]
    assert "fictional" in data["summary"].lower()
    assert all("fictional" in source["status"].lower() for source in data["sources"])
    assert all(
        "fictional" in evidence["note"].lower()
        for finding in data["findings"]
        for evidence in finding["evidence"]
    )
    assert data["scope"] == "Africa"


def test_research_validates_question_length():
    response = client.post("/api/research", json={"question": "short"})
    assert response.status_code == 422


def test_research_rejects_whitespace_only_question():
    response = client.post("/api/research", json={"question": " " * 20})
    assert response.status_code == 422


def test_research_normalizes_question_scope_and_clarifications():
    response = client.post(
        "/api/research",
        json={
            "question": "  What affects small business AI adoption?  ",
            "scope": "  Canada  ",
            "clarifications": {"focus": "  staff readiness  ", "audience": "   "},
        },
    )
    assert response.status_code == 200
    brief = response.json()
    assert brief["question"] == "What affects small business AI adoption?"
    assert brief["scope"] == "Canada"
    assert brief["clarifications"] == {"focus": "staff readiness"}


def test_research_validates_maximum_question_and_scope_lengths():
    long_question = client.post(
        "/api/research", json={"question": "q" * 501}
    )
    long_scope = client.post(
        "/api/research",
        json={"question": "What affects small business AI adoption?", "scope": "s" * 1001},
    )
    assert long_question.status_code == 422
    assert long_scope.status_code == 422


def test_intake_reflects_question_and_asks_scope_questions():
    response = client.post(
        "/api/research/intake",
        json={"question": "What affects small business AI adoption?"},
    )
    assert response.status_code == 200
    intake = response.json()
    assert "What affects small business AI adoption?" in intake["interpretation"]
    assert {item["id"] for item in intake["questions"]} == {
        "audience",
        "focus",
        "boundaries",
    }
    assert intake["investigation_plan"]


def test_intake_includes_optional_scope_in_interpretation():
    response = client.post(
        "/api/research/intake",
        json={
            "question": "What affects small business AI adoption?",
            "scope": "  Canada  ",
        },
    )
    assert response.status_code == 200
    assert "Canada" in response.json()["interpretation"]


def test_research_returns_detailed_transparent_synthesis_and_scope():
    response = client.post(
        "/api/research",
        json={
            "question": "What affects small business AI adoption?",
            "clarifications": {"focus": "staff readiness"},
        },
    )
    assert response.status_code == 200
    brief = response.json()
    assert "fictional" in brief["detailed_answer"].lower()
    assert "staff readiness" in brief["clarifications"]["focus"]
