import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_upload_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"file": ("test.png", b"fakebytes", "image/png")}
        response = await ac.post("/api/v1/upload", files=files)
        assert response.status_code == 200
