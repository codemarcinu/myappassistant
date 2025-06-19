from typing import Any, List, Optional

from ..llm_api.llm_client import LLMClient


class EnhancedVectorStoreImpl:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def add_documents(self, documents: List[str]) -> None:
        raise NotImplementedError(
            "EnhancedVectorStoreImpl.add_documents() not implemented"
        )

    async def similarity_search(self, query: str, k: int = 4) -> List[str]:
        raise NotImplementedError(
            "EnhancedVectorStoreImpl.similarity_search() not implemented"
        )

    async def get_relevant_documents(self, query: str) -> List[str]:
        raise NotImplementedError(
            "EnhancedVectorStoreImpl.get_relevant_documents() not implemented"
        )
