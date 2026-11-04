from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app


@pytest.fixture()
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as test_client:
        response = test_client.post("/ingest", json={"reset": True})
        assert response.status_code == 200
        yield test_client


def test_health_reports_ready_store(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["chunks"] > 0
    assert body["documents"] == 2
    assert body["llm_provider"] == "offline"


def test_query_returns_answer_citations_and_sources(client: TestClient) -> None:
    response = client.post(
        "/query",
        json={"question": "How many PTO days do employees get?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert "20 days" in body["answer"]
    assert body["citations"]
    assert body["sources"]
    assert body["sources"][0]["cited"] is True
    assert body["sources"][0]["text"]
    assert body["mode"] == "offline-extractive"


def test_query_validation(client: TestClient) -> None:
    response = client.post("/query", json={"question": "   ", "top_k": 3})
    assert response.status_code == 422


def test_sources_endpoint(client: TestClient) -> None:
    response = client.get("/sources")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert {item["source"] for item in body["sources"]} == {"handbook.md", "security.md"}


def test_query_before_ingest_returns_conflict(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app) as empty_client:
        response = empty_client.post("/query", json={"question": "How much PTO?"})

    assert response.status_code == 409
    assert "ingest" in response.json()["hint"].lower()
