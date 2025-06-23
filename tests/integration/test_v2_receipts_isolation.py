from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.agents.base_agent import BaseAgent
from src.backend.agents.interfaces import AgentResponse
from src.backend.api.v2.endpoints.receipts import router
from src.backend.api.v2.exceptions import APIErrorCodes

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True


def test_upload_receipt_success_image(client, mock_ocr_success):
    test_image = BytesIO(b"fake image data")
    response = client.post(
        "/api/v2/receipts/upload",
        files={"file": ("receipt.jpg", test_image, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Receipt processed successfully",
        "data": {
            "text": "Test receipt text",
            "message": "Pomyślnie wyodrębniono tekst z pliku",
        },
    }


def test_upload_receipt_missing_content_type(client, mock_ocr_success):
    response = client.post(
        "/api/v2/receipts/upload",
        files={
            "file": ("receipt.jpg", b"fake data", "")
        },  # Set content_type to empty string
    )
    assert response.status_code == 400  # FastAPI zwraca 400 dla pustego content_type
    response_json = response.json()
    # FastAPI zwraca błąd walidacji, nie nasz custom error
