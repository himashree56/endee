"""Configuration management for PDF semantic search."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Endee Server
    ENDEE_URL = os.getenv("ENDEE_URL")
    if not ENDEE_URL:
        _raw_host = os.getenv("ENDEE_HOST", "localhost")
        ENDEE_PORT = int(os.getenv("ENDEE_PORT", "8080"))
        
        # Handle user including protocol in host
        if _raw_host.startswith("https://"):
            _clean_host = _raw_host.replace("https://", "")
            _scheme = "https"
        elif _raw_host.startswith("http://"):
            _clean_host = _raw_host.replace("http://", "")
            _scheme = "http"
        else:
            _clean_host = _raw_host
            _scheme = "http"
            
        _clean_host = _clean_host.rstrip("/")
        ENDEE_URL = f"{_scheme}://{_clean_host}:{ENDEE_PORT}"

    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
    
    # PDF Processing
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # LLM Configuration (OpenRouter)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent
    PDF_DIR = PROJECT_ROOT / "pdfs"
    INDEX_DIR = PROJECT_ROOT / "index"
    
    # Endee Collection
    COLLECTION_NAME = "pdf_documents"
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories."""
        cls.PDF_DIR.mkdir(exist_ok=True)
        cls.INDEX_DIR.mkdir(exist_ok=True)

# Create directories on import
Config.ensure_dirs()
