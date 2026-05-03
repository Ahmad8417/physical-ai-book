# Physical AI Chatbot Backend

RAG-powered chatbot backend for the Physical AI & Humanoid Robotics textbook.

## Features

- **RAG (Retrieval-Augmented Generation)**: Answers questions using textbook content
- **Vector Search**: Qdrant for semantic search
- **LLM Integration**: Ollama with Llama 3.2
- **FastAPI**: Modern async API
- **In-Memory Mode**: No external database required

## Prerequisites

1. **Python 3.10+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai/)

## Installation

### 1. Install Ollama

```bash
# Download and install from https://ollama.ai/

# Pull the Llama 3.2 model
ollama pull llama3.2
```

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (defaults should work)
```

## Usage

### Start the Backend Server

```bash
cd backend
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Embed Documents (First Time Only)
```bash
curl -X POST http://localhost:8000/embed
```

This reads all markdown files from `docs/` and creates embeddings. Takes ~30 seconds.

#### 3. Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is ROS 2?"}'
```

### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

```
┌─────────────────────────────────────────┐
│         RAG Chatbot Backend             │
├─────────────────────────────────────────┤
│                                         │
│  User Question                          │
│       ↓                                 │
│  Embedder (sentence-transformers)       │
│       ↓                                 │
│  Qdrant Vector Search                   │
│       ↓                                 │
│  Retrieve Top-K Documents               │
│       ↓                                 │
│  LLM (Ollama + Llama 3.2)              │
│       ↓                                 │
│  Generated Answer + Sources             │
│                                         │
└─────────────────────────────────────────┘
```

## Components

### 1. Document Embedder (`rag/embedder.py`)
- Reads markdown files from `docs/`
- Chunks documents (1000 chars with 200 overlap)
- Creates embeddings using sentence-transformers
- Stores in Qdrant vector database

### 2. Document Retriever (`rag/retriever.py`)
- Embeds user question
- Searches Qdrant for similar chunks
- Returns top-K most relevant passages

### 3. Answer Generator (`rag/generator.py`)
- Takes question + retrieved context
- Sends to Ollama LLM
- Returns generated answer

### 4. FastAPI Server (`main.py`)
- REST API endpoints
- CORS enabled for frontend
- Async request handling

## Configuration

Edit `.env` file:

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Qdrant (in-memory, no config needed)
QDRANT_COLLECTION_NAME=physical_ai_docs

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Troubleshooting

### Ollama Not Available
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull model if missing
ollama pull llama3.2
```

### Port Already in Use
```bash
# Change port in .env
API_PORT=8001
```

### CORS Errors
```bash
# Add your frontend URL to CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Development

### Run Tests
```bash
# Test embedder
python -m rag.embedder

# Test retriever
python -m rag.retriever

# Test generator
python -m rag.generator
```

### Hot Reload
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### Using Docker (Coming Soon)
```bash
docker build -t physical-ai-chatbot .
docker run -p 8000:8000 physical-ai-chatbot
```

### Using Systemd
```bash
# Create service file
sudo nano /etc/systemd/system/physical-ai-chatbot.service

# Enable and start
sudo systemctl enable physical-ai-chatbot
sudo systemctl start physical-ai-chatbot
```

## Performance

- **Embedding**: ~30 seconds for full textbook
- **Query**: ~2-3 seconds per question
- **Memory**: ~500MB RAM (in-memory Qdrant)

## License

Same as parent project
