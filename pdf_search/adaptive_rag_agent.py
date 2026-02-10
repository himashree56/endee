"""Adaptive Reasoning RAG Agent with explainability and multi-step reasoning."""
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import os
from dotenv import load_dotenv
from datetime import datetime

from search_engine import SemanticSearchEngine
from memory_manager import MemoryManager

# Load environment variables
load_dotenv()


class AdaptiveRAGState(TypedDict):
    """State for the adaptive RAG graph."""
    question: str
    chat_history: List[Dict[str, str]]
    complexity: str
    query_type: str
    key_entities: List[str]
    requires_multi_hop: bool
    retrieval_iterations: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    reflection_notes: str
    needs_refinement: bool
    refined_query: str
    mode: Literal["standard", "insight"]
    answer: str
    confidence: float
    reasoning_steps: List[Dict[str, str]]
    sources: List[str]
    # Reliability Layer
    critique_report: Dict[str, Any]
    reliability_score: Dict[str, Any]
    truth_label: str


class AdaptiveRAGAgent:
    """Adaptive RAG agent with multi-step reasoning and explainability."""
    
    def __init__(self):
        """Initialize the adaptive RAG agent."""
        self.search_engine = SemanticSearchEngine.get_instance()
        self.memory = MemoryManager()
        self.mode = "standard"
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_headers={
                "HTTP-Referer": "https://pdf-search.ai",
                "X-Title": "Adaptive RAG"
            }
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _query_analysis_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Analyze the query to understand complexity and intent."""
        question = state["question"]
        
        prompt = ChatPromptTemplate.from_template("""You are a query analyzer for a document search system.

User Question: "{question}"

Chat History:
{chat_history}

User Context (Previous Research):
{memory_context}

Analyze this question:

Determine:
1. complexity: "simple" (single fact), "moderate" (multiple facts), or "complex" (requires reasoning/synthesis)
2. query_type: "factual", "analytical", "comparative", or "exploratory"
3. key_entities: List of important terms/concepts
4. requires_multi_hop: true if needs multiple retrieval steps

Output JSON only.""")
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            # Get context from memory
            memory_context = self.memory.get_context(limit=3)
            
            # Format chat history
            chat_history_str = ""
            if "chat_history" in state and state["chat_history"]:
                for msg in state["chat_history"][-3:]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    chat_history_str += f"{role}: {content}\n"
            
            analysis = chain.invoke({
                "question": question, 
                "memory_context": memory_context,
                "chat_history": chat_history_str
            })
        except Exception as e:
            print(f"Error during query analysis: {e}")
            analysis = {
                "complexity": "moderate",
                "query_type": "factual",
                "key_entities": [],
                "requires_multi_hop": False
            }
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Query Analysis",
            "timestamp": datetime.now().isoformat(),
            "details": f"Complexity: {analysis.get('complexity')}, Type: {analysis.get('query_type')}"
        })
        
        return {
            **state,
            "complexity": analysis.get("complexity", "moderate"),
            "query_type": analysis.get("query_type", "factual"),
            "key_entities": analysis.get("key_entities", []),
            "requires_multi_hop": analysis.get("requires_multi_hop", False),
            "reasoning_steps": reasoning_steps
        }
    
    def _initial_retrieval_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Perform initial retrieval from vector database."""
        question = state["question"]
        
        # Determine top_k based on complexity
        complexity = state.get("complexity", "moderate")
        top_k = 3 if complexity == "simple" else 5 if complexity == "moderate" else 8
        
        # Search
        results = self.search_engine.search(question, top_k=top_k)
        
        # Process results
        retrieved_docs = []
        for result in results:
            metadata = result.get("metadata", {})
            retrieved_docs.append({
                "text": metadata.get("text", ""),
                "file_name": metadata.get("file_name", "Unknown"),
                "page": metadata.get("page", "?"),
                "score": result.get("score", 0.0)
            })
        
        # Track iteration
        iterations = state.get("retrieval_iterations", [])
        iterations.append({
            "iteration": len(iterations) + 1,
            "query": question,
            "num_results": len(retrieved_docs),
            "avg_score": sum(d["score"] for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0
        })
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Initial Retrieval",
            "timestamp": datetime.now().isoformat(),
            "details": f"Retrieved {len(retrieved_docs)} documents (avg score: {iterations[-1]['avg_score']:.3f})"
        })
        
        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "retrieval_iterations": iterations,
            "reasoning_steps": reasoning_steps
        }
    
    def _self_reflection_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Reflect on whether retrieved documents can answer the question."""
        question = state["question"]
        docs = state["retrieved_docs"]
        
        if not docs:
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_steps.append({
                "step": "Self-Reflection",
                "timestamp": datetime.now().isoformat(),
                "details": "No documents retrieved - needs refinement"
            })
            return {
                **state,
                "needs_refinement": True,
                "reflection_notes": "No relevant documents found",
                "reasoning_steps": reasoning_steps
            }
        
        # Build context
        context = "\n\n".join([f"Doc {i+1}: {doc['text'][:200]}..." for i, doc in enumerate(docs[:3])])
        
        prompt = ChatPromptTemplate.from_template("""You are evaluating if retrieved documents can answer a question.

