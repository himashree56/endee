import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm

from config import Config
from pdf_processor import PDFProcessor, TextChunk
from embedder import Embedder
from endee_client import EndeeClient


class SemanticSearchEngine:
    """
    Semantic Search Engine for PDF documents.
    Handles ingesting, embedding, and searching.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        if cls._instance is None:
            print("Initializing SemanticSearchEngine Singleton...")
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the search engine."""
        # Ensure only initialized once via get_instance if possible, 
        # but keep __init__ functional for direct usage if needed (though discouraged).
        pass  # Real init logic follows...
        
        self.config = Config
        self.pdf_processor = PDFProcessor()
        self.embedder = Embedder()
        
        # Select Vector DB based on config
        if Config.VECTOR_DB_TYPE == "qdrant":
            print("Using Local Qdrant Vector DB")
            from local_vector_db import LocalVectorDB
            self.endee_client = LocalVectorDB()
        else:
            print("Using Remote Endee Vector DB")
            self.endee_client = EndeeClient()
            
        self.index_file = Config.INDEX_DIR / "document_index.json"
        self.chunk_store_file = Config.INDEX_DIR / "chunk_store.json"
        
    def initialize(self) -> bool:
        """Initialize the search engine (create collection).
        
        Returns:
            True if successful
        """
        print("Initializing Endee collection...")
        dimension = self.embedder.get_dimension()
        return self.endee_client.create_collection(dimension=dimension)
    
    def ingest_pdfs(self, pdf_source: Optional[Path] = None) -> Tuple[bool, str]:
        """Ingest documents using streaming and batching to save memory.
        
        Args:
            pdf_source: Directory containing PDFs or path to a single PDF
            
        Returns:
            (Success boolean, Error message string)
        """
        pdf_source = pdf_source or Config.PDF_DIR
        
        # Ensure collection exists
        if not self.initialize():
            return False, "Failed to initialize/create vector collection"
        
        print(f"\n{'='*60}")
        print("PDF INGESTION PIPELINE (STREAMING)")
        print(f"{'='*60}\n")
        
        # Step 1: Get Generator
        if pdf_source.is_file():
            if not pdf_source.suffix.lower() == '.pdf':
                return False, f"File {pdf_source} is not a PDF"
            chunk_generator = self.pdf_processor.process_pdf_generator(pdf_source)
        else:
            chunk_generator = self.pdf_processor.process_directory_generator(pdf_source)
            
        BATCH_SIZE = 50
        batch = []
        total_ingested = 0
        
        print(f"Starting ingestion with batch size {BATCH_SIZE}...")
        
        try:
            for chunk in chunk_generator:
                batch.append(chunk)
                
                if len(batch) >= BATCH_SIZE:
                    if not self._process_batch(batch):
                        return False, "Batch processing failed (Database Error?)"
                    total_ingested += len(batch)
                    print(f"Processed batch of {len(batch)} chunks (Total: {total_ingested})")
                    batch = [] # Clear memory
            
            # Process remaining chunks
            if batch:
                if not self._process_batch(batch):
                    return False, "Final batch processing failed"
                total_ingested += len(batch)
                print(f"Processed final batch of {len(batch)} chunks")
            
            if total_ingested == 0:
                return False, "No text extracted from documents."
                
            print(f"\n[DONE] Ingestion Complete. Total chunks: {total_ingested}\n")
            return True, f"Ingestion successful ({total_ingested} chunks)"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Ingestion stream failed: {str(e)}"
            
    def _process_batch(self, chunks: List[TextChunk]) -> bool:
        """Process a single batch of chunks: Embed -> Insert -> Save Local."""
        try:
            # 1. Generate Embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed_batch(texts, show_progress=False)
            
            # 2. Prepare Metadata
            metadata = []
            for chunk in chunks:
                meta = {
                    "text": chunk.text,
                    "file_name": chunk.source_file,
                    "page": chunk.page_num,
                    "chunk_id": chunk.chunk_id,
                    "file_path": chunk.metadata.get("file_path", "")
                }
                # Create ID
                meta['id'] = f"{meta['file_name']}_{meta['chunk_id']}"
                metadata.append(meta)
            
            # 3. Insert into Endee
            success = self.endee_client.insert_vectors(embeddings, metadata)
            if not success:
                return False
                
            # 4. Update Local Stores
            self._update_index_metadata(chunks)
            self._update_chunk_store(chunks)
            
            return True
        except Exception as e:
            print(f"Error processing batch: {e}")
            return False

    def _update_chunk_store(self, new_chunks: List[TextChunk]):
        """Append new chunks to local store.
        
        Args:
            new_chunks: List of new text chunks
        """
        store = self._load_chunk_store()
        for chunk in new_chunks:
            # We need a globally unique ID for chunks across all files
            # Using filename + chunk_id as key
            uid = f"{chunk.source_file}_{chunk.chunk_id}"
            store[uid] = {
                "text": chunk.text,
                "file_name": chunk.source_file,
                "page": chunk.page_num,
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.metadata.get("file_path", "")
            }
            
        with open(self.chunk_store_file, 'w') as f:
            json.dump(store, f)
        print(f"[DONE] Updated chunk store with {len(new_chunks)} new chunks")

    def _update_index_metadata(self, new_chunks: List[TextChunk]):
        """Update index metadata with new chunks.
        
        Args:
            new_chunks: List of new text chunks
        """
        metadata = self.get_index_info() or {
            "total_chunks": 0,
            "files": {},
            "embedding_model": self.embedder.model_name,
            "embedding_dimension": self.embedder.get_dimension()
        }
        
        metadata["total_chunks"] += len(new_chunks)
        
        # Update by file
        for chunk in new_chunks:
            filename = chunk.source_file
            if filename not in metadata["files"]:
                metadata["files"][filename] = {
                    "chunks": 0,
                    "pages": [] 
                }
            
            metadata["files"][filename]["chunks"] += 1
            if chunk.page_num not in metadata["files"][filename]["pages"]:
                metadata["files"][filename]["pages"].append(chunk.page_num)
                metadata["files"][filename]["pages"].sort()
        
        # Save to file
        with open(self.index_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[DONE] Updated index metadata at {self.index_file}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_by_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_by_file: Optional filename to filter results
            
        Returns:
            List of search results with metadata and scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Prepare filter
        filter_dict = None
        if filter_by_file:
            filter_dict = {"file_name": filter_by_file}
        
        # Search in Endee
        results = self.endee_client.search(
            query_vector=query_embedding,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        # Hydrate results from local chunk store
        # Hydrate results from local chunk store
        chunk_store = self._load_chunk_store()
        hydrated_results = []
        missing_count = 0
        
        for res in results:
            res_id = res["id"]
            if res_id in chunk_store:
                res["metadata"] = chunk_store[res_id]
                hydrated_results.append(res)
            else:
                missing_count += 1
                # print(f"Warning: Result ID {res_id} not found in local chunk store")
        
        if missing_count > 0:
            print(f"Warning: {missing_count} search results found in DB but missing locally. Index mismatch.")
            
        return hydrated_results

    def _save_chunk_store(self, chunks: List[TextChunk]):
        """Save full chunk text and metadata to local store.
        
        Args:
            chunks: List of text chunks
        """
        store = {}
        for chunk in chunks:
            store[str(chunk.chunk_id)] = {
                "text": chunk.text,
                "file_name": chunk.source_file,
                "page": chunk.page_num,
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.metadata.get("file_path", "")
            }
            
        with open(self.chunk_store_file, 'w') as f:
            json.dump(store, f)
        print(f"[DONE] Saved {len(store)} chunks to {self.chunk_store_file}")

    def _load_chunk_store(self) -> Dict[str, Any]:
        """Load local chunk store.
        
        Returns:
            Dict of chunk_id -> metadata
        """
        if self.chunk_store_file.exists():
            with open(self.chunk_store_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_index_metadata(self, chunks: List[TextChunk]):
        """Save index metadata to file.
        
        Args:
            chunks: List of text chunks
        """
        metadata = {
            "total_chunks": len(chunks),
            "files": {},
            "embedding_model": self.embedder.model_name,
            "embedding_dimension": self.embedder.get_dimension()
        }
        
        # Aggregate by file
        for chunk in chunks:
            filename = chunk.source_file
            if filename not in metadata["files"]:
                metadata["files"][filename] = {
                    "chunks": 0,
                    "pages": set()
                }
            
            metadata["files"][filename]["chunks"] += 1
            metadata["files"][filename]["pages"].add(chunk.page_num)
        
        # Convert sets to lists for JSON serialization
        for file_data in metadata["files"].values():
            file_data["pages"] = sorted(list(file_data["pages"]))
        
        # Save to file
        with open(self.index_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Saved index metadata to {self.index_file}")
    
    def get_index_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current index.
        
        Returns:
            Index metadata or None
        """
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_available_documents(self) -> List[str]:
        """Get list of available documents in the index.
        
        Returns:
            List of filenames
        """
        info = self.get_index_info()
        if info and "files" in info:
            return list(info["files"].keys())
        return []
    
    def reset_index(self) -> bool:
        """Delete the collection and reset the index.
        
        Returns:
            True if successful
        """
        print("Resetting index...")
        success = self.endee_client.delete_collection()
        
        if success:
            if self.index_file.exists():
                self.index_file.unlink()
            if self.chunk_store_file.exists():
                self.chunk_store_file.unlink()
            print("[DONE] Index reset complete")
        
        return success
