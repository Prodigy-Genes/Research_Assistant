import os
import json
from datetime import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MemoryStore:
    """Simple JSON-based memory store"""
    
    def __init__(self, file_path: str = "memory_store.json"):
        self.file_path = file_path
        self.memory = self._load_memory()
    
    def _load_memory(self) -> List[Dict[str, Any]]:
        """Load memory from file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
        return []
    
    def save_memory(self) -> None:
        """Save memory to file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def add_entry(self, question: str, answer: str, citations: List[str] = None) -> None:
        """Add a new Q&A entry"""
        entry = {
            "question": question,
            "answer": answer,
            "citations": citations or [],
            "timestamp": datetime.now().isoformat()
        }
        self.memory.append(entry)
        self.save_memory()
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory for relevant entries"""
        query_words = set(query.lower().split())
        scored_entries = []
        
        for entry in self.memory:
            question_words = set(entry["question"].lower().split())
            answer_words = set(entry["answer"].lower().split())
            
            # Simple word overlap scoring
            score = len(query_words & question_words) + 0.5 * len(query_words & answer_words)
            
            if score > 0:
                scored_entries.append((score, entry))
        
        # Sort by score and return top results
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]