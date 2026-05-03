"""
FastAPI server for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

from rag.embedder import DocumentEmbedder
from rag.retriever import DocumentRetriever
from rag.generator import AnswerGenerator

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "physical_ai_docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize FastAPI
app = FastAPI(
    title="Physical AI Chatbot API",
    description="RAG-powered chatbot for Physical AI & Humanoid Robotics textbook",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
qdrant_client = None
embedder = None
retriever = None
generator = None
is_embedded = False


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list
    success: bool
    error: Optional[str] = None


class EmbedResponse(BaseModel):
    message: str
    num_chunks: int
    success: bool


class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    documents_embedded: bool


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global qdrant_client, embedder, retriever, generator

    print("Initializing RAG Chatbot...")

    # Initialize Qdrant (in-memory)
    qdrant_client = QdrantClient(":memory:")
    print("✓ Qdrant client initialized (in-memory mode)")

    # Initialize embedder
    embedder = DocumentEmbedder(
        embedding_model=EMBEDDING_MODEL,
        collection_name=QDRANT_COLLECTION_NAME
    )
    embedder.initialize_qdrant(qdrant_client)
    print("✓ Document embedder initialized")

    # Initialize retriever
    retriever = DocumentRetriever(
        client=qdrant_client,
        embedding_model=EMBEDDING_MODEL,
        collection_name=QDRANT_COLLECTION_NAME
    )
    print("✓ Document retriever initialized")

    # Initialize generator
    generator = AnswerGenerator(
        model=OLLAMA_MODEL,
        ollama_host=OLLAMA_HOST
    )
    print("✓ Answer generator initialized")

    # Check Ollama availability
    if generator.check_ollama_available():
        print(f"✓ Ollama is available with model: {OLLAMA_MODEL}")
    else:
        print(f"⚠ Ollama not available. Please install and run: ollama pull {OLLAMA_MODEL}")

    print("RAG Chatbot ready!")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Physical AI Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "embed": "/embed"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    ollama_available = generator.check_ollama_available() if generator else False

    return HealthResponse(
        status="healthy",
        ollama_available=ollama_available,
        documents_embedded=is_embedded
    )


@app.post("/embed", response_model=EmbedResponse)
async def embed_documents():
    """
    Embed all documentation into vector database.
    This should be called once to initialize the knowledge base.
    """
    global is_embedded

    try:
        if not embedder:
            raise HTTPException(status_code=500, detail="Embedder not initialized")

        # Read documents
        documents = embedder.read_markdown_files()

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found in docs/ directory")

        # Embed documents
        num_chunks = embedder.embed_documents(documents)

        is_embedded = True

        return EmbedResponse(
            message=f"Successfully embedded {len(documents)} documents into {num_chunks} chunks",
            num_chunks=num_chunks,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - answer questions using RAG.

    Process:
    1. Retrieve relevant context from vector database
    2. Generate answer using LLM with context
    3. Return answer with sources
    """
    try:
        if not is_embedded:
            raise HTTPException(
                status_code=400,
                detail="Documents not embedded yet. Please call /embed first."
            )

        if not retriever or not generator:
            raise HTTPException(status_code=500, detail="RAG components not initialized")

        # Retrieve relevant documents
        results = retriever.retrieve(request.question, top_k=request.top_k)

        if not results:
            return ChatResponse(
                answer="I couldn't find relevant information in the textbook to answer your question. Could you rephrase or ask about a different topic?",
                sources=[],
                success=True
            )

        # Format context
        context = retriever.format_context(results)

        # Generate answer
        generation_result = generator.generate(request.question, context)

        if not generation_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Answer generation failed: {generation_result.get('error', 'Unknown error')}"
            )

        # Format sources
        sources = [
            {
                'title': r['title'],
                'module': r['module'],
                'path': r['path'],
                'score': round(r['score'], 3)
            }
            for r in results
        ]

        return ChatResponse(
            answer=generation_result['answer'],
            sources=sources,
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
