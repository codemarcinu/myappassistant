from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.backend.agents.base_agent import BaseAgent
from src.backend.agents.interfaces import AgentResponse
from src.backend.api.v2.endpoints.receipts import router
from src.backend.api.v2.exceptions import APIErrorCodes

app = FastAPI()
app.include_router(router)


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True


@pytest.fixture
def mock_ocr_agent_success():
    with patch(
        "src.backend.agents.ocr_agent.OCRAgent.process", new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = AgentResponse(
            success=True,
            text="BIEDRONKA\nData: 2024-06-23\nMleko 4.50zł\nChleb 3.20zł\nRazem: 7.70zł",
            message="Pomyślnie wyodrębniono tekst z pliku",
            metadata={"file_type": "image"},
        )
        yield mock_process


@pytest.mark.asyncio
async def test_upload_receipt_success_image(mock_ocr_agent_success):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        test_image = BytesIO(b"fake image data")
        response = await ac.post(
            "/receipts/upload",
            files={"file": ("receipt.jpg", test_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 200
        assert data["message"] == "Receipt processed successfully"
        assert "text" in data["data"]
        assert "message" in data["data"]
        assert "BIEDRONKA" in data["data"]["text"]


@pytest.mark.asyncio
async def test_upload_receipt_missing_content_type(mock_ocr_agent_success):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/receipts/upload",
            files={
                "file": ("receipt.jpg", b"fake data", "")
            },  # Set content_type to empty string
        )
        assert (
            response.status_code == 400
        )  # FastAPI zwraca 400 dla pustego content_type
        response_json = response.json()
        # FastAPI zwraca błąd walidacji, nie nasz custom error
