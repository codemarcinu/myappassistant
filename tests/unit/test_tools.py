from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.tools.tools import extract_entities, recognize_intent


@pytest.mark.asyncio
async def test_recognize_intent():
    with patch("backend.agents.tools.tools.llm_client") as mock_llm_client:
        mock_llm_client.chat = AsyncMock(
            return_value={"message": {"content": '{"intent": "TEST"}'}}
        )

        result = await recognize_intent("test prompt")
        assert result == '{"intent": "TEST"}'


@pytest.mark.asyncio
async def test_extract_entities():
    with patch("backend.agents.tools.tools.llm_client") as mock_llm_client:
        mock_llm_client.chat = AsyncMock(
            return_value={"message": {"content": '{"entity": "test"}'}}
        )

        result = await extract_entities("test prompt")
        assert result == '{"entity": "test"}'
