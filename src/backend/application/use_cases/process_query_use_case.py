import logging
from typing import Any, Dict, List

from backend.domain.repositories import FoodItemRepository, UserRepository
from backend.infrastructure.llm_api.llm_client import LLMClient
from backend.infrastructure.vector_store.vector_store_impl import \
    EnhancedVectorStoreImpl

logger = logging.getLogger(__name__)


class ProcessQueryUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        food_item_repository: FoodItemRepository,
        llm_client: LLMClient,
        vector_store: EnhancedVectorStoreImpl,
    ) -> None:
        self.user_repository = user_repository
        self.food_item_repository = food_item_repository
        self.llm_client = llm_client
        self.vector_store = vector_store

    async def execute(self, query: str, user_id: str) -> Dict[str, Any]:
        """Execute query processing use case"""
        logger.info(f"Starting query processing for user_id: {user_id}")
        try:
            # Get user context
            logger.info(f"Fetching user: {user_id}")
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return {"success": False, "error": "User not found", "query": query}
            logger.info(f"User found: {user.username}")

            # Get relevant documents from vector store
            logger.info("Fetching relevant documents from vector store")
            relevant_docs = await self.vector_store.get_relevant_documents(query)
            logger.info(f"Found {len(relevant_docs)} relevant documents")

            # Get user's food items
            logger.info(f"Fetching food items for user: {user_id}")
            food_items = await self.food_item_repository.get_by_user_id(user_id)
            logger.info(f"Found {len(food_items)} food items")

            # Create context for LLM
            context = {
                "user": user,
                "food_items": food_items,
                "relevant_documents": relevant_docs,
                "query": query,
            }

            # Generate response using LLM
            logger.info("Generating response from LLM")
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful food assistant. Use the provided context to answer the user's query.",
                },
                {"role": "user", "content": f"Query: {query}\nContext: {str(context)}"},
            ]

            response = await self.llm_client.chat(messages)
            logger.info("LLM response generated successfully")

            return {
                "success": True,
                "response": response,
                "query": query,
                "user_id": user_id,
                "relevant_documents_count": len(relevant_docs),
                "food_items_count": len(food_items),
            }

        except Exception as e:
            logger.error(
                f"Error processing query for user {user_id}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "user_id": user_id,
            }
