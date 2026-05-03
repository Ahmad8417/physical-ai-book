"""
RAG Retriever - Search Qdrant for relevant content
"""
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient


class DocumentRetriever:
    """Retrieve relevant documents from vector database."""

    def __init__(
        self,
        client: QdrantClient,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        collection_name: str = "physical_ai_docs"
    ):
        self.client = client
        self.embedding_model = SentenceTransformer(embedding_model)
        self.collection_name = collection_name

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve most relevant documents for a query.

        Args:
            query: User question
            top_k: Number of results to return

        Returns:
            List of relevant document chunks with metadata
        """
        # Embed the query
        query_embedding = self.embedding_model.encode(query)

        # Search Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k
        )

        # Format results
        results = []
        for hit in search_results:
            results.append({
                'text': hit.payload['text'],
                'title': hit.payload['title'],
                'path': hit.payload['path'],
                'module': hit.payload['module'],
                'score': hit.score
            })

        return results

    def format_context(self, results: List[Dict]) -> str:
        """Format retrieved documents into context string."""
        if not results:
            return "No relevant information found in the textbook."

        context_parts = []
        for idx, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {idx}: {result['title']} - {result['module']}]\n"
                f"{result['text']}\n"
            )

        return "\n---\n".join(context_parts)


if __name__ == "__main__":
    # Test retrieval
    from qdrant_client import QdrantClient

    client = QdrantClient(":memory:")
    retriever = DocumentRetriever(client)

    # Test query
    results = retriever.retrieve("What is ROS 2?")
    print(f"Found {len(results)} results")

    for result in results:
        print(f"\nTitle: {result['title']}")
        print(f"Score: {result['score']:.3f}")
        print(f"Text preview: {result['text'][:200]}...")
