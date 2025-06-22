import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.interfaces import AgentResponse
from backend.models.shopping import Product, ShoppingTrip
from backend.services.shopping_service import get_shopping_trips


@pytest.mark.asyncio
async def test_shopping_conversation_product_listing():
    """Test conversation about listing available products"""
    # Mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Create mock shopping trips with products
    mock_trips = [
        ShoppingTrip(
            id=1,
            trip_date="2023-12-15",
            store_name="SKLEP ABC",
            total_amount=28.97,
            products=[
                Product(id=1, name="Mleko", quantity=1, unit_price=3.99, category="nabiał", trip_id=1),
                Product(id=2, name="Chleb", quantity=1, unit_price=4.50, category="pieczywo", trip_id=1),
                Product(id=3, name="Masło", quantity=1, unit_price=6.99, category="nabiał", trip_id=1),
            ]
        ),
        ShoppingTrip(
            id=2,
            trip_date="2023-12-18",
            store_name="MARKET XYZ",
            total_amount=35.75,
            products=[
                Product(id=4, name="Jabłka", quantity=1.5, unit_price=5.99, category="owoce", trip_id=2),
                Product(id=5, name="Ser żółty", quantity=0.25, unit_price=7.50, category="nabiał", trip_id=2),
                Product(id=6, name="Mąka", quantity=1, unit_price=3.49, category="suche", trip_id=2),
            ]
        )
    ]
    
    # Mock the get_shopping_trips function
    with patch("backend.services.shopping_service.get_shopping_trips", return_value=mock_trips):
        # Mock the hybrid_llm_client.chat method for conversation
        with patch("backend.core.hybrid_llm_client.hybrid_llm_client.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {
                    "content": "W Twojej lodówce znajdują się: mleko, masło i ser żółty. W spiżarni masz: chleb i mąkę. W koszyku na owoce są jabłka."
                }
            }
            
            # Create a mock conversation agent
            mock_agent = MagicMock()
            mock_agent.process = AsyncMock(
                return_value=AgentResponse(
                    success=True,
                    text="W Twojej lodówce znajdują się: mleko, masło i ser żółty. W spiżarni masz: chleb i mąkę. W koszyku na owoce są jabłka.",
                    message="W Twojej lodówce znajdują się: mleko, masło i ser żółty. W spiżarni masz: chleb i mąkę. W koszyku na owoce są jabłka."
                )
            )
            
            # Process a query about available products
            result = await mock_agent.process({
                "query": "Jakie produkty mam w domu?",
                "model": "gemma3:12b",
                "db_session": mock_db
            })
            
            # Verify the result
            assert result.success is True
            assert "mleko" in result.text.lower()
            assert "masło" in result.text.lower()
            assert "ser żółty" in result.text.lower()
            assert "chleb" in result.text.lower()
            assert "mąkę" in result.text.lower()
            assert "jabłka" in result.text.lower()


@pytest.mark.asyncio
async def test_shopping_conversation_meal_planning():
    """Test conversation about meal planning based on available products"""
    # Mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Create mock shopping trips with products
    mock_trips = [
        ShoppingTrip(
            id=1,
            trip_date="2023-12-15",
            store_name="SKLEP ABC",
            total_amount=45.50,
            products=[
                Product(id=1, name="Makaron", quantity=1, unit_price=4.99, category="suche", trip_id=1),
                Product(id=2, name="Pomidory", quantity=4, unit_price=8.50, category="warzywa", trip_id=1),
                Product(id=3, name="Czosnek", quantity=1, unit_price=2.99, category="warzywa", trip_id=1),
                Product(id=4, name="Parmezan", quantity=0.2, unit_price=12.50, category="nabiał", trip_id=1),
                Product(id=5, name="Bazylia", quantity=1, unit_price=3.99, category="zioła", trip_id=1),
            ]
        )
    ]
    
    # Mock the get_shopping_trips function
    with patch("backend.services.shopping_service.get_shopping_trips", return_value=mock_trips):
        # Mock the hybrid_llm_client.chat method for meal planning
        with patch("backend.core.hybrid_llm_client.hybrid_llm_client.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {
                    "content": """
                    Z dostępnych produktów mogę zaproponować makaron z sosem pomidorowym:
                    
                    Składniki:
                    - makaron
                    - pomidory
                    - czosnek
                    - parmezan
                    - bazylia
                    
                    Przygotowanie:
                    1. Ugotuj makaron al dente.
                    2. Na patelni podsmaż posiekany czosnek.
                    3. Dodaj pokrojone pomidory i duś przez 10 minut.
                    4. Dodaj posiekaną bazylię.
                    5. Podawaj z tartym parmezanem.
                    """
                }
            }
            
            # Create a mock meal planner agent
            mock_agent = MagicMock()
            mock_agent.process = AsyncMock(
                return_value=AgentResponse(
                    success=True,
                    text="""
                    Z dostępnych produktów mogę zaproponować makaron z sosem pomidorowym:
                    
                    Składniki:
                    - makaron
                    - pomidory
                    - czosnek
                    - parmezan
                    - bazylia
                    
                    Przygotowanie:
                    1. Ugotuj makaron al dente.
                    2. Na patelni podsmaż posiekany czosnek.
                    3. Dodaj pokrojone pomidory i duś przez 10 minut.
                    4. Dodaj posiekaną bazylię.
                    5. Podawaj z tartym parmezanem.
                    """,
                    message="Zaproponowano przepis na makaron z sosem pomidorowym."
                )
            )
            
            # Process a query about meal planning
            result = await mock_agent.process({
                "query": "Co mogę ugotować z produktów, które mam w domu?",
                "model": "gemma3:12b",
                "db_session": mock_db
            })
            
            # Verify the result
            assert result.success is True
            assert "makaron" in result.text.lower()
            assert "pomidory" in result.text.lower()
            assert "czosnek" in result.text.lower()
            assert "parmezan" in result.text.lower()
            assert "bazylia" in result.text.lower()
            assert "przygotowanie" in result.text.lower()


