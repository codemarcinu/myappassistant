from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.backend.main import app  # Import main FastAPI instance

client = TestClient(app)


@pytest.fixture(scope="module")
def test_app():
    # Setup test database, mock external services if needed
    yield client
    # Cleanup after tests


def test_full_orchestration_flow(test_app):
    # Simulate API request that uses the orchestrator
    response = test_app.post(
        "/api/agents/execute",
        json={"task": "Find a recipe for spaghetti", "session_id": "test_session_123"},
    )
    assert response.status_code == 200
    assert "spaghetti" in (response.json().get("response") or "").lower()


def test_add_item_to_list_flow(test_app):
    response = test_app.post(
        "/api/agents/execute",
        json={"task": "add milk to shopping list", "session_id": "test_session_123"},
    )
    assert response.status_code == 200
    assert "milk" in (response.json().get("response") or "").lower()


def test_invalid_input_query(test_app):
    response = test_app.post(
        "/api/agents/execute", json={"task": "", "session_id": "test_session"}
    )  # Empty task
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "error" in response.json()


@patch(
    "backend.infrastructure.database.database.get_db",
    side_effect=Exception("DB connection error"),
)
def test_database_connection_failure(mock_get_db, test_app):
    # Simulate DB connection failure
    response = test_app.post(
        "/api/agents/process_query", json={"task": "some query", "session_id": "test_session"}
    )
    assert response.status_code == 500
    assert response.json()["error_code"] == "INTERNAL_SERVER_ERROR"


def test_error_handling_value_error(test_app):
    response = test_app.get("/raise_error?type=value")
    assert response.status_code == 500
    assert "error" in response.json()
    assert response.json()["error"]["message"] == "Test ValueError"


def test_error_handling_key_error(test_app):
    response = test_app.get("/raise_error?type=key")
    assert response.status_code == 500
    assert "error" in response.json()
    assert "Missing required field" in response.json()["error"]["message"]


def test_error_handling_custom_exception(test_app):
    response = test_app.get("/raise_error?type=custom")
    assert response.status_code == 500
    assert "error" in response.json()
    assert "Test custom exception" in response.json()["error"]["message"]


def test_error_handling_http_exception(test_app):
    response = test_app.get("/raise_error?type=http")
    assert response.status_code == 418
    assert response.json()["detail"] == "I'm a teapot"


def test_error_handling_generic_exception(test_app):
    response = test_app.get("/raise_error?type=other")
    assert response.status_code == 500
    assert "error" in response.json()
    assert "Unexpected error" in response.json()["error"]["message"]
