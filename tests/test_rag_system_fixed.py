import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import numpy as np
from dataclasses import dataclass

from backend.agents.enhanced_rag_agent import EnhancedRAGAgent
from backend.agents.interfaces import AgentResponse
from backend.core.vector_store import VectorStore

# Definicja klasy DocumentChunk zgodna z rzeczywistą implementacją
@dataclass
class DocumentChunk:
    """Document chunk z testów"""
    id: str
    content: str
    metadata: dict

@pytest.fixture
def sample_rag_document():
    """Create a sample document for RAG testing"""
    return """
    # FoodSave - Poradnik Przechowywania Żywności
    
    ## Wskazówki dotyczące przechowywania produktów
    
    ### Nabiał
    - Mleko: Przechowuj w lodówce w temperaturze 2-4°C, najlepiej spożyć w ciągu 3-5 dni po otwarciu.
    - Ser żółty: Przechowuj w lodówce w papierze pergaminowym, nie w plastiku; dobrze przechowuje się 2-3 tygodnie.
    - Jogurt: Przechowuj w lodówce, najlepiej spożyć w ciągu 5-7 dni po otwarciu.
    
    ### Pieczywo
    - Chleb: Przechowuj w chlebaku lub papierowej torbie, nie w lodówce; możesz zamrozić na dłuższe przechowywanie.
    - Bułki: Najlepiej spożyć w dniu zakupu lub zamrozić.
    
    ### Owoce i Warzywa
    - Jabłka: Przechowuj w lodówce, wytrzymują do 4-6 tygodni.
    - Banany: Przechowuj w temperaturze pokojowej, z dala od innych owoców.
    - Pomidory: Przechowuj w temperaturze pokojowej, nie w lodówce.
    - Ziemniaki: Przechowuj w chłodnym, ciemnym i suchym miejscu, nie w lodówce.
    
    ### Mięso
    - Surowe mięso: Przechowuj w najchłodniejszej części lodówki, najlepiej spożyć w ciągu 1-2 dni lub zamrozić.
    - Wędliny: Przechowuj w lodówce, najlepiej spożyć w ciągu 3-5 dni po otwarciu.
    """

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for RAG testing"""
    mock_store = MagicMock(spec=VectorStore)
    
    # Dodaj atrybut chunks, aby uniknąć błędu w initialize()
    mock_store.chunks = []
    
    # Mock search method to return relevant document chunks
    async def mock_search(query_embedding, k=5):
        chunk1 = DocumentChunk(
            id="1",
            content="Mleko: Przechowuj w lodówce w temperaturze 2-4°C, najlepiej spożyć w ciągu 3-5 dni po otwarciu.",
            metadata={"source": "food_storage_guide.md", "section": "Nabiał"}
        )
        chunk2 = DocumentChunk(
            id="2",
            content="Ser żółty: Przechowuj w lodówce w papierze pergaminowym, nie w plastiku; dobrze przechowuje się 2-3 tygodnie.",
            metadata={"source": "food_storage_guide.md", "section": "Nabiał"}
        )
        chunk3 = DocumentChunk(
            id="3",
            content="Jogurt: Przechowuj w lodówce, najlepiej spożyć w ciągu 5-7 dni po otwarciu.",
            metadata={"source": "food_storage_guide.md", "section": "Nabiał"}
        )
        
        return [(chunk1, 0.95), (chunk2, 0.88), (chunk3, 0.82)]
    
    mock_store.search = AsyncMock(side_effect=mock_search)
    return mock_store

@pytest.mark.asyncio
async def test_rag_agent_query(mock_vector_store):
    """Test RAG agent functionality with a basic query"""
    # Create a mock embedding model
    mock_llm_client = MagicMock()
    mock_llm_client.embed = AsyncMock(
        return_value=np.random.rand(768).tolist()  # Simulating an embedding
    )
    mock_llm_client.chat = AsyncMock(
        return_value={
            "message": {
                "content": "Mleko należy przechowywać w lodówce w temperaturze 2-4°C i najlepiej spożyć w ciągu 3-5 dni po otwarciu.",
            }
        }
    )
    
    # Create an instance of RAG agent
    rag_agent = EnhancedRAGAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        name="TestRAGAgent"
    )
    
    # Ustaw initialized na True, aby uniknąć wywołania initialize()
    rag_agent.initialized = True
    
    # Process a query related to milk storage
    result = await rag_agent.process({
        "query": "Jak przechowywać mleko?",
        "model": "gemma3:12b"
    })
    
    # Verify the result
    assert result.success is True
    assert "mleko" in result.text.lower()
    assert "lodówce" in result.text.lower()
    assert "3-5 dni" in result.text

@pytest.mark.asyncio
async def test_rag_agent_document_ingestion(sample_rag_document):
    """Test RAG document ingestion process"""
    # Create a temp file with the sample document
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+") as tmp:
        tmp.write(sample_rag_document)
        tmp.flush()
        
        # Create mock vector store with document adding capability
        mock_store = MagicMock(spec=VectorStore)
        mock_store.add_documents = AsyncMock()
        mock_store.chunks = []  # Dodaj atrybut chunks
        
        # Create mock embedding model
        mock_llm_client = MagicMock()
        mock_llm_client.embed = AsyncMock(
            return_value=np.random.rand(768).tolist()  # Simulating embedding
        )
        
        # Create a RAG agent
        rag_agent = EnhancedRAGAgent(
            vector_store=mock_store,
            llm_client=mock_llm_client,
            name="TestRAGAgent"
        )
        
        # Ustaw initialized na True, aby uniknąć wywołania initialize()
        rag_agent.initialized = True
        
        # Mock the add_file method
        with patch.object(rag_agent, "add_file") as mock_add_file:
            mock_add_file.return_value = {"chunks_added": 5}
            
            # Process document ingestion
            result = await rag_agent.ingest_document(tmp.name)
            
            # Verify the document was processed
            assert result["success"] is True
            assert result["chunks_added"] > 0
            mock_add_file.assert_called_once()

@pytest.mark.asyncio
async def test_rag_agent_with_db_context(mock_vector_store):
    """Test RAG agent with database product context integration"""
    # Mock database session with products
    mock_db = MagicMock()
    
    # Mock the product query
    mock_db.execute = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        MagicMock(name="Mleko UHT 3.2%", category="nabiał", purchase_date="2023-06-20"),
        MagicMock(name="Ser żółty", category="nabiał", purchase_date="2023-06-20"),
        MagicMock(name="Jabłka", category="owoce", purchase_date="2023-06-21"),
    ]
    mock_db.execute.return_value = mock_result
    
    # Mock LLM client responses
    mock_llm_client = MagicMock()
    mock_llm_client.embed = AsyncMock(
        return_value=np.random.rand(768).tolist()  # Simulating embedding
    )
    mock_llm_client.chat = AsyncMock(
        return_value={
            "message": {
                "content": "Dla dostępnych produktów: mleko, ser żółty i jabłka, zalecam przechowywanie w następujący sposób:\n"
                           "- Mleko UHT należy przechowywać w lodówce i spożyć w ciągu 3-5 dni po otwarciu.\n"
                           "- Ser żółty najlepiej trzymać w papierze pergaminowym zamiast plastiku, wytrzyma 2-3 tygodnie.\n"
                           "- Jabłka można przechowywać w lodówce nawet do 6 tygodni."
            }
        }
    )
    
    # Create RAG agent with access to products
    rag_agent = EnhancedRAGAgent(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        name="TestRAGAgent"
    )
    
    # Ustaw initialized na True, aby uniknąć wywołania initialize()
    rag_agent.initialized = True
    
    # Process a query about storing available products
    result = await rag_agent.process({
        "query": "Jak przechowywać produkty które mam?",
        "db": mock_db,
        "model": "gemma3:12b"
    })
    
    # Verify the result contains personalized advice for available products
    assert result.success is True
    assert "mleko" in result.text.lower()
    assert "ser żółty" in result.text.lower()
    assert "jabłka" in result.text.lower()
    assert "lodówce" in result.text.lower()

@pytest.mark.asyncio
async def test_rag_fallback_to_general_knowledge():
    """Test RAG agent's ability to fall back to general knowledge when no documents match"""
    # Create mock vector store that returns empty results
    mock_store = MagicMock(spec=VectorStore)
    mock_store.search = AsyncMock(return_value=[])  # No results found
    mock_store.chunks = []  # Dodaj atrybut chunks
    
    # Mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.embed = AsyncMock(
        return_value=np.random.rand(768).tolist()
    )
    mock_llm_client.chat = AsyncMock(
        return_value={
            "message": {
                "content": "Nie mam dokładnych informacji na temat przechowywania gruszek w mojej bazie wiedzy,"
                           " ale generalnie gruszki najlepiej przechowywać w lodówce, aby przedłużyć ich świeżość."
                           " W temperaturze pokojowej dojrzewają szybciej."
            }
        }
    )
    
    # Create RAG agent
    rag_agent = EnhancedRAGAgent(
        vector_store=mock_store,
        llm_client=mock_llm_client,
        name="TestRAGAgent"
    )
    
    # Ustaw initialized na True, aby uniknąć wywołania initialize()
    rag_agent.initialized = True
    
    # Query about something not in the knowledge base
    result = await rag_agent.process({
        "query": "Jak przechowywać gruszki?",
        "model": "gemma3:12b"
    })
    
    # Verify the result contains a general knowledge response
    assert result.success is True
    assert "gruszki" in result.text.lower()
    assert "lodówce" in result.text.lower()
    # Verify that fallback was used
    assert result.data.get("used_fallback") is True

if __name__ == "__main__":
    pytest.main(["-v", "test_rag_system_fixed.py"])
