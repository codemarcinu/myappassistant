import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from backend.agents.interfaces import AgentResponse
from backend.core.database import AsyncSessionLocal
from backend.models.shopping import Product, ShoppingTrip


@pytest.fixture
async def db_session():
    """Pytest fixture to provide a test database session"""
    async with AsyncSessionLocal() as session:
        # Add test data to session
        yield session
        # Clean up created data
        await session.execute(text("DELETE FROM products"))
        await session.execute(text("DELETE FROM shopping_trips"))
        await session.commit()


@pytest.fixture
async def sample_products():
    """Create sample products for tests"""
    return [
        Product(
            name="Chleb pszenny",
            unit_price=4.99,
            quantity=1,
            category="pieczywo",
            created_at=datetime.now() - timedelta(days=1),
        ),
        Product(
            name="Mleko UHT 3.2%",
            unit_price=3.49,
            quantity=2,
            category="nabiał",
            created_at=datetime.now() - timedelta(days=1),
        ),
        Product(
            name="Jabłka",
            unit_price=2.99,
            quantity=1.5,
            category="owoce",
            created_at=datetime.now() - timedelta(days=2),
        ),
        Product(
            name="Ser żółty",
            unit_price=24.99,
            quantity=0.5,
            category="nabiał",
            created_at=datetime.now() - timedelta(days=3),
        ),
        Product(
            name="Jajka",
            unit_price=14.99,
            quantity=10,
            category="nabiał",
            created_at=datetime.now() - timedelta(days=3),
            unit="sztuka",
        ),
    ]


async def add_test_data(db_session, products):
    """Add test data to database"""
    # Create a shopping trip
    trip = ShoppingTrip(
        store_name="LIDL",
        trip_date=datetime.now() - timedelta(days=1),
        total_amount=50.00,
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    # Add products to database with reference to shopping trip
    for product in products:
        product.trip_id = trip.id
        db_session.add(product)

    await db_session.commit()
    return trip


# Helper do generowania asynchronicznego strumienia tekstu
async def fake_text_stream():
    for chunk in [
        "W Twojej lodówce masz: ",
        "chleb pszenny, ",
        "mleko, ",
        "jabłka, ",
        "ser żółty i jajka.",
    ]:
        yield chunk


@pytest.mark.skip(
    reason="get_orchestrator nie istnieje w backend.api.chat po refaktorze orchestratora - test wymaga aktualizacji do nowej architektury"
)
@pytest.mark.asyncio
async def test_shopping_conversation(db_session, sample_products):
    """Test conversation about shopping products"""
    # Add test data to the database
    trip = await add_test_data(db_session, sample_products)

    # Mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.process_request = AsyncMock()

    # Mock conversation agent
    conversation_response = AgentResponse(
        success=True,
        text="W Twojej lodówce masz: chleb pszenny, mleko, jabłka, ser żółty i jajka.",
        text_stream=fake_text_stream(),
    )
    mock_orchestrator.process_request.return_value = conversation_response

    # Simulate a conversation about shopping
    with patch("backend.api.chat.get_orchestrator", return_value=mock_orchestrator):
        from backend.api.chat import process_chat_message

        # Query about products in fridge
        result = await process_chat_message(
            "Co mam w lodówce?",
            user_id="test_user",
            conversation_id="test_conversation",
            db=db_session,
        )

        # Verify response
        assert result["success"] is True
        assert "W Twojej lodówce masz" in result["message"]

        # Check that the orchestrator was called with product context
        context = mock_orchestrator.process_request.call_args[0][0]
        assert "db" in context
        assert context["query"] == "Co mam w lodówce?"


# Helper do generowania asynchronicznego strumienia tekstu
async def fake_meal_text_stream():
    for chunk in [
        "Z dostępnych produktów (chleb, mleko, jajka, jabłka, ser) ",
        "mogę zaproponować następujące dania:\n",
        "1. Tosty z serem\n",
        "2. Jajecznica na grzankach\n",
        "3. Szarlotka",
    ]:
        yield chunk


async def fake_llm_stream(*args, **kwargs):
    for chunk in [
        {
            "message": {
                "content": "Z dostępnych produktów (chleb, mleko, jajka, jabłka, ser) mogę zaproponować następujące dania:\n1. Tosty z serem\n2. Jajecznica na grzankach\n3. Szarlotka"
            }
        },
    ]:
        yield chunk


@pytest.mark.asyncio
async def test_meal_planning_conversation(db_session, sample_products):
    """Test conversation about meal planning based on available products"""
    # Add test data to the database
    trip = await add_test_data(db_session, sample_products)

    with patch(
        "backend.core.llm_client.llm_client.generate_stream", new=fake_llm_stream
    ):
        from backend.agents.meal_planner_agent import MealPlannerAgent

        agent = MealPlannerAgent(name="TestMealPlanner")
        result = await agent.process(
            {
                "query": "Co mogę zrobić na obiad?",
                "db": db_session,
                "model": "gemma3:12b",
            }
        )
        assert result.success is True
        response_text = ""
        async for chunk in result.text_stream:
            response_text += chunk
        assert "mogę zaproponować" in response_text
        assert "Tosty z serem" in response_text
        assert "Jajecznica" in response_text


@pytest.mark.skip(
    reason="get_orchestrator nie istnieje w backend.api.chat po refaktorze orchestratora - test wymaga aktualizacji do nowej architektury"
)
@pytest.mark.asyncio
async def test_product_query_with_date_filter(db_session, sample_products):
    """Test querying products with date filters"""
    # Add test data to the database
    trip = await add_test_data(db_session, sample_products)

    # Mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.process_request = AsyncMock()

    # Return a response about products from yesterday
    yesterday_response = AgentResponse(
        success=True,
        text="Wczoraj kupiłeś: chleb pszenny i mleko.",
    )
    mock_orchestrator.process_request.return_value = yesterday_response

    # Simulate a conversation with date filtering
    with patch("backend.api.chat.get_orchestrator", return_value=mock_orchestrator):
        from backend.api.chat import process_chat_message

        # Query about yesterday's products
        result = await process_chat_message(
            "Co kupiłem wczoraj?",
            user_id="test_user",
            conversation_id="test_conversation",
            db=db_session,
        )

        # Verify response
        assert result["success"] is True
        assert "Wczoraj kupiłeś" in result["message"]

        # Check that date extraction and filtering was attempted
        context = mock_orchestrator.process_request.call_args[0][0]
        assert "db" in context
        assert context["query"] == "Co kupiłem wczoraj?"


if __name__ == "__main__":
    pytest.main(["-v", "test_shopping_conversation.py"])
