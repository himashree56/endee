"""Unified Production API for PDF Search with Adaptive RAG and Research History."""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from datetime import datetime
import traceback
import uvicorn

# Core logic imports
from search_engine import SemanticSearchEngine
from rag_agent import RAGAgent
from summarizer import DocumentSummarizer
from adaptive_rag_agent import AdaptiveRAGAgent
from memory_manager import MemoryManager
from config import Config
from ingestion_status import IngestionStatus

app = FastAPI(title="EndeeNova PDF Search API", version="1.1.0")

print(f"--- STARTUP CONFIG ---")
print(f"ENDEE_URL: {Config.ENDEE_URL}")
print(f"VECTOR_DB_TYPE: {Config.VECTOR_DB_TYPE}")
if not Config.OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY is not set! Chat/Summarizer will fail.")
else:
    print("OPENROUTER_API_KEY is set.")
print(f"----------------------")

# Enable CORS
origins = [
    "http://localhost:5173",  # Local React
    "http://localhost:3000",  # Local React (alternative)
    "https://endee.vercel.app", # Vercel Frontend
]

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines (Lazy loaded)
search_engine = None
adaptive_rag_agent = None
summarizer = None

# --- Models ---
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    file_filter: Optional[str] = None

class ChatRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []

class SummarizeRequest(BaseModel):
    filename: Optional[str] = None
    summarize_all: bool = False
    length: str = "medium"

class AdaptiveRAGRequest(BaseModel):
    question: str
    mode: str = "standard"

class RenameRequest(BaseModel):
    title: str

class SearchResultModel(BaseModel):
    text: str
    file_name: str
    page: Any
    score: float

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.1.0"}

@app.get("/api/info")
def get_info():
    search_engine = SemanticSearchEngine.get_instance()
    info = search_engine.get_index_info()
    return info or {"total_chunks": 0, "files": {}, "message": "No index found"}

