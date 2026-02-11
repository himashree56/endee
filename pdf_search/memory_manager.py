import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

class MemoryManager:
    """Manages personal research memory for the user."""
    
    def __init__(self, memory_file: str = "user_memory.json"):
        """Initialize memory manager."""
        from config import Config
        self.memory_file = Config.DATA_DIR / memory_file
        print(f"[MemoryManager] Using memory file: {self.memory_file}")
        self.memory = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file and migrate if needed."""
        # Migration: Check if old file exists in CWD and move it
        if not self.memory_file.exists() and os.path.exists("user_memory.json"):
            print("[MemoryManager] Migrating old user_memory.json to data dir...")
            try:
                with open("user_memory.json", "r") as f:
                    old_data = json.load(f)
                with open(self.memory_file, "w") as f:
                    json.dump(old_data, f, indent=2)
                # optionally delete old file
            except Exception as e:
                print(f"Error migrating memory: {e}")

        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                
                # Migrate
                memory, changed = self._migrate_memory(memory)
                if changed:
                    with open(self.memory_file, 'w') as f:
                        json.dump(memory, f, indent=2)
                
                return memory
            except Exception as e:
                print(f"Error loading memory: {e}")
                return self._init_empty_memory()
        else:
            return self._init_empty_memory()
            
    def _migrate_memory(self, memory: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """Migrate memory to latest schema (add IDs and titles)."""
        interactions = memory.get("interactions", [])
        changed = False
        
        for interaction in interactions:
            if "id" not in interaction:
                interaction["id"] = str(uuid.uuid4())
                changed = True
            if "title" not in interaction:
                interaction["title"] = interaction.get("question", "Untitled Interaction")
                changed = True
                
        return memory, changed

    def _init_empty_memory(self) -> Dict[str, Any]:
        """Initialize empty memory structure."""
        return {
            "interactions": [],
            "topics_explored": [],
            "verified_facts": [],
            "last_updated": datetime.now().isoformat()
        }
        
    def save_memory(self):
        """Save memory to file."""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
            
    def add_interaction(self, question: str, answer: str, topics: List[str] = None, sources: List[str] = None):
        """Add an interaction to memory."""
        interaction = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "title": question, # Default title is the question
            "answer": answer, # Store full answer (or truncate if too huge, but usually OK)
            "topics": topics or [],
            "sources": sources or []
        }
        self.memory["interactions"].append(interaction)
        
        # Update topics
        if topics:
            existing_topics = set(self.memory["topics_explored"])
            for topic in topics:
                if topic not in existing_topics:
                    self.memory["topics_explored"].append(topic)
        
        self.save_memory()
        
    def delete_interaction(self, interaction_id: str) -> bool:
        """Delete an interaction by ID."""
        original_count = len(self.memory["interactions"])
        self.memory["interactions"] = [
            i for i in self.memory["interactions"] 
            if i.get("id") != interaction_id
        ]
        if len(self.memory["interactions"]) < original_count:
            self.save_memory()
            return True
        return False
        
    def update_interaction(self, interaction_id: str, title: str) -> bool:
        """Update an interaction's title."""
        for interaction in self.memory["interactions"]:
            if interaction.get("id") == interaction_id:
                interaction["title"] = title
                self.save_memory()
                return True
        return False
        
    def clear_history(self):
        """Clear all interactions and research context."""
        self.memory["interactions"] = []
        self.memory["topics_explored"] = []
        self.memory["verified_facts"] = []
        self.save_memory()

    def get_context(self, limit: int = 5) -> str:
        """Get recent context formatted for LLM."""
        recent_interactions = self.memory["interactions"][-limit:]
        if not recent_interactions:
            return "No previous research context."
        
        context = "User's Research History:\n"
        
        # Topics
        topics = self.memory["topics_explored"]
        if topics:
            context += f"Explore Topics: {', '.join(topics[-10:])}\n"
            
        # Recent Q&A
        context += "\nRecent Interactions:\n"
        for i, interaction in enumerate(recent_interactions, 1):
             # Handle missing topics key just in case
            topics_list = interaction.get("topics", [])
            context += f"{i}. Q: {interaction['question']}\n   Topics: {', '.join(topics_list)}\n"
            
        return context
