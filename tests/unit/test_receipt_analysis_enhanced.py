"""
Testy dla ulepszonego ReceiptAnalysisAgent z obsługą polskich paragonów.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.receipt_analysis_agent import ReceiptAnalysisAgent


class TestReceiptAnalysisAgentEnhanced:
    """Testy dla ulepszonego ReceiptAnalysisAgent."""

    @pytest.fixture
    def agent(self):
        """Tworzy instancję ReceiptAnalysisAgent do testów."""
        return ReceiptAnalysisAgent()

    @pytest.fixture
    def mock_llm_response(self):
        """Mock odpowiedzi LLM dla testów."""
        return {
            "message": {
                "content": """
                {
                    "store_name": "Lidl",
                    "store_address": "ul. Testowa 1, Warszawa",
                    "date": "2024-01-15",
                    "time": "14:30",
                    "receipt_number": "12345",
                    "items": [
                        {
                            "name": "Mleko 3.2%",
                            "original_name": "Mleko 3.2% 1L",
                            "product_code": "123456",
                            "quantity": 1,
                            "unit": "szt",
                            "unit_price": 4.99,
                            "total_price": 4.99,
                            "vat_rate": "A",
                            "discount": 0,
                            "category": "Nabiał"
                        }
                    ],
                    "subtotals": {
                        "vat_a_amount": 0.93,
                        "vat_b_amount": 0,
                        "vat_c_amount": 0,
                        "total_discount": 0
                    },
                    "total_amount": 4.99,
                    "payment_method": "Karta"
                }
                """
            }
        }

    @pytest.mark.asyncio
    async def test_receipt_analysis_lidl_format(self, agent, mock_llm_response):
        """Test analizy paragonu z Lidl."""
        ocr_text = """
        Lidl sp. z.o. o. sp. k.
        2024-01-15 14:30
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Krakers Dobry Chrup 1 * 5,29 5,29 C
        RAZEM PLN 10,28
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=mock_llm_response)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Lidl"
            assert len(result.data["items"]) == 1
            assert result.data["total_amount"] == 4.99
            assert result.data["date"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_receipt_analysis_auchan_format(self, agent):
        """Test analizy paragonu z Auchan."""
        ocr_text = """
        AUCHAN POLSKA SP. Z O.O.
        15.01.2024
        Chleb razowy 1 * 3,50 3,50 A
        Masło 82% 1 * 6,99 6,99 A
        SUMA PLN 10,49
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(
                return_value=None
            )  # Symuluj brak odpowiedzi LLM

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Auchan"
            assert len(result.data["items"]) >= 1
            assert result.data["total_amount"] == 10.49

    @pytest.mark.asyncio
    async def test_receipt_analysis_kaufland_format(self, agent):
        """Test analizy paragonu z Kaufland."""
        ocr_text = """
        KAUFLAND POLSKA MARKETY SP. Z O.O.
        2024-01-15
        Banany 1.5 kg * 3,99/kg 5,99 A
        Jogurt naturalny 400g 1 * 2,49 2,49 A
        RAZEM 8,48 PLN
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Kaufland"
            assert len(result.data["items"]) >= 1
            assert result.data["total_amount"] == 8.48

    @pytest.mark.asyncio
    async def test_receipt_analysis_biedronka_format(self, agent):
        """Test analizy paragonu z Biedronka."""
        ocr_text = """
        JERONIMO MARTINS POLSKA S.A.
        15.01.2024 16:45
        Woda mineralna 1.5L 1 * 1,99 1,99 A
        Chipsy Lays 100g 1 * 4,99 4,99 A
        PROMOCJA -1,00
        SUMA PLN 5,98
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Biedronka"
            assert len(result.data["items"]) >= 1
            assert result.data["total_amount"] == 5.98

    @pytest.mark.asyncio
    async def test_fallback_parser_with_invalid_json(self, agent):
        """Test fallback parser gdy JSON jest nieprawidłowy."""
        ocr_text = """
        Lidl
        15.01.2024
        Mleko 4,99
        Chleb 3,50
        """

        invalid_json_response = {
            "message": {"content": "To nie jest prawidłowy JSON { invalid json }"}
        }

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=invalid_json_response)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Lidl"
            assert len(result.data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_date_normalization(self, agent):
        """Test normalizacji różnych formatów dat."""
        test_cases = [
            ("15.01.2024", "2024-01-15"),
            ("2024-01-15", "2024-01-15"),
            ("15-01-2024", "2024-01-15"),
            ("1.1.2024", "2024-01-01"),
        ]

        for input_date, expected_date in test_cases:
            normalized = agent._normalize_date(input_date)
            assert normalized == expected_date

    @pytest.mark.asyncio
    async def test_data_validation_future_date(self, agent):
        """Test walidacji daty w przyszłości."""
        future_date_data = {
            "store_name": "Test",
            "date": "2030-01-01",
            "items": [],
            "total_amount": 0,
        }

        validated_data = agent._validate_and_fix_data(future_date_data)
        current_date = datetime.now().strftime("%Y-%m-%d")
        assert validated_data["date"] == current_date
        assert "validation_warnings" in validated_data

    @pytest.mark.asyncio
    async def test_data_validation_price_mismatch(self, agent):
        """Test walidacji niezgodności cen."""
        data_with_mismatch = {
            "store_name": "Test",
            "items": [{"total_price": 5.00}, {"total_price": 3.00}],
            "total_amount": 10.00,  # Różnica 2 PLN
        }

        validated_data = agent._validate_and_fix_data(data_with_mismatch)
        assert "validation_warnings" in validated_data
        assert (
            "Różnica między sumą produktów" in validated_data["validation_warnings"][0]
        )

    @pytest.mark.asyncio
    async def test_empty_ocr_text(self, agent):
        """Test obsługi pustego tekstu OCR."""
        result = await agent.process({"ocr_text": ""})

        assert not result.success
        assert "Brak tekstu OCR do analizy" in result.error

    @pytest.mark.asyncio
    async def test_llm_no_response_fallback(self, agent):
        """Test fallback gdy LLM nie odpowiada."""
        ocr_text = "Lidl 15.01.2024 Mleko 4,99"

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Lidl"

    @pytest.mark.asyncio
    async def test_categorization_error_handling(self, agent):
        """Test obsługi błędów kategoryzacji."""
        ocr_text = "Test paragon"

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

        with patch(
            "backend.agents.receipt_analysis_agent.AgentFactory"
        ) as mock_factory:
            mock_factory_instance = Mock()
            mock_factory_instance.create_agent = Mock(
                side_effect=Exception("Kategoryzacja nie działa")
            )
            mock_factory.return_value = mock_factory_instance

            result = await agent.process({"ocr_text": ocr_text})

            # Proces powinien się zakończyć sukcesem mimo błędu kategoryzacji
            assert result.success

    def test_store_pattern_recognition(self, agent):
        """Test rozpoznawania wzorców sklepów."""
        test_cases = [
            ("LIDL SP. Z O.O.", "Lidl"),
            ("AUCHAN POLSKA", "Auchan"),
            ("KAUFLAND MARKETY", "Kaufland"),
            ("BIEDRONKA JERONIMO", "Biedronka"),
            ("TESCO POLSKA", "Tesco"),
            ("CARREFOUR POLSKA", "Carrefour"),
        ]

        for text, expected_store in test_cases:
            result = agent._fallback_parse(text)
            assert result["store_name"] == expected_store

    def test_product_pattern_recognition(self, agent):
        """Test rozpoznawania wzorców produktów."""
        ocr_text = """
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Chleb razowy 1 * 3,50 3,50 A
        """

        result = agent._fallback_parse(ocr_text)

        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert "name" in item
            assert "total_price" in item
            assert "vat_rate" in item

    @pytest.mark.asyncio
    async def test_complete_receipt_processing_workflow(self, agent, mock_llm_response):
        """Test kompletnego workflow przetwarzania paragonu."""
        ocr_text = """
        Lidl sp. z.o. o. sp. k.
        2024-01-15 14:30
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Chleb razowy 1 * 3,50 3,50 A
        RAZEM PLN 8,49
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=mock_llm_response)

        with patch(
            "backend.agents.receipt_analysis_agent.AgentFactory"
        ) as mock_factory:
            mock_factory_instance = Mock()
            mock_categorization_agent = Mock()
            mock_categorization_agent.process = AsyncMock(
                return_value=AgentResponse(success=True, data={"category": "Nabiał"})
            )
            mock_factory_instance.create_agent = Mock(
                return_value=mock_categorization_agent
            )
            mock_factory.return_value = mock_factory_instance

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data["store_name"] == "Lidl"
            assert result.data["date"] == "2024-01-15"
            assert result.data["total_amount"] == 4.99
            assert len(result.data["items"]) == 1


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_analysis_enhanced.py"])
