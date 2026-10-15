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
    assert data["scope"] == "Africa"


def test_research_validates_question_length():
    response = client.post("/api/research", json={"question": "short"})
    assert response.status_code == 422
