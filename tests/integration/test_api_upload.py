import io

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


def test_upload_endpoint_image():
    """Testuje endpoint /upload z plikiem obrazu."""
    image_bytes = create_dummy_image_bytes()
    files = {"file": ("test.png", image_bytes, "image/png")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert data["content_type"] == "image/png"
    # W tym przypadku Tesseract może zwrócić pusty string, co jest ok
    assert isinstance(data["text"], str)
