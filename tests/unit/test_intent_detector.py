import json
from unittest.mock import patch

import pytest

from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.interfaces import MemoryContext
from backend.agents.tools.tools import recognize_intent


@pytest.mark.asyncio
async def test_detect_recipe_intent():
    detector = SimpleIntentDetector()
    context = MemoryContext(session_id="test")
    expected_intent = "food_conversation"
    mock_response = {"message": {"content": json.dumps({"intent": expected_intent})}}

    async def mock_chat(*args, **kwargs):
        return mock_response

    with patch("src.backend.core.llm_client.llm_client.chat", new=mock_chat):
        intent = await detector.detect_intent("please give me a cake recipe", context)
        assert intent.type == expected_intent


@pytest.mark.asyncio
async def test_detect_add_to_list_intent():
    detector = SimpleIntentDetector()
    context = MemoryContext(session_id="test")
    expected_intent = "shopping_conversation"
    mock_response = {"message": {"content": json.dumps({"intent": expected_intent})}}

    async def mock_chat(*args, **kwargs):
        return mock_response

    with patch("src.backend.core.llm_client.llm_client.chat", new=mock_chat):
        intent = await detector.detect_intent("add eggs to shopping", context)
        assert intent.type == expected_intent


@pytest.mark.asyncio
async def test_detect_unknown_intent():
    detector = SimpleIntentDetector()
    context = MemoryContext(session_id="test")
    expected_intent = "rag"
    mock_response = {"message": {"content": json.dumps({"intent": expected_intent})}}

    async def mock_chat(*args, **kwargs):
        return mock_response

    with patch("src.backend.core.llm_client.llm_client.chat", new=mock_chat):
        intent = await detector.detect_intent(
            "random text that doesn't match any intent", context
        )
        assert intent.type == expected_intent
