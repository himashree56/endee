"""Configuration management for PDF semantic search."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Endee Server
    # Use ENDEE_URL if provided, otherwise construct from HOST and PORT
    ENDEE_URL = os.getenv("ENDEE_URL")
    if not ENDEE_URL:
        ENDEE_HOST = os.getenv("ENDEE_HOST", "localhost")
        ENDEE_PORT = int(os.getenv("ENDEE_PORT", "8080"))
        ENDEE_URL = f"http://{ENDEE_HOST}:{ENDEE_PORT}"
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
    
    # PDF Processing
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
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
