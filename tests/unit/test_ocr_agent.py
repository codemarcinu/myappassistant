import pytest

from backend.agents.ocr_agent import OCRAgent, OCRAgentInput


@pytest.mark.asyncio
async def test_ocr_agent_image_success(monkeypatch):
    agent = OCRAgent()
    monkeypatch.setattr(
        "backend.agents.ocr_agent.process_image_file", lambda x: "mocked text"
    )
    input_data = OCRAgentInput(file_bytes=b"abc", file_type="image/png")
    response = await agent.process(input_data)
    assert response.success
    assert response.data["text"] == "mocked text"
