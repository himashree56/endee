# PDF Search - Adaptive RAG System

An intelligent PDF search and analysis system with adaptive reasoning, explainability, and a modern web interface.

## 🌟 Features

### Core Capabilities
- **🔍 Semantic Search** - Vector-based document retrieval using Endee Vector DB
- **💬 RAG Chat** - Conversational Q&A with source citations
- **📄 Document Summarization** - AI-powered document summaries (short/medium/long)
- **🧠 Adaptive Reasoning RAG** - Multi-step reasoning with self-reflection and explainability
- **📤 PDF Upload** - Upload and index new documents through the web interface

### Advanced Features
- **Query Analysis** - Automatic detection of query complexity and intent
- **Iterative Retrieval** - Self-reflection and query refinement for better results
- **Confidence Scoring** - Reliability assessment for every answer
- **Full Explainability** - Complete visibility into the reasoning process
- **🎨 Dynamic Theming** - Support for Light, Dark, and high-contrast Neon themes
- **📜 Research History** - Persistent interaction history with topic extraction and export
- **🧹 Deep Reset** - Synced clearing of interactions and research context
- **Multi-Mode Interface** - CLI and modern web UI

## 🏗️ Architecture

```
User Query → Adaptive RAG Agent → Query Analyzer
                ↓
        Iterative Retriever → Endee Vector DB
                ↓
        Self-Reflector → Answer Generator
                ↓
        Confidence Scorer → Explainability
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for web UI)
- Endee Vector Database (hosted on Render.com)

### Installation

1. **Clone and setup Python environment**
```bash
cd pdf_search
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
# or: source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

2. **Configure environment**
```bash
# Copy and edit .env file
cp .env.example .env
# Add your OpenRouter API key
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
```

### Running the Application

#### Option 1: Web UI (Recommended)

**Start Backend:**
```bash
# From pdf_search directory
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the startup script (Windows)
backend\start.bat
```
Backend runs on: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

**Start Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

**Access:** Open `http://localhost:3000` in your browser

#### Option 2: CLI

```bash
# Ingest PDFs
python cli.py ingest

# Semantic search
python cli.py search "your query"

# RAG chat
python cli.py chat "your question"

# Adaptive RAG with explainability
python cli.py adaptive-rag "complex question"

# Summarize document
python cli.py summarize --file "document.pdf" --length medium

# List documents
python cli.py list-documents
```

## 📚 Usage Examples

### Web UI

1. **Upload PDFs** - Click "📤 Upload" tab, select PDF, and upload
2. **Search** - Use "🔍 Search" for quick document retrieval
3. **Chat** - Use "💬 Chat" for Q&A with citations
4. **Adaptive RAG** - Use "🧠 Adaptive RAG" for complex queries with full reasoning visibility
5. **Summarize** - Use "📄 Summarize" to generate document summaries

### CLI Examples

```bash
# Simple search
python cli.py search "machine learning"

# Ask a question
python cli.py chat "What is agentic AI?"

# Complex query with reasoning
python cli.py adaptive-rag "What are the main challenges in building agentic AI systems and how do they compare to traditional AI approaches?"

# Summarize a document
python cli.py summarize --file "research_paper.pdf" --length long

# Interactive modes
python cli.py interactive        # Interactive search
python cli.py interactive-chat   # Interactive Q&A
```

## 🎨 Web UI Features

### Multi-Mode Interface
- **Search** - Direct semantic search with relevance scores
- **Chat** - Conversational Q&A with source citations
- **Summarize** - Document summarization with length options
- **Adaptive RAG** - Advanced reasoning with explainability
- **Upload** - PDF upload and automatic indexing

### Explainability Visualization
The Adaptive RAG interface shows:
- **Query Analysis** - Complexity and type detection
- **Reasoning Steps** - Step-by-step process timeline
- **Confidence Meter** - Visual reliability indicator
- **Sources** - All cited documents with page numbers
- **Retrieval Iterations** - Query refinement process

### Research History & Context
- **Interaction History** - Access previous Q&A and reasoning steps
- **Topic Extraction** - Automatically identifies key research topics
- **Management** - Rename, delete, or clear history
- **Context Persistence** - History is saved locally and survives browser restarts
- **Synced Reset** - Clearing history also purges research context and topics

### Theme System
- **Light** - Clean, high-visibility professional mode
- **Dark** - Modern, eye-strain reducing night mode
- **Neon** - High-contrast, vibrant cyberpunk aesthetic for deep research sessions

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | POST | Semantic search |
| `/api/chat` | POST | RAG Q&A |
| `/api/summarize` | POST | Document summarization |
| `/api/adaptive-rag` | POST | Adaptive reasoning RAG |
| `/api/upload` | POST | Upload & index PDF |
| `/api/documents` | GET | List indexed documents |
| `/health` | GET | Health check |

## 📁 Project Structure

```
pdf_search/
├── backend/
│   └── main.py              # FastAPI server
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.jsx          # Main app
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js
├── adaptive_rag_agent.py    # Adaptive RAG with LangGraph
├── rag_agent.py             # Simple RAG agent
├── summarizer.py            # Document summarizer
├── search_engine.py         # Semantic search engine
├── endee_client.py          # Endee DB client
├── memory_manager.py        # Local history and context management
├── embedder.py              # Embedding generation
├── pdf_processor.py         # PDF text extraction
├── cli.py                   # Command-line interface
├── user_memory.json         # Local storage for research history
└── requirements.txt         # Python dependencies
```

## 🛠️ Technology Stack

- **Vector Database**: Endee (hosted on Render.com)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
- **LLM**: OpenRouter API (`gpt-4o-mini`)
- **Orchestration**: LangGraph
- **Backend**: FastAPI
- **Frontend**: React + Vite
- **CLI**: Click + Rich

## ⚙️ Configuration

Edit `.env` file:

```env
# Endee Vector Database
ENDEE_URL=https://endee-1.onrender.com

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# PDF Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# LLM (OpenRouter)
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

## 🧪 Testing

```bash
# Test backend
python backend\main.py
# Visit http://localhost:8000/docs for API documentation

# Test CLI
python cli.py adaptive-rag "test question"

# Test frontend
cd frontend
npm run dev
```

## 📖 Documentation

- **Walkthrough**: See `walkthrough.md` in artifacts for detailed implementation guide
- **API Docs**: Visit `http://localhost:8000/docs` when backend is running
- **CLI Help**: Run `python cli.py --help`

## 🎯 Key Features Explained

### Adaptive Reasoning RAG
Unlike traditional RAG systems, our adaptive RAG:
1. **Analyzes** query complexity before retrieval
2. **Retrieves** documents adaptively based on complexity
3. **Reflects** on whether retrieved docs answer the question
4. **Refines** the query and re-retrieves if needed
5. **Generates** answer with multi-step reasoning
6. **Scores** confidence based on multiple factors
7. **Explains** every step of the process

### Explainability
Every adaptive RAG query provides:
- Query analysis (complexity, type, entities)
- Reasoning steps with timestamps
- Retrieval iterations and scores
- Confidence breakdown
- Source quality assessment

## 🤝 Contributing

This is a demonstration project showcasing adaptive RAG with explainability.

## 📄 License

MIT License

## 🙏 Acknowledgments

- **Endee Vector DB** - High-performance vector database
- **OpenRouter** - LLM API access
- **LangGraph** - Agent orchestration framework
- **sentence-transformers** - Embedding models

---

**Built with ❤️ using Adaptive Reasoning RAG**
