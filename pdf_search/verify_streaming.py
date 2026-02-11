
from search_engine import SemanticSearchEngine
from config import Config
from pathlib import Path
import sys

# Force flushing
import functools
print = functools.partial(print, flush=True)

def verify():
    print("--- Verifying Streaming Ingestion with Auto-Collection Create ---")
    engine = SemanticSearchEngine.get_instance()
    
    # Test with test_doc.pdf
    pdf_path = Config.PDF_DIR / "test_doc.pdf"
    if not pdf_path.exists():
        # Try fall back to creating a dummy PDF if not exists?
        # Or check if process_directory works
        print(f"Warning: {pdf_path} not found. Trying directory scan...")
        pdf_path = Config.PDF_DIR
        
    print(f"Ingesting {pdf_path}...")
    success, msg = engine.ingest_pdfs(pdf_path)
    
    print(f"Result: {success} - {msg}")
    
    if success:
        print("SUCCESS: Ingestion works (Collection likely created).")
    else:
        print("FAILURE: Ingestion failed.")
        sys.exit(1)

if __name__ == "__main__":
    verify()
