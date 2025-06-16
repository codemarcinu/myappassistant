# This is a placeholder for the vector store implementation.
# In a real application, you would use a library like FAISS or Chroma.


class VectorStore:
    def __init__(self):
        self.vectors = {}

    def add(self, text: str, vector: list[float]):
        self.vectors[text] = vector

    def search(self, query_vector: list[float], k: int = 5) -> list[str]:
        # This is a naive implementation of a vector search.
        # In a real application, you would use a more efficient algorithm.

        scores = {}
        for text, vector in self.vectors.items():
            scores[text] = self.cosine_similarity(query_vector, vector)

        return sorted(scores, key=lambda item: scores[item], reverse=True)[:k]

    def cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude1 = sum(x * x for x in v1) ** 0.5
        magnitude2 = sum(x * x for x in v2) ** 0.5
        return dot_product / (magnitude1 * magnitude2)


vector_store = VectorStore()