Question: {question}

Retrieved Documents:
{context}

Can these documents answer the question adequately?

Respond with JSON:
{{
    "can_answer": true/false,
    "confidence": 0.0-1.0,
    "missing_info": "what's missing if can't answer",
    "refinement_suggestion": "how to refine query if needed"
}}""")
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            reflection = chain.invoke({"question": question, "context": context})
        except Exception as e:
            print(f"Error during self-reflection: {e}")
            reflection = {"can_answer": True, "confidence": 0.7, "missing_info": "", "refinement_suggestion": ""}
        
        needs_refinement = not reflection.get("can_answer", True) and len(state.get("retrieval_iterations", [])) < 2
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Self-Reflection",
            "timestamp": datetime.now().isoformat(),
            "details": f"Can answer: {reflection.get('can_answer')}, Confidence: {reflection.get('confidence'):.2f}"
        })
        
        return {
            **state,
            "needs_refinement": needs_refinement,
            "reflection_notes": reflection.get("missing_info", ""),
            "refined_query": reflection.get("refinement_suggestion", ""),
            "reasoning_steps": reasoning_steps
        }
    
    def _query_refinement_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Refine the query based on reflection."""
        original_question = state["question"]
        refinement_suggestion = state.get("refined_query", "")
        
        if not refinement_suggestion:
            return state
        
        # Use the refined query for next retrieval
        refined_question = f"{original_question} {refinement_suggestion}"
        
        # Search again
        results = self.search_engine.search(refined_question, top_k=5)
        
        # Process results
        new_docs = []
        for result in results:
            metadata = result.get("metadata", {})
            new_docs.append({
                "text": metadata.get("text", ""),
                "file_name": metadata.get("file_name", "Unknown"),
                "page": metadata.get("page", "?"),
                "score": result.get("score", 0.0)
            })
        
        # Merge with existing docs (avoid duplicates)
        existing_texts = {doc["text"] for doc in state["retrieved_docs"]}
        for doc in new_docs:
            if doc["text"] not in existing_texts:
                state["retrieved_docs"].append(doc)
        
        # Track iteration
        iterations = state.get("retrieval_iterations", [])
        iterations.append({
            "iteration": len(iterations) + 1,
            "query": refined_question,
            "num_results": len(new_docs),
            "avg_score": sum(d["score"] for d in new_docs) / len(new_docs) if new_docs else 0
        })
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Query Refinement",
            "timestamp": datetime.now().isoformat(),
            "details": f"Refined query and retrieved {len(new_docs)} additional documents"
        })
        
        return {
            **state,
            "retrieval_iterations": iterations,
            "needs_refinement": False,
            "reasoning_steps": reasoning_steps
        }
    
    def _answer_generation_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Generate answer with multi-step reasoning."""
        question = state["question"]
        docs = state["retrieved_docs"]
        
        if not docs:
            return {
                **state,
                "answer": "I couldn't find relevant information to answer your question.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Build context
        context_parts = []
        sources = []
        for i, doc in enumerate(docs[:5], 1):
            context_parts.append(f"[Source {i}: {doc['file_name']}, Page {doc['page']}, Score: {doc['score']:.3f}]\n{doc['text']}")
            source = f"{doc['file_name']} (Page {doc['page']})"
            if source not in sources:
                sources.append(source)
        
        context = "\n\n".join(context_parts)
        
        # Check if complex reasoning needed
        complexity = state.get("complexity", "moderate")
        
        if complexity == "complex":
            prompt_template = """You are an AI assistant that provides detailed, well-reasoned answers.

Question: {question}

Context from documents:
{context}

Instructions:
1. Think step-by-step about how to answer this question
2. Synthesize information from multiple sources
3. Provide a comprehensive answer with clear reasoning
4. Cite sources using [Source X] notation

Answer:"""
        else:
            prompt_template = """You are an AI assistant that provides clear, accurate answers.

Question: {question}

Context:
{context}

Provide a concise answer using only the information above. Cite sources with [Source X].

