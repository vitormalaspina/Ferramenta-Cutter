import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ffmpeg_available" in data
    assert "ytdlp_version" in data
    assert "disk_space_bytes" in data


def test_analyze_empty_url():
    response = client.post("/api/analyze", json={"url": ""})
    assert response.status_code == 400


def test_analyze_invalid_domain():
    response = client.post("/api/analyze", json={"url": "https://example.com/not-youtube"})
    assert response.status_code == 400


def test_list_jobs_empty_or_existing():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_job_not_found():
    response = client.get("/api/jobs/non-existent-uuid-12345")
    assert response.status_code == 404

