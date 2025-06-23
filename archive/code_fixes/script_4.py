# Tworzę przykłady kodu naprawczego dla głównych problemów

# 1. Przykład poprawki SQLAlchemy Multiple Classes Error
sqlalchemy_fix = """
# PRZED: src/backend/models/conversations.py
from sqlalchemy.orm import relationship

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="messages")

# PRZED: src/backend/models/chat.py
from sqlalchemy.orm import relationship

class Message(Base):  # Konflikt nazwy klasy!
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)

# PO NAPRAWIE: src/backend/models/conversations.py
from sqlalchemy.orm import relationship

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    messages = relationship("src.backend.models.conversations.Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("src.backend.models.conversations.Conversation", back_populates="messages")

# PO NAPRAWIE: src/backend/models/chat.py
from sqlalchemy.orm import relationship

class ChatMessage(Base):  # Zmieniona nazwa klasy
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)
"""

# 2. Przykład poprawki Agent Factory
agent_factory_fix = """
# PRZED: src/backend/agents/agent_factory.py
class AgentFactory:
    def create_agent(self, agent_type: str, **kwargs):
        if agent_type == "general_conversation":
            return GeneralConversationAgent(**kwargs)
        elif agent_type == "search":
            return SearchAgent(**kwargs)
        else:
            raise FileProcessingError(f"Unsupported agent type: {agent_type}")

# PO NAPRAWIE: src/backend/agents/agent_factory.py
class AgentFactory:
    AGENT_REGISTRY = {
        "general_conversation": GeneralConversationAgent,
        "shopping_conversation": ShoppingConversationAgent,
        "food_conversation": FoodConversationAgent,
        "information_query": InformationQueryAgent,
        "cooking": CookingAgent,
        "search": SearchAgent,
        "weather": WeatherAgent,
        "rag": RAGAgent,
        "categorization": CategorizationAgent,
        "meal_planning": MealPlannerAgent,
        "ocr": OCRAgent,
        "analytics": AnalyticsAgent,
    }

    def create_agent(self, agent_type: str, **kwargs):
        if agent_type not in self.AGENT_REGISTRY:
            logger.warning(f"Unknown agent type: {agent_type}, using GeneralConversationAgent")
            agent_type = "general_conversation"
        return self.AGENT_REGISTRY[agent_type](**kwargs)
"""

# 3. Przykład poprawki Pytest Async Issues
pytest_async_fix = """
# PRZED: tests/unit/test_entity_extraction.py
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent, user_prompt",
    [(item["intent"], item["prompt"]) for item in TEST_DATA],
)
async def test_entity_extraction_parametrized(intent: str, user_prompt: str) -> None:
    # Testuje pełny przepływ: ekstrakcję, wyszukiwanie i podejmowanie decyzji,
    # w tym generowanie pytania doprecyzowującego.
    # ... kod testu

# PRZED: conftest.py
@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as db:
        yield db

# PO NAPRAWIE: tests/unit/test_entity_extraction.py
import pytest_asyncio  # Dodane

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent, user_prompt",
    [(item["intent"], item["prompt"]) for item in TEST_DATA],
)
async def test_entity_extraction_parametrized(intent: str, user_prompt: str) -> None:
    # Testuje pełny przepływ: ekstrakcję, wyszukiwanie i podejmowanie decyzji,
    # w tym generowanie pytania doprecyzowującego.
    # ... kod testu

# PO NAPRAWIE: conftest.py
import pytest_asyncio  # Dodane

@pytest_asyncio.fixture  # Zmienione na pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as db:
        yield db

# PO NAPRAWIE: pyproject.toml
'''
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "--strict-markers"
markers = [
    "asyncio: marks tests as requiring asyncio",
]
'''
"""

# 4. Przykład poprawki AttributeError
attribute_error_fix = """
# PRZED: src/backend/core/vector_store.py
class VectorStore:
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        # ... kod metody

# PO NAPRAWIE: src/backend/core/vector_store.py
class VectorStore:
    def is_empty(self) -> bool:
        """Check if vector store is empty."""
        return len(self._vectors) == 0

    def add_document(self, document: Document) -> None:
        """Add document to vector store"""
        # ... implementacja

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        # ... kod metody

# PRZED: tests/unit/test_rag_agent.py
def test_process_empty_query():
    vector_store = Mock()
    rag_agent = RAGAgent(vector_store=vector_store)
    # vector_store.is_empty() będzie powodować AttributeError

# PO NAPRAWIE: tests/unit/test_rag_agent.py
def test_process_empty_query():
    vector_store = Mock(spec=VectorStore)  # Używamy spec aby Mock miał poprawne metody
    vector_store.is_empty.return_value = True
    rag_agent = RAGAgent(vector_store=vector_store)
    # Teraz vector_store.is_empty() działa poprawnie
"""

# Podsumowanie napraw
print("# Przykłady Napraw Głównych Problemów\n")

print("## 1. Naprawa SQLAlchemy Multiple Classes Error")
print("```python")
print(sqlalchemy_fix)
print("```\n")

print("## 2. Naprawa Agent Factory")
print("```python")
print(agent_factory_fix)
print("```\n")

print("## 3. Naprawa Pytest Async Issues")
print("```python")
print(pytest_async_fix)
print("```\n")

print("## 4. Naprawa AttributeError")
print("```python")
print(attribute_error_fix)
print("```")
