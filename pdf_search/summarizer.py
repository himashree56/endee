"""Document summarizer using LLM to summarize documents from vector database."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

from search_engine import SemanticSearchEngine

# Load environment variables
load_dotenv()


class DocumentSummarizer:
    """Summarize documents stored in the vector database."""
    
    def __init__(self):
        """Initialize the document summarizer."""
        self.search_engine = SemanticSearchEngine()
        
        # Initialize LLM with OpenRouter (Using correct params for newer LangChain)
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        
        print(f"Summarizer Config: Model={model}, Base={base_url}")
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://pdf-search.ai",
                "X-Title": "PDF Document Summarizer"
            }
        )
    
    def get_available_documents(self) -> List[str]:
        """Get list of available documents in the index."""
        # Method body is same, just skipped for brevity unless changing
        index_info = self.search_engine.get_index_info()
        if not index_info:
            return []
        
        files = index_info.get("files", {})
        return list(files.keys())
    
    def get_document_chunks(self, filename: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a specific document."""
        chunk_store = self.search_engine._load_chunk_store()
        
        document_chunks = []
        for chunk_id, chunk_data in chunk_store.items():
            if chunk_data.get("file_name") == filename:
                document_chunks.append({
                    "text": chunk_data.get("text", ""),
                    "page": chunk_data.get("page", "?"),
                    "chunk_id": chunk_data.get("chunk_id", "")
                })
        
        document_chunks.sort(key=lambda x: x.get("page", 0))
        return document_chunks
    
    def summarize_document(self, filename: str, max_length: str = "medium") -> Dict[str, Any]:
        """Generate a summary of a document."""
        chunks = self.get_document_chunks(filename)
        
        if not chunks:
            return {
                "filename": filename,
                "summary": "Document not found in the database.",
                "chunk_count": 0,
                "error": "Document not found"
            }
        
        # Combine all chunk texts
        full_text = "\n\n".join([chunk["text"] for chunk in chunks])
        print(f"Summarizing {filename}: {len(chunks)} chunks, {len(full_text)} chars")
        
        length_instructions = {
            "short": "Provide a brief 2-3 sentence summary highlighting the main topic.",
            "medium": "Provide a comprehensive summary in 1-2 paragraphs covering key points and main themes.",
            "long": "Provide a detailed summary with multiple paragraphs covering all major sections, key findings, and important details."
        }
        
        instruction = length_instructions.get(max_length, length_instructions["medium"])
        
        prompt = ChatPromptTemplate.from_template("""You are a helpful AI assistant that creates clear and accurate document summaries.

Document: {filename}

Content:
{content}

Task: {instruction}

Summary:""")
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            summary = chain.invoke({
                "filename": filename,
                "content": full_text[:20000],  # Increased limit slightly, typical 8k context might handle 20k chars roughly but safe is 15-20k
                "instruction": instruction
            })
            
            if not summary:
                summary = "Error: LLM returned empty response."
                
        except Exception as e:
            print(f"Summarization failed: {e}")
            summary = f"Error generating summary: {str(e)}"
        
        return {
            "filename": filename,
            "summary": summary,
            "chunk_count": len(chunks),
            "page_count": len(set(chunk["page"] for chunk in chunks))
        }
    
    def summarize_all_documents(self, max_length: str = "short") -> List[Dict[str, Any]]:
        """Generate summaries for all documents in the database.
        
        Args:
            max_length: Summary length for each document
            
        Returns:
            List of summaries for all documents
        """
        documents = self.get_available_documents()
        summaries = []
        
        for doc in documents:
            summary = self.summarize_document(doc, max_length)
            summaries.append(summary)
        
        return summaries


# Convenience function
def summarize(filename: str, length: str = "medium") -> str:
    """Quick function to summarize a document.
    
    Args:
        filename: Name of the document
        length: Summary length ("short", "medium", "long")
        
    Returns:
        Summary text
    """
    summarizer = DocumentSummarizer()
    result = summarizer.summarize_document(filename, length)
    return result["summary"]
