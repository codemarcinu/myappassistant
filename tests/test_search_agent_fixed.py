import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.search_agent import SearchAgent
from backend.agents.interfaces import AgentResponse
from backend.core.vector_store import VectorStore
from backend.core.llm_client import LLMClient

@pytest.mark.asyncio
async def test_search_agent():
    """Test that SearchAgent can handle basic search queries"""
    # Mock the dependencies
    mock_vector_store = MagicMock(spec=VectorStore)
    mock_llm_client = MagicMock(spec=LLMClient)
    
    # Create search agent with mocked dependencies
    agent = SearchAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client
    )
    
    # Mock the perplexity client
    mock_perplexity = MagicMock()
    mock_perplexity.search = AsyncMock(
        return_value={
            "success": True,
            "content": "Python jest językiem programowania wysokiego poziomu.",
        }
    )
    
    # Replace the perplexity client in the agent
    with patch("backend.agents.search_agent.perplexity_client", mock_perplexity):
        # Process a query
        result = await agent.process({"query": "co to jest Python?", "model": "gemma3:12b"})
        
        # Verify the result
        assert result.success is True
        assert result.text_stream is not None
        
        # Validate the streaming content
        response_text = ""
        async for chunk in result.text_stream:
            response_text += chunk
        
        assert "Python" in response_text

@pytest.mark.asyncio
async def test_search_agent_empty_query():
    """Test that SearchAgent handles empty queries properly"""
    # Mock the dependencies
    mock_vector_store = MagicMock(spec=VectorStore)
    mock_llm_client = MagicMock(spec=LLMClient)
    
    # Create search agent with mocked dependencies
    agent = SearchAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client
    )
    
    # Process an empty query
    result = await agent.process({"query": "", "model": "gemma3:12b"})
    
    # Verify the result
    assert result.success is False
    assert "potrzebuję zapytania" in result.text.lower()

@pytest.mark.asyncio
async def test_search_agent_api_error():
    """Test that SearchAgent handles API errors gracefully"""
    # Mock the dependencies
    mock_vector_store = MagicMock(spec=VectorStore)
    mock_llm_client = MagicMock(spec=LLMClient)
    
    # Create search agent with mocked dependencies
    agent = SearchAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client
    )
    
    # Mock the perplexity client
    mock_perplexity = MagicMock()
    mock_perplexity.search = AsyncMock(
        return_value={
            "success": False,
            "error": "API error",
            "content": "",
        }
    )
    
    # Replace the perplexity client in the agent
    with patch("backend.agents.search_agent.perplexity_client", mock_perplexity):
        # Process a query
        result = await agent.process({"query": "co to jest Python?", "model": "gemma3:12b"})
        
        # Verify the result is still successful (as the agent has fallback handling)
        assert result.success is True
        
        # Validate the streaming content contains error message
        response_text = ""
        async for chunk in result.text_stream:
            response_text += chunk
        
        assert "Błąd" in response_text

@pytest.mark.asyncio
async def test_search_agent_with_duckduckgo_fallback():
    """Test that SearchAgent falls back to DuckDuckGo when Perplexity fails"""
    # Mock the dependencies
    mock_vector_store = MagicMock(spec=VectorStore)
    mock_llm_client = MagicMock(spec=LLMClient)
    
    # Create search agent with mocked dependencies
    agent = SearchAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client
    )
    
    # Mock the perplexity client to fail
    mock_perplexity = MagicMock()
    mock_perplexity.search = AsyncMock(
        return_value={
            "success": False,
            "error": "API error",
            "content": "",
        }
    )
    
    # Mock the DuckDuckGo search method
    mock_duckduckgo_result = {
        "success": True,
        "content": "Python to język programowania wysokiego poziomu.",
        "source": "duckduckgo",
    }
    
    # Replace the clients in the agent
    with patch("backend.agents.search_agent.perplexity_client", mock_perplexity):
        with patch.object(agent, "_duckduckgo_search") as mock_duckduckgo:
            mock_duckduckgo.return_value = mock_duckduckgo_result
            
            # Process a query with use_perplexity=False to force DuckDuckGo
            result = await agent.process({
                "query": "co to jest Python?", 
                "model": "gemma3:12b",
                "use_perplexity": False
            })
            
            # Verify the result
            assert result.success is True
            
            # Validate the streaming content
            response_text = ""
            async for chunk in result.text_stream:
                response_text += chunk
            
            assert "Python" in response_text
            mock_duckduckgo.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-v", "test_search_agent_fixed.py"]) 