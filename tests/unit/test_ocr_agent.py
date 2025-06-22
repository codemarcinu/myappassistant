import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.ocr_agent import OCRAgent, OCRAgentInput
from backend.agents.interfaces import AgentResponse


class TestOCRAgent:
    """Unit tests for OCRAgent with mocked OCR processing."""

    @pytest.fixture
    def sample_image_bytes(self):
        """Sample image bytes for testing."""
        return b"mock_image_data"

    @pytest.fixture
    def sample_pdf_bytes(self):
        """Sample PDF bytes for testing."""
        return b"mock_pdf_data"

    @pytest.mark.asyncio
    async def test_ocr_agent_process_image(self, sample_image_bytes):
        """Test OCRAgent.process with image input."""
        # Create agent and input
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=sample_image_bytes, file_type="image")
        
        # Mock the process_image_file function
        expected_text = "Sample receipt text\nMilk 3.99\nBread 4.50\nTotal 8.49"
        
        with patch('backend.core.ocr.process_image_file', return_value=expected_text):
            # Process the image
            result = await agent.process(input_data)
            
            # Verify the result
            assert isinstance(result, AgentResponse)
            assert result.success is True
            assert result.text == expected_text
            assert result.message == "Pomyślnie wyodrębniono tekst z pliku"
            assert result.metadata == {"file_type": "image"}

    @pytest.mark.asyncio
    async def test_ocr_agent_process_pdf(self, sample_pdf_bytes):
        """Test OCRAgent.process with PDF input."""
        # Create agent and input
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=sample_pdf_bytes, file_type="pdf")
        
        # Mock the process_pdf_file function
        expected_text = "Page 1\nInvoice #12345\nTotal: $123.45\n\nPage 2\nThank you for your business"
        
        with patch('backend.core.ocr.process_pdf_file', return_value=expected_text):
            # Process the PDF
            result = await agent.process(input_data)
            
            # Verify the result
            assert isinstance(result, AgentResponse)
            assert result.success is True
            assert result.text == expected_text
            assert result.message == "Pomyślnie wyodrębniono tekst z pliku"
            assert result.metadata == {"file_type": "pdf"}

    @pytest.mark.asyncio
    async def test_ocr_agent_process_unsupported_file_type(self, sample_image_bytes):
        """Test OCRAgent.process with unsupported file type."""
        # Create agent and input with unsupported file type
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=sample_image_bytes, file_type="docx")
        
        # Process with unsupported file type
        result = await agent.process(input_data)
        
        # Verify the error response
        assert isinstance(result, AgentResponse)
        assert result.success is False
        assert "Nieobsługiwany typ pliku" in result.error
        assert result.text is None

    @pytest.mark.asyncio
    async def test_ocr_agent_process_image_failure(self, sample_image_bytes):
        """Test OCRAgent.process with image processing failure."""
        # Create agent and input
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=sample_image_bytes, file_type="image")
        
        # Mock the process_image_file function to return None (failure)
        with patch('backend.core.ocr.process_image_file', return_value=None):
            # Process the image
            result = await agent.process(input_data)
            
            # Verify the error response
            assert isinstance(result, AgentResponse)
            assert result.success is False
            assert "Nie udało się rozpoznać tekstu z pliku" in result.error
            assert result.text is None

    @pytest.mark.asyncio
    async def test_ocr_agent_process_exception(self, sample_image_bytes):
        """Test OCRAgent.process with exception during processing."""
        # Create agent and input
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=sample_image_bytes, file_type="image")
        
        # Mock the process_image_file function to raise an exception
        with patch('backend.core.ocr.process_image_file', side_effect=Exception("Test error")):
            # Process the image
            result = await agent.process(input_data)
            
            # Verify the error response
            assert isinstance(result, AgentResponse)
            assert result.success is False
            assert "Wystąpił błąd podczas przetwarzania pliku" in result.error
            assert "Test error" in result.error
            assert result.text is None

    @pytest.mark.asyncio
    async def test_ocr_agent_process_dict_input(self, sample_image_bytes):
        """Test OCRAgent.process with dictionary input instead of OCRAgentInput."""
        # Create agent and dictionary input
        agent = OCRAgent()
        input_dict = {
            "file_bytes": sample_image_bytes,
            "file_type": "image"
        }
        
        # Mock the process_image_file function
        expected_text = "Sample receipt text from dictionary input"
        
        with patch('backend.core.ocr.process_image_file', return_value=expected_text):
            # Process with dictionary input
            result = await agent.process(input_dict)
            
            # Verify the result
            assert isinstance(result, AgentResponse)
            assert result.success is True
            assert result.text == expected_text
            assert result.message == "Pomyślnie wyodrębniono tekst z pliku"
            assert result.metadata == {"file_type": "image"}

    @pytest.mark.asyncio
    async def test_ocr_agent_process_invalid_input(self):
        """Test OCRAgent.process with invalid input that fails validation."""
        # Create agent and invalid input (missing required fields)
        agent = OCRAgent()
        invalid_input = {"some_field": "some_value"}
        
        # Process with invalid input
        result = await agent.process(invalid_input)
        
        # Verify the error response
        assert isinstance(result, AgentResponse)
        assert result.success is False
        assert "Błąd walidacji danych wejściowych" in result.error

    @pytest.mark.asyncio
    async def test_ocr_agent_execute(self, sample_image_bytes):
        """Test OCRAgent.execute method."""
        # Create agent
        agent = OCRAgent()
        
        # Create context with file data
        context = {
            "file_bytes": sample_image_bytes,
            "file_type": "image"
        }
        
        # Mock the process method
        mock_response = AgentResponse(
            success=True,
            text="Sample receipt text from execute method",
            message="Pomyślnie wyodrębniono tekst z pliku",
            metadata={"file_type": "image"}
        )
        
        with patch.object(agent, 'process', AsyncMock(return_value=mock_response)) as mock_process:
            # Execute the agent
            result = await agent.execute("Extract text from receipt", context)
            
            # Verify the process method was called with the context
            mock_process.assert_called_once_with(context)
            
            # Verify the result is the same as the mocked response
            assert result == mock_response


if __name__ == "__main__":
    pytest.main(["-v", "test_ocr_agent.py"])