Answer:"""
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        answer = chain.invoke({"question": question, "context": context})
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Answer Generation",
            "timestamp": datetime.now().isoformat(),
            "details": f"Generated answer using {len(docs)} documents"
        })
        
        return {
            **state,
            "answer": answer,
            "sources": sources,
            "reasoning_steps": reasoning_steps
        }
    
    def _confidence_scoring_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Calculate confidence score for the answer."""
        docs = state["retrieved_docs"]
        answer = state["answer"]
        
        if not docs or "couldn't find" in answer.lower():
            confidence = 0.0
        else:
            # Calculate based on:
            # 1. Average retrieval score
            # 2. Number of sources
            # 3. Query complexity match
            
            avg_score = sum(d["score"] for d in docs[:5]) / min(len(docs), 5)
            num_sources = len(state.get("sources", []))
            complexity = state.get("complexity", "moderate")
            
            # Base confidence from retrieval scores
            confidence = avg_score * 0.6
            
            # Boost for multiple sources
            if num_sources >= 3:
                confidence += 0.2
            elif num_sources >= 2:
                confidence += 0.1
            
            # Adjust for complexity
            if complexity == "simple" and num_sources >= 1:
                confidence += 0.1
            elif complexity == "complex" and num_sources >= 3:
                confidence += 0.1
            
            # Cap at 0.95
            confidence = min(confidence, 0.95)
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Confidence Scoring",
            "timestamp": datetime.now().isoformat(),
            "details": f"Final confidence: {confidence:.2%}"
        })
        
        return {
            **state,
            "confidence": confidence,
            "reasoning_steps": reasoning_steps
        }
    
    def _critic_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Critique the answer for reliability and truthfulness."""
        question = state["question"]
        answer = state["answer"]
        docs = state["retrieved_docs"]
        
        if not docs or "couldn't find" in answer.lower():
            return {
                **state,
                "truth_label": "uncrtain",
                "reliability_score": {"score": 0, "evidence_strength": "none"},
                "critique_report": {"issues": ["No documents found"]}
            }
        
        # Build context for critique
        context = "\\n\\n".join([f"[Source {i+1}]: {doc['text'][:300]}..." for i, doc in enumerate(docs[:3])])
        
        prompt = ChatPromptTemplate.from_template("""You are a strict fact-checker and critical evaluator.
        
Question: {question}

Answer Generated: {answer}

Source Evidence:
{context}

Task: Evaluate the answer's reliability.
1. Does the evidence support the claims? (0-100 score)
2. Are there any contradictions between sources?
3. Assign a Truth Label: "well-supported", "conditionally-supported", "disputed", or "uncertain".

Output JSON:
{{
    "truth_label": "label",
    "reliability_score": {{
        "score": 0-100,
        "evidence_strength": "high/medium/low",
        "consensus": "high/medium/low/conflict"
    }},
    "critique": {{
        "missing_context": [],
        "assumptions_made": [],
        "contradictions": [],
        "limitations_text": "text to append if needed"
    }}
}}""")
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            critique_result = chain.invoke({"question": question, "answer": answer, "context": context})
        except Exception as e:
            print(f"Error during critique: {e}")
            critique_result = {
                "truth_label": "uncertain",
                "reliability_score": {"score": 50, "evidence_strength": "medium", "consensus": "medium"},
                "critique": {"missing_context": ["Critique generation failed"], "assumptions_made": [], "contradictions": [], "limitations_text": ""}
            }
            
        # Refine Answer if needed
        final_answer = answer
        limitations = critique_result.get("critique", {}).get("limitations_text", "")
        truth_label = critique_result.get("truth_label", "uncertain")
        
        if truth_label != "well-supported" and limitations:
            final_answer += f"\n\n**Limitations & Critical Analysis:**\n{limitations}"
            
        # Save to Memory
        self.memory.add_interaction(
            question=question,
            answer=final_answer,
            topics=state.get("key_entities", []),
            sources=state.get("sources", [])
        )

        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Reliability Critique",
            "timestamp": datetime.now().isoformat(),
            "details": f"Truth Label: {truth_label.upper()}, Saved to Memory."
        })
        
        return {
            **state,
            "answer": final_answer,
            "truth_label": truth_label,
            "reliability_score": critique_result.get("reliability_score", {}),
            "critique_report": critique_result.get("critique", {}),
            "reasoning_steps": reasoning_steps
        }
    def _insight_generation_node(self, state: AdaptiveRAGState) -> AdaptiveRAGState:
        """Generate deep insights instead of direct answers."""
        question = state["question"]
        docs = state["retrieved_docs"]
        
        if not docs:
            return {
                **state,
                "answer": "Insufficient information to generate insights.",
                "confidence": 0.0,
                "sources": []
            }
            
        # Build context
        context_parts = []
        sources = []
        for i, doc in enumerate(docs[:7], 1): # Use more docs for insights
            context_parts.append(f"[Source {i}: {doc['file_name']}]\\n{doc['text']}")
            source = f"{doc['file_name']} (Page {doc['page']})"
            if source not in sources:
                sources.append(source)
        
        context = "\\n\\n".join(context_parts)
        
        prompt = ChatPromptTemplate.from_template("""You are a strategic analyst and concept reliability engine.
        
