
import sys
import traceback
from pathlib import Path
from config import Config
from search_engine import SemanticSearchEngine

# Force immediate stdout flushing
import functools
print = functools.partial(print, flush=True)

def reproduce():
    print("--- STARTING REPRODUCTION SCRIPT ---")
    
    # 1. Check Config
    print(f"Config ENDEE_URL: {Config.ENDEE_URL}")
    print(f"Config PDF_DIR: {Config.PDF_DIR}")
    print(f"Config INDEX_DIR: {Config.INDEX_DIR}")
    
    # 2. Initialize Engine
    try:
        engine = SemanticSearchEngine.get_instance()
        print("Engine initialized.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize engine: {e}")
        traceback.print_exc()
        return

    # 3. Check for test PDF
    test_pdf = Config.PDF_DIR / "test_doc.pdf"
    if not test_pdf.exists():
        print(f"WARNING: {test_pdf} does not exist. Creating a dummy PDF...")
        # create a dummy pdf if needed, but we saw it in the file list, so it should be there.
        # If not, we might need to use another one or create one.
        # But wait, looking at file list, 'test_doc.pdf' (868 bytes) exists.
        pass

    # 4. Run Ingestion synchronously
    print(f"Attempting to ingest {test_pdf}...")
    try:
        success, message = engine.ingest_pdfs(test_pdf)
        print(f"Ingestion Result: Success={success}, Message='{message}'")
    except Exception as e:
        print(f"CRITICAL: Ingestion threw exception: {e}")
        traceback.print_exc()

    # 5. Check Index
    print("Checking Index persistence...")
    info = engine.get_index_info()
    print(f"Index Info: {info}")
    
    available_docs = engine.get_available_documents()
    print(f"Available Documents: {available_docs}")
    
    if "test_doc.pdf" in available_docs:
        print("SUCCESS: test_doc.pdf found in index.")
    else:
        print("FAILURE: test_doc.pdf NOT found in index.")

if __name__ == "__main__":
    reproduce()