@app.post("/api/search")
def search(request: SearchRequest):
    try:
        search_engine = SemanticSearchEngine.get_instance()
        results = search_engine.search(
            query=request.query,
            top_k=request.top_k,
            filter_by_file=request.file_filter
        )
        
        formatted = []
        for r in results:
            meta = r.get("metadata", {})
            formatted.append({
                "text": meta.get("text", ""),
                "file_name": meta.get("file_name", "Unknown"),
                "page": meta.get("page", "?"),
                "score": r.get("score", 0.0)
            })
            
        # Save to history
        try:
            memory = MemoryManager()
            # Summary of top result for answer
            top_text = formatted[0]['text'] if formatted else "No results found."
            memory.add_interaction(
                question=f"Search: {request.query}",
                answer=f"Found {len(formatted)} results. Top result: {top_text[:200]}...",
                sources=[r['file_name'] for r in formatted]
            )
        except Exception as e:
            print(f"Failed to save search history: {e}")

        return {
            "success": True,
            "query": request.query,
            "num_results": len(formatted),
            "results": formatted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(request: ChatRequest):
    global adaptive_rag_agent
    try:
        if adaptive_rag_agent is None:
            adaptive_rag_agent = AdaptiveRAGAgent()
        
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
        # Save to history
        try:
            memory = MemoryManager()
            memory.add_interaction(
                question=request.question,
                answer=result["answer"],
                sources=result["sources"]
            )
        except Exception as e:
            print(f"Failed to save chat history: {e}")

        print(f"[API] Chat response sent. Answer length: {len(result['answer'])}")
        return response
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/adaptive-rag")
def adaptive_rag(request: AdaptiveRAGRequest):
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

@app.post("/api/summarize")
def summarize(request: SummarizeRequest):
    global summarizer
    try:
        if summarizer is None:
            summarizer = DocumentSummarizer()
        
        if request.summarize_all:
            summaries = summarizer.summarize_all_documents(max_length=request.length)
             # Save to history
            try:
                memory = MemoryManager()
                memory.add_interaction(
                    question="Summarize All Documents",
                    answer=f"Summarized {len(summaries)} documents.",
                    sources=[s['filename'] for s in summaries]
                )
            except Exception as e:
                print(f"Failed to save summary history: {e}")

            return {"success": True, "summaries": summaries}
        elif request.filename:
            summary = summarizer.summarize_document(request.filename, max_length=request.length)
             # Save to history
            try:
                memory = MemoryManager()
                memory.add_interaction(
                    question=f"Summarize {request.filename}",
                    answer=summary["summary"],
                    sources=[request.filename]
                )
            except Exception as e:
                print(f"Failed to save summary history: {e}")

            return {"success": True, "summary": summary}
        else:
            raise HTTPException(status_code=400, detail="Must specify filename or summarize_all")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/version")
def version():
    return {"version": "1.0.2-debug", "timestamp": str(datetime.now())}

@app.get("/api/documents")
def list_documents():
    try:
        # Debugging logging
        print("Accessing /api/documents...")
        # Lazy load
        search_engine = SemanticSearchEngine.get_instance()
        
        docs = search_engine.get_available_documents()
        index_info = search_engine.get_index_info()
        
        # Handle None return
        if index_info is None:
            index_info = {}
            
        files = index_info.get("files", {})
        
        doc_list = []
        for doc in docs:
            finfo = files.get(doc, {})
            doc_list.append({
                "filename": doc,
                "chunks": finfo.get("chunks", 0),
                "pages": len(finfo.get("pages", []))
            })
        return {"success": True, "documents": doc_list, "total": len(doc_list)}
    except Exception as e:
        print(f"Error in list_documents: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{str(e)} | Cause: {type(e).__name__}")

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    try:
        if not Config.PDF_DIR.exists():
            Config.PDF_DIR.mkdir(parents=True)
            
        uploaded_names = []
        valid_paths = []
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
            file_path = Config.PDF_DIR / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            uploaded_names.append(file.filename)
            valid_paths.append(file_path)
            
        if not uploaded_names:
             raise HTTPException(status_code=400, detail="No valid PDF files uploaded")

        if background_tasks:
            background_tasks.add_task(process_upload_background, valid_paths)
        else:
            process_upload_background(valid_paths)
        
        return {
            "success": True, 
            "message": f"Uploaded {len(uploaded_names)} files. Indexing in background.",
            "filenames": uploaded_names
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ingestion/status")
def get_ingestion_status():
    status_tracker = IngestionStatus.get_instance()
    # status_tracker.clear_completed() # Optional: Clear old tasks? Maybe not immediately so UI can see completion.
    return {"success": True, "status": status_tracker.get_status()}

def process_upload_background(file_paths: List[Path]):
    # Lazy load inside background task
    search_engine = SemanticSearchEngine.get_instance()
    for path in file_paths:
        try:
            success, message = search_engine.ingest_pdfs(path)
            if not success:
                error_msg = f"Failed to ingest {path.name}: {message}"
                print(error_msg, flush=True)
                try:
                     with open("api_debug.log", "a") as f:
                        f.write(f"[{datetime.now()}] ERROR: {error_msg}\n")
                except: pass
            else:
                print(f"Successfully ingested {path.name}", flush=True)

        except Exception as e:
            print(f"Error indexing {path.name}: {e}", flush=True)
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            try:
                 with open("api_debug.log", "a") as f:
                    f.write(f"Error indexing {path.name}: {str(e)}\n")
                    traceback.print_exc(file=f)
            except: pass
# --- History Endpoints ---

@app.get("/api/history")
async def get_history():
    try:
        memory = MemoryManager()
        print(f"[API] get_history: Memory file is {memory.memory_file}")
        print(f"[API] get_history: Found {len(memory.memory.get('interactions', []))} interactions")
        return {"success": True, "history": memory.memory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history")
async def clear_history():
    try:
        memory = MemoryManager()
        memory.clear_history()
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.delete("/api/history/{interaction_id}")
async def delete_history_item(interaction_id: str):
    try:
        memory = MemoryManager()
        if memory.delete_interaction(interaction_id):
            return {"success": True, "message": "Interaction deleted"}
        raise HTTPException(status_code=404, detail="Interaction not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/history/{interaction_id}")
async def rename_history_item(interaction_id: str, request: RenameRequest):
    try:
        memory = MemoryManager()
        if memory.update_interaction(interaction_id, request.title):
            return {"success": True, "message": "Interaction renamed"}
        raise HTTPException(status_code=404, detail="Interaction not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