Topic: {question}

Context:
{context}

Task: Generate a "Deep Insight Report". Do NOT just summarize.
Structure your response as:

### 1. Core Synthesis
(What is the fundamental truth here?)

### 2. Hidden Themes & Patterns
(What connects these documents that isn't obvious?)

### 3. Strategic Implications
(Why does this matter? What are the second-order effects?)

### 4. Conceptual Relationships
(How do these ideas map to broader concepts?)

Provide a sophisticated, professional analysis.""")

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"question": question, "context": context})
        
        # Log reasoning step
        reasoning_steps = state.get("reasoning_steps", [])
        reasoning_steps.append({
            "step": "Insight Generation",
            "timestamp": datetime.now().isoformat(),
            "details": f"Synthesized insights from {len(docs)} documents"
        })
        
        return {
            **state,
            "answer": answer,
            "sources": sources,
            "reasoning_steps": reasoning_steps
        }

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AdaptiveRAGState)
        
        # Add nodes
        workflow.add_node("query_analysis", self._query_analysis_node)
        workflow.add_node("initial_retrieval", self._initial_retrieval_node)
        workflow.add_node("self_reflection", self._self_reflection_node)
        workflow.add_node("query_refinement", self._query_refinement_node)
        workflow.add_node("answer_generation", self._answer_generation_node)
        workflow.add_node("insight_generation", self._insight_generation_node)
        workflow.add_node("confidence_scoring", self._confidence_scoring_node)
        workflow.add_node("critic", self._critic_node)
        
        # Define edges
        workflow.set_entry_point("query_analysis")
        workflow.add_edge("query_analysis", "initial_retrieval")
        workflow.add_edge("initial_retrieval", "self_reflection")
        
        # Conditional: refine or generate (standard vs insight)
        def route_generation(state):
            if state.get("needs_refinement", False):
                return "query_refinement"
            elif state.get("mode") == "insight":
                return "insight_generation"
            else:
                return "answer_generation"

        workflow.add_conditional_edges(
            "self_reflection",
            route_generation,
            {
                "query_refinement": "query_refinement",
                "answer_generation": "answer_generation",
                "insight_generation": "insight_generation"
            }
        )
        
        # Route refinement to appropriate generation
        def route_after_refinement(state):
            return "insight_generation" if state.get("mode") == "insight" else "answer_generation"

        workflow.add_conditional_edges(
            "query_refinement",
            route_after_refinement,
            {
                "answer_generation": "answer_generation",
                "insight_generation": "insight_generation"
            }
        )
        
        workflow.add_edge("answer_generation", "confidence_scoring")
        workflow.add_edge("insight_generation", "confidence_scoring")
        workflow.add_edge("confidence_scoring", "critic")
        workflow.add_edge("critic", END)
        
        return workflow.compile()
    
    def ask(self, question: str, mode: str = "standard", chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Ask a question and get an answer with sources.
        
        Args:
            question: The question to ask
            mode: "standard" or "insight"
            chat_history: List of previous messages
            
        Returns:
            Dict with 'answer', 'sources', 'retrieved_docs', etc.
        """
        self.mode = mode
        
        # Initialize state
        initial_state = {
            "question": question,
            "chat_history": chat_history or [],
            "complexity": "",
            "query_type": "",
            "key_entities": [],
            "requires_multi_hop": False,
            "retrieval_iterations": [],
            "retrieved_docs": [],
            "reflection_notes": "",
            "needs_refinement": False,
            "refined_query": "",
            "answer": "",
            "answer": "",
            "confidence": 0.0,
            "reasoning_steps": [],
            "sources": [],
            "critique_report": {},
            "reliability_score": {},
            "truth_label": "uncertain"
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        return {
            "question": question,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "reasoning_steps": result["reasoning_steps"],
            "sources": result["sources"],
            "query_analysis": {
                "complexity": result.get("complexity", "moderate"),
                "query_type": result.get("query_type", "factual"),
                "key_entities": result.get("key_entities", []),
                "requires_multi_hop": result.get("requires_multi_hop", False)
            },
            "retrieval_iterations": result["retrieval_iterations"],
            "num_documents": len(result["retrieved_docs"]),
            "truth_label": result.get("truth_label", "uncertain"),
            "reliability_score": result.get("reliability_score", {}),
            "critique_report": result.get("critique_report", {})
        }
