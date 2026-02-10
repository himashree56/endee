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
        """Ingest documents from a directory or a single PDF file.
        
        Args:
            pdf_source: Directory containing PDFs or path to a single PDF
            
        Returns:
            (Success boolean, Error message string)
        """
        pdf_source = pdf_source or Config.PDF_DIR
        
        print(f"\n{'='*60}")
        print("PDF INGESTION PIPELINE")
        print(f"{'='*60}\n")
        
        # Step 1: Extract text chunks
        print(f"Step 1: Extracting text from {pdf_source}...")
        if pdf_source.is_file():
            if not pdf_source.suffix.lower() == '.pdf':
                print(f"File {pdf_source} is not a PDF. Skipping.")
                return False, f"File {pdf_source} is not a PDF"
            chunks = self.pdf_processor.process_pdf(pdf_source)
        else:
            chunks = self.pdf_processor.process_directory(pdf_source)
        
        if not chunks:
            print("No chunks extracted. Aborting.")
            return False, "No chunks extracted. File might be empty or unreadable."
        
        print(f"\n[DONE] Extracted {len(chunks)} total chunks from PDFs\n")
        
        # Step 2: Generate embeddings
        try:
            print("Step 2: Generating embeddings...")
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed_batch(texts, show_progress=True)
            print(f"\n[DONE] Generated {len(embeddings)} embeddings\n")
        except Exception as e:
            return False, f"Embedding generation failed: {str(e)}"
        
        # Step 3: Prepare metadata
        print("Step 3: Preparing metadata...")
        metadata = []
        for i, chunk in enumerate(chunks):
            meta = {
                "text": chunk.text,
                "file_name": chunk.source_file,
                "page": chunk.page_num,
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.metadata.get("file_path", "")
            }
            metadata.append(meta)
        print(f"[DONE] Prepared metadata for {len(metadata)} chunks\n")
        
        # Step 4: Insert into Endee
        print("Step 4: Inserting into Endee vector database...")
        # Prepare vector IDs: unique across documents
        # EndeeClient expects a list of IDs or we provide it in metadata
        prepared_metadata = []
        for i, meta in enumerate(metadata):
            uid = f"{meta['file_name']}_{meta['chunk_id']}"
            meta['id'] = uid
            prepared_metadata.append(meta)
            
        try:
            success = self.endee_client.insert_vectors(embeddings, prepared_metadata)
        except Exception as e:
            return False, f"Endee insertion exception: {str(e)}"
        
        if success:
            print(f"[DONE] Successfully inserted {len(embeddings)} vectors into Endee\n")
            
            # Update index metadata and full chunk store (APPEND instead of overwrite)
            self._update_index_metadata(chunks)
            self._update_chunk_store(chunks)
            
            print(f"{'='*60}")
            print("INGESTION COMPLETE")
            print(f"{'='*60}\n")
            return True, "Ingestion successful"
        else:
            print("[ERROR] Failed to insert vectors into Endee\n")
            return False, "Database insertion failed (Check logs/connection)"

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
        chunk_store = self._load_chunk_store()
        hydrated_results = []
        
        for res in results:
            res_id = res["id"]
            if res_id in chunk_store:
                res["metadata"] = chunk_store[res_id]
            else:
                print(f"Warning: Result ID {res_id} not found in local chunk store")
            hydrated_results.append(res)
            
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
