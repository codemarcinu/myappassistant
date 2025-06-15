import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.skip(reason="Wymaga ręcznego uruchomienia serwera FastAPI")
@pytest.mark.asyncio
async def test_upload_endpoint():
    async with AsyncClient(base_url="http://localhost:8000") as ac:
        files = {"file": ("test.png", b"fakebytes", "image/png")}
        response = await ac.post("/api/v1/upload", files=files)
        assert response.status_code == 200
        assert "text" in response.json()
