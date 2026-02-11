"""PDF processing and text extraction."""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from config import Config


@dataclass
class TextChunk:
    """Represents a chunk of text from a PDF."""
    text: str
    page_num: int
    chunk_id: int
    source_file: str
    metadata: Dict[str, Any]


class PDFProcessor:
    """Process PDFs and extract text chunks."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """Initialize PDF processor.
        
        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters
        """
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def extract_text_by_page(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract text from PDF, organized by page.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dicts with page number and text
        """
        try:
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():  # Only include non-empty pages
                    pages.append({
                        "page_num": page_num,
                        "text": text
                    })
            
            doc.close()
            return pages
            
        except Exception as e:
            print(f"Error extracting pages from {pdf_path}: {e}")
            return []
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                for delimiter in ['. ', '.\n', '! ', '?\n', '? ']:
                    last_delim = chunk.rfind(delimiter)
                    if last_delim > self.chunk_size * 0.5:  # At least 50% through
                        chunk = chunk[:last_delim + 1]
                        break
            
            chunks.append(chunk.strip())
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def process_pdf(self, pdf_path: Path) -> List[TextChunk]:
        """Process a PDF into text chunks with metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        pages = self.extract_text_by_page(pdf_path)
        
        chunk_counter = 0
        
        for page_data in pages:
            page_num = page_data["page_num"]
            page_text = page_data["text"]
            
            # Chunk the page text
            page_chunks = self.chunk_text(page_text)
            
            for chunk_text in page_chunks:
                if chunk_text.strip():  # Skip empty chunks
                    chunk = TextChunk(
                        text=chunk_text,
                        page_num=page_num,
                        chunk_id=chunk_counter,
                        source_file=pdf_path.name,
                        metadata={
                            "file_path": str(pdf_path),
                            "file_name": pdf_path.name,
                            "page": page_num,
                            "chunk_id": chunk_counter
                        }
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
        
        return chunks
    
    def yield_text_by_page(self, pdf_path: Path):
        """Yield text from PDF page by page (generator)."""
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    yield {
                        "page_num": page_num,
                        "text": text
                    }
            doc.close()
        except Exception as e:
            print(f"Error extracting pages from {pdf_path}: {e}")

    def process_pdf_generator(self, pdf_path: Path):
        """Yield chunks from a PDF (generator)."""
        chunk_counter = 0
        for page_data in self.yield_text_by_page(pdf_path):
            page_num = page_data["page_num"]
            page_text = page_data["text"]
            
            page_chunks = self.chunk_text(page_text)
            
            for chunk_text in page_chunks:
                if chunk_text.strip():
                    yield TextChunk(
                        text=chunk_text,
                        page_num=page_num,
                        chunk_id=chunk_counter,
                        source_file=pdf_path.name,
                        metadata={
                            "file_path": str(pdf_path),
                            "file_name": pdf_path.name,
                            "page": page_num,
                            "chunk_id": chunk_counter
                        }
                    )
                    chunk_counter += 1

    def process_directory_generator(self, directory: Path = None):
        """Yield chunks from all PDFs in a directory."""
        directory = directory or Config.PDF_DIR
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory}")
            return
        
        print(f"Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            print(f"Processing: {pdf_path.name}")
            yield from self.process_pdf_generator(pdf_path)
