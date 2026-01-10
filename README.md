# RAG Document Q&A System

A local Retrieval-Augmented Generation (RAG) system for querying PDF documents using Ollama LLMs. Features hybrid search (keyword + semantic), multilingual support (including Bulgarian/Cyrillic), and a transparency UI showing the reasoning process.

## Features

- **PDF Upload & Processing**: Upload PDFs, extract text, and chunk for vector storage
- **Hybrid Search**: Combines keyword matching with semantic search for better retrieval
- **Two-Stage MCQ Pipeline**: Special handling for multiple choice questions with:
  - Stage 1: LLM analyzes question to determine search terms
  - Stage 2: Grep-style search with context (lines before/after matches)
  - Stage 3: LLM reasons over evidence to select answer
- **Transparency UI**: See the full reasoning process (keywords extracted, chunks retrieved, prompts sent)
- **Multilingual Support**: Works with Bulgarian, English, and other languages
- **Local & Private**: Everything runs locally using Ollama - no data leaves your machine

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend│────▶│  FastAPI Backend│────▶│     Ollama      │
│   (Vite + TS)   │     │    (Python)     │     │  (LLM + Embed)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │    ChromaDB     │
                        │ (Vector Store)  │
                        └─────────────────┘
```

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** (with npm)
- **Ollama** running locally or on a network host
  - Required models: embedding model + chat model

### Recommended Ollama Models

```bash
# Embedding models (choose one)
ollama pull nomic-embed-text          # Fast, good for English
ollama pull snowflake-arctic-embed2   # Multilingual (recommended for non-English)

# Chat models (choose one)
ollama pull llama3.2                  # Fast, good general purpose
ollama pull dolphin-mixtral           # Larger, better reasoning
ollama pull mistral                   # Good balance of speed/quality
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/rag-app.git
cd rag-app
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your Ollama host and model preferences
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Edit if backend is not on localhost:8000
```

## Configuration

### Backend (.env)

```env
# Ollama host (use localhost or network IP)
OLLAMA_HOST=http://localhost:11434

# Models (must be pulled in Ollama first)
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=llama3.2

# Text chunking settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Running the Application

### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

Access the application at: **http://localhost:5173**

## Usage

1. **Upload PDFs**: Click "Upload PDF" in the sidebar to add documents
2. **Ask Questions**: Type your question in the chat input
3. **View Sources**: Click "Sources" to see which documents were used
4. **View Reasoning**: Click "Thought process" to see:
   - Keywords extracted from your question
   - Which chunks matched and how (keyword/semantic/both)
   - The full prompt sent to the LLM

### Multiple Choice Questions

The system has special handling for MCQ format. Just paste the full question with options:

```
Геоикономически познания съществуват още от времето на:
А) Мохамед
Б) Херодот
В) Жан дьо Мон
Г) Савицки
Д) Ратцел
```

The system will:
1. Detect MCQ format automatically
2. Search for each option name in the documents
3. Only select answers that are explicitly found in the text

## Project Structure

```
rag-app/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── documents.py    # PDF upload endpoints
│   │   │   ├── query.py        # Question answering endpoint
│   │   │   └── health.py       # Health check endpoint
│   │   ├── services/
│   │   │   ├── pdf_service.py      # PDF text extraction & chunking
│   │   │   ├── embedding_service.py # Ollama embedding calls
│   │   │   ├── vector_store.py     # ChromaDB + hybrid search
│   │   │   └── llm_service.py      # Ollama LLM calls & prompts
│   │   ├── config.py           # Settings management
│   │   └── main.py             # FastAPI app entry point
│   ├── data/                   # Created at runtime
│   │   ├── uploads/            # Uploaded PDFs
│   │   └── chroma_db/          # Vector database
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatArea.tsx        # Main chat interface
│   │   │   ├── Message.tsx         # Chat message display
│   │   │   ├── Citation.tsx        # Source citations
│   │   │   ├── ThoughtProcess.tsx  # Reasoning transparency
│   │   │   ├── FileUpload.tsx      # PDF upload UI
│   │   │   ├── DocumentList.tsx    # Uploaded docs list
│   │   │   ├── Sidebar.tsx         # Left sidebar
│   │   │   └── Header.tsx          # Top header with status
│   │   ├── hooks/
│   │   │   ├── useQuery.ts         # Chat state management
│   │   │   ├── useDocuments.ts     # Document state
│   │   │   └── useHealth.ts        # Connection status
│   │   ├── services/
│   │   │   └── api.ts              # Backend API calls
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── .env.example
│
├── .gitignore
├── LICENSE
└── README.md
```

## API Endpoints

### Health Check
```
GET /health
```
Returns API and Ollama connection status.

### Documents
```
POST /documents/upload    # Upload a PDF
GET  /documents          # List uploaded documents
DELETE /documents/{name} # Delete a document
```

### Query
```
POST /query
Body: { "question": "Your question here", "top_k": 5 }
```

Returns:
- `answer`: LLM-generated response
- `citations`: Source documents with excerpts
- `reasoning`: Full transparency data (keywords, chunks, prompts)

## Troubleshooting

### "Ollama unreachable"
- Ensure Ollama is running: `ollama serve`
- Check the host URL in `.env` matches your Ollama instance
- If using a remote host, ensure the port is accessible

### "Model not found"
- Pull the required models:
  ```bash
  ollama pull nomic-embed-text
  ollama pull llama3.2
  ```

### Poor results with non-English text
- Use a multilingual embedding model: `snowflake-arctic-embed2`
- Use a larger chat model: `dolphin-mixtral`

### Slow responses
- Use smaller models for faster inference
- Reduce `top_k` to retrieve fewer chunks
- Ensure Ollama has GPU acceleration enabled

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Python, Pydantic
- **Vector Store**: ChromaDB
- **LLM**: Ollama (local inference)
- **PDF Processing**: PyMuPDF (fitz)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
