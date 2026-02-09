"""FastAPI backend for PDF Search with Adaptive RAG."""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import os
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_engine import SemanticSearchEngine
from rag_agent import RAGAgent
from summarizer import DocumentSummarizer
from adaptive_rag_agent import AdaptiveRAGAgent

app = FastAPI(title="PDF Search API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
search_engine = SemanticSearchEngine()
rag_agent = None
summarizer = None
adaptive_rag_agent = None


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    file_filter: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []  # List of {role: "user"|"assistant", content: "..."}


class SummarizeRequest(BaseModel):
    filename: Optional[str] = None
    summarize_all: bool = False
    length: str = "medium"


class AdaptiveRAGRequest(BaseModel):
    question: str
    mode: str = "standard"  # "standard" or "insight"


# Endpoints
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "PDF Search API",
        "version": "1.0.0",
        "endpoints": [
            "/api/search",
            "/api/chat",
            "/api/summarize",
            "/api/adaptive-rag",
            "/api/documents"
        ]
    }


@app.post("/api/search")
def search(request: SearchRequest):
    """Semantic search endpoint."""
    try:
        results = search_engine.search(
            query=request.query,
            top_k=request.top_k,
            filter_by_file=request.file_filter
        )
        
        # Format results
        formatted_results = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted_results.append({
                "text": metadata.get("text", ""),
                "file_name": metadata.get("file_name", "Unknown"),
                "page": metadata.get("page", "?"),
                "score": result.get("score", 0.0)
            })
        
        return {
            "success": True,
            "query": request.query,
            "num_results": len(formatted_results),
            "results": formatted_results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(request: ChatRequest):
    """RAG chat endpoint using Adaptive Agent."""
    global adaptive_rag_agent
    
    try:
        if adaptive_rag_agent is None:
            adaptive_rag_agent = AdaptiveRAGAgent()
        
        # Use adaptive agent with chat history
        result = adaptive_rag_agent.ask(
            question=request.question, 
            mode="standard",
            chat_history=request.history
        )
        
        return {
            "success": True,
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    
    except Exception as e:
        error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/summarize")
def summarize(request: SummarizeRequest):
    """Document summarization endpoint."""
    global summarizer
    
    try:
        if summarizer is None:
            summarizer = DocumentSummarizer()
        
        if request.summarize_all:
            summaries = summarizer.summarize_all_documents(max_length=request.length)
            return {
                "success": True,
                "summaries": summaries
            }
        elif request.filename:
            summary = summarizer.summarize_document(request.filename, max_length=request.length)
            return {
                "success": True,
                "summary": summary
            }
        else:
            raise HTTPException(status_code=400, detail="Must specify filename or summarize_all")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/adaptive-rag")
def adaptive_rag(request: AdaptiveRAGRequest):
    """Adaptive reasoning RAG endpoint with explainability."""
    global adaptive_rag_agent
    
    try:
        if adaptive_rag_agent is None:
            adaptive_rag_agent = AdaptiveRAGAgent()
        
        result = adaptive_rag_agent.ask(request.question, mode=request.mode)
        
        return {
            "success": True,
            "question": result["question"],
            "answer": result["answer"],
            "confidence": result["confidence"],
            "reasoning_steps": result["reasoning_steps"],
            "sources": result["sources"],
            "query_analysis": result["query_analysis"],
            "retrieval_iterations": result["retrieval_iterations"],
            "num_documents": result["num_documents"],
            "truth_label": result.get("truth_label"),
            "reliability_score": result.get("reliability_score"),
            "critique_report": result.get("critique_report")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
def list_documents():
    """List all indexed documents."""
    global summarizer
    
    try:
        if summarizer is None:
            summarizer = DocumentSummarizer()
        
        documents = summarizer.get_available_documents()
        index_info = summarizer.search_engine.get_index_info()
        files = index_info.get("files", {})
        
        doc_list = []
        for doc in documents:
            file_info = files.get(doc, {})
            doc_list.append({
                "filename": doc,
                "chunks": file_info.get("chunks", 0),
                "pages": len(file_info.get("pages", []))
            })
        
        return {
            "success": True,
            "documents": doc_list,
            "total": len(doc_list)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_pdf(
    files: List[UploadFile] = File(...), 
    background_tasks: BackgroundTasks = None
):
    """Upload and index multiple PDF files."""
    try:
        uploaded_files = []
        
        # Ensure pdfs directory exists
        pdf_dir = Path(__file__).parent.parent / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        
        valid_files = []
        
        for file in files:
            # Validate file type
            if not file.filename.endswith('.pdf'):
                continue
            
            file_path = pdf_dir / file.filename
            
            # Save uploaded file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append(file.filename)
            valid_files.append(file_path)
        
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No valid PDF files uploaded")
            
        # Index files in background
        if background_tasks:
            background_tasks.add_task(process_upload_background, valid_files)
        else:
            # Fallback for sync execution (testing)
            process_upload_background(valid_files)
        
        return {
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} files. Indexing started in background.",
            "filenames": uploaded_files
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_upload_background(file_paths: List[Path]):
    """Process uploaded files in background."""
    print(f"Starting background indexing for {len(file_paths)} files...")
    for file_path in file_paths:
        try:
            print(f"Indexing {file_path.name}...")
            search_engine.ingest_pdfs(file_path)
        except Exception as e:
            print(f"Error indexing {file_path.name}: {e}")
    print("Background indexing complete.")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/history")
async def get_history():
    """Get user research history."""
    try:
        # Initialize memory manager if agent not active
        # Or just read the file directly/via new instance
        # Since it's file-based, a new instance is fine for reading
        from memory_manager import MemoryManager
        memory = MemoryManager()
        data = memory._load_memory()
        return {
            "success": True,
            "history": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RenameRequest(BaseModel):
    title: str

@app.delete("/api/history")
async def clear_history():
    """Clear all history."""
    try:
        from memory_manager import MemoryManager
        memory = MemoryManager()
        memory.clear_history()
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{interaction_id}")
async def delete_history_item(interaction_id: str):
    """Delete a specific history item."""
    try:
        from memory_manager import MemoryManager
        memory = MemoryManager()
        if memory.delete_interaction(interaction_id):
            return {"success": True, "message": "Interaction deleted"}
        else:
            raise HTTPException(status_code=404, detail="Interaction not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/history/{interaction_id}")
async def rename_history_item(interaction_id: str, request: RenameRequest):
    """Rename a history item."""
    try:
        from memory_manager import MemoryManager
        memory = MemoryManager()
        if memory.update_interaction(interaction_id, request.title):
            return {"success": True, "message": "Interaction renamed"}
        else:
            raise HTTPException(status_code=404, detail="Interaction not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