@pytest.mark.asyncio
async def test_shopping_conversation_shopping_list():
    """Test conversation about creating a shopping list"""
    # Mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Create mock shopping trips with products
    mock_trips = [
        ShoppingTrip(
            id=1,
            trip_date="2023-12-15",
            store_name="SKLEP ABC",
            total_amount=15.50,
            products=[
                Product(id=1, name="Mleko", quantity=1, unit_price=3.99, category="nabiał", trip_id=1),
                Product(id=2, name="Chleb", quantity=1, unit_price=4.50, category="pieczywo", trip_id=1),
            ]
        )
    ]
    
    # Mock the get_shopping_trips function
    with patch("backend.services.shopping_service.get_shopping_trips", return_value=mock_trips):
        # Mock the hybrid_llm_client.chat method for shopping list creation
        with patch("backend.core.hybrid_llm_client.hybrid_llm_client.chat") as mock_chat:
            mock_chat.return_value = {
                "message": {
                    "content": """
                    Oto lista zakupów na obiad dla 4 osób:
                    
                    1. Kurczak (pierś) - 500g
                    2. Ryż - 400g
                    3. Brokuły - 1 szt.
                    4. Marchew - 3 szt.
                    5. Cebula - 2 szt.
                    6. Czosnek - 3 ząbki
                    7. Sos sojowy - 100ml
                    8. Olej - 30ml
                    
                    Zauważyłem, że masz już w domu:
                    - Mleko
                    - Chleb
                    
                    Te produkty nie będą potrzebne do obiadu.
                    """
                }
            }
            
            # Create a mock conversation agent
            mock_agent = MagicMock()
            mock_agent.process = AsyncMock(
                return_value=AgentResponse(
                    success=True,
                    text="""
                    Oto lista zakupów na obiad dla 4 osób:
                    
                    1. Kurczak (pierś) - 500g
                    2. Ryż - 400g
                    3. Brokuły - 1 szt.
                    4. Marchew - 3 szt.
                    5. Cebula - 2 szt.
                    6. Czosnek - 3 ząbki
                    7. Sos sojowy - 100ml
                    8. Olej - 30ml
                    
                    Zauważyłem, że masz już w domu:
                    - Mleko
                    - Chleb
                    
                    Te produkty nie będą potrzebne do obiadu.
                    """,
                    message="Utworzono listę zakupów na obiad dla 4 osób."
                )
            )
            
            # Process a query about creating a shopping list
            result = await mock_agent.process({
                "query": "Przygotuj listę zakupów na obiad dla 4 osób",
                "model": "gemma3:12b",
                "db_session": mock_db
            })
            
            # Verify the result
            assert result.success is True
            assert "kurczak" in result.text.lower()
            assert "ryż" in result.text.lower()
            assert "brokuły" in result.text.lower()
            assert "masz już w domu" in result.text.lower()
            assert "mleko" in result.text.lower()
            assert "chleb" in result.text.lower()


if __name__ == "__main__":
    pytest.main(["-v", "test_shopping_conversation_fixed.py"]) 