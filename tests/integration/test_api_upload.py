import io
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)


def create_dummy_image_bytes() -> bytes:
    """Tworzy prosty obraz PNG w pamięci i zwraca jego bajty."""
    img = Image.new("RGB", (100, 30), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@patch("backend.api.upload.Orchestrator.process_file", new_callable=AsyncMock)
def test_upload_endpoint_image(mock_process_file):
    """Testuje endpoint /upload z plikiem obrazu."""
    mock_process_file.return_value = {"response": "File processed successfully"}
    image_bytes = create_dummy_image_bytes()
    files = {"file": ("test.png", image_bytes, "image/png")}
    data = {"session_id": "test-session"}
    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert "response" in response_data
    assert response_data["response"] == "File processed successfully"
