
import time
import json
from pathlib import Path
from unittest.mock import MagicMock
import sys

# Add current directory to sys.path to import modules
sys.path.append(str(Path(__file__).parent))

from search_engine import SemanticSearchEngine
from pdf_processor import TextChunk
from config import Config

# Mock Config to avoid real paths if needed, or just use a temp dir for index
class MockConfig:
    PROJECT_ROOT = Path("test_benchmark_data")
    PDF_DIR = PROJECT_ROOT / "pdfs"
    INDEX_DIR = PROJECT_ROOT / "index"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    EMBEDDING_DIM = 384
    VECTOR_DB_TYPE = "mock"
    ENDEE_URL = "http://mock"

# Setup directories
MockConfig.PROJECT_ROOT.mkdir(exist_ok=True)
MockConfig.INDEX_DIR.mkdir(exist_ok=True)

def benchmark_local_store_updates():
    print("Benchmarking Local Store Updates...")
    
    # Patch Config in search_engine (a bit hacky, but works for quick test)
    # Actually, we can just instantiate SemanticSearchEngine and patch its config/paths
    
    engine = SemanticSearchEngine.get_instance()
    engine.index_file = MockConfig.INDEX_DIR / "document_index.json"
    engine.chunk_store_file = MockConfig.INDEX_DIR / "chunk_store.json"
    
    # Reset files
    if engine.index_file.exists(): engine.index_file.unlink()
    if engine.chunk_store_file.exists(): engine.chunk_store_file.unlink()
    
    # Mock Embedder and EndeeClient to isolate JSON logic
    engine.embedder = MagicMock()
    engine.embedder.model_name = "mock_model"
    engine.embedder.get_dimension.return_value = 384
    engine.embedder.embed_batch.return_value = [] # processed elsewhere? No, used in _process_batch
    # We aren't calling _process_batch directly, we want to test _update_chunk_store specifically
    
    # Generate dummy chunks
    num_batches = 20
    batch_size = 50
    
    total_time = 0
    
    all_chunks = []
    
    for i in range(num_batches):
        chunks = []
        for j in range(batch_size):
            chunk_id = i * batch_size + j
            chunks.append(TextChunk(
                text=f"This is some dummy text for chunk {chunk_id} " * 10,
                page_num=1,
                chunk_id=chunk_id,
                source_file="benchmark_doc.pdf",
                metadata={"file_path": "benchmark_doc.pdf"}
            ))
        all_chunks.extend(chunks)

    # Benchmark: Batch Update (Simulating the fix)
    start_time = time.time()
    try:
        engine._flush_updates_to_disk(all_chunks)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
    end_time = time.time()
    
    print(f"Time to flush {len(all_chunks)} chunks in one go: {end_time - start_time:.4f}s")

if __name__ == "__main__":
    benchmark_local_store_updates()
