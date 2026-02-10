"""RAG Agent using LangGraph for conversational Q&A over PDF documents."""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

from search_engine import SemanticSearchEngine

# Load environment variables
load_dotenv()


class RAGState(TypedDict):
    """State for the RAG agent."""
    question: str
    retrieved_docs: List[Dict[str, Any]]
    context: str
    answer: str
    sources: List[str]


class RAGAgent:
    """Conversational RAG agent using LangGraph."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        self.search_engine = SemanticSearchEngine.get_instance()
        
        # Initialize LLM with OpenRouter
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_headers={
                "HTTP-Referer": "https://pdf-search.ai",
                "X-Title": "PDF Search RAG"
            }
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _retrieval_node(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents based on the question."""
        question = state["question"]
        
        # Search for relevant chunks
        results = self.search_engine.search(question, top_k=5)
        
        # Extract documents and sources
        retrieved_docs = []
        sources = []
        
        for result in results:
            metadata = result.get("metadata", {})
            retrieved_docs.append({
                "text": metadata.get("text", ""),
                "file_name": metadata.get("file_name", "Unknown"),
                "page": metadata.get("page", "?"),
                "score": result.get("score", 0.0)
            })
            
            source = f"{metadata.get('file_name', 'Unknown')} (Page {metadata.get('page', '?')})"
            if source not in sources:
                sources.append(source)
        
        # Build context string
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"[Source {i}: {doc['file_name']}, Page {doc['page']}]\n{doc['text']}\n"
            )
        
        context = "\n".join(context_parts)
        
        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "context": context,
            "sources": sources
        }
    
    def _generation_node(self, state: RAGState) -> RAGState:
        """Generate answer using retrieved context."""
        question = state["question"]
        context = state["context"]
        
        if not context:
            return {
                **state,
                "answer": "I couldn't find any relevant information in the documents to answer your question."
            }
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template("""You are a helpful AI assistant that answers questions based on PDF documents.

Use the following context from the documents to answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Instructions:
1. Answer the question using ONLY the information from the context above
2. Be specific and cite which source you're using when relevant
3. If the context doesn't contain enough information, acknowledge this
4. Keep your answer clear and concise

Answer:""")
        
        # Generate answer
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})
        
        return {
            **state,
            "answer": answer
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("generation", self._generation_node)
        
        # Define edges
        workflow.set_entry_point("retrieval")
        workflow.add_edge("retrieval", "generation")
        workflow.add_edge("generation", END)
        
        return workflow.compile()
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Ask a question and get an answer with sources.
        
        Args:
            question: The question to ask
            
        Returns:
            Dict with 'answer', 'sources', and 'retrieved_docs'
        """
        # Initialize state
        initial_state = {
            "question": question,
            "retrieved_docs": [],
            "context": "",
            "answer": "",
            "sources": []
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "retrieved_docs": result["retrieved_docs"]
        }


# Convenience function for quick usage
def ask_question(question: str) -> str:
    """Quick function to ask a question and get an answer.
    
    Args:
        question: The question to ask
        
    Returns:
        The answer string
    """
    agent = RAGAgent()
    result = agent.ask(question)
    return result["answer"]
