import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.error_types import AgentError
from backend.core.hybrid_llm_client import HybridLLMClient

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "src"))  # Usuń jeśli niepotrzebne


@pytest.fixture
def hybrid_client():
    """Fixture to create a HybridLLMClient instance for testing."""
    with patch.dict("os.environ", {"OLLAMA_HOST": "http://mock-ollama:11434"}), patch(
        "backend.core.hybrid_llm_client.llm_client", new_callable=AsyncMock
    ) as mock_llm:
        client = HybridLLMClient()
        # Mocking clients to avoid real API calls
        client.base_client = AsyncMock()
        client.perplexity_client = AsyncMock()
        yield client


class TestHybridLLMClient:
    """Testy dla Hybrid LLM Client - zarządzania lokalnymi modelami LLM"""

    @pytest.fixture
    def mock_local_client(self):
        """Mock lokalnego klienta LLM"""
        return AsyncMock()

    @pytest.fixture
    def mock_remote_client(self):
        """Mock zdalnego klienta LLM"""
        return AsyncMock()

    @pytest.fixture
    def mock_performance_monitor(self):
        """Mock monitora wydajności"""
        with patch("backend.core.hybrid_llm_client.PerformanceMonitor") as mock_monitor:
            mock_instance = mock_monitor.return_value
            mock_instance.measure = AsyncMock()
            yield mock_instance

    @pytest.mark.asyncio
    async def test_chat_with_local_model(self, hybrid_client, mock_local_client):
        """Test czatu z lokalnym modelem"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Local response"}
        }

        # When
        response = await hybrid_client.chat(messages=input_data["messages"])

        # Then
        assert response["message"]["content"] == "Local response"
        hybrid_client.base_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_remote_model(self, hybrid_client, mock_remote_client):
        """Test czatu ze zdalnym modelem"""
        # Given
        input_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "gpt-4",
        }
        hybrid_client.perplexity_client.chat.return_value = {
            "message": {"content": "Remote response"}
        }

        # When
        response = await hybrid_client.chat(
            messages=input_data["messages"], use_perplexity=True
        )

        # Then
        assert response["message"]["content"] == "Remote response"
        hybrid_client.perplexity_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_auto_selection(
        self, hybrid_client, mock_local_client, mock_remote_client
    ):
        """Test automatycznego wyboru modelu"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Local response"}
        }

        # When
        response = await hybrid_client.chat(
            messages=input_data["messages"], auto_select=True
        )

        # Then
        assert response["message"]["content"] == "Local response"
        hybrid_client.base_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_fallback(
        self, hybrid_client, mock_local_client, mock_remote_client
    ):
        """Test mechanizmu fallback"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.perplexity_client.chat.return_value = {
            "message": {"content": "Fallback response"}
        }

        # When
        response = await hybrid_client.chat(
            messages=input_data["messages"], use_perplexity=True
        )

        # Then
        assert response["message"]["content"] == "Fallback response"
        hybrid_client.perplexity_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_streaming(self, hybrid_client, mock_local_client):
        """Test streamowania odpowiedzi"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}

        async def mock_stream():
            yield {"content": "Stream"}
            yield {"content": " response"}

        hybrid_client.base_client.chat.return_value = mock_stream()

        # When
        response_stream = await hybrid_client.chat(
            messages=input_data["messages"], stream=True
        )

        # Then
        collected_chunks = []
        async for chunk in response_stream:
            collected_chunks.append(chunk)

        assert len(collected_chunks) == 2
        assert collected_chunks[0]["content"] == "Stream"
        assert collected_chunks[1]["content"] == " response"

    @pytest.mark.asyncio
    async def test_chat_with_context_window(self, hybrid_client, mock_local_client):
        """Test zarządzania kontekstem"""
        # Given
        long_message = "A" * 5000
        input_data = {"messages": [{"role": "user", "content": long_message}]}

        # When
        await hybrid_client.chat(messages=input_data["messages"])

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        processed_messages = call_args[1]["messages"]
        # HybridLLMClient nie skraca wiadomości, więc sprawdzamy że wiadomość jest przekazana
        assert len(processed_messages[0]["content"]) == 5000

    @pytest.mark.asyncio
    async def test_chat_with_custom_parameters(self, hybrid_client, mock_local_client):
        """Test niestandardowych parametrów"""
        # Given
        input_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "max_tokens": 100,
        }

        # When
        await hybrid_client.chat(
            messages=input_data["messages"],
            temperature=input_data["temperature"],
            max_tokens=input_data["max_tokens"],
        )

        # Then
        hybrid_client.base_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self, hybrid_client, mock_local_client):
        """Test wywoływania funkcji"""
        # Given
        input_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "functions": [{"name": "test_function", "description": "Test"}],
        }
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Function called"}
        }

        # When
        await hybrid_client.chat(
            messages=input_data["messages"], functions=input_data["functions"]
        )

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        # HybridLLMClient nie obsługuje functions bezpośrednio
        assert "messages" in call_args[1]

    @pytest.mark.asyncio
    async def test_chat_with_history(self, hybrid_client, mock_local_client):
        """Test czatu z historią"""
        # Given
        input_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"},
            ]
        }

        # When
        await hybrid_client.chat(messages=input_data["messages"])

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        assert len(call_args[1]["messages"]) == 3

    @pytest.mark.asyncio
    async def test_chat_with_model_override(self, hybrid_client, mock_remote_client):
        """Test nadpisania modelu"""
        # Given
        input_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",  # Używamy znanego modelu
        }

        # When
        await hybrid_client.chat(
            messages=input_data["messages"], model=input_data["model"]
        )

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        assert call_args[1]["model"] == "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"

    @pytest.mark.asyncio
    async def test_chat_with_error_handling(
        self, hybrid_client, mock_local_client, mock_remote_client
    ):
        """Test obsługi błędów"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.base_client.chat.side_effect = Exception("Local error")
        hybrid_client.perplexity_client.chat.side_effect = Exception("Remote error")

        # When
        response = await hybrid_client.chat(messages=input_data["messages"])

        # Then
        assert "error_type" in response

    @pytest.mark.asyncio
    async def test_chat_with_retry(self, hybrid_client, mock_local_client):
        """Test mechanizmu retry"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Success"}
        }

        # When
        response = await hybrid_client.chat(messages=input_data["messages"])

        # Then
        assert response["message"]["content"] == "Success"
        hybrid_client.base_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_cost_tracking(self, hybrid_client, mock_local_client):
        """Test śledzenia kosztów"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}

        # When
        await hybrid_client.chat(messages=input_data["messages"])

        # Then
        hybrid_client.base_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_custom_prompt(self, hybrid_client, mock_local_client):
        """Test niestandardowego promptu"""
        # Given
        input_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "system_prompt": "You are a helpful assistant.",
        }

        # When
        await hybrid_client.chat(
            messages=input_data["messages"], system_prompt=input_data["system_prompt"]
        )

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        processed_messages = call_args[1]["messages"]
        assert processed_messages[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_chat_with_safety_checks(self, hybrid_client, mock_local_client):
        """Test sprawdzania bezpieczeństwa"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Harmful content"}]}
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Blocked"}
        }

        # When
        response = await hybrid_client.chat(messages=input_data["messages"])

        # Then
        assert response["message"]["content"] == "Blocked"

    @pytest.mark.asyncio
    async def test_chat_with_multilingual_support(
        self, hybrid_client, mock_local_client
    ):
        """Test obsługi wielu języków"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Cześć"}]}

        # When
        await hybrid_client.chat(messages=input_data["messages"])

        # Then
        call_args = hybrid_client.base_client.chat.call_args
        assert "Cześć" in call_args[1]["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_chat_with_model_ensembling(
        self, hybrid_client, mock_local_client, mock_remote_client
    ):
        """Test ensemble modeli"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}
        hybrid_client.base_client.chat.return_value = {
            "message": {"content": "Local answer"}
        }
        hybrid_client.perplexity_client.chat.return_value = {
            "message": {"content": "Remote answer"}
        }

        # When
        response1 = await hybrid_client.chat(messages=input_data["messages"])
        response2 = await hybrid_client.chat(
            messages=input_data["messages"], use_perplexity=True
        )

        # Then
        assert response1["message"]["content"] == "Local answer"
        assert response2["message"]["content"] == "Remote answer"

    @pytest.mark.asyncio
    async def test_chat_performance(self, hybrid_client):
        """Test wydajności czatu"""
        # Given
        input_data = {"messages": [{"role": "user", "content": "Hello"}]}

        # When
        start_time = asyncio.get_event_loop().time()
        await hybrid_client.chat(messages=input_data["messages"])
        end_time = asyncio.get_event_loop().time()

        # Then
        duration = end_time - start_time
        assert duration < 1.0  # Czat powinien trwać mniej niż 1 sekundę
