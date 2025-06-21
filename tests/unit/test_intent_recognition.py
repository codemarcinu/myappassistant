import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from src.backend.agents.tools.tools import recognize_intent

# Ladowanie danych testowych bezposrednio z pliku JSON
TEST_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "test_data.json"
)
with open(TEST_DATA_PATH, "r") as f:
    TEST_DATA = json.load(f)

TEST_DATA = [
    {
        "prompt": "Dodaj paragon z Biedronki z wczoraj: mleko 4.50zł, chleb 3.20zł, masło 6.80zł",
        "intent": "DODAJ_ZAKUPY",
    },
    {
        "prompt": "Ile wydałem w tym miesiącu na nabiał?",
        "intent": "CZYTAJ_PODSUMOWANIE",
    },
    {
        "prompt": "Zmień cenę mleka z ostatniego paragonu na 4.20zł",
        "intent": "UPDATE_ITEM",
    },
    {"prompt": "Usuń masło z paragonu z Biedronki", "intent": "DELETE_ITEM"},
    {"prompt": "Zmień datę paragonu z Lidla na wczoraj", "intent": "UPDATE_PURCHASE"},
    {"prompt": "Usuń paragon z Biedronki z 10 maja", "intent": "DELETE_PURCHASE"},
    {"prompt": "Zeskanuj ten paragon", "intent": "PROCESS_FILE"},
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_prompt, expected_intent",
    [(item["prompt"], item["intent"]) for item in TEST_DATA],
)
async def test_intent_recognition_with_mock(user_prompt, expected_intent):
    # Tworzymy mocka odpowiedzi, ktora bedzie symulowac odpowiedz z LLM
    mock_llm_response = {
        "message": {"content": json.dumps({"intent": expected_intent})}
    }

    # Uzywamy patch, aby podmienic prawdziwego klienta LLM na naszego mocka
    # Sciezka musi wskazywac na miejsce UZYCIA obiektu, a nie jego definicji
    with patch(
        "src.backend.agents.tools.tools.llm_client.chat",
        new_callable=AsyncMock,
        return_value=mock_llm_response,
    ):
        raw_json_response = await recognize_intent(user_prompt)
        parsed_response = json.loads(raw_json_response)
        assert parsed_response["intent"] == expected_intent
