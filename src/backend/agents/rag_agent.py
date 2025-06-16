from typing import Any, Dict

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.core.document_loader import load_documents
from backend.core.llm_client import llm_client
from backend.core.vector_store import vector_store


class RAGAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.initialized = False

    async def initialize(self):
        if not self.initialized:
            documents = load_documents("data/docs")
            for doc in documents:
                embedding = await llm_client.embed(model="gemma3:12b", text=doc)
                vector_store.add(doc, embedding)
            self.initialized = True

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        await self.initialize()

        query = context["query"]

        query_embedding = await llm_client.embed(model="gemma3:12b", text=query)

        retrieved_docs = vector_store.search(query_embedding)

        context_text = "\n".join(retrieved_docs)

        prompt = f"Context: {context_text}\n\nQuestion: {query}\n\nAnswer:"

        response = await llm_client.chat(
            model="gemma3:12b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        if response and "message" in response:
            return AgentResponse(
                text=response["message"]["content"],
                data={},
                success=True,
            )
        else:
            return AgentResponse(
                text="Failed to answer question.",
                data={},
                success=False,
            )
