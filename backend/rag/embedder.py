"""
RAG Embedder - Reads markdown files and creates embeddings
"""
import os
import re
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib


class DocumentEmbedder:
    """Embed documentation into vector database."""

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        collection_name: str = "physical_ai_docs"
    ):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.collection_name = collection_name
        self.client = None

    def initialize_qdrant(self, client: QdrantClient):
        """Initialize Qdrant collection."""
        self.client = client

        # Get embedding dimension
        sample_embedding = self.embedding_model.encode("test")
        vector_size = len(sample_embedding)

        # Create collection if it doesn't exist
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)

        if not collection_exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {self.collection_name}")
        else:
            print(f"Collection already exists: {self.collection_name}")

    def read_markdown_files(self, docs_dir: str = "../docs") -> List[Dict]:
        """Read all markdown files from docs directory."""
        docs_path = Path(__file__).parent.parent / docs_dir
        documents = []

        # Find all markdown files
        for md_file in docs_path.rglob("*.md*"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract frontmatter
                frontmatter = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter_text = parts[1]
                        content = parts[2]

                        # Parse frontmatter
                        for line in frontmatter_text.strip().split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                frontmatter[key.strip()] = value.strip().strip('"')

                # Get relative path
                rel_path = md_file.relative_to(docs_path)

                # Extract title
                title = frontmatter.get('title', '')
                if not title:
                    # Try to extract from first heading
                    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if match:
                        title = match.group(1)
                    else:
                        title = md_file.stem

                documents.append({
                    'path': str(rel_path),
                    'title': title,
                    'content': content.strip(),
                    'module': self._extract_module(str(rel_path))
                })

            except Exception as e:
                print(f"Error reading {md_file}: {e}")

        print(f"Read {len(documents)} documents")
        return documents

    def _extract_module(self, path: str) -> str:
        """Extract module name from path."""
        if 'module-1' in path:
            return 'Module 1: ROS 2'
        elif 'module-2' in path:
            return 'Module 2: Gazebo & Unity'
        elif 'module-3' in path:
            return 'Module 3: NVIDIA Isaac'
        elif 'module-4' in path:
            return 'Module 4: VLA'
        else:
            return 'Introduction'

    def chunk_document(self, doc: Dict, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Split document into overlapping chunks."""
        content = doc['content']
        chunks = []

        # Split by paragraphs first
        paragraphs = content.split('\n\n')

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'title': doc['title'],
                        'path': doc['path'],
                        'module': doc['module']
                    })
                current_chunk = para + "\n\n"

        # Add last chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'title': doc['title'],
                'path': doc['path'],
                'module': doc['module']
            })

        return chunks

    def embed_documents(self, documents: List[Dict]) -> int:
        """Embed documents and store in Qdrant."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")

        # Create embeddings
        texts = [chunk['text'] for chunk in all_chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        # Create points for Qdrant
        points = []
        for idx, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
            # Create unique ID from content hash
            content_hash = hashlib.md5(chunk['text'].encode()).hexdigest()
            point_id = int(content_hash[:8], 16)

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        'text': chunk['text'],
                        'title': chunk['title'],
                        'path': chunk['path'],
                        'module': chunk['module']
                    }
                )
            )

        # Upload to Qdrant in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        print(f"Embedded {len(points)} chunks into Qdrant")
        return len(points)


if __name__ == "__main__":
    # Test embedding
    embedder = DocumentEmbedder()

    # Initialize Qdrant (in-memory)
    from qdrant_client import QdrantClient
    client = QdrantClient(":memory:")
    embedder.initialize_qdrant(client)

    # Read and embed documents
    docs = embedder.read_markdown_files()
    num_embedded = embedder.embed_documents(docs)

    print(f"Successfully embedded {num_embedded} chunks")
